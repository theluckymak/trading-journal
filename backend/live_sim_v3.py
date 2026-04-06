"""
LIVE Walk-Forward Simulation — Bar-by-bar, like real trading
Symbol: CL=F (Crude Oil Futures) — NEVER seen in training
Period: Last 30 days, 1H bars

Rules:
- One trade at a time (no stacking)
- 60% confidence gate
- SL = 1x ATR(14), TP = 1x ATR(14) — 1:1 RR sized to volatility
- Enter at close of signal bar
- Track SL/TP bar-by-bar until hit
- Both SL+TP same bar = loss (conservative)
- Timeout after 10 bars = close at market
"""
import sys, os, json
import functools
print = functools.partial(print, flush=True)
sys.path.insert(0, r"F:\trading-journal\backend")

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import joblib, warnings
warnings.filterwarnings("ignore")

from ai.smc.detector import SMCDetector, PatternType
from ai.data.indicators import add_all_indicators
from train_smc_v3 import (extract_smc_features_causal, extract_ta_features,
                           add_lagged_features, WINDOW, FORWARD, INTERVAL,
                           CONFIDENCE_THRESHOLD)

SAVE_DIR = r"F:\trading-journal\backend\ai\saved_models\smc"
SYMBOL = "CL=F"  # Crude Oil — NEVER in training
TIMEOUT_BARS = 10


