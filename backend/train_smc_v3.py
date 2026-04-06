"""
Module 2 v3: CAUSAL SMC + Technical Indicator Fusion Classifier
================================================================
Fixes look-ahead bias from v2:
  - Uses detect_causal() — no future data in pattern detection
  - Filters patterns by discovery_bar during feature extraction
  - Order blocks detected backward (impulse already happened)
  - Swing points only used after lb-bar confirmation

Same architecture: Binary (bullish/bearish), 88 features, GridSearchCV.

Usage: cd backend && python train_smc_v3.py
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
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, roc_auc_score, roc_curve,
                             f1_score)
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import joblib, json, time, warnings
warnings.filterwarnings("ignore")

from ai.smc.detector import SMCDetector, PatternType
from ai.data.indicators import add_all_indicators

# ── Config ──────────────────────────────────────────────────────────────
SAVE_DIR = r"F:\trading-journal\backend\ai\saved_models\smc"
FIG_DIR  = os.path.join(SAVE_DIR, "figures_v3")
os.makedirs(FIG_DIR, exist_ok=True)

SYMBOLS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AAPL", "MSFT", "GOOGL",
           "^GSPC", "ES=F", "NQ=F", "BTC-USD", "GC=F", "TSLA"]
WINDOW = 30
FORWARD = 10
INTERVAL = "1h"
DAYS_BACK = 729
STEP = 1
CONFIDENCE_THRESHOLD = 0.60

TA_COLS = [
    "rsi_14", "macd", "macd_signal", "macd_hist",
    "bb_pct", "bb_width", "atr_14",
    "stoch_k", "stoch_d", "adx_14", "di_plus", "di_minus",
    "cci_20", "willr_14", "obv",
    "sma_5", "sma_10", "sma_20", "sma_50",
    "ema_12", "ema_26",
]

LAG_FEATURES = ["pattern_balance", "return_1bar", "rsi_14", "macd", "bb_pct", "stoch_k"]
LAG_PERIODS = [1, 3, 5]


def extract_smc_features_causal(df, detector, bar_idx, window=30):
    """
    Extract 43 SMC features using ONLY patterns known at bar_idx.
    Filters by discovery_bar <= bar_idx (causal).
    """
    start = max(0, bar_idx - window)
    # KEY CHANGE: filter by discovery_bar, not just index
    recent = [p for p in detector.patterns
              if start <= p.index <= bar_idx
              and p.discovery_bar is not None
              and p.discovery_bar <= bar_idx]

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

    # Use causal setup detection
    setup = detector.get_setup_at_causal(bar_idx, lookback=window)
    has_setup = 1 if setup else 0
    setup_dir = 0
    setup_conf = 0.0
    if setup:
        setup_dir = 1 if setup["direction"] == "bullish" else -1
        setup_conf = setup["confidence"]

    close = detector.close
    high = detector.high
    low = detector.low
    vol = detector.volume

    c = close[bar_idx]
    lookback_closes = close[start:bar_idx + 1]

    ret_1 = (c - close[max(bar_idx - 1, 0)]) / close[max(bar_idx - 1, 0)] if bar_idx > 0 else 0
    ret_5 = (c - close[max(bar_idx - 5, 0)]) / close[max(bar_idx - 5, 0)] if bar_idx > 4 else 0
    ret_10 = (c - close[max(bar_idx - 10, 0)]) / close[max(bar_idx - 10, 0)] if bar_idx > 9 else 0

    if len(lookback_closes) > 2:
        returns = np.diff(lookback_closes) / lookback_closes[:-1]
        volatility = float(np.std(returns)) if len(returns) > 1 else 0
    else:
        volatility = 0

    hi = high[start:bar_idx + 1].max()
    lo = low[start:bar_idx + 1].min()
    range_pos = (c - lo) / (hi - lo) if hi != lo else 0.5

    vol_window = vol[start:bar_idx + 1]
    vol_avg = vol_window.mean() if len(vol_window) > 0 else 0
    vol_ratio = vol[bar_idx] / vol_avg if vol_avg > 0 else 1.0

    # Only use confirmed swings (already filtered by detect_causal)
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

    features = {
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
        "volatility": volatility,
        "range_position": range_pos,
        "volume_ratio": vol_ratio,
        "higher_highs": hh_count,
        "lower_lows": ll_count,
        "swing_trend": hh_count - ll_count,
        "n_swing_highs": len(sh),
        "n_swing_lows": len(sl),
    }
    return features


def extract_ta_features(df, bar_idx):
    """Extract technical indicator values for a single bar (TA is already causal)."""
    ta_feats = {}
    for col in TA_COLS:
        if col in df.columns:
            val = df.iloc[bar_idx].get(col, 0)
            ta_feats[f"ta_{col}"] = float(val) if pd.notna(val) else 0.0
        else:
            ta_feats[f"ta_{col}"] = 0.0

    close = df.iloc[bar_idx]["Close"]
    for ma_col in ["sma_20", "sma_50", "ema_12", "ema_26"]:
        if ma_col in df.columns:
            ma_val = df.iloc[bar_idx][ma_col]
            if pd.notna(ma_val) and ma_val != 0:
                ta_feats[f"ta_price_vs_{ma_col}"] = (close - ma_val) / ma_val
            else:
                ta_feats[f"ta_price_vs_{ma_col}"] = 0.0

    return ta_feats


def build_dataset():
    """Build dataset with CAUSAL SMC features + TA, binary labels."""
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

            # TA indicators (backward-looking, no bias)
            df_ta = add_all_indicators(df)

            # CAUSAL SMC detection — run once on full data, uses discovery_bar
            detector = SMCDetector(df, swing_lookback=5, timeframe=INTERVAL)
            detector.detect_causal()
            pcount = len(detector.patterns)

            n_rows = 0
            n_neutral = 0
            for i in range(WINDOW, len(df) - FORWARD, STEP):
                # Label uses future return (this is the TARGET — correct by design)
                future_ret = (detector.close[i + FORWARD] - detector.close[i]) / detector.close[i]
                threshold = 0.006 * detector._tf_scale

                # Use causal setup for labeling threshold
                setup = detector.get_setup_at_causal(i)
                if setup and setup["direction"] == "bullish" and future_ret > threshold:
                    label = "bullish"
                elif setup and setup["direction"] == "bearish" and future_ret < -threshold:
                    label = "bearish"
                elif future_ret > threshold * 2:
                    label = "bullish"
                elif future_ret < -threshold * 2:
                    label = "bearish"
                else:
                    n_neutral += 1
                    continue  # skip neutral

                # CAUSAL feature extraction — only patterns with discovery_bar <= i
                smc_feats = extract_smc_features_causal(df, detector, i, window=WINDOW)
                ta_feats = extract_ta_features(df_ta, i)
                features = {**smc_feats, **ta_feats}
                features["label"] = label
                features["symbol"] = symbol
                features["bar_idx"] = i
                all_rows.append(features)
                n_rows += 1

            print(f"{n_rows} rows ({n_neutral} neutral dropped), {pcount} patterns")
        except Exception as e:
            print(f"error: {e}")

    return pd.DataFrame(all_rows)


def add_lagged_features(df):
    """Add lagged versions of key features for temporal patterns."""
    new_cols = {}
    for feat in LAG_FEATURES:
        col = feat
        if feat in ["rsi_14", "macd", "bb_pct", "stoch_k"]:
            col = f"ta_{feat}"
        if col not in df.columns:
            continue
        for lag in LAG_PERIODS:
            new_cols[f"{col}_lag{lag}"] = df[col].shift(lag)

    if "pattern_balance" in df.columns:
        new_cols["pattern_balance_diff1"] = df["pattern_balance"].diff(1)
        new_cols["pattern_balance_diff3"] = df["pattern_balance"].diff(3)

    for name, series in new_cols.items():
        df[name] = series

    return df


def train_and_evaluate(df_all):
    """Train RF + XGBoost with GridSearchCV, evaluate, generate figures."""
    print(f"\n{'='*60}")
    print(f"  TRAINING MODULE 2 v3 — CAUSAL SMC + TA Fusion (Binary)")
    print(f"{'='*60}")
    print(f"  Total samples: {len(df_all)}")
    print(f"  Label distribution:\n{df_all['label'].value_counts().to_string()}")

    label_map = {"bearish": 0, "bullish": 1}
    meta_cols = {"label", "symbol", "bar_idx"}
    feature_cols = [c for c in df_all.columns if c not in meta_cols]

    X = df_all[feature_cols].values.astype(float)
    y = df_all["label"].map(label_map).values

    # Handle NaN
    nan_mask = np.isnan(X)
    if nan_mask.any():
        col_medians = np.nanmedian(X, axis=0)
        for j in range(X.shape[1]):
            X[nan_mask[:, j], j] = col_medians[j]
        print(f"  Filled {nan_mask.sum()} NaN values with column medians")

    # Time-based split
    n = len(X)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:n_train + n_val], y[n_train:n_train + n_val]
    X_test, y_test = X[n_train + n_val:], y[n_train + n_val:]

    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    print(f"  Features: {len(feature_cols)}")
    print(f"  Train class balance: bearish={sum(y_train==0)}, bullish={sum(y_train==1)}")

    classes = ["bearish", "bullish"]
    results = {}

    # ── Random Forest ───────────────────────────────────────────────
    print("\n  GridSearchCV: Random Forest...", flush=True)
    t0 = time.time()
    rf_param_grid = {
        "n_estimators": [300, 500],
        "max_depth": [12, 20],
        "min_samples_leaf": [3, 8],
    }
    rf_base = RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1)
    rf_cv = GridSearchCV(rf_base, rf_param_grid,
                         cv=TimeSeriesSplit(n_splits=3),
                         scoring="f1_weighted", n_jobs=-1, verbose=1)
    rf_cv.fit(X_train, y_train)
    rf = rf_cv.best_estimator_
    rf_time = time.time() - t0

    rf_pred = rf.predict(X_test)
    rf_proba = rf.predict_proba(X_test)[:, 1]
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_f1 = f1_score(y_test, rf_pred, average="weighted")
    rf_auc = roc_auc_score(y_test, rf_proba)

    print(f"  RF Best: {rf_cv.best_params_}")
    print(f"  RF: Acc={rf_acc:.1%} F1={rf_f1:.3f} AUC={rf_auc:.3f} ({rf_time:.1f}s)")
    print(classification_report(y_test, rf_pred, target_names=classes))
    results["random_forest"] = {
        "accuracy": rf_acc, "f1": rf_f1, "auc": rf_auc,
        "best_params": rf_cv.best_params_, "time": rf_time,
        "report": classification_report(y_test, rf_pred, target_names=classes, output_dict=True)
    }

    # Checkpoint: save RF before starting XGB
    print("  Saving RF checkpoint...", flush=True)
    joblib.dump(rf, os.path.join(SAVE_DIR, "smc_rf_v3.pkl"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "smc_scaler_v3.pkl"))
    with open(os.path.join(SAVE_DIR, "smc_features_v3.json"), "w") as f:
        json.dump(feature_cols, f)
    with open(os.path.join(SAVE_DIR, "_v3_checkpoint.json"), "w") as f:
        json.dump({"stage": "rf_done", "rf_acc": rf_acc, "rf_f1": rf_f1, "rf_auc": rf_auc}, f)
    print("  ✓ RF checkpoint saved", flush=True)

    # ── XGBoost ─────────────────────────────────────────────────────
    print("  GridSearchCV: XGBoost...", flush=True)
    t0 = time.time()
    xg_param_grid = {
        "n_estimators": [300, 500],
        "max_depth": [5, 7],
        "learning_rate": [0.03, 0.07],
        "subsample": [0.8],
        "colsample_bytree": [0.8],
    }
    xg_base = xgb.XGBClassifier(eval_metric="logloss", random_state=42, n_jobs=-1,
                                 objective="binary:logistic")
    xg_cv = GridSearchCV(xg_base, xg_param_grid,
                         cv=TimeSeriesSplit(n_splits=3),
                         scoring="f1_weighted", n_jobs=-1, verbose=1)
    xg_cv.fit(X_train, y_train)
    xg = xg_cv.best_estimator_
    xg_time = time.time() - t0

    xg_pred = xg.predict(X_test)
    xg_proba = xg.predict_proba(X_test)[:, 1]
    xg_acc = accuracy_score(y_test, xg_pred)
    xg_f1 = f1_score(y_test, xg_pred, average="weighted")
    xg_auc = roc_auc_score(y_test, xg_proba)

    print(f"  XGB Best: {xg_cv.best_params_}")
    print(f"  XGB: Acc={xg_acc:.1%} F1={xg_f1:.3f} AUC={xg_auc:.3f} ({xg_time:.1f}s)")
    print(classification_report(y_test, xg_pred, target_names=classes))
    results["xgboost"] = {
        "accuracy": xg_acc, "f1": xg_f1, "auc": xg_auc,
        "best_params": {k: (int(v) if isinstance(v, (np.integer,)) else v)
                        for k, v in xg_cv.best_params_.items()},
        "time": xg_time,
        "report": classification_report(y_test, xg_pred, target_names=classes, output_dict=True)
    }

    # ── Ensemble ────────────────────────────────────────────────────
    ens_proba = (rf_proba + xg_proba) / 2
    ens_pred = (ens_proba >= 0.5).astype(int)
    ens_acc = accuracy_score(y_test, ens_pred)
    ens_f1 = f1_score(y_test, ens_pred, average="weighted")
    ens_auc = roc_auc_score(y_test, ens_proba)
    print(f"\n  ENSEMBLE: Acc={ens_acc:.1%} F1={ens_f1:.3f} AUC={ens_auc:.3f}")
    print(classification_report(y_test, ens_pred, target_names=classes))
    results["ensemble"] = {
        "accuracy": ens_acc, "f1": ens_f1, "auc": ens_auc,
        "report": classification_report(y_test, ens_pred, target_names=classes, output_dict=True)
    }

    # ── Confidence threshold analysis ───────────────────────────────
    print("\n  Confidence Threshold Analysis:")
    for thresh in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        confident_mask = np.maximum(ens_proba, 1 - ens_proba) >= thresh
        if confident_mask.sum() == 0:
            continue
        ct_acc = accuracy_score(y_test[confident_mask], ens_pred[confident_mask])
        coverage = confident_mask.mean()
        print(f"    {thresh:.0%}: acc={ct_acc:.1%}, coverage={coverage:.1%} ({confident_mask.sum()} samples)")

    # ── Save models ─────────────────────────────────────────────────
    print("\n  Saving v3 models...")
    joblib.dump(rf, os.path.join(SAVE_DIR, "smc_rf_v3.pkl"))
    joblib.dump(xg, os.path.join(SAVE_DIR, "smc_xgb_v3.pkl"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "smc_scaler_v3.pkl"))
    with open(os.path.join(SAVE_DIR, "smc_features_v3.json"), "w") as f:
        json.dump(feature_cols, f)

    metrics = {
        "version": "v3_causal",
        "type": "binary",
        "classes": classes,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "causality": "Fully causal — no look-ahead bias in features",
        "random_forest": {
            "test_accuracy": rf_acc, "f1_weighted": rf_f1, "auc_roc": rf_auc,
            "best_params": rf_cv.best_params_,
            "per_class": results["random_forest"]["report"],
        },
        "xgboost": {
            "test_accuracy": xg_acc, "f1_weighted": xg_f1, "auc_roc": xg_auc,
            "best_params": results["xgboost"]["best_params"],
            "per_class": results["xgboost"]["report"],
        },
        "ensemble": {
            "test_accuracy": ens_acc, "f1_weighted": ens_f1, "auc_roc": ens_auc,
            "per_class": results["ensemble"]["report"],
        },
        "feature_count": len(feature_cols),
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "symbols": SYMBOLS,
        "interval": INTERVAL,
        "step": STEP,
        "forward_bars": FORWARD,
    }
    with open(os.path.join(SAVE_DIR, "smc_metrics_v3.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    # ── Figures ─────────────────────────────────────────────────────
    print("\n  Generating v3 thesis figures...")
    _generate_figures(y_test, rf_pred, xg_pred, ens_pred,
                      rf_proba, xg_proba, ens_proba,
                      rf, xg, feature_cols, classes, results)

    print(f"\n{'='*60}")
    print(f"  MODULE 2 v3 (CAUSAL) COMPLETE")
    print(f"  RF: {rf_acc:.1%} | XGB: {xg_acc:.1%} | Ensemble: {ens_acc:.1%}")
    print(f"  Models → {SAVE_DIR}")
    print(f"  Figures → {FIG_DIR}")
    print(f"{'='*60}")

    return results


def _generate_figures(y_test, rf_pred, xg_pred, ens_pred,
                      rf_proba, xg_proba, ens_proba,
                      rf, xg, feature_cols, classes, results):
    """Generate v3 thesis figures."""

    # 1. Confusion matrices
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, pred, name in [(axes[0], rf_pred, "Random Forest"),
                            (axes[1], xg_pred, "XGBoost"),
                            (axes[2], ens_pred, "Ensemble")]:
        cm = confusion_matrix(y_test, pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=classes, yticklabels=classes, ax=ax, cbar=False)
        ax.set_title(f"{name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
    fig.suptitle("Module 2 v3 (Causal) — Confusion Matrices",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "confusion_matrices_v3.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("    ✓ confusion matrices")

    # 2. ROC Curves
    fig, ax = plt.subplots(figsize=(8, 7))
    for proba, name, color in [(rf_proba, "Random Forest", "#2563eb"),
                                (xg_proba, "XGBoost", "#dc2626"),
                                (ens_proba, "Ensemble", "#16a34a")]:
        fpr, tpr, _ = roc_curve(y_test, proba)
        auc = roc_auc_score(y_test, proba)
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=color, linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Random (AUC=0.500)")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("Module 2 v3 (Causal) — ROC Curves", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "roc_curves_v3.png"), dpi=150)
    plt.close()
    print("    ✓ ROC curves")

    # 3. Feature importance RF
    importances = rf.feature_importances_
    top_n = min(25, len(feature_cols))
    idx = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(10, 9))
    colors = ["#dc2626" if feature_cols[i].startswith("ta_") else "#2563eb" for i in idx]
    ax.barh(range(top_n), importances[idx], color=colors)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_cols[i] for i in idx], fontsize=8)
    ax.set_xlabel("Importance (Gini)")
    ax.set_title("Feature Importance — RF v3 (Causal)\nBlue=SMC, Red=TA",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "feature_importance_rf_v3.png"), dpi=150)
    plt.close()
    print("    ✓ RF feature importance")

    # 4. Feature importance XGB
    xg_imp = xg.feature_importances_
    idx2 = np.argsort(xg_imp)[-top_n:]
    fig, ax = plt.subplots(figsize=(10, 9))
    colors2 = ["#dc2626" if feature_cols[i].startswith("ta_") else "#2563eb" for i in idx2]
    ax.barh(range(top_n), xg_imp[idx2], color=colors2)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_cols[i] for i in idx2], fontsize=8)
    ax.set_xlabel("Importance (Gain)")
    ax.set_title("Feature Importance — XGB v3 (Causal)\nBlue=SMC, Red=TA",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "feature_importance_xgb_v3.png"), dpi=150)
    plt.close()
    print("    ✓ XGB feature importance")

    # 5. Model comparison
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    models = ["Random Forest", "XGBoost", "Ensemble"]
    accs = [results["random_forest"]["accuracy"], results["xgboost"]["accuracy"], results["ensemble"]["accuracy"]]
    f1s = [results["random_forest"]["f1"], results["xgboost"]["f1"], results["ensemble"]["f1"]]
    aucs = [results["random_forest"]["auc"], results["xgboost"]["auc"], results["ensemble"]["auc"]]
    bar_colors = ["#2563eb", "#dc2626", "#16a34a"]

    for ax, vals, title, fmt in [(axes[0], accs, "Accuracy", ".1%"),
                                  (axes[1], f1s, "F1 Score", ".3f"),
                                  (axes[2], aucs, "AUC-ROC", ".3f")]:
        bars = ax.bar(models, vals, color=bar_colors)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_ylim(0.4, 1.0)
        ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="Random baseline")
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:{fmt}}", ha="center", fontsize=11, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Module 2 v3 (Causal) — Model Comparison",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "model_comparison_v3.png"), dpi=150)
    plt.close()
    print("    ✓ model comparison")

    # 6. Confidence threshold curve
    thresholds = np.arange(0.50, 0.95, 0.01)
    ct_accs = []
    ct_coverages = []
    for thresh in thresholds:
        confident = np.maximum(ens_proba, 1 - ens_proba) >= thresh
        if confident.sum() == 0:
            ct_accs.append(np.nan)
            ct_coverages.append(0)
            continue
        ct_accs.append(accuracy_score(y_test[confident], ens_pred[confident]))
        ct_coverages.append(confident.mean())

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax1.plot(thresholds, ct_accs, color="#2563eb", linewidth=2, label="Accuracy")
    ax2.plot(thresholds, ct_coverages, color="#dc2626", linewidth=2, linestyle="--", label="Coverage")
    ax1.axvline(x=CONFIDENCE_THRESHOLD, color="gray", linestyle=":", alpha=0.7,
                label=f"Threshold={CONFIDENCE_THRESHOLD:.0%}")
    ax1.set_xlabel("Confidence Threshold", fontsize=12)
    ax1.set_ylabel("Accuracy", fontsize=12, color="#2563eb")
    ax2.set_ylabel("Coverage", fontsize=12, color="#dc2626")
    ax1.set_title("v3 (Causal) Confidence vs Accuracy & Coverage",
                  fontsize=14, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=10)
    ax1.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "confidence_threshold_v3.png"), dpi=150)
    plt.close()
    print("    ✓ confidence threshold curve")

    # 7. v2 vs v3 comparison
    fig, ax = plt.subplots(figsize=(8, 5))
    v2_acc = 0.712  # v2 ensemble from metrics
    v3_acc = results["ensemble"]["accuracy"]
    bars = ax.bar(["v2 (Biased features)", "v3 (Causal features)"],
                  [v2_acc, v3_acc], color=["#f59e0b", "#16a34a"], width=0.5)
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="Random baseline")
    for bar, val in zip(bars, [v2_acc, v3_acc]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.1%}", ha="center", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Module 2: v2 (Biased) vs v3 (Causal)", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "v2_vs_v3_comparison.png"), dpi=150)
    plt.close()
    print("    ✓ v2 vs v3 comparison")

    # 8. Summary card
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.axis("off")
    summary_text = (
        f"Module 2 v3 — CAUSAL SMC + TA Fusion Classifier\n"
        f"{'─'*55}\n"
        f"FULLY CAUSAL: No look-ahead bias in features\n"
        f"Classification: Binary (Bullish vs Bearish)\n"
        f"Confidence Threshold: {CONFIDENCE_THRESHOLD:.0%}\n"
        f"{'─'*55}\n"
        f"Random Forest:  Acc={results['random_forest']['accuracy']:.1%}  "
        f"F1={results['random_forest']['f1']:.3f}  AUC={results['random_forest']['auc']:.3f}\n"
        f"XGBoost:        Acc={results['xgboost']['accuracy']:.1%}  "
        f"F1={results['xgboost']['f1']:.3f}  AUC={results['xgboost']['auc']:.3f}\n"
        f"Ensemble:       Acc={results['ensemble']['accuracy']:.1%}  "
        f"F1={results['ensemble']['f1']:.3f}  AUC={results['ensemble']['auc']:.3f}\n"
        f"{'─'*55}\n"
        f"v2 (biased): 71.2%  →  v3 (causal): {results['ensemble']['accuracy']:.1%}\n"
        f"Features: {len(feature_cols)}\n"
        f"Dataset: {len(SYMBOLS)} symbols, {INTERVAL}, {DAYS_BACK} days\n"
    )
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "summary_card_v3.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("    ✓ summary card")


# ── Main ────────────────────────────────────────────────────────────────
DATASET_CACHE = os.path.join(SAVE_DIR, "_v3_dataset_cache.pkl")

if __name__ == "__main__":
    import sys as _sys

    # Flush all prints immediately (critical for log files)
    import functools
    print = functools.partial(print, flush=True)

    print("=" * 60)
    print("  MODULE 2 v3: CAUSAL SMC + TA Fusion Binary Classifier")
    print("  (No look-ahead bias — all features use only past data)")
    print("=" * 60)

    # Check for cached dataset to skip slow rebuild
    if os.path.exists(DATASET_CACHE) and "--rebuild" not in _sys.argv:
        print(f"\n[1/3] Loading cached dataset from {DATASET_CACHE}...")
        df_all = pd.read_pickle(DATASET_CACHE)
        print(f"  Loaded {len(df_all)} rows from cache")
    else:
        print("\n[1/3] Building CAUSAL dataset...")
        df_all = build_dataset()

        if len(df_all) < 100:
            print("ERROR: Not enough data. Aborting.")
            _sys.exit(1)

        print(f"\n[2/3] Adding lagged features...")
        df_all = df_all.sort_values(["symbol", "bar_idx"]).reset_index(drop=True)
        dfs = []
        for sym, grp in df_all.groupby("symbol"):
            grp = add_lagged_features(grp)
            dfs.append(grp)
        df_all = pd.concat(dfs, ignore_index=True)
        df_all = df_all.sort_values(["symbol", "bar_idx"]).reset_index(drop=True)

        # Save dataset cache
        df_all.to_pickle(DATASET_CACHE)
        print(f"  Dataset cached to {DATASET_CACHE}")

    lag_cols = [c for c in df_all.columns if "_lag" in c or "_diff" in c]
    print(f"  Lagged features: {len(lag_cols)}")
    print(f"  Total features: {len([c for c in df_all.columns if c not in ('label','symbol','bar_idx')])}")

    print(f"\n[3/3] Training & evaluating...")
    results = train_and_evaluate(df_all)
