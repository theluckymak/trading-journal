"""
Module 2B: SMC Tabular Feature Classifier
Extracts numeric SMC features from OHLCV data and trains RF/XGBoost classifiers.
"""
import sys, os
sys.path.insert(0, r"F:\trading-journal\backend")

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import joblib, json, time, warnings
warnings.filterwarnings("ignore")

from ai.smc.detector import SMCDetector, PatternType

SAVE_DIR = r"F:\trading-journal\backend\ai\saved_models\smc"
FIG_DIR  = os.path.join(SAVE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

SYMBOLS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AAPL", "MSFT", "GOOGL",
           "^GSPC", "ES=F", "NQ=F", "BTC-USD", "GC=F", "TSLA"]
WINDOW = 30       # bars to look back for feature extraction
FORWARD = 10      # bars ahead for labeling
INTERVAL = "1h"
DAYS_BACK = 729


def extract_smc_features(df, detector, bar_idx, window=30):
    """Extract numeric SMC features for a single bar."""
    start = max(0, bar_idx - window)
    recent = [p for p in detector.patterns if start <= p.index <= bar_idx]
    
    # Count each pattern type in the window
    ptype_counts = {}
    for pt in PatternType:
        ptype_counts[f"count_{pt.value}"] = sum(1 for p in recent if p.pattern_type == pt)
    
    # Aggregate bullish vs bearish
    bull_patterns = sum(1 for p in recent if "bullish" in p.pattern_type.value)
    bear_patterns = sum(1 for p in recent if "bearish" in p.pattern_type.value)
    
    # Nearest pattern distances (bars since last occurrence)
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
    
    # Pattern strength (average strength of recent patterns)
    bull_strengths = [p.strength for p in recent if "bullish" in p.pattern_type.value]
    bear_strengths = [p.strength for p in recent if "bearish" in p.pattern_type.value]
    
    # Full setup detection
    setup = detector.get_setup_at(bar_idx, lookback=window)
    has_setup = 1 if setup else 0
    setup_dir = 0  # -1 bear, 0 none, 1 bull
    setup_conf = 0.0
    if setup:
        setup_dir = 1 if setup["direction"] == "bullish" else -1
        setup_conf = setup["confidence"]
    
    # Price context features
    close = detector.close
    high = detector.high
    low = detector.low
    volume = detector.volume
    
    c = close[bar_idx]
    lookback_closes = close[start:bar_idx+1]
    
    # Returns over different horizons
    ret_1 = (c - close[max(bar_idx-1, 0)]) / close[max(bar_idx-1, 0)] if bar_idx > 0 else 0
    ret_5 = (c - close[max(bar_idx-5, 0)]) / close[max(bar_idx-5, 0)] if bar_idx > 4 else 0
    ret_10 = (c - close[max(bar_idx-10, 0)]) / close[max(bar_idx-10, 0)] if bar_idx > 9 else 0
    
    # Volatility
    if len(lookback_closes) > 2:
        returns = np.diff(lookback_closes) / lookback_closes[:-1]
        vol = np.std(returns) if len(returns) > 1 else 0
    else:
        vol = 0
    
    # Relative position in range
    hi = high[start:bar_idx+1].max()
    lo = low[start:bar_idx+1].min()
    range_pos = (c - lo) / (hi - lo) if hi != lo else 0.5
    
    # Volume trend
    vol_window = volume[start:bar_idx+1]
    vol_avg = vol_window.mean() if len(vol_window) > 0 else 0
    vol_ratio = volume[bar_idx] / vol_avg if vol_avg > 0 else 1.0
    
    # Swing structure (higher highs / lower lows)
    sh = [(i, h) for i, h in detector.swing_highs if start <= i <= bar_idx]
    sl = [(i, l) for i, l in detector.swing_lows if start <= i <= bar_idx]
    
    hh_count = 0  # Higher highs
    ll_count = 0  # Lower lows
    if len(sh) >= 2:
        for j in range(1, len(sh)):
            if sh[j][1] > sh[j-1][1]: hh_count += 1
    if len(sl) >= 2:
        for j in range(1, len(sl)):
            if sl[j][1] < sl[j-1][1]: ll_count += 1
    
    features = {
        **ptype_counts,
        "bull_pattern_count": bull_patterns,
        "bear_pattern_count": bear_patterns,
        "pattern_balance": bull_patterns - bear_patterns,
        **dist_features,
        "avg_bull_strength": np.mean(bull_strengths) if bull_strengths else 0,
        "avg_bear_strength": np.mean(bear_strengths) if bear_strengths else 0,
        "max_bull_strength": max(bull_strengths) if bull_strengths else 0,
        "max_bear_strength": max(bear_strengths) if bear_strengths else 0,
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
    return features


def build_dataset():
    """Build full tabular dataset from all symbols."""
    all_rows = []
    
    for symbol in SYMBOLS:
        print(f"  {symbol}...", end=" ", flush=True)
        try:
            end = datetime.now()
            start = end - timedelta(days=DAYS_BACK)
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start.strftime("%Y-%m-%d"),
                               end=end.strftime("%Y-%m-%d"),
                               interval=INTERVAL, auto_adjust=True)
            
            if df.empty or len(df) < WINDOW + FORWARD + 50:
                print(f"skip ({len(df)} rows)")
                continue
            
            df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df = df.sort_index().ffill().dropna()
            
            detector = SMCDetector(df, swing_lookback=5, timeframe=INTERVAL)
            detector.detect_all()
            pcount = len(detector.patterns)
            
            n_rows = 0
            for i in range(WINDOW, len(df) - FORWARD, 3):  # step=3 for more data
                features = extract_smc_features(df, detector, i, window=WINDOW)
                
                # Label: same logic as get_label_for_bar but simplified
                future_ret = (detector.close[i + FORWARD] - detector.close[i]) / detector.close[i]
                threshold = 0.006 * detector._tf_scale
                
                setup = detector.get_setup_at(i)
                if setup and setup["direction"] == "bullish" and future_ret > threshold:
                    label = "bullish"
                elif setup and setup["direction"] == "bearish" and future_ret < -threshold:
                    label = "bearish"
                elif future_ret > threshold * 2:
                    label = "bullish"
                elif future_ret < -threshold * 2:
                    label = "bearish"
                else:
                    label = "neutral"
                
                features["label"] = label
                features["symbol"] = symbol
                features["bar_idx"] = i
                all_rows.append(features)
                n_rows += 1
            
            print(f"{n_rows} rows, {pcount} patterns")
        except Exception as e:
            print(f"error: {e}")
    
    return pd.DataFrame(all_rows)