def run_live_sim():
    # Load models
    print("Loading v3 models...")
    rf = joblib.load(os.path.join(SAVE_DIR, "smc_rf_v3.pkl"))
    xg = joblib.load(os.path.join(SAVE_DIR, "smc_xgb_v3.pkl"))
    scaler = joblib.load(os.path.join(SAVE_DIR, "smc_scaler_v3.pkl"))
    with open(os.path.join(SAVE_DIR, "smc_features_v3.json")) as f:
        feature_cols = json.load(f)

    # Fetch data — need extra history for indicators + detector warmup
    print(f"Fetching {SYMBOL} 1H data...")
    end = datetime.now()
    start = end - timedelta(days=120)  # extra buffer for TA warmup
    ticker = yf.Ticker(SYMBOL)
    df = ticker.history(start=start.strftime("%Y-%m-%d"),
                        end=end.strftime("%Y-%m-%d"),
                        interval="1h", auto_adjust=True)

    df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.sort_index().ffill().dropna()
    print(f"Got {len(df)} bars ({df.index[0]} → {df.index[-1]})")

    # Compute TA indicators + ATR on full history
    df_ta = add_all_indicators(df)

    # Compute ATR(14) manually if not in indicators
    if "atr_14" not in df_ta.columns:
        high = df_ta["High"]
        low = df_ta["Low"]
        close = df_ta["Close"]
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        df_ta["atr_14"] = tr.rolling(14).mean()

    # Find where "last 30 days" starts
    cutoff = end - timedelta(days=30)
    sim_start = None
    for idx in range(len(df)):
        if df.index[idx] >= pd.Timestamp(cutoff):
            sim_start = idx
            break
    if sim_start is None or sim_start < WINDOW + 50:
        sim_start = max(WINDOW + 50, len(df) - 500)

    avg_atr = df_ta["atr_14"].iloc[sim_start:].mean()
    print(f"\n{'='*70}")
    print(f"  LIVE SIMULATION: {SYMBOL} (Crude Oil) — NEVER SEEN IN TRAINING")
    print(f"  Period: {df.index[sim_start].strftime('%Y-%m-%d %H:%M')} → "
          f"{df.index[-1].strftime('%Y-%m-%d %H:%M')}")
    print(f"  Rules: 1x ATR SL, 1x ATR TP (1:1 RR), 60% confidence gate")
    print(f"  Avg ATR(14): ${avg_atr:.2f} | Timeout: {TIMEOUT_BARS} bars")
    print(f"  One trade at a time — bar-by-bar execution")
    print(f"{'='*70}\n")

    # State
    in_trade = False
    trade_dir = 0
    entry_price = 0
    entry_bar = 0
    entry_time = None
    tp_price = 0
    sl_price = 0
    trade_atr = 0

    trades = []
    running_pnl = 0.0

    # Walk forward bar by bar
    for i in range(sim_start, len(df)):
        bar_time = df.index[i]
        bar_close = df.iloc[i]["Close"]
        bar_high = df.iloc[i]["High"]
        bar_low = df.iloc[i]["Low"]

        # ── Check open trade first ──
        if in_trade:
            bars_held = i - entry_bar
            hit_tp = False
            hit_sl = False

            if trade_dir == 1:  # LONG
                hit_tp = bar_high >= tp_price
                hit_sl = bar_low <= sl_price
            else:  # SHORT
                hit_tp = bar_low <= tp_price
                hit_sl = bar_high >= sl_price

            if hit_tp and hit_sl:
                pnl_r = -1.0  # conservative: count as loss
                result = "LOSS (ambig)"
            elif hit_tp:
                pnl_r = 1.0
                result = "WIN ✓"
            elif hit_sl:
                pnl_r = -1.0
                result = "LOSS ✗"
            elif bars_held >= TIMEOUT_BARS:
                # Timeout — close at market
                move = (bar_close - entry_price) * trade_dir
                pnl_r = move / trade_atr  # P&L in R
                pnl_r = max(-1.0, min(1.0, pnl_r))
                result = f"TIMEOUT ({pnl_r:+.1f}R)"
            else:
                continue  # trade still open, next bar

            running_pnl += pnl_r
            dir_str = "LONG" if trade_dir == 1 else "SHORT"
            trades.append({
                "entry_time": entry_time, "exit_time": bar_time,
                "direction": dir_str, "entry": entry_price,
                "pnl_r": pnl_r, "duration": bars_held, "result": result,
                "atr": trade_atr,
            })
            print(f"  CLOSE {dir_str:5s} | {bar_time.strftime('%m/%d %H:%M')} | "
                  f"{result:18s} | {pnl_r:+.1f}R | "
                  f"Dur: {bars_held} bars | Running: {running_pnl:+.1f}R")
            in_trade = False
            continue

        # ── No open trade — check for signal ──
        if i >= len(df) - 2:
            continue  # don't trade last bars

        # Get current ATR
        current_atr = df_ta["atr_14"].iloc[i]
        if pd.isna(current_atr) or current_atr <= 0:
            continue

        # Run causal detector up to current bar
        detector = SMCDetector(df.iloc[:i+1], swing_lookback=5, timeframe="1h")
        detector.detect_causal()

        # Extract features
        smc_feats = extract_smc_features_causal(df.iloc[:i+1], detector, i, window=WINDOW)
        ta_feats = extract_ta_features(df_ta, i)
        features = {**smc_feats, **ta_feats}

        row = pd.DataFrame([features])
        for col in feature_cols:
            if col not in row.columns:
                row[col] = 0.0
        X = row[feature_cols].values.astype(float)
        nan_mask = np.isnan(X)
        if nan_mask.any():
            X[nan_mask] = 0.0
        X = scaler.transform(X)

        # Ensemble prediction
        rf_proba = rf.predict_proba(X)[0][1]
        xg_proba = xg.predict_proba(X)[0][1]
        ens_proba = (rf_proba + xg_proba) / 2
        confidence = max(ens_proba, 1 - ens_proba)

        if confidence < CONFIDENCE_THRESHOLD:
            continue  # no trade — low confidence

        # Enter trade with ATR-based SL/TP
        trade_dir = 1 if ens_proba >= 0.5 else -1
        entry_price = bar_close
        entry_bar = i
        entry_time = bar_time
        trade_atr = current_atr
        in_trade = True

        if trade_dir == 1:
            tp_price = entry_price + current_atr
            sl_price = entry_price - current_atr
        else:
            tp_price = entry_price - current_atr
            sl_price = entry_price + current_atr

        dir_str = "LONG" if trade_dir == 1 else "SHORT"
        print(f"  ENTER {dir_str:5s} | {bar_time.strftime('%m/%d %H:%M')} | "
              f"@ ${entry_price:.2f} | Conf: {confidence:.0%} | "
              f"ATR=${current_atr:.2f} | TP=${tp_price:.2f} SL=${sl_price:.2f}")

    # Close any open trade at market
    if in_trade:
        last_close = df.iloc[-1]["Close"]
        move = (last_close - entry_price) * trade_dir
        pnl_r = move / trade_atr
        pnl_r = max(-1.0, min(1.0, pnl_r))
        running_pnl += pnl_r
        dir_str = "LONG" if trade_dir == 1 else "SHORT"
        print(f"  CLOSE {dir_str:5s} | {df.index[-1].strftime('%m/%d %H:%M')} | "
              f"MARKET CLOSE      | {pnl_r:+.1f}R | Running: {running_pnl:+.1f}R")
        trades.append({
            "entry_time": entry_time, "exit_time": df.index[-1],
            "direction": dir_str, "entry": entry_price,
            "pnl_r": pnl_r, "duration": len(df) - 1 - entry_bar,
            "result": "MARKET CLOSE", "atr": trade_atr,
        })

    # Summary
    wins = sum(1 for t in trades if t["pnl_r"] > 0)
    losses = sum(1 for t in trades if t["pnl_r"] < 0)
    scratches = sum(1 for t in trades if t["pnl_r"] == 0)
    total = len(trades)
    wr = wins / total * 100 if total > 0 else 0
    avg_dur = np.mean([t["duration"] for t in trades]) if trades else 0
    avg_atr_trades = np.mean([t["atr"] for t in trades]) if trades else 0

    print(f"\n{'='*70}")
    print(f"  SIMULATION COMPLETE — {SYMBOL} (Crude Oil)")
    print(f"{'='*70}")
    print(f"  Total trades:   {total}")
    print(f"  Wins:           {wins}")
    print(f"  Losses:         {losses}")
    print(f"  Scratches:      {scratches}")
    print(f"  Win rate:       {wr:.0f}%")
    print(f"  Avg duration:   {avg_dur:.1f} bars")
    print(f"  Avg ATR/trade:  ${avg_atr_trades:.2f}")
    print(f"  ──────────────────────────")
    print(f"  TOTAL P&L:      {running_pnl:+.1f}R")
    print(f"  (At $10/pip:    ${running_pnl * avg_atr_trades * 100:+,.0f})")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_live_sim()
