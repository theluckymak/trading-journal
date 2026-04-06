"""
Local Training Script — Random Forest + XGBoost
Trains models for the trading journal AI module.
TensorFlow/LSTM skipped (incompatible with Python 3.13) — use Colab for LSTM.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from ta import trend, momentum, volatility, volume
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from xgboost import XGBClassifier
import joblib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================
SYMBOL = "AAPL"  # Primary training symbol
YEARS = 5
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "saved_models")
FIGURES_DIR = os.path.join(SAVE_DIR, "figures")
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Reduced grid for faster local training (~5-10 min instead of 30+)
RF_PARAM_GRID = {
    "n_estimators": [100, 200, 500],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2],
}

XGB_PARAM_GRID = {
    "n_estimators": [100, 300, 500],
    "max_depth": [3, 6, 9],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
}

# ============================================================================
# 1. DATA FETCHING
# ============================================================================
def fetch_data(symbol, years):
    print(f"\n{'='*60}")
    print(f"  STEP 1: Fetching {years} years of data for {symbol}")
    print(f"{'='*60}")
    
    end = datetime.now()
    start = end - timedelta(days=years * 365)
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval="1d", auto_adjust=True)
    
    if df.empty:
        raise ValueError(f"No data for {symbol}")
    
    df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.sort_index().ffill().dropna()
    
    print(f"  ✓ Fetched {len(df)} rows ({df.index[0].date()} → {df.index[-1].date()})")
    return df


# ============================================================================
# 2. TECHNICAL INDICATORS
# ============================================================================
def add_indicators(df):
    print(f"\n{'='*60}")
    print(f"  STEP 2: Computing Technical Indicators")
    print(f"{'='*60}")
    
    df = df.copy()
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]
    
    # Moving Averages
    for p in [5, 10, 20, 50, 200]:
        df[f"sma_{p}"] = close.rolling(p).mean()
    for p in [12, 26]:
        df[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()
    
    # RSI
    df["rsi_14"] = momentum.RSIIndicator(close=close, window=14).rsi()
    
    # MACD
    macd = trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()
    
    # Bollinger Bands
    bb = volatility.BollingerBands(close=close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()
    df["bb_pct"] = bb.bollinger_pband()
    
    # ATR
    df["atr_14"] = volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    
    # Stochastic
    stoch = momentum.StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    
    # OBV
    df["obv"] = volume.OnBalanceVolumeIndicator(close=close, volume=vol).on_balance_volume()
    
    # ADX
    adx = trend.ADXIndicator(high=high, low=low, close=close, window=14)
    df["adx_14"] = adx.adx()
    
    # CCI
    df["cci_20"] = trend.CCIIndicator(high=high, low=low, close=close, window=20).cci()
    
    # Williams %R
    df["willr_14"] = momentum.WilliamsRIndicator(high=high, low=low, close=close, lbp=14).williams_r()
    
    # ROC
    df["roc_10"] = momentum.ROCIndicator(close=close, window=10).roc()
    
    n_indicators = len([c for c in df.columns if c not in ["Open", "High", "Low", "Close", "Volume"]])
    print(f"  ✓ Added {n_indicators} indicator columns")
    return df


# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================
def engineer_features(df):
    print(f"\n{'='*60}")
    print(f"  STEP 3: Engineering Derived Features")
    print(f"{'='*60}")
    
    df = df.copy()
    
    # Price returns
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_10d"] = df["Close"].pct_change(10)
    
    # Volatility
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volatility_20d"] = df["return_1d"].rolling(20).std()
    
    # MA Crossovers
    df["sma_cross_5_20"] = (df["sma_5"] > df["sma_20"]).astype(int)
    df["sma_cross_50_200"] = (df["sma_50"] > df["sma_200"]).astype(int)
    
    # Bollinger distance
    bb_range = df["bb_upper"] - df["bb_lower"]
    bb_range = bb_range.replace(0, np.nan)
    df["bb_distance"] = (df["Close"] - df["bb_middle"]) / bb_range
    
    # Price vs SMA50
    df["price_vs_sma50"] = (df["Close"] - df["sma_50"]) / df["sma_50"]
    
    # Volume change
    df["volume_change"] = df["Volume"].pct_change(1).replace([np.inf, -np.inf], 0)
    
    # High-Low range
    df["high_low_range"] = (df["High"] - df["Low"]) / df["Close"]
    
    # Day of week (cyclical)
    df["day_of_week_sin"] = np.sin(2 * np.pi * df.index.dayofweek / 5)
    df["day_of_week_cos"] = np.cos(2 * np.pi * df.index.dayofweek / 5)
    
    # Target: 1 = next day close > today close
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    
    initial = len(df)
    df = df.dropna()
    
    feature_cols = [c for c in df.columns if c not in ["Open", "High", "Low", "Close", "Volume", "target"]]
    
    up_pct = df["target"].mean() * 100
    print(f"  ✓ {len(feature_cols)} features, {len(df)} samples (dropped {initial-len(df)} warmup rows)")
    print(f"  ✓ Class balance: UP={up_pct:.1f}%, DOWN={100-up_pct:.1f}%")
    print(f"  ✓ Features: {feature_cols}")
    
    return df, feature_cols


# ============================================================================
# 4. SPLIT & SCALE
# ============================================================================
def split_and_scale(df, feature_cols):
    print(f"\n{'='*60}")
    print(f"  STEP 4: Time-Series Split & Scaling")
    print(f"{'='*60}")
    
    n = len(df)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))
    
    train = df.iloc[:train_end].copy()
    val = df.iloc[train_end:val_end].copy()
    test = df.iloc[val_end:].copy()
    
    print(f"  Train: {len(train)} rows ({train.index[0].date()} → {train.index[-1].date()})")
    print(f"  Val:   {len(val)} rows ({val.index[0].date()} → {val.index[-1].date()})")
    print(f"  Test:  {len(test)} rows ({test.index[0].date()} → {test.index[-1].date()})")
    
    # Scale — fit ONLY on train
    scaler = MinMaxScaler()
    train[feature_cols] = scaler.fit_transform(train[feature_cols])
    val[feature_cols] = scaler.transform(val[feature_cols])
    test[feature_cols] = scaler.transform(test[feature_cols])
    
    # Save scaler
    joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.pkl"))
    with open(os.path.join(SAVE_DIR, "feature_columns.json"), "w") as f:
        json.dump(feature_cols, f)
    
    print(f"  ✓ Scaler fitted on training data only (no data leakage)")
    print(f"  ✓ Saved scaler.pkl and feature_columns.json")
    
    # Extract X, y
    X_train, y_train = train[feature_cols].values, train["target"].values
    X_val, y_val = val[feature_cols].values, val["target"].values
    X_test, y_test = test[feature_cols].values, test["target"].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test, scaler


# ============================================================================
# 5. TRAIN RANDOM FOREST
# ============================================================================
def train_random_forest(X_train, y_train, X_val, y_val, feature_cols):
    print(f"\n{'='*60}")
    print(f"  STEP 5: Training Random Forest (GridSearchCV)")
    print(f"{'='*60}")
    
    cv = TimeSeriesSplit(n_splits=5)
    
    grid = GridSearchCV(
        estimator=RandomForestClassifier(random_state=42, n_jobs=-1, class_weight="balanced"),
        param_grid=RF_PARAM_GRID,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
        verbose=1,
    )
    
    print(f"  Searching {np.prod([len(v) for v in RF_PARAM_GRID.values()])} parameter combinations...")
    grid.fit(X_train, y_train)
    
    model = grid.best_estimator_
    print(f"\n  ✓ Best params: {grid.best_params_}")
    print(f"  ✓ Best CV accuracy: {grid.best_score_:.4f}")
    print(f"  ✓ Train accuracy: {model.score(X_train, y_train):.4f}")
    print(f"  ✓ Val accuracy: {model.score(X_val, y_val):.4f}")
    
    # Save
    joblib.dump(model, os.path.join(SAVE_DIR, "rf_model.pkl"))
    print(f"  ✓ Saved rf_model.pkl")
    
    # Feature importance
    importance = dict(zip(feature_cols, [float(v) for v in model.feature_importances_]))
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    return model, importance


# ============================================================================
# 6. TRAIN XGBOOST
# ============================================================================
def train_xgboost(X_train, y_train, X_val, y_val, feature_cols):
    print(f"\n{'='*60}")
    print(f"  STEP 6: Training XGBoost (GridSearchCV)")
    print(f"{'='*60}")
    
    cv = TimeSeriesSplit(n_splits=5)
    
    grid = GridSearchCV(
        estimator=XGBClassifier(random_state=42, eval_metric="logloss", use_label_encoder=False, n_jobs=-1, verbosity=0),
        param_grid=XGB_PARAM_GRID,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
        verbose=1,
    )
    
    print(f"  Searching {np.prod([len(v) for v in XGB_PARAM_GRID.values()])} parameter combinations...")
    grid.fit(X_train, y_train)
    
    model = grid.best_estimator_
    print(f"\n  ✓ Best params: {grid.best_params_}")
    print(f"  ✓ Best CV accuracy: {grid.best_score_:.4f}")
    print(f"  ✓ Train accuracy: {model.score(X_train, y_train):.4f}")
    print(f"  ✓ Val accuracy: {model.score(X_val, y_val):.4f}")
    
    # Save
    model.save_model(os.path.join(SAVE_DIR, "xgb_model.json"))
    print(f"  ✓ Saved xgb_model.json")
    
    # Feature importance
    importance = dict(zip(feature_cols, [float(v) for v in model.feature_importances_]))
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    # SHAP
    shap_importance = None
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_val[:200])
        shap_importance = dict(zip(feature_cols, [float(v) for v in np.abs(sv).mean(axis=0)]))
        shap_importance = dict(sorted(shap_importance.items(), key=lambda x: x[1], reverse=True))
        print(f"  ✓ SHAP values computed")
    except Exception as e:
        print(f"  ⚠ SHAP failed: {e}")
    
    return model, importance, shap_importance


# ============================================================================
# 7. EVALUATION & THESIS FIGURES
# ============================================================================
def evaluate_and_plot(rf_model, xgb_model, X_test, y_test, feature_cols, rf_importance, xgb_importance, shap_importance):
    print(f"\n{'='*60}")
    print(f"  STEP 7: Evaluation & Generating Thesis Figures")
    print(f"{'='*60}")
    
    results = {}
    
    for name, model in [("Random Forest", rf_model), ("XGBoost", xgb_model)]:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)
        
        results[name] = {
            "accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "auc_roc": auc, "y_pred": y_pred, "y_prob": y_prob
        }
        
        print(f"\n  {name} (Test Set):")
        print(f"    Accuracy:  {acc:.4f}")
        print(f"    Precision: {prec:.4f}")
        print(f"    Recall:    {rec:.4f}")
        print(f"    F1-Score:  {f1:.4f}")
        print(f"    AUC-ROC:   {auc:.4f}")
        print(f"\n{classification_report(y_test, y_pred, target_names=['DOWN', 'UP'])}")
    
    # Save metrics
    metrics = {}
    for name in results:
        metrics[name] = {k: float(v) for k, v in results[name].items() if k not in ["y_pred", "y_prob"]}
    with open(os.path.join(SAVE_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    
    # ---- THESIS FIGURES ----
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Figure 1: Model Comparison Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    metric_names = ["accuracy", "precision", "recall", "f1", "auc_roc"]
    x = np.arange(len(metric_names))
    width = 0.35
    rf_vals = [results["Random Forest"][m] for m in metric_names]
    xgb_vals = [results["XGBoost"][m] for m in metric_names]
    bars1 = ax.bar(x - width/2, rf_vals, width, label="Random Forest", color="#2196F3")
    bars2 = ax.bar(x + width/2, xgb_vals, width, label="XGBoost", color="#FF9800")
    ax.set_ylabel("Score")
    ax.set_title("Model Performance Comparison (Test Set)")
    ax.set_xticks(x)
    ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC"])
    ax.legend()
    ax.set_ylim(0, 1)
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.annotate(f'{bar.get_height():.3f}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "model_comparison.png"), dpi=150)
    plt.close()
    print(f"  ✓ Saved model_comparison.png")
    
    # Figure 2 & 3: Confusion Matrices
    for name in ["Random Forest", "XGBoost"]:
        fig, ax = plt.subplots(figsize=(6, 5))
        cm = confusion_matrix(y_test, results[name]["y_pred"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["DOWN", "UP"], yticklabels=["DOWN", "UP"], ax=ax)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(f"Confusion Matrix — {name}")
        plt.tight_layout()
        fname = f"confusion_matrix_{name.lower().replace(' ', '_')}.png"
        plt.savefig(os.path.join(FIGURES_DIR, fname), dpi=150)
        plt.close()
        print(f"  ✓ Saved {fname}")
    
    # Figure 4: ROC Curves
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, color in [("Random Forest", "#2196F3"), ("XGBoost", "#FF9800")]:
        fpr, tpr, _ = roc_curve(y_test, results[name]["y_prob"])
        ax.plot(fpr, tpr, color=color, lw=2, label=f'{name} (AUC={results[name]["auc_roc"]:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, label="Random (AUC=0.500)")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves — Model Comparison")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "roc_curves.png"), dpi=150)
    plt.close()
    print(f"  ✓ Saved roc_curves.png")
    
    # Figure 5: Feature Importance — Random Forest (Top 15)
    fig, ax = plt.subplots(figsize=(10, 8))
    top_rf = dict(list(rf_importance.items())[:15])
    bars = ax.barh(list(top_rf.keys())[::-1], list(top_rf.values())[::-1], color="#2196F3")
    ax.set_xlabel("Importance (Gini)")
    ax.set_title("Feature Importance — Random Forest (Top 15)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "feature_importance_rf.png"), dpi=150)
    plt.close()
    print(f"  ✓ Saved feature_importance_rf.png")
    
    # Figure 6: Feature Importance — XGBoost (Top 15)
    fig, ax = plt.subplots(figsize=(10, 8))
    top_xgb = dict(list(xgb_importance.items())[:15])
    bars = ax.barh(list(top_xgb.keys())[::-1], list(top_xgb.values())[::-1], color="#FF9800")
    ax.set_xlabel("Importance (Gain)")
    ax.set_title("Feature Importance — XGBoost (Top 15)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "feature_importance_xgb.png"), dpi=150)
    plt.close()
    print(f"  ✓ Saved feature_importance_xgb.png")
    
    # Figure 7: SHAP Importance (if available)
    if shap_importance:
        fig, ax = plt.subplots(figsize=(10, 8))
        top_shap = dict(list(shap_importance.items())[:15])
        bars = ax.barh(list(top_shap.keys())[::-1], list(top_shap.values())[::-1], color="#4CAF50")
        ax.set_xlabel("Mean |SHAP Value|")
        ax.set_title("SHAP Feature Importance — XGBoost (Top 15)")
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "shap_importance.png"), dpi=150)
        plt.close()
        print(f"  ✓ Saved shap_importance.png")
    
    # Figure 8: Simple backtest equity curve
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, color in [("Random Forest", "#2196F3"), ("XGBoost", "#FF9800")]:
        predictions = results[name]["y_pred"]
        # Simple strategy: buy when model predicts UP, sell when DOWN
        # Return = actual_direction * position
        actual_returns = np.where(y_test == 1, 0.001, -0.001)  # simplified daily returns
        strategy_returns = np.where(predictions == 1, actual_returns, -actual_returns)
        equity = 10000 * np.cumprod(1 + strategy_returns)
        ax.plot(equity, label=f"{name}", color=color, lw=1.5)
    
    # Buy & hold baseline
    bh_returns = np.where(y_test == 1, 0.001, -0.001)
    bh_equity = 10000 * np.cumprod(1 + bh_returns)
    ax.plot(bh_equity, label="Buy & Hold", color="gray", linestyle="--", lw=1)
    
    ax.set_xlabel("Trading Days")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_title("Backtesting — Strategy Equity Curves")
    ax.legend()
    ax.axhline(y=10000, color="black", linestyle=":", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "equity_curves.png"), dpi=150)
    plt.close()
    print(f"  ✓ Saved equity_curves.png")
    
    return results, metrics


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  BEAST VPN Trading Journal — AI Model Training")
    print(f"  Symbol: {SYMBOL} | Period: {YEARS}Y | Python {sys.version.split()[0]}")
    print("  Models: Random Forest + XGBoost (LSTM → Colab)")
    print("=" * 60)
    
    import time
    start_time = time.time()
    
    # Pipeline
    df = fetch_data(SYMBOL, YEARS)
    df = add_indicators(df)
    df, feature_cols = engineer_features(df)
    X_train, y_train, X_val, y_val, X_test, y_test, scaler = split_and_scale(df, feature_cols)
    
    rf_model, rf_importance = train_random_forest(X_train, y_train, X_val, y_val, feature_cols)
    xgb_model, xgb_importance, shap_importance = train_xgboost(X_train, y_train, X_val, y_val, feature_cols)
    
    results, metrics = evaluate_and_plot(rf_model, xgb_model, X_test, y_test, feature_cols, rf_importance, xgb_importance, shap_importance)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"  ✅ TRAINING COMPLETE — {elapsed:.1f} seconds")
    print(f"{'='*60}")
    print(f"\n  Saved files in {SAVE_DIR}:")
    for f in os.listdir(SAVE_DIR):
        if os.path.isfile(os.path.join(SAVE_DIR, f)):
            size = os.path.getsize(os.path.join(SAVE_DIR, f))
            print(f"    {f} ({size/1024:.1f} KB)")
    print(f"\n  Figures in {FIGURES_DIR}:")
    for f in os.listdir(FIGURES_DIR):
        print(f"    {f}")
    
    print(f"\n  Next steps:")
    print(f"  1. Review figures in {FIGURES_DIR}")
    print(f"  2. For LSTM model, use Google Colab with model_training_colab.ipynb")
    print(f"  3. Start backend: cd backend && uvicorn app.main:app")
    print(f"  4. Visit /ai-insights in the frontend")
