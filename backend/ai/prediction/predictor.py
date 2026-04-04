"""
Prediction Service

Loads trained models and serves real-time predictions.
Used by the FastAPI endpoints.
"""
import numpy as np
import pandas as pd
import json
import joblib
from typing import Optional
from pathlib import Path
import logging

from ai.data.fetcher import fetch_ohlcv
from ai.data.indicators import add_all_indicators
from ai.features.engineer import build_features, get_feature_columns
from ai.config import SAVED_MODELS_DIR, SEQUENCE_LENGTH

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Singleton-style service that loads all trained models into memory
    and serves predictions for any supported symbol.
    """

    def __init__(self):
        self.lstm_model = None
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.feature_columns = None
        self.training_metrics = None
        self.is_loaded = False

    def load_models(self) -> bool:
        """Load all trained models and scaler from disk."""
        try:
            # Load scaler
            scaler_path = SAVED_MODELS_DIR / "scaler.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded scaler")

            # Load feature columns
            cols_path = SAVED_MODELS_DIR / "feature_columns.json"
            if cols_path.exists():
                with open(cols_path) as f:
                    self.feature_columns = json.load(f)
                logger.info(f"Loaded {len(self.feature_columns)} feature columns")

            # Load LSTM
            from ai.models.lstm_model import load_lstm_model
            self.lstm_model = load_lstm_model()
            if self.lstm_model:
                logger.info("Loaded LSTM model")

            # Load Random Forest
            from ai.models.rf_model import load_rf_model
            self.rf_model = load_rf_model()
            if self.rf_model:
                logger.info("Loaded Random Forest model")

            # Load XGBoost
            from ai.models.xgb_model import load_xgb_model
            self.xgb_model = load_xgb_model()
            if self.xgb_model:
                logger.info("Loaded XGBoost model")

            # Load training metrics
            metrics_path = SAVED_MODELS_DIR / "training_metrics.json"
            if metrics_path.exists():
                with open(metrics_path) as f:
                    self.training_metrics = json.load(f)

            self.is_loaded = any([self.lstm_model, self.rf_model, self.xgb_model])
            logger.info(f"Prediction service loaded: {self.is_loaded}")
            return self.is_loaded

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False

    def predict(self, symbol: str) -> dict:
        """
        Generate predictions from all loaded models for a symbol.

        Fetches recent data, computes indicators, and runs inference.
        """
        if not self.is_loaded:
            raise RuntimeError("Models not loaded. Train models first or call load_models().")

        # Fetch recent data (enough for indicator warmup + sequence length)
        df = fetch_ohlcv(symbol, years=1)
        df = add_all_indicators(df)
        df = build_features(df)
        df = df.dropna()

        if len(df) < SEQUENCE_LENGTH + 1:
            raise ValueError(f"Insufficient data for {symbol}. Need at least {SEQUENCE_LENGTH + 1} rows, got {len(df)}")

        # Use saved feature columns to ensure consistency
        feature_cols = self.feature_columns or get_feature_columns(df)
        missing_cols = [c for c in feature_cols if c not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns: {missing_cols}")
            for c in missing_cols:
                df[c] = 0

        # Scale features
        features_df = df[feature_cols].copy()
        if self.scaler:
            features_df[feature_cols] = self.scaler.transform(features_df[feature_cols])

        result = {
            "symbol": symbol,
            "date": str(df.index[-1].date()),
            "prediction_for": str((df.index[-1] + pd.Timedelta(days=1)).date()),
            "models": {},
        }

        # Latest row for flat models
        latest_flat = features_df.iloc[-1:].values

        # LSTM prediction (needs sequence)
        if self.lstm_model:
            seq = features_df.iloc[-SEQUENCE_LENGTH:].values
            seq = seq.reshape(1, SEQUENCE_LENGTH, len(feature_cols))
            proba = float(self.lstm_model.predict(seq, verbose=0)[0][0])
            result["models"]["LSTM"] = {
                "direction": "UP" if proba > 0.5 else "DOWN",
                "confidence": round(proba if proba > 0.5 else 1 - proba, 4),
                "raw_probability": round(proba, 4),
            }

        # Random Forest prediction
        if self.rf_model:
            proba = float(self.rf_model.predict_proba(latest_flat)[0][1])
            result["models"]["Random Forest"] = {
                "direction": "UP" if proba > 0.5 else "DOWN",
                "confidence": round(proba if proba > 0.5 else 1 - proba, 4),
                "raw_probability": round(proba, 4),
            }

        # XGBoost prediction
        if self.xgb_model:
            proba = float(self.xgb_model.predict_proba(latest_flat)[0][1])
            result["models"]["XGBoost"] = {
                "direction": "UP" if proba > 0.5 else "DOWN",
                "confidence": round(proba if proba > 0.5 else 1 - proba, 4),
                "raw_probability": round(proba, 4),
            }

        # Consensus
        directions = [m["direction"] for m in result["models"].values()]
        up_count = directions.count("UP")
        down_count = directions.count("DOWN")
        total = len(directions)
        result["consensus"] = {
            "direction": "UP" if up_count > down_count else "DOWN",
            "agreement": f"{max(up_count, down_count)}/{total}",
        }

        # Current indicators (unscaled)
        latest_raw = df.iloc[-1]
        result["indicators"] = {}
        for col in ["rsi_14", "macd", "macd_signal", "macd_hist",
                     "bb_upper", "bb_middle", "bb_lower", "bb_pct",
                     "atr_14", "adx_14", "stoch_k", "stoch_d",
                     "cci_20", "willr_14", "roc_10",
                     "sma_5", "sma_20", "sma_50", "ema_12", "ema_26"]:
            if col in latest_raw:
                result["indicators"][col] = round(float(latest_raw[col]), 4)

        # Current price info
        result["price"] = {
            "close": round(float(latest_raw["Close"]), 4),
            "open": round(float(latest_raw["Open"]), 4),
            "high": round(float(latest_raw["High"]), 4),
            "low": round(float(latest_raw["Low"]), 4),
            "volume": int(latest_raw.get("Volume", 0)),
        }

        return result

    def get_model_performance(self) -> Optional[dict]:
        """Return training metrics for all models."""
        return self.training_metrics

    def get_feature_importance(self) -> dict:
        """Return feature importance from RF and XGBoost."""
        result = {}
        if self.rf_model and hasattr(self.rf_model, "feature_importances_"):
            importance = self.rf_model.feature_importances_
            if self.feature_columns:
                result["random_forest"] = dict(sorted(
                    zip(self.feature_columns, [float(v) for v in importance]),
                    key=lambda x: x[1], reverse=True,
                ))

        if self.xgb_model and hasattr(self.xgb_model, "feature_importances_"):
            importance = self.xgb_model.feature_importances_
            if self.feature_columns:
                result["xgboost"] = dict(sorted(
                    zip(self.feature_columns, [float(v) for v in importance]),
                    key=lambda x: x[1], reverse=True,
                ))

        return result


# Global singleton instance
prediction_service = PredictionService()
