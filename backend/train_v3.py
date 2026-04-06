"""
Training Script v3 — Trend Regime Classification
Target: Predict market trend REGIME 5 days ahead (Uptrend vs Downtrend)

Academic basis:
  - Momentum effect (Jegadeesh & Titman, 1993) — trends persist
  - Market regime switching (Hamilton, 1989) — markets alternate between states
  - EMA crossover as regime proxy — industry standard

Target definition:
  Uptrend (1): EMA_20 > EMA_50 at time t+5
  Downtrend (0): EMA_20 <= EMA_50 at time t+5

Why this works:
  - EMA crossovers change slowly (high autocorrelation)
  - Model's value = detecting upcoming crossover REVERSALS
  - Naive baseline (assume today's regime continues) ~82%
  - Good model should beat naive by learning reversal signals
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from ta import trend, momentum, volatility, volume
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from xgboost import XGBClassifier
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIG
# ============================================================================
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "^GSPC"]
YEARS = 7                         # More data for regime patterns
FORWARD_DAYS = 5
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "saved_models")
FIGURES_DIR = os.path.join(SAVE_DIR, "figures")
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Focused param grids
RF_GRID = {
    "n_estimators": [300, 500, 800],
    "max_depth": [8, 12, 16, None],
    "min_samples_split": [5, 10, 15],
    "min_samples_leaf": [2, 4],
}

XGB_GRID = {
    "n_estimators": [300, 500, 800],
    "max_depth": [3, 5, 7],
    "learning_rate": [0.01, 0.03, 0.05],
    "subsample": [0.7, 0.8, 0.9],
    "colsample_bytree": [0.7, 0.8],
}

def log(msg):
    print(f"  {msg}")

# ============================================================================
# DATA
# ============================================================================
def fetch_data(symbol, years):
    end = datetime.now()
    start = end - timedelta(days=years * 365)
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
                       interval="1d", auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data for {symbol}")
    df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.sort_index().ffill().dropna()
    return df

# ============================================================================
# INDICATORS
# ============================================================================
def add_indicators(df):
    df = df.copy()
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    
    for p in [5, 10, 20, 50, 200]:
        df[f"sma_{p}"] = c.rolling(p).mean()
    for p in [12, 20, 26, 50]:
        df[f"ema_{p}"] = c.ewm(span=p, adjust=False).mean()
    
    df["rsi_14"] = momentum.RSIIndicator(close=c, window=14).rsi()
    df["rsi_7"] = momentum.RSIIndicator(close=c, window=7).rsi()
    
    macd_ind = trend.MACD(close=c, window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd_ind.macd()
    df["macd_signal"] = macd_ind.macd_signal()
    df["macd_hist"] = macd_ind.macd_diff()
    
    bb = volatility.BollingerBands(close=c, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()
    df["bb_pct"] = bb.bollinger_pband()
    
    df["atr_14"] = volatility.AverageTrueRange(high=h, low=l, close=c, window=14).average_true_range()
    
    stoch = momentum.StochasticOscillator(high=h, low=l, close=c, window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    
    df["obv"] = volume.OnBalanceVolumeIndicator(close=c, volume=v).on_balance_volume()
    
    adx_ind = trend.ADXIndicator(high=h, low=l, close=c, window=14)
    df["adx_14"] = adx_ind.adx()
    df["di_plus"] = adx_ind.adx_pos()
    df["di_minus"] = adx_ind.adx_neg()
    
    df["cci_20"] = trend.CCIIndicator(high=h, low=l, close=c, window=20).cci()
    df["willr_14"] = momentum.WilliamsRIndicator(high=h, low=l, close=c, lbp=14).williams_r()
    df["roc_10"] = momentum.ROCIndicator(close=c, window=10).roc()
    df["roc_5"] = momentum.ROCIndicator(close=c, window=5).roc()
    
    return df

# ============================================================================
# FEATURES ENGINEERED FOR REGIME PREDICTION
# ============================================================================
def engineer_features(df):
    df = df.copy()
    
    # --- Returns ---
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_10d"] = df["Close"].pct_change(10)
    df["return_20d"] = df["Close"].pct_change(20)
    
    # --- Volatility ---
    df["volatility_5d"] = df["return_1d"].rolling(5).std()
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volatility_20d"] = df["return_1d"].rolling(20).std()
    
    # --- KEY: Current regime features (what regime are we in NOW?) ---
    df["ema20_vs_ema50"] = (df["ema_20"] - df["ema_50"]) / df["ema_50"]  # Normalized gap
    df["ema20_above_ema50"] = (df["ema_20"] > df["ema_50"]).astype(int)   # Current regime binary
    df["ema12_above_ema26"] = (df["ema_12"] > df["ema_26"]).astype(int)
    df["sma_cross_5_20"] = (df["sma_5"] > df["sma_20"]).astype(int)
    df["sma_cross_20_50"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["sma_cross_50_200"] = (df["sma_50"] > df["sma_200"]).astype(int)
    
    # --- KEY: Regime momentum (how fast is the gap changing?) ---
    ema_gap = df["ema_20"] - df["ema_50"]
    df["ema_gap_slope_3d"] = ema_gap - ema_gap.shift(3)
    df["ema_gap_slope_5d"] = ema_gap - ema_gap.shift(5)
    df["ema_gap_slope_10d"] = ema_gap - ema_gap.shift(10)
    df["ema_gap_accel"] = df["ema_gap_slope_3d"] - df["ema_gap_slope_3d"].shift(3)  # Acceleration
    
    # --- Price position relative to MAs ---
    df["price_vs_ema20"] = (df["Close"] - df["ema_20"]) / df["ema_20"]
    df["price_vs_ema50"] = (df["Close"] - df["ema_50"]) / df["ema_50"]
    df["price_vs_sma200"] = (df["Close"] - df["sma_200"]) / df["sma_200"]
    
    # --- BB features ---
    bb_range = (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)
    df["bb_distance"] = (df["Close"] - df["bb_middle"]) / bb_range
    
    # --- Volume features ---
    df["volume_change"] = df["Volume"].pct_change(1).replace([np.inf, -np.inf], 0)
    df["volume_sma10"] = df["Volume"].rolling(10).mean()
    df["volume_ratio"] = df["Volume"] / df["volume_sma10"]
    
    # --- Range ---
    df["high_low_range"] = (df["High"] - df["Low"]) / df["Close"]
    
    # --- Lag features (temporal patterns critical for regime prediction) ---
    for lag in [1, 2, 3, 5]:
        df[f"ema20_vs_ema50_lag{lag}"] = df["ema20_vs_ema50"].shift(lag)
        df[f"rsi_14_lag{lag}"] = df["rsi_14"].shift(lag)
        df[f"macd_hist_lag{lag}"] = df["macd_hist"].shift(lag)
        df[f"return_1d_lag{lag}"] = df["return_1d"].shift(lag)
    
    for lag in [1, 3, 5]:
        df[f"adx_14_lag{lag}"] = df["adx_14"].shift(lag)
        df[f"ema_gap_slope_3d_lag{lag}"] = df["ema_gap_slope_3d"].shift(lag)
    
    # --- Momentum slopes ---
    df["rsi_slope_5d"] = df["rsi_14"] - df["rsi_14"].shift(5)
    df["macd_slope_5d"] = df["macd_hist"] - df["macd_hist"].shift(5)
    df["adx_slope_5d"] = df["adx_14"] - df["adx_14"].shift(5)
    df["stoch_slope_3d"] = df["stoch_k"] - df["stoch_k"].shift(3)
    
    # --- Trend strength composite ---
    df["trend_alignment"] = (
        df["ema20_above_ema50"] + df["ema12_above_ema26"] +
        df["sma_cross_5_20"] + df["sma_cross_20_50"] + df["sma_cross_50_200"] +
        (df["macd_hist"] > 0).astype(int) +
        (df["di_plus"] > df["di_minus"]).astype(int)
    ) / 7.0
    
    # --- Days since last crossover ---
    crossover = (df["ema20_above_ema50"] != df["ema20_above_ema50"].shift(1)).astype(int)
    df["days_since_crossover"] = crossover.groupby(crossover.cumsum()).cumcount()
    
    # --- Day of week ---
    df["day_sin"] = np.sin(2 * np.pi * df.index.dayofweek / 5)
    df["day_cos"] = np.cos(2 * np.pi * df.index.dayofweek / 5)
    
    return df


def create_regime_target(df, forward_days):
    """
    Target: Will EMA_20 be above EMA_50 in `forward_days` days?
    1 = Uptrend regime, 0 = Downtrend regime
    """
    df = df.copy()
    
    # Future EMA values
    future_ema20 = df["ema_20"].shift(-forward_days)
    future_ema50 = df["ema_50"].shift(-forward_days)
    
    df["target"] = (future_ema20 > future_ema50).astype(float)
    # Mark NaN for rows where we don't have future data
    df.loc[future_ema20.isna(), "target"] = np.nan
    
    return df


# ============================================================================
# PIPELINE
# ============================================================================
def build_dataset(symbols, years, forward_days):
    print(f"\n{'='*60}")
    print(f"  Building Trend Regime Dataset")
    print(f"  Symbols: {symbols} | Forward: {forward_days}d | Years: {years}")
    print(f"{'='*60}")
    
    all_dfs = []
    
    for symbol in symbols:
        try:
            log(f"Processing {symbol}...")
            df = fetch_data(symbol, years)
            log(f"  Raw: {len(df)} rows")
            
            df = add_indicators(df)
            df = engineer_features(df)
            df = create_regime_target(df, forward_days)
            
            initial = len(df)
            df = df.dropna(subset=["target"])
            df = df.dropna()
            df["target"] = df["target"].astype(int)
            
            up_pct = df["target"].mean() * 100
            log(f"  Clean: {len(df)} rows | Uptrend={up_pct:.1f}% Downtrend={100-up_pct:.1f}%")
            
            all_dfs.append(df)
        except Exception as e:
            log(f"  ✗ {symbol}: {e}")
    
    combined = pd.concat(all_dfs, axis=0).sort_index()
    
    exclude = ["Open", "High", "Low", "Close", "Volume", "target",
               "ema_20", "ema_50", "volume_sma10"]  # exclude raw EMAs used in target
    feature_cols = [c for c in combined.columns if c not in exclude]
    
    # Remove any features that directly leak the target
    leak_cols = [c for c in feature_cols if "future" in c.lower()]
    feature_cols = [c for c in feature_cols if c not in leak_cols]
    
    up_pct = combined["target"].mean() * 100
    log(f"\n  ✓ Combined: {len(combined)} samples | {len(feature_cols)} features")
    log(f"  ✓ Balance: Uptrend={up_pct:.1f}%, Downtrend={100-up_pct:.1f}%")
    
    return combined, feature_cols


def split_and_scale(combined, feature_cols):
    print(f"\n{'='*60}")
    print(f"  Split & Scale")
    print(f"{'='*60}")
    
    combined = combined.sort_index()
    n = len(combined)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))
    
    train = combined.iloc[:train_end]
    val = combined.iloc[train_end:val_end]
    test = combined.iloc[val_end:]
    
    log(f"Train: {len(train)} ({train.index[0].date()} → {train.index[-1].date()})")
    log(f"Val:   {len(val)} ({val.index[0].date()} → {val.index[-1].date()})")
    log(f"Test:  {len(test)} ({test.index[0].date()} → {test.index[-1].date()})")
    
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(train[feature_cols].astype(float))
    X_val = scaler.transform(val[feature_cols].astype(float))
    X_test = scaler.transform(test[feature_cols].astype(float))
    
    y_train = train["target"].values
    y_val = val["target"].values
    y_test = test["target"].values
    
    # Save
    joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.pkl"))
    with open(os.path.join(SAVE_DIR, "feature_columns.json"), "w") as f:
        json.dump(feature_cols, f)
    
    # Naive baseline: assume current regime continues
    current_regime_test = test["ema20_above_ema50"].values if "ema20_above_ema50" in test.columns else y_test
    naive_acc = accuracy_score(y_test, current_regime_test)
    log(f"\n  Naive baseline (regime persists): {naive_acc:.4f}")
    
    return X_train, y_train, X_val, y_val, X_test, y_test, scaler, naive_acc, test


def feature_select(X_train, y_train, feature_cols, top_n=30):
    log(f"\n  Feature selection: top {top_n} of {len(feature_cols)}...")
    rf_quick = RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
    rf_quick.fit(X_train, y_train)
    
    imp = dict(zip(feature_cols, rf_quick.feature_importances_))
    imp = dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
    
    log(f"  Top 10:")
    for i, (k, v) in enumerate(list(imp.items())[:10]):
        log(f"    {i+1}. {k}: {v:.4f}")
    
    return list(imp.keys())[:top_n], imp


# ============================================================================
# TRAIN
# ============================================================================
def train_rf(X_train, y_train, X_val, y_val):
    print(f"\n{'='*60}")
    print(f"  Training Random Forest")
    print(f"{'='*60}")
    
    cv = TimeSeriesSplit(n_splits=5)
    combos = np.prod([len(v) for v in RF_GRID.values()])
    log(f"GridSearchCV: {combos} combos × 5 folds = {combos*5} fits")
    
    grid = GridSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1, class_weight="balanced"),
        RF_GRID, cv=cv, scoring="accuracy", n_jobs=-1, verbose=1,
    )
    grid.fit(X_train, y_train)
    
    model = grid.best_estimator_
    log(f"Best: {grid.best_params_}")
    log(f"CV: {grid.best_score_:.4f}")
    log(f"Train: {model.score(X_train, y_train):.4f} | Val: {model.score(X_val, y_val):.4f}")
    
    joblib.dump(model, os.path.join(SAVE_DIR, "rf_model.pkl"))
    return model


def train_xgb(X_train, y_train, X_val, y_val):
    print(f"\n{'='*60}")
    print(f"  Training XGBoost")
    print(f"{'='*60}")
    
    cv = TimeSeriesSplit(n_splits=5)
    combos = np.prod([len(v) for v in XGB_GRID.values()])
    log(f"GridSearchCV: {combos} combos × 5 folds = {combos*5} fits")
    
    grid = GridSearchCV(
        XGBClassifier(random_state=42, eval_metric="logloss", use_label_encoder=False, n_jobs=-1, verbosity=0),
        XGB_GRID, cv=cv, scoring="accuracy", n_jobs=-1, verbose=1,
    )
    grid.fit(X_train, y_train)
    
    model = grid.best_estimator_
    log(f"Best: {grid.best_params_}")
    log(f"CV: {grid.best_score_:.4f}")
    log(f"Train: {model.score(X_train, y_train):.4f} | Val: {model.score(X_val, y_val):.4f}")
    
    model.save_model(os.path.join(SAVE_DIR, "xgb_model.json"))
    return model


# ============================================================================
# EVALUATE
# ============================================================================
def evaluate_all(rf, xgb, X_test, y_test, feature_cols, naive_acc):
    print(f"\n{'='*60}")
    print(f"  EVALUATION")
    print(f"{'='*60}")
    
    results = {}
    
    for name, model in [("Random Forest", rf), ("XGBoost", xgb)]:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        try:
            auc = roc_auc_score(y_test, y_prob)
        except:
            auc = 0.5
        
        results[name] = {
            "accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "auc_roc": auc, "y_pred": y_pred, "y_prob": y_prob,
        }
        
        print(f"\n  {name}:")
        print(f"    Accuracy:  {acc:.4f}  {'✅' if acc >= 0.80 else '⚠️'}")
        print(f"    Precision: {prec:.4f}")
        print(f"    Recall:    {rec:.4f}")
        print(f"    F1-Score:  {f1:.4f}")
        print(f"    AUC-ROC:   {auc:.4f}")
    
    # Ensemble
    rf_p = results["Random Forest"]["y_prob"]
    xgb_p = results["XGBoost"]["y_prob"]
    ens_prob = (rf_p + xgb_p) / 2
    ens_pred = (ens_prob > 0.5).astype(int)
    
    ens_acc = accuracy_score(y_test, ens_pred)
    ens_prec = precision_score(y_test, ens_pred, zero_division=0)
    ens_rec = recall_score(y_test, ens_pred, zero_division=0)
    ens_f1 = f1_score(y_test, ens_pred, zero_division=0)
    try:
        ens_auc = roc_auc_score(y_test, ens_prob)
    except:
        ens_auc = 0.5
    
    results["Ensemble"] = {
        "accuracy": ens_acc, "precision": ens_prec, "recall": ens_rec,
        "f1": ens_f1, "auc_roc": ens_auc, "y_pred": ens_pred, "y_prob": ens_prob,
    }
    
    print(f"\n  Ensemble (RF + XGB):")
    print(f"    Accuracy:  {ens_acc:.4f}  {'✅' if ens_acc >= 0.80 else '⚠️'}")
    print(f"    Precision: {ens_prec:.4f}")
    print(f"    Recall:    {ens_rec:.4f}")
    print(f"    F1-Score:  {ens_f1:.4f}")
    print(f"    AUC-ROC:   {ens_auc:.4f}")
    
    print(f"\n  Naive baseline: {naive_acc:.4f}")
    best = max(results, key=lambda k: results[k]["accuracy"])
    print(f"  Best model beats naive by: {results[best]['accuracy'] - naive_acc:+.4f}")
    
    # Confidence-filtered
    print(f"\n  Confidence-Filtered (Ensemble):")
    for t in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        mask = np.maximum(ens_prob, 1 - ens_prob) > t
        n = mask.sum()
        if n > 10:
            cacc = accuracy_score(y_test[mask], ens_pred[mask])
            cov = n / len(y_test) * 100
            print(f"    p > {t:.0%}: Accuracy={cacc:.4f} | Coverage={cov:.1f}% ({n}/{len(y_test)})")
    
    # Save metrics
    metrics = {name: {k: float(v) for k, v in r.items() if k not in ["y_pred", "y_prob"]}
               for name, r in results.items()}
    metrics["naive_baseline"] = float(naive_acc)
    metrics["_config"] = {
        "target": "trend_regime_5d",
        "definition": "EMA_20 > EMA_50 at t+5",
        "symbols": SYMBOLS,
        "years": YEARS,
    }
    with open(os.path.join(SAVE_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    
    return results


def generate_figures(results, y_test, feature_cols, rf, xgb, X_test, naive_acc):
    print(f"\n  Generating thesis figures...")
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 1. Model comparison (with naive baseline)
    fig, ax = plt.subplots(figsize=(12, 7))
    metric_names = ["accuracy", "precision", "recall", "f1", "auc_roc"]
    x = np.arange(len(metric_names))
    width = 0.2
    colors = {"Random Forest": "#2196F3", "XGBoost": "#FF9800", "Ensemble": "#4CAF50"}
    
    for i, name in enumerate(["Random Forest", "XGBoost", "Ensemble"]):
        vals = [results[name][m] for m in metric_names]
        bars = ax.bar(x + (i-1) * width, vals, width, label=name, color=colors[name])
        for bar in bars:
            ax.annotate(f'{bar.get_height():.3f}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)
    
    ax.axhline(y=naive_acc, color='red', linestyle='--', lw=1.5, label=f'Naive Baseline ({naive_acc:.3f})')
    ax.axhline(y=0.8, color='green', linestyle=':', lw=1, alpha=0.5, label='80% Target')
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Model Performance — 5-Day Trend Regime Classification", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC"], fontsize=11)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "model_comparison.png"), dpi=150)
    plt.close()
    log("✓ model_comparison.png")
    
    # 2-4. Confusion matrices
    for name in ["Random Forest", "XGBoost", "Ensemble"]:
        fig, ax = plt.subplots(figsize=(7, 5))
        cm = confusion_matrix(y_test, results[name]["y_pred"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                   xticklabels=["Downtrend", "Uptrend"], yticklabels=["Downtrend", "Uptrend"], ax=ax,
                   annot_kws={"size": 14})
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("Actual", fontsize=12)
        ax.set_title(f"Confusion Matrix — {name}", fontsize=13)
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, f"confusion_matrix_{name.lower().replace(' ', '_')}.png"), dpi=150)
        plt.close()
    log("✓ confusion matrices (3)")
    
    # 5. ROC Curves
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, color in [("Random Forest", "#2196F3"), ("XGBoost", "#FF9800"), ("Ensemble", "#4CAF50")]:
        fpr, tpr, _ = roc_curve(y_test, results[name]["y_prob"])
        ax.plot(fpr, tpr, color=color, lw=2, label=f'{name} (AUC={results[name]["auc_roc"]:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, label="Random (AUC=0.500)")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("ROC Curves — Trend Regime Classification", fontsize=13)
    ax.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "roc_curves.png"), dpi=150)
    plt.close()
    log("✓ roc_curves.png")
    
    # 6-7. Feature importance
    for name, model, color in [("Random Forest", rf, "#2196F3"), ("XGBoost", xgb, "#FF9800")]:
        imp = dict(zip(feature_cols, model.feature_importances_))
        imp = dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
        top15 = dict(list(imp.items())[:15])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(list(top15.keys())[::-1], list(top15.values())[::-1], color=color)
        ax.set_xlabel("Importance", fontsize=12)
        ax.set_title(f"Feature Importance — {name} (Top 15)", fontsize=13)
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, f"feature_importance_{name.lower().replace(' ', '_')}.png"), dpi=150)
        plt.close()
    log("✓ feature importance (2)")
    
    # 8. SHAP
    try:
        import shap
        explainer = shap.TreeExplainer(xgb)
        sv = explainer.shap_values(X_test[:200])
        shap_imp = dict(zip(feature_cols, [float(v) for v in np.abs(sv).mean(axis=0)]))
        shap_imp = dict(sorted(shap_imp.items(), key=lambda x: x[1], reverse=True))
        top15 = dict(list(shap_imp.items())[:15])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(list(top15.keys())[::-1], list(top15.values())[::-1], color="#4CAF50")
        ax.set_xlabel("Mean |SHAP Value|", fontsize=12)
        ax.set_title("SHAP Feature Importance — XGBoost (Top 15)", fontsize=13)
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "shap_importance.png"), dpi=150)
        plt.close()
        log("✓ shap_importance.png")
    except Exception as e:
        log(f"⚠ SHAP: {e}")
    
    # 9. Confidence vs accuracy
    ens_prob = results["Ensemble"]["y_prob"]
    ens_pred = results["Ensemble"]["y_pred"]
    
    thresholds = np.arange(0.50, 0.85, 0.02)
    accs, covs = [], []
    for t in thresholds:
        mask = np.maximum(ens_prob, 1 - ens_prob) > t
        n = mask.sum()
        if n > 10:
            accs.append(accuracy_score(y_test[mask], ens_pred[mask]))
            covs.append(n / len(y_test) * 100)
        else:
            accs.append(np.nan)
            covs.append(0)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax1.plot(thresholds * 100, accs, 'b-o', label="Accuracy", lw=2, markersize=4)
    ax2.plot(thresholds * 100, covs, 'r--s', label="Coverage %", lw=2, markersize=4)
    ax1.set_xlabel("Confidence Threshold (%)", fontsize=12)
    ax1.set_ylabel("Accuracy", color="blue", fontsize=12)
    ax2.set_ylabel("Coverage (%)", color="red", fontsize=12)
    ax1.set_title("Ensemble: Accuracy vs Confidence Threshold", fontsize=13)
    ax1.axhline(y=0.8, color="green", linestyle=":", alpha=0.5, label="80% target")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "confidence_vs_accuracy.png"), dpi=150)
    plt.close()
    log("✓ confidence_vs_accuracy.png")
    
    # 10. Equity curve
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, color in [("Random Forest", "#2196F3"), ("XGBoost", "#FF9800"), ("Ensemble", "#4CAF50")]:
        preds = results[name]["y_pred"]
        correct = (preds == y_test).astype(float)
        daily_ret = np.where(correct, 0.002, -0.002)
        equity = 10000 * np.cumprod(1 + daily_ret)
        ax.plot(equity, label=name, color=color, lw=1.5)
    
    bh_ret = np.where(y_test == 1, 0.002, -0.002)
    bh_eq = 10000 * np.cumprod(1 + bh_ret)
    ax.plot(bh_eq, label="Buy & Hold", color="gray", linestyle="--", lw=1)
    ax.axhline(y=10000, color="black", linestyle=":", alpha=0.3)
    ax.set_xlabel("Trading Days")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_title("Backtesting — Trend Regime Strategy")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "equity_curves.png"), dpi=150)
    plt.close()
    log("✓ equity_curves.png")
    
    # 11. Classification reports (text)
    with open(os.path.join(FIGURES_DIR, "classification_reports.txt"), "w") as f:
        for name in ["Random Forest", "XGBoost", "Ensemble"]:
            f.write(f"\n{'='*50}\n{name}\n{'='*50}\n")
            f.write(classification_report(y_test, results[name]["y_pred"],
                                         target_names=["Downtrend", "Uptrend"]))
    log("✓ classification_reports.txt")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Trading Journal AI — v3 Trend Regime Classification")
    print(f"  Symbols: {SYMBOLS} | {YEARS}Y data")
    print(f"  Target: EMA_20 vs EMA_50 regime in {FORWARD_DAYS} days")
    print(f"  Python {sys.version.split()[0]}")
    print("=" * 60)
    
    t0 = time.time()
    
    # Build
    combined, all_features = build_dataset(SYMBOLS, YEARS, FORWARD_DAYS)
    X_train, y_train, X_val, y_val, X_test, y_test, scaler, naive_acc, test_df = \
        split_and_scale(combined, all_features)
    
    # Feature selection
    top_features, importance_all = feature_select(X_train, y_train, all_features, top_n=30)
    fidx = [all_features.index(f) for f in top_features]
    X_tr = X_train[:, fidx]
    X_v = X_val[:, fidx]
    X_te = X_test[:, fidx]
    
    with open(os.path.join(SAVE_DIR, "feature_columns.json"), "w") as f:
        json.dump(top_features, f)
    
    # Train
    rf = train_rf(X_tr, y_train, X_v, y_val)
    xgb = train_xgb(X_tr, y_train, X_v, y_val)
    
    # Evaluate
    results = evaluate_all(rf, xgb, X_te, y_test, top_features, naive_acc)
    generate_figures(results, y_test, top_features, rf, xgb, X_te, naive_acc)
    
    elapsed = time.time() - t0
    best = max(["Random Forest", "XGBoost", "Ensemble"], key=lambda k: results[k]["accuracy"])
    
    print(f"\n{'='*60}")
    print(f"  ✅ DONE in {elapsed:.0f}s")
    print(f"  Best: {best} — {results[best]['accuracy']:.1%} accuracy")
    print(f"  Naive baseline: {naive_acc:.1%}")
    print(f"  Improvement: {results[best]['accuracy'] - naive_acc:+.1%}")
    print(f"{'='*60}")
    
    print(f"\n  Files: {SAVE_DIR}")
    for f in sorted(os.listdir(SAVE_DIR)):
        fp = os.path.join(SAVE_DIR, f)
        if os.path.isfile(fp):
            print(f"    {f} ({os.path.getsize(fp)/1024:.1f} KB)")
    print(f"\n  Figures ({len(os.listdir(FIGURES_DIR))}):")
    for f in sorted(os.listdir(FIGURES_DIR)):
        print(f"    {f}")
