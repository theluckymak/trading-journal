"""
SMC Pattern Predictor v2 — Binary classification with confidence gating.

Combines 43 SMC features + ~25 technical indicators + lagged features.
Binary: bullish vs bearish. Low confidence → "no_signal" (synthetic neutral).
"""
import os
import numpy as np
import pandas as pd
import joblib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SAVE_DIR = Path(__file__).parent.parent / "saved_models" / "smc"
CLASSES = ["bearish", "bullish"]
CONFIDENCE_THRESHOLD = 0.60

# Technical indicator columns matching training
TA_COLS = [
    "rsi_14", "macd", "macd_signal", "macd_hist",
    "bb_pct", "bb_width", "atr_14",
    "stoch_k", "stoch_d", "adx_14", "di_plus", "di_minus",
    "cci_20", "willr_14", "obv",
    "sma_5", "sma_10", "sma_20", "sma_50",
    "ema_12", "ema_26",
]

LAG_FEATURES = ["pattern_balance", "return_1bar", "ta_rsi_14", "ta_macd", "ta_bb_pct", "ta_stoch_k"]
LAG_PERIODS = [1, 3, 5]


class SMCPredictor:
    """Predicts SMC setups using trained RF/XGBoost v2 binary models."""

    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.feature_cols = None
        self.is_loaded = False

    def load_models(self):
        """Load v2 saved models, scaler, and feature list."""
        try:
            self.rf_model = joblib.load(SAVE_DIR / "smc_rf_v2.pkl")
            self.xgb_model = joblib.load(SAVE_DIR / "smc_xgb_v2.pkl")
            self.scaler = joblib.load(SAVE_DIR / "smc_scaler_v2.pkl")
            with open(SAVE_DIR / "smc_features_v2.json") as f:
                self.feature_cols = json.load(f)
            self.is_loaded = True
            logger.info(f"SMC v2 models loaded ({len(self.feature_cols)} features)")
        except Exception as e:
            logger.warning(f"Failed to load SMC v2 models: {e}")
            self.is_loaded = False

    def predict_symbol(self, symbol: str, interval: str = "1h", days_back: int = 60) -> dict:
        """Fetch live data for a symbol and predict current SMC setup."""
        if not self.is_loaded:
            self.load_models()
        if not self.is_loaded:
            raise RuntimeError("SMC v2 models not loaded")

        import yfinance as yf
        from datetime import datetime, timedelta
        from ai.smc.detector import SMCDetector
        from ai.data.indicators import add_all_indicators

        end = datetime.now()
        start = end - timedelta(days=days_back)
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=interval, auto_adjust=True
        )

        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient data for {symbol} ({len(df)} bars)")

        df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.sort_index().ffill().dropna()

        # Compute technical indicators
        df_ta = add_all_indicators(df)

        # Run SMC detector
        detector = SMCDetector(df, swing_lookback=5, timeframe=interval)
        detector.detect_all()

        # Extract features for the latest bar
        bar_idx = len(df) - 1
        smc_feats = self._extract_smc_features(detector, bar_idx, window=30)
        ta_feats = self._extract_ta_features(df_ta, bar_idx)
        lag_feats = self._extract_lag_features(detector, df_ta, bar_idx, window=30)
        features = {**smc_feats, **ta_feats, **lag_feats}

        # Build feature vector in correct order
        X = np.array([[features.get(c, 0) for c in self.feature_cols]], dtype=float)
        # Replace NaN with 0
        X = np.nan_to_num(X, nan=0.0)
        X_scaled = self.scaler.transform(X)

        rf_proba = self.rf_model.predict_proba(X_scaled)[0]
        xgb_proba = self.xgb_model.predict_proba(X_scaled)[0]

        # Ensemble average (binary: [bearish_prob, bullish_prob])
        avg_proba = (rf_proba + xgb_proba) / 2
        pred_idx = int(np.argmax(avg_proba))
        confidence = float(avg_proba[pred_idx])
        pred_class = CLASSES[pred_idx]

        # Confidence gating: low confidence → no_signal
        if confidence < CONFIDENCE_THRESHOLD:
            display_prediction = "no_signal"
            display_description = "No clear signal — model confidence below threshold, wait for stronger setup"
        else:
            display_prediction = pred_class
            display_description = {
                "bullish": "Bullish setup detected — potential long entry (SMC + TA alignment)",
                "bearish": "Bearish setup detected — potential short entry (SMC + TA alignment)",
            }[pred_class]

        # Get detected patterns summary
        setup = detector.get_setup_at(bar_idx)
        pattern_summary = detector.summary()

        return {
            "symbol": symbol,
            "interval": interval,
            "version": "v2",
            "prediction": display_prediction,
            "raw_prediction": pred_class,
            "confidence": round(confidence, 4),
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "above_threshold": confidence >= CONFIDENCE_THRESHOLD,
            "probabilities": {
                "bearish": round(float(avg_proba[0]), 4),
                "bullish": round(float(avg_proba[1]), 4),
            },
            "models": {
                "random_forest": {
                    "prediction": CLASSES[int(np.argmax(rf_proba))],
                    "probabilities": {c: round(float(rf_proba[i]), 4) for i, c in enumerate(CLASSES)},
                },
                "xgboost": {
                    "prediction": CLASSES[int(np.argmax(xgb_proba))],
                    "probabilities": {c: round(float(xgb_proba[i]), 4) for i, c in enumerate(CLASSES)},
                },
            },
            "smc_setup": {
                "detected": setup is not None,
                "direction": setup["direction"] if setup else None,
                "confidence": round(setup["confidence"], 4) if setup else None,
            } if setup else {"detected": False},
            "pattern_counts": pattern_summary,
            "bars_analyzed": len(df),
            "features_used": len(self.feature_cols),
            "description": display_description,
        }

    def _extract_smc_features(self, detector, bar_idx, window=30):
        """Extract 43 SMC features (same as training)."""
        from ai.smc.detector import PatternType

        start = max(0, bar_idx - window)
        recent = [p for p in detector.patterns if start <= p.index <= bar_idx]

        ptype_counts = {}
        for pt in PatternType:
            ptype_counts[f"count_{pt.value}"] = sum(1 for p in recent if p.pattern_type == pt)

        bull_patterns = sum(1 for p in recent if "bullish" in p.pattern_type.value)
        bear_patterns = sum(1 for p in recent if "bearish" in p.pattern_type.value)

        def bars_since(ptype):
            matching = [p.index for p in recent if p.pattern_type == ptype]
            return bar_idx - max(matching) if matching else window + 1

        dist_features = {
            "dist_sweep_low": bars_since(PatternType.LIQUIDITY_SWEEP_LOW),
            "dist_sweep_high": bars_since(PatternType.LIQUIDITY_SWEEP_HIGH),
            "dist_choch_bull": bars_since(PatternType.CHOCH_BULLISH),
            "dist_choch_bear": bars_since(PatternType.CHOCH_BEARISH),
            "dist_fvg_bull": bars_since(PatternType.FVG_BULLISH),
            "dist_fvg_bear": bars_since(PatternType.FVG_BEARISH),
            "dist_ob_bull": bars_since(PatternType.ORDER_BLOCK_BULLISH),
            "dist_ob_bear": bars_since(PatternType.ORDER_BLOCK_BEARISH),
        }

        bull_strengths = [p.strength for p in recent if "bullish" in p.pattern_type.value]
        bear_strengths = [p.strength for p in recent if "bearish" in p.pattern_type.value]

        setup = detector.get_setup_at(bar_idx, lookback=window)
        has_setup = 1 if setup else 0
        setup_dir = 0
        setup_conf = 0.0
        if setup:
            setup_dir = 1 if setup["direction"] == "bullish" else -1
            setup_conf = setup["confidence"]

        close = detector.close
        high = detector.high
        low = detector.low
        volume = detector.volume

        c = close[bar_idx]
        lookback_closes = close[start:bar_idx + 1]

        ret_1 = (c - close[max(bar_idx - 1, 0)]) / close[max(bar_idx - 1, 0)] if bar_idx > 0 else 0
        ret_5 = (c - close[max(bar_idx - 5, 0)]) / close[max(bar_idx - 5, 0)] if bar_idx > 4 else 0
        ret_10 = (c - close[max(bar_idx - 10, 0)]) / close[max(bar_idx - 10, 0)] if bar_idx > 9 else 0

        if len(lookback_closes) > 2:
            returns = np.diff(lookback_closes) / lookback_closes[:-1]
            vol = float(np.std(returns)) if len(returns) > 1 else 0
        else:
            vol = 0

        hi = high[start:bar_idx + 1].max()
        lo = low[start:bar_idx + 1].min()
        range_pos = (c - lo) / (hi - lo) if hi != lo else 0.5

        vol_window = volume[start:bar_idx + 1]
        vol_avg = vol_window.mean() if len(vol_window) > 0 else 0
        vol_ratio = volume[bar_idx] / vol_avg if vol_avg > 0 else 1.0

        sh = [(i, h) for i, h in detector.swing_highs if start <= i <= bar_idx]
        sl = [(i, l) for i, l in detector.swing_lows if start <= i <= bar_idx]

        hh_count = 0
        ll_count = 0
        if len(sh) >= 2:
            for j in range(1, len(sh)):
                if sh[j][1] > sh[j - 1][1]:
                    hh_count += 1
        if len(sl) >= 2:
            for j in range(1, len(sl)):
                if sl[j][1] < sl[j - 1][1]:
                    ll_count += 1

        return {
            **ptype_counts,
            "bull_pattern_count": bull_patterns,
            "bear_pattern_count": bear_patterns,
            "pattern_balance": bull_patterns - bear_patterns,
            **dist_features,
            "avg_bull_strength": float(np.mean(bull_strengths)) if bull_strengths else 0,
            "avg_bear_strength": float(np.mean(bear_strengths)) if bear_strengths else 0,
            "max_bull_strength": float(max(bull_strengths)) if bull_strengths else 0,
            "max_bear_strength": float(max(bear_strengths)) if bear_strengths else 0,
            "has_setup": has_setup,
            "setup_direction": setup_dir,
            "setup_confidence": setup_conf,
            "return_1bar": ret_1,
            "return_5bar": ret_5,
            "return_10bar": ret_10,
            "volatility": vol,
            "range_position": range_pos,
            "volume_ratio": vol_ratio,
            "higher_highs": hh_count,
            "lower_lows": ll_count,
            "swing_trend": hh_count - ll_count,
            "n_swing_highs": len(sh),
            "n_swing_lows": len(sl),
        }

    def _extract_ta_features(self, df_ta, bar_idx):
        """Extract technical indicator features from pre-computed DataFrame."""
        ta_feats = {}
        for col in TA_COLS:
            if col in df_ta.columns:
                val = df_ta.iloc[bar_idx].get(col, 0)
                ta_feats[f"ta_{col}"] = float(val) if pd.notna(val) else 0.0
            else:
                ta_feats[f"ta_{col}"] = 0.0

        close = df_ta.iloc[bar_idx]["Close"]
        for ma_col in ["sma_20", "sma_50", "ema_12", "ema_26"]:
            if ma_col in df_ta.columns:
                ma_val = df_ta.iloc[bar_idx][ma_col]
                if pd.notna(ma_val) and ma_val != 0:
                    ta_feats[f"ta_price_vs_{ma_col}"] = (close - ma_val) / ma_val
                else:
                    ta_feats[f"ta_price_vs_{ma_col}"] = 0.0

        return ta_feats

    def _extract_lag_features(self, detector, df_ta, bar_idx, window=30):
        """Extract lagged features by computing features at prior bars."""
        lag_feats = {}

        for lag in LAG_PERIODS:
            prev_idx = bar_idx - lag
            if prev_idx < 0:
                for feat in LAG_FEATURES:
                    lag_feats[f"{feat}_lag{lag}"] = 0.0
                continue

            # pattern_balance at prev bar
            start = max(0, prev_idx - window)
            recent = [p for p in detector.patterns if start <= p.index <= prev_idx]
            bull_p = sum(1 for p in recent if "bullish" in p.pattern_type.value)
            bear_p = sum(1 for p in recent if "bearish" in p.pattern_type.value)
            lag_feats[f"pattern_balance_lag{lag}"] = bull_p - bear_p

            # return_1bar at prev bar
            close = detector.close
            if prev_idx > 0:
                lag_feats[f"return_1bar_lag{lag}"] = (close[prev_idx] - close[prev_idx - 1]) / close[prev_idx - 1]
            else:
                lag_feats[f"return_1bar_lag{lag}"] = 0.0

            # TA features at prev bar
            for ta_feat in ["rsi_14", "macd", "bb_pct", "stoch_k"]:
                col = f"ta_{ta_feat}"
                if ta_feat in df_ta.columns and prev_idx < len(df_ta):
                    val = df_ta.iloc[prev_idx].get(ta_feat, 0)
                    lag_feats[f"{col}_lag{lag}"] = float(val) if pd.notna(val) else 0.0
                else:
                    lag_feats[f"{col}_lag{lag}"] = 0.0

        # pattern_balance diffs
        close = detector.close
        start_cur = max(0, bar_idx - window)
        recent_cur = [p for p in detector.patterns if start_cur <= p.index <= bar_idx]
        cur_balance = sum(1 for p in recent_cur if "bullish" in p.pattern_type.value) - \
                      sum(1 for p in recent_cur if "bearish" in p.pattern_type.value)

        for diff_lag in [1, 3]:
            prev_idx = bar_idx - diff_lag
            if prev_idx >= 0:
                start_p = max(0, prev_idx - window)
                recent_p = [p for p in detector.patterns if start_p <= p.index <= prev_idx]
                prev_balance = sum(1 for p in recent_p if "bullish" in p.pattern_type.value) - \
                               sum(1 for p in recent_p if "bearish" in p.pattern_type.value)
                lag_feats[f"pattern_balance_diff{diff_lag}"] = cur_balance - prev_balance
            else:
                lag_feats[f"pattern_balance_diff{diff_lag}"] = 0.0

        return lag_feats

    def get_metrics(self) -> dict:
        """Load saved evaluation metrics."""
        for name in ["smc_metrics_v2.json", "smc_metrics.json"]:
            metrics_path = SAVE_DIR / name
            if metrics_path.exists():
                with open(metrics_path) as f:
                    return json.load(f)
        return {}