def train_and_evaluate(df_all):
    """Train RF + XGBoost on SMC features, evaluate, generate figures."""
    print(f"\n  Total samples: {len(df_all)}")
    print(f"  Label distribution:\n{df_all['label'].value_counts()}")
    
    label_map = {"bearish": 0, "bullish": 1, "neutral": 2}
    feature_cols = [c for c in df_all.columns if c not in ("label", "symbol", "bar_idx")]
    
    X = df_all[feature_cols].values.astype(float)
    y = df_all["label"].map(label_map).values
    
    # Time-based split (data is ordered by symbol then time)
    n = len(X)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    
    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:n_train+n_val], y[n_train:n_train+n_val]
    X_test, y_test = X[n_train+n_val:], y[n_train+n_val:]
    
    # Scale
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    print(f"  Features: {len(feature_cols)}")
    
    classes = ["bearish", "bullish", "neutral"]
    results = {}
    
    # --- Random Forest ---
    print("\n  Training Random Forest...")
    t0 = time.time()
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=15, min_samples_leaf=5,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_time = time.time() - t0
    
    rf_pred = rf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_report = classification_report(y_test, rf_pred, target_names=classes, output_dict=True)
    print(f"  RF Test Accuracy: {rf_acc:.1%} ({rf_time:.1f}s)")
    print(classification_report(y_test, rf_pred, target_names=classes))
    results["random_forest"] = {"accuracy": rf_acc, "report": rf_report, "time": rf_time}
    
    # --- XGBoost ---
    print("  Training XGBoost...")
    t0 = time.time()
    # Compute sample weights for class balance
    class_counts = np.bincount(y_train, minlength=3)
    total = len(y_train)
    sample_weights = np.array([total / (3 * class_counts[yi]) for yi in y_train])
    
    xg = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric="mlogloss", random_state=42, n_jobs=-1,
        num_class=3, objective="multi:softmax"
    )
    xg.fit(X_train, y_train, sample_weight=sample_weights)
    xg_time = time.time() - t0
    
    xg_pred = xg.predict(X_test)
    xg_acc = accuracy_score(y_test, xg_pred)
    xg_report = classification_report(y_test, xg_pred, target_names=classes, output_dict=True)
    print(f"  XGB Test Accuracy: {xg_acc:.1%} ({xg_time:.1f}s)")
    print(classification_report(y_test, xg_pred, target_names=classes))
    results["xgboost"] = {"accuracy": xg_acc, "report": xg_report, "time": xg_time}
    
    # --- Save models ---
    joblib.dump(rf, os.path.join(SAVE_DIR, "smc_rf.pkl"))
    joblib.dump(xg, os.path.join(SAVE_DIR, "smc_xgb.pkl"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "smc_scaler.pkl"))
    with open(os.path.join(SAVE_DIR, "smc_features.json"), "w") as f:
        json.dump(feature_cols, f)
    
    # --- Generate thesis figures ---
    print("\n  Generating figures...")
    
    # 1. Confusion matrices
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, pred, name in [(axes[0], rf_pred, "Random Forest"), (axes[1], xg_pred, "XGBoost")]:
        cm = confusion_matrix(y_test, pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes,
                    yticklabels=classes, ax=ax, cbar=False)
        ax.set_title(f"{name} — Confusion Matrix", fontsize=13, fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_confusion_matrices.png"), dpi=150)
    plt.close()
    print("    confusion matrices")
    
    # 2. Feature importance (RF)
    importances = rf.feature_importances_
    top_n = 20
    idx = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(top_n), importances[idx], color="#2563eb")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_cols[i] for i in idx], fontsize=9)
    ax.set_xlabel("Importance (Gini)")
    ax.set_title("SMC Feature Importance — Random Forest (Top 20)", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_feature_importance_rf.png"), dpi=150)
    plt.close()
    print("    RF feature importance")
    
    # 3. Feature importance (XGBoost)
    xg_imp = xg.feature_importances_
    idx2 = np.argsort(xg_imp)[-top_n:]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(top_n), xg_imp[idx2], color="#dc2626")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_cols[i] for i in idx2], fontsize=9)
    ax.set_xlabel("Importance (gain)")
    ax.set_title("SMC Feature Importance — XGBoost (Top 20)", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_feature_importance_xgb.png"), dpi=150)
    plt.close()
    print("    XGB feature importance")
    
    # 4. Model comparison bar chart
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics_names = ["accuracy", "macro avg"]
    x = np.arange(4)
    width = 0.35
    rf_vals = [rf_acc, rf_report["macro avg"]["precision"], rf_report["macro avg"]["recall"], rf_report["macro avg"]["f1-score"]]
    xg_vals = [xg_acc, xg_report["macro avg"]["precision"], xg_report["macro avg"]["recall"], xg_report["macro avg"]["f1-score"]]
    ax.bar(x - width/2, rf_vals, width, label="Random Forest", color="#2563eb")
    ax.bar(x + width/2, xg_vals, width, label="XGBoost", color="#dc2626")
    ax.set_xticks(x)
    ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1-Score"])
    ax.set_ylim(0, 1)
    ax.set_title("SMC Pattern Classifier — Model Comparison", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for i, (rv, xv) in enumerate(zip(rf_vals, xg_vals)):
        ax.text(i - width/2, rv + 0.02, f"{rv:.1%}", ha="center", fontsize=9)
        ax.text(i + width/2, xv + 0.02, f"{xv:.1%}", ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_model_comparison.png"), dpi=150)
    plt.close()
    print("    model comparison")
    
    # 5. Per-class accuracy
    fig, ax = plt.subplots(figsize=(8, 5))
    rf_per = [rf_report[c]["f1-score"] for c in classes]
    xg_per = [xg_report[c]["f1-score"] for c in classes]
    x = np.arange(3)
    ax.bar(x - width/2, rf_per, width, label="Random Forest", color="#2563eb")
    ax.bar(x + width/2, xg_per, width, label="XGBoost", color="#dc2626")
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 1)
    ax.set_ylabel("F1-Score")
    ax.set_title("Per-Class F1-Score — SMC Pattern Detection", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_per_class_f1.png"), dpi=150)
    plt.close()
    print("    per-class F1")
    
    # 6. Summary card
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    best_name = "Random Forest" if rf_acc >= xg_acc else "XGBoost"
    best_acc = max(rf_acc, xg_acc)
    text = (
        f"SMC Pattern Classifier — Module 2 Results\n"
        f"{'='*50}\n\n"
        f"Approach:  Tabular SMC features + Tree ensemble classifiers\n"
        f"Features:  {len(feature_cols)} numeric features from SMC detector\n"
        f"Symbols:   {len(SYMBOLS)} ({', '.join(SYMBOLS[:5])}...)\n"
        f"Interval:  {INTERVAL} (hourly candles)\n"
        f"Samples:   {len(X_train)+len(X_val)+len(X_test):,}\n"
        f"Split:     70/15/15 time-based\n\n"
        f"Random Forest:  {rf_acc:.1%} accuracy\n"
        f"XGBoost:        {xg_acc:.1%} accuracy\n"
        f"Random baseline: 33.3%\n\n"
        f"Best model: {best_name} ({best_acc:.1%})\n"
    )
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=11,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="#f0f0f0", alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "smc_summary_card.png"), dpi=150)
    plt.close()
    print("    summary card")
    
    # Save metrics
    metrics = {
        "random_forest": {"test_accuracy": rf_acc, "per_class": {c: rf_report[c] for c in classes}},
        "xgboost": {"test_accuracy": xg_acc, "per_class": {c: xg_report[c] for c in classes}},
        "feature_count": len(feature_cols),
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "symbols": SYMBOLS,
        "interval": INTERVAL,
    }
    with open(os.path.join(SAVE_DIR, "smc_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=float)
    
    return results


if __name__ == "__main__":
    print("="*60)
    print("  Module 2B: SMC Tabular Feature Classifier")
    print("="*60)
    
    print("\nStep 1: Building dataset...")
    df = build_dataset()
    
    if len(df) < 100:
        print(f"  Only {len(df)} samples — not enough to train.")
        sys.exit(1)
    
    print(f"\nStep 2: Training + evaluating...")
    results = train_and_evaluate(df)
    
    print(f"\nDone! Models + figures saved to {SAVE_DIR}")
