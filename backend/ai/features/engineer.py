"""
Feature Engineering Pipeline

Transforms raw OHLCV + technical indicators into a model-ready feature matrix.
Handles:
- Derived feature calculation
- Target variable creation (binary: UP/DOWN)
- Time-series aware train/val/test split (NO random shuffle — prevents look-ahead bias)
- Feature scaling (MinMaxScaler fitted ONLY on training data)
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional
import json
import joblib
import logging

from ai.data.fetcher import fetch_ohlcv
from ai.data.indicators import add_all_indicators
from ai.config import (
    SEQUENCE_LENGTH, TARGET_COLUMN,
    TRAIN_RATIO, VAL_RATIO, TEST_RATIO,
    SAVED_MODELS_DIR, DATA_YEARS,
)

logger = logging.getLogger(__name__)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features on top of OHLCV + technical indicators.
    These capture relationships between indicators and price action.
    """
    df = df.copy()

    # --- Price Returns (percentage change) ---
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_10d"] = df["Close"].pct_change(10)

    # --- Volatility (rolling std of returns) ---
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volatility_20d"] = df["return_1d"].rolling(20).std()

    # --- Moving Average Crossover Signals ---
    # 1 if short MA > long MA (bullish), 0 if not
    if "sma_5" in df.columns and "sma_20" in df.columns:
        df["sma_cross_5_20"] = (df["sma_5"] > df["sma_20"]).astype(int)
    if "sma_50" in df.columns and "sma_200" in df.columns:
        df["sma_cross_50_200"] = (df["sma_50"] > df["sma_200"]).astype(int)

    # --- Bollinger Band Distance (normalized) ---
    if "bb_upper" in df.columns and "bb_lower" in df.columns:
        bb_range = df["bb_upper"] - df["bb_lower"]
        bb_range = bb_range.replace(0, np.nan)
        df["bb_distance"] = (df["Close"] - df["bb_middle"]) / bb_range

    # --- Price vs SMA50 (normalized) ---
    if "sma_50" in df.columns:
        df["price_vs_sma50"] = (df["Close"] - df["sma_50"]) / df["sma_50"]

    # --- Volume Change ---
    df["volume_change"] = df["Volume"].pct_change(1)
    df["volume_change"] = df["volume_change"].replace([np.inf, -np.inf], 0)

    # --- High-Low Range (normalized by close) ---
    df["high_low_range"] = (df["High"] - df["Low"]) / df["Close"]

    # --- Day of Week (cyclical encoding for seasonality) ---
    df["day_of_week_sin"] = np.sin(2 * np.pi * df.index.dayofweek / 5)
    df["day_of_week_cos"] = np.cos(2 * np.pi * df.index.dayofweek / 5)

    return df


def create_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create binary target variable.
    1 = Close price tomorrow > Close price today (UP)
    0 = Close price tomorrow <= Close price today (DOWN)

    Uses shift(-1) to look at NEXT day's close. Last row will be NaN (dropped).
    """
    df = df.copy()
    df[TARGET_COLUMN] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    return df


def prepare_full_dataset(
    symbol: str,
    years: int = DATA_YEARS,
) -> pd.DataFrame:
    """
    Complete pipeline: fetch → indicators → features → target → clean.

    Returns a clean DataFrame ready for splitting and model training.
    """
    logger.info(f"Preparing dataset for {symbol}...")

    # 1. Fetch OHLCV data
    df = fetch_ohlcv(symbol, years=years)
    logger.info(f"  Raw data: {len(df)} rows")

    # 2. Add technical indicators
    df = add_all_indicators(df)

    # 3. Add derived features
    df = build_features(df)

    # 4. Create target variable
    df = create_target(df)

    # 5. Drop rows with NaN (indicator warmup period + last row from target shift)
    initial_len = len(df)
    df = df.dropna()
    logger.info(f"  After cleanup: {len(df)} rows (dropped {initial_len - len(df)} warmup rows)")

    # 6. Check class balance
    up_pct = df[TARGET_COLUMN].mean() * 100
    logger.info(f"  Class balance: UP={up_pct:.1f}%, DOWN={100-up_pct:.1f}%")

    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Get the list of feature columns (everything except OHLCV, Volume, and target).
    """
    exclude = ["Open", "High", "Low", "Close", "Volume", TARGET_COLUMN]
    return [col for col in df.columns if col not in exclude]


def time_series_split(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/val/test sets using TIME-BASED split.
    NO random shuffle — this prevents look-ahead bias.

    Train: first 70% (oldest)
    Val:   next 15%
    Test:  last 15% (newest — simulates real-world future prediction)
    """
    n = len(df)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))

    train = df.iloc[:train_end].copy()
    val = df.iloc[train_end:val_end].copy()
    test = df.iloc[val_end:].copy()

    logger.info(f"  Split: Train={len(train)} | Val={len(val)} | Test={len(test)}")
    logger.info(f"  Train period: {train.index[0].date()} → {train.index[-1].date()}")
    logger.info(f"  Val period:   {val.index[0].date()} → {val.index[-1].date()}")
    logger.info(f"  Test period:  {test.index[0].date()} → {test.index[-1].date()}")

    return train, val, test


def scale_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    save: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, MinMaxScaler]:
    """
    Scale features using MinMaxScaler fitted ONLY on training data.
    This prevents data leakage from validation/test sets.

    Saves scaler and feature column list for inference.
    """
    scaler = MinMaxScaler()

    # Fit on training data ONLY
    train[feature_columns] = scaler.fit_transform(train[feature_columns])
    # Transform val and test using training scaler
    val[feature_columns] = scaler.transform(val[feature_columns])
    test[feature_columns] = scaler.transform(test[feature_columns])

    if save:
        # Save scaler for inference
        scaler_path = SAVED_MODELS_DIR / "scaler.pkl"
        joblib.dump(scaler, scaler_path)
        logger.info(f"  Saved scaler to {scaler_path}")

        # Save feature columns
        cols_path = SAVED_MODELS_DIR / "feature_columns.json"
        with open(cols_path, "w") as f:
            json.dump(feature_columns, f)
        logger.info(f"  Saved feature columns to {cols_path}")

    return train, val, test, scaler


def create_lstm_sequences(
    data: pd.DataFrame,
    feature_columns: list[str],
    sequence_length: int = SEQUENCE_LENGTH,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sliding window sequences for LSTM input.

    The LSTM needs 3D input: (samples, timesteps, features)
    Each sample is a window of 'sequence_length' consecutive days.

    Args:
        data: Scaled DataFrame
        feature_columns: List of feature column names
        sequence_length: Number of past days to include (default: 60)

    Returns:
        X: shape (n_samples, sequence_length, n_features)
        y: shape (n_samples,) — target for the day AFTER each sequence
    """
    features = data[feature_columns].values
    target = data[TARGET_COLUMN].values

    X, y = [], []
    for i in range(sequence_length, len(features)):
        X.append(features[i - sequence_length : i])
        y.append(target[i])

    X = np.array(X)
    y = np.array(y)

    logger.info(f"  LSTM sequences: X={X.shape}, y={y.shape}")
    return X, y


def create_flat_features(
    data: pd.DataFrame,
    feature_columns: list[str],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create flat feature vectors for tree-based models (RF, XGBoost).
    Each row is one day's feature values.

    Returns:
        X: shape (n_samples, n_features)
        y: shape (n_samples,)
    """
    X = data[feature_columns].values
    y = data[TARGET_COLUMN].values

    logger.info(f"  Flat features: X={X.shape}, y={y.shape}")
    return X, y
