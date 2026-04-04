"""
AI Module Configuration
Centralized settings for data fetching, model hyperparameters, and paths.
"""
import os
from pathlib import Path

# --- Paths ---
AI_DIR = Path(__file__).parent
SAVED_MODELS_DIR = AI_DIR / "saved_models"
NOTEBOOKS_DIR = AI_DIR / "notebooks"

SAVED_MODELS_DIR.mkdir(exist_ok=True)

# --- Data Settings ---
DEFAULT_SYMBOLS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X",   # Forex
    "XAUUSD=X",                               # Gold
    "BTC-USD", "ETH-USD",                     # Crypto
    "^GSPC", "^IXIC",                         # Indices (S&P500, NASDAQ)
    "AAPL", "MSFT", "TSLA",                   # Stocks
    "NQ=F", "ES=F",                            # Futures
]

DATA_YEARS = 5                      # Years of historical data to fetch
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# --- Feature Settings ---
SEQUENCE_LENGTH = 60                # Lookback window for LSTM (trading days)
TARGET_COLUMN = "target"            # 1 = price went UP, 0 = DOWN

TECHNICAL_INDICATORS = [
    "sma_5", "sma_10", "sma_20", "sma_50", "sma_200",
    "ema_12", "ema_26",
    "rsi_14",
    "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_pct",
    "atr_14",
    "stoch_k", "stoch_d",
    "obv",
    "adx_14",
    "cci_20",
    "willr_14",
    "roc_10",
]

DERIVED_FEATURES = [
    "return_1d", "return_5d", "return_10d",
    "volatility_10d", "volatility_20d",
    "sma_cross_5_20",       # Golden/death cross signal
    "sma_cross_50_200",
    "bb_distance",           # Normalized distance from middle band
    "price_vs_sma50",        # Price relative to SMA50
    "volume_change",         # Volume % change
    "high_low_range",        # Daily range normalized
]

# --- LSTM Hyperparameters ---
LSTM_CONFIG = {
    "units_layer1": 128,
    "units_layer2": 64,
    "dropout": 0.2,
    "dense_units": 32,
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100,
    "patience": 15,           # Early stopping patience
}

# --- Random Forest Hyperparameters (GridSearchCV ranges) ---
RF_CONFIG = {
    "param_grid": {
        "n_estimators": [100, 200, 500],
        "max_depth": [10, 20, 30, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    },
    "cv_folds": 5,            # TimeSeriesSplit folds
    "n_jobs": -1,
    "random_state": 42,
}

# --- XGBoost Hyperparameters (GridSearchCV ranges) ---
XGB_CONFIG = {
    "param_grid": {
        "n_estimators": [100, 300, 500],
        "max_depth": [3, 6, 9],
        "learning_rate": [0.01, 0.05, 0.1],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    },
    "cv_folds": 5,
    "n_jobs": -1,
    "random_state": 42,
    "eval_metric": "logloss",
    "use_label_encoder": False,
}

# --- Backtesting ---
INITIAL_CAPITAL = 10000.0
COMMISSION_PCT = 0.001              # 0.1% per trade
