"""
AI Prediction API Routes

Endpoints for serving ML model predictions, technical indicators,
model performance metrics, feature importance data, and chart pattern analysis.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Predictions"])

# Lazy-loaded prediction services
_service = None
_smc_service = None


def get_prediction_service():
    """Get or initialize the prediction service singleton."""
    global _service
    if _service is None:
        try:
            from ai.prediction.predictor import PredictionService
            _service = PredictionService()
            _service.load_models()
        except Exception as e:
            logger.warning(f"AI models not loaded: {e}")
            _service = None
    return _service


def get_smc_service():
    """Get or initialize the SMC prediction service singleton."""
    global _smc_service
    if _smc_service is None:
        try:
            from ai.smc.predictor import SMCPredictor
            _smc_service = SMCPredictor()
            _smc_service.load_models()
        except Exception as e:
            logger.warning(f"SMC models not loaded: {e}")
            _smc_service = None
    return _smc_service


@router.get("/predict/{symbol}")
async def predict_symbol(symbol: str):
    """
    Get AI predictions for a given trading symbol.

    Returns predictions from all 3 models (LSTM, Random Forest, XGBoost),
    consensus direction, current technical indicators, and price data.

    Examples: /api/ai/predict/EURUSD=X, /api/ai/predict/AAPL, /api/ai/predict/BTC-USD
    """
    service = get_prediction_service()
    if service is None or not service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="AI models not available. Train models first using the Jupyter notebook."
        )

    try:
        result = service.predict(symbol)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    """
    Get current technical indicators for a symbol (without model predictions).
    Useful for displaying indicator panels independently.
    """
    try:
        from ai.data.fetcher import fetch_ohlcv
        from ai.data.indicators import add_all_indicators
        from ai.features.engineer import build_features

        df = fetch_ohlcv(symbol, years=1)
        df = add_all_indicators(df)
        df = build_features(df)
        df = df.dropna()

        if df.empty:
            raise HTTPException(status_code=400, detail=f"No data available for {symbol}")

        latest = df.iloc[-1]

        indicators = {}
        indicator_cols = [
            "rsi_14", "macd", "macd_signal", "macd_hist",
            "bb_upper", "bb_middle", "bb_lower", "bb_pct", "bb_width",
            "atr_14", "adx_14", "di_plus", "di_minus",
            "stoch_k", "stoch_d", "cci_20", "willr_14", "roc_10",
            "sma_5", "sma_10", "sma_20", "sma_50", "sma_200",
            "ema_12", "ema_26", "obv",
            "return_1d", "return_5d", "return_10d",
            "volatility_10d", "volatility_20d",
        ]
        for col in indicator_cols:
            if col in latest:
                indicators[col] = round(float(latest[col]), 6)

        return {
            "symbol": symbol,
            "date": str(df.index[-1].date()),
            "price": {
                "open": round(float(latest["Open"]), 4),
                "high": round(float(latest["High"]), 4),
                "low": round(float(latest["Low"]), 4),
                "close": round(float(latest["Close"]), 4),
                "volume": int(latest.get("Volume", 0)),
            },
            "indicators": indicators,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indicators failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/performance")
async def get_model_performance():
    """
    Get training performance metrics for all models.
    Returns accuracy, precision, recall, F1, AUC-ROC for each model.
    """
    service = get_prediction_service()
    if service is None:
        raise HTTPException(status_code=503, detail="AI models not available.")

    metrics = service.get_model_performance()
    if not metrics:
        raise HTTPException(status_code=404, detail="No training metrics found. Train models first.")

    return metrics


@router.get("/feature-importance")
async def get_feature_importance():
    """
    Get feature importance rankings from Random Forest and XGBoost models.
    Shows which technical indicators have the most predictive power.
    """
    service = get_prediction_service()
    if service is None:
        raise HTTPException(status_code=503, detail="AI models not available.")

    importance = service.get_feature_importance()
    if not importance:
        raise HTTPException(status_code=404, detail="No feature importance data available.")

    return importance


@router.get("/symbols")
async def list_supported_symbols():
    """
    List commonly supported symbols for prediction.
    Any Yahoo Finance symbol is supported, but these are pre-configured defaults.
    """
    from ai.config import DEFAULT_SYMBOLS

    symbols_info = []
    categories = {
        "Forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
        "Commodities": ["XAUUSD=X"],
        "Crypto": ["BTC-USD", "ETH-USD"],
        "Indices": ["^GSPC", "^IXIC"],
        "Stocks": ["AAPL", "MSFT", "TSLA"],
        "Futures": ["NQ=F", "ES=F"],
    }

    return {
        "symbols": DEFAULT_SYMBOLS,
        "categories": categories,
        "note": "Any valid Yahoo Finance symbol can be used for predictions.",
    }


@router.get("/backtest/{symbol}")
async def get_backtest_results(symbol: str):
    """
    Get backtesting results for the trained models.
    Returns equity curves, Sharpe ratio, max drawdown, and total return.
    """
    try:
        import json
        from ai.config import SAVED_MODELS_DIR

        path = SAVED_MODELS_DIR / "backtest_results.json"
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail="No backtest results found. Run the training notebook first."
            )

        with open(path) as f:
            results = json.load(f)

        return {"symbol": symbol, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain")
async def trigger_retrain(
    symbol: str = "EURUSD=X",
    years: int = 5,
    tune: bool = False,
):
    """
    Trigger model retraining (admin only in production).
    This runs the full training pipeline for the specified symbol.

    WARNING: This is a long-running operation. For production use,
    consider running via the Jupyter notebook or a background task.
    """
    try:
        from ai.training.trainer import train_all_models

        result = train_all_models(
            symbol=symbol,
            years=years,
            tune_hyperparams=tune,
            generate_plots=True,
        )

        # Reload models
        global _service
        _service = None
        get_prediction_service()

        return {
            "status": "success",
            "symbol": symbol,
            "comparison": result["comparison"],
        }
    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/smc-analysis/{symbol}")
async def smc_analysis(symbol: str, interval: str = "1h"):
    """
    Get SMC (Smart Money Concepts) pattern analysis for a symbol.
    
    Fetches live OHLCV data, detects SMC patterns (liquidity sweeps,
    CHoCH, FVG, order blocks, breaker blocks), and predicts setup direction
    using trained RF + XGBoost ensemble.
    
    Args:
        symbol: Trading symbol (e.g., EURUSD=X, AAPL, BTC-USD)
        interval: Timeframe for analysis (1h, 4h, 1d). Default: 1h
    """
    smc = get_smc_service()
    if smc is None or not smc.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="SMC models not available. Train the SMC classifier first."
        )
    
    try:
        result = smc.predict_symbol(symbol, interval=interval)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SMC analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/chart-analysis")
async def analyze_chart(file: UploadFile = File(...)):
    """
    Upload a candlestick chart image and get CNN pattern analysis.
    
    Accepts PNG/JPG images. Returns:
    - Predicted pattern class (bullish/bearish/neutral)
    - Confidence score
    - Per-class probabilities
    
    The CNN is trained on SMC (Smart Money Concepts) patterns:
    liquidity sweeps, CHoCH, FVG, order blocks, breaker blocks.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (PNG or JPG)")
    
    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "ai", "saved_models", "cnn", "chart_cnn.pth"
    )
    # Also check flat path (saved_models/chart_cnn.pth)
    if not os.path.exists(model_path):
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "ai", "saved_models", "chart_cnn.pth"
        )
    if not os.path.exists(model_path):
        raise HTTPException(
            status_code=503,
            detail="CNN model not available. Train the chart pattern model first."
        )
    
    tmp_path = None
    try:
        # Save uploaded file to temp
        contents = await file.read()
        suffix = ".png" if "png" in (file.content_type or "") else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        from ai.cnn.model import predict_chart
        result = predict_chart(tmp_path, model_path, device='cpu')
        
        return {
            "prediction": result["prediction"],
            "confidence": round(result["confidence"], 4),
            "probabilities": {k: round(v, 4) for k, v in result["probabilities"].items()},
            "model": "ResNet-18 (transfer learning)",
            "classes": ["bearish", "bullish", "neutral"],
            "description": {
                "bullish": "Bullish SMC setup detected (liquidity sweep + CHoCH + FVG)",
                "bearish": "Bearish SMC setup detected (liquidity sweep + CHoCH + FVG)",
                "neutral": "No clear SMC setup pattern detected",
            }.get(result["prediction"], ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/combined-signal/{symbol}")
async def combined_signal(symbol: str, interval: str = "1h"):
    """
    Get combined signal from both models:
    1. Regime Classifier (daily) → 5-day trend direction
    2. SMC Classifier (hourly) → short-term entry signal
    
    Both models must agree for a strong signal.
    """
    # Get regime prediction (Module 1 — 5-day)
    service = get_prediction_service()
    regime_result = None
    if service and service.is_loaded:
        try:
            regime_result = service.predict(symbol)
        except Exception as e:
            logger.warning(f"Regime prediction failed for {symbol}: {e}")
    
    # Get SMC prediction (Module 2 — hourly)
    smc = get_smc_service()
    smc_result = None
    if smc and smc.is_loaded:
        try:
            smc_result = smc.predict_symbol(symbol, interval=interval)
        except Exception as e:
            logger.warning(f"SMC prediction failed for {symbol}: {e}")
    
    # Determine combined signal
    combined = "no_signal"
    combined_confidence = 0.0
    if regime_result and smc_result:
        regime_dir = regime_result.get("prediction", "")
        smc_dir = smc_result.get("prediction", "no_signal")
        smc_conf = smc_result.get("confidence", 0)
        
        # Map regime prediction to direction
        regime_bullish = regime_dir in ["uptrend", "bullish"]
        regime_bearish = regime_dir in ["downtrend", "bearish"]
        
        if smc_dir == "bullish" and regime_bullish:
            combined = "strong_bullish"
            combined_confidence = smc_conf
        elif smc_dir == "bearish" and regime_bearish:
            combined = "strong_bearish"
            combined_confidence = smc_conf
        elif smc_dir in ["bullish", "bearish"]:
            combined = f"weak_{smc_dir}"
            combined_confidence = smc_conf * 0.7
        else:
            combined = "no_signal"
    
    return {
        "symbol": symbol,
        "combined_signal": combined,
        "combined_confidence": round(combined_confidence, 4),
        "regime_signal": regime_result if regime_result else {"status": "unavailable"},
        "smc_signal": smc_result if smc_result else {"status": "unavailable"},
        "pipeline": {
            "module1": "Trend Regime Classifier (daily, 5-day projection)",
            "module2": f"SMC + TA Fusion Classifier ({interval}, short-term)",
            "combined": "Both models agree → strong signal; disagree → weak signal",
        }
    }


@router.get("/health")
async def ai_health():
    """Check if AI models are loaded and ready."""
    service = get_prediction_service()
    
    smc = get_smc_service()
    
    cnn_model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "ai", "saved_models", "cnn", "chart_cnn.pth"
    )
    
    drl_ready = _drl_service is not None
    
    return {
        "status": "ready" if (service and service.is_loaded) or (smc and smc.is_loaded) or drl_ready else "not_ready",
        "models_loaded": {
            "lstm": service.lstm_model is not None if service else False,
            "random_forest": service.rf_model is not None if service else False,
            "xgboost": service.xgb_model is not None if service else False,
            "cnn_chart": os.path.exists(cnn_model_path),
            "smc_classifier": smc.is_loaded if smc else False,
            "drl_ensemble": drl_ready,
        },
    }


# ── DRL Ensemble Prediction (h1-rebuild models) ──

_drl_service = None

def get_drl_service():
    """Lazy-load the DRL ensemble prediction service."""
    global _drl_service
    if _drl_service is None:
        try:
            from ai.drl.predictor import DRLPredictionService
            _drl_service = DRLPredictionService()
            _drl_service.load_models()
            logger.info("DRL ensemble models loaded")
        except Exception as e:
            logger.warning(f"DRL models not loaded: {e}")
            _drl_service = None
    return _drl_service


@router.get("/drl-predict/{symbol}")
async def drl_predict(symbol: str):
    """
    Get DRL ensemble prediction (PPO + A2C + SAC majority vote).
    Returns signal direction, confidence, individual votes, regime,
    entry score with reasons, risk levels, and event status.
    """
    svc = get_drl_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="DRL models not available")
    try:
        return svc.predict(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"DRL prediction failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(instruments: str = "futures"):
    """
    Get upcoming economic calendar events filtered by instrument group.
    Instrument groups: futures, forex, crypto, stocks
    """
    from datetime import datetime, timedelta

    EVENTS_BY_GROUP = {
        "futures": ["USD", "NQ", "ES", "CL", "GC"],
        "forex": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"],
        "crypto": ["BTC", "ETH", "CRYPTO"],
        "stocks": ["USD", "SPX", "EARNINGS"],
    }

    currencies = EVENTS_BY_GROUP.get(instruments, EVENTS_BY_GROUP["futures"])

    try:
        svc = get_drl_service()
        if svc and hasattr(svc, 'get_upcoming_events'):
            events = svc.get_upcoming_events(currencies)
            return events
    except Exception as e:
        logger.warning(f"Events fetch failed: {e}")

    # Fallback: return static calendar events
    return []


@router.get("/news/{symbol}")
async def get_symbol_news(symbol: str):
    """
    Get recent news for a symbol using yfinance.
    Returns list of news items with title, publisher, time, link, and sentiment.
    """
    try:
        import yfinance as yf
        from datetime import datetime, timezone

        # Map common names to yfinance tickers
        ticker_map = {
            "NQ": "NQ=F", "ES": "ES=F", "YM": "YM=F", "RTY": "RTY=F",
            "CL": "CL=F", "GC": "GC=F",
            "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X", "AUDUSD": "AUDUSD=X",
            "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
            "AAPL": "AAPL", "TSLA": "TSLA", "NVDA": "NVDA", "MSFT": "MSFT",
            "META": "META", "GOOGL": "GOOGL", "AMZN": "AMZN",
        }
        symbol_clean = symbol.replace("/", "").upper()
        ticker_str = ticker_map.get(symbol, ticker_map.get(symbol_clean, symbol))

        ticker = yf.Ticker(ticker_str)
        raw_news = ticker.news if hasattr(ticker, 'news') else []

        if not raw_news:
            return []

        # Bearish/bullish keyword heuristic for sentiment
        bearish = {"fall", "drop", "crash", "decline", "loss", "bear", "sell", "risk",
                   "fear", "recession", "down", "cut", "miss", "warning", "weak", "tariff"}
        bullish = {"rise", "gain", "rally", "bull", "buy", "surge", "profit", "beat",
                   "growth", "up", "strong", "record", "high", "boost", "upgrade"}

        news_items = []
        for item in raw_news[:10]:
            title = item.get("title", "") or item.get("content", {}).get("title", "")
            publisher = item.get("publisher", "") or item.get("content", {}).get("provider", {}).get("displayName", "")
            link = item.get("link", "") or item.get("content", {}).get("canonicalUrl", {}).get("url", "")

            pub_time = ""
            ts = item.get("providerPublishTime") or item.get("content", {}).get("pubDate", "")
            if isinstance(ts, (int, float)):
                pub_time = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%b %d, %H:%M UTC")
            elif isinstance(ts, str) and ts:
                pub_time = ts[:16]

            # Simple sentiment
            title_lower = title.lower()
            b_count = sum(1 for w in bullish if w in title_lower)
            s_count = sum(1 for w in bearish if w in title_lower)
            if b_count > s_count:
                sentiment = "positive"
            elif s_count > b_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            if title:
                news_items.append({
                    "title": title,
                    "publisher": publisher,
                    "time": pub_time,
                    "link": link,
                    "sentiment": sentiment,
                })

        return news_items

    except Exception as e:
        logger.warning(f"News fetch failed for {symbol}: {e}")
        return []
