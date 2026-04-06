"""
DRL Ensemble Prediction Service

Loads PPO, A2C, SAC models from h1-rebuild and serves predictions
via the /api/ai/drl-predict endpoint.
"""
import os
import logging
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("DRL_MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "saved_models", "drl"))

SIGNAL_LABELS = {-1: "SHORT", 0: "FLAT", 1: "LONG"}
REGIME_LABELS = {0: "Uptrend", 1: "Downtrend", 2: "Range"}


class DRLPredictionService:
    """Serves DRL ensemble predictions from trained SB3 models."""

    def __init__(self):
        self.ppo = None
        self.a2c = None
        self.sac = None
        self.hmm = None
        self.loaded = False

    def load_models(self):
        """Load all three SB3 agents + HMM regime model."""
        try:
            from stable_baselines3 import PPO, A2C, SAC

            ppo_path = os.path.join(MODEL_DIR, "ppo_daily.zip")
            a2c_path = os.path.join(MODEL_DIR, "a2c_daily.zip")
            sac_path = os.path.join(MODEL_DIR, "sac_daily.zip")

            if os.path.exists(ppo_path):
                self.ppo = PPO.load(ppo_path)
                logger.info("PPO model loaded")
            if os.path.exists(a2c_path):
                self.a2c = A2C.load(a2c_path)
                logger.info("A2C model loaded")
            if os.path.exists(sac_path):
                self.sac = SAC.load(sac_path)
                logger.info("SAC model loaded")

            hmm_path = os.path.join(MODEL_DIR, "hmm_model.pkl")
            if os.path.exists(hmm_path):
                import joblib
                self.hmm = joblib.load(hmm_path)
                logger.info("HMM regime model loaded")

            self.loaded = any([self.ppo, self.a2c, self.sac])
            if not self.loaded:
                logger.warning(f"No DRL models found in {MODEL_DIR}")
        except ImportError as e:
            logger.error(f"Missing dependency for DRL models: {e}")
        except Exception as e:
            logger.error(f"Failed to load DRL models: {e}")

    def _get_market_data(self, symbol: str):
        """Fetch recent OHLCV data for the symbol."""
        import yfinance as yf
        import pandas as pd

        # Map common names to yfinance tickers
        ticker_map = {
            "NQ": "NQ=F", "ES": "ES=F", "YM": "YM=F", "RTY": "RTY=F",
            "CL": "CL=F", "GC": "GC=F", "SI": "SI=F", "NG": "NG=F",
            "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X",
            "USD/JPY": "USDJPY=X", "AUD/USD": "AUDUSD=X",
            "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X", "AUDUSD": "AUDUSD=X",
            "USDCAD": "USDCAD=X", "NZDUSD": "NZDUSD=X",
            "USDCHF": "USDCHF=X", "EURGBP": "EURGBP=X",
            "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
            "XRP": "XRP-USD", "ADA": "ADA-USD", "DOGE": "DOGE-USD",
            "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL",
            "AMZN": "AMZN", "TSLA": "TSLA", "NVDA": "NVDA", "META": "META",
            "SPY": "SPY", "QQQ": "QQQ",
        }
        # Normalize: strip slashes and uppercase
        symbol_clean = symbol.replace("/", "").upper()
        ticker = ticker_map.get(symbol, ticker_map.get(symbol_clean, symbol))

        daily = yf.download(ticker, period="2y", interval="1d", progress=False)
        h1 = yf.download(ticker, period="60d", interval="1h", progress=False)

        # Flatten MultiIndex columns from yfinance (e.g. ('Close','NQ=F') → 'Close')
        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)
        if isinstance(h1.columns, pd.MultiIndex):
            h1.columns = h1.columns.get_level_values(0)

        if daily.empty:
            raise ValueError(f"No data available for {symbol}")

        return daily, h1, ticker

    def _compute_features(self, df):
        """Compute exactly the 52 features matching the training environment."""
        import pandas as pd

        c = df["Close"].values.flatten() if hasattr(df["Close"], 'values') else df["Close"]
        h = df["High"].values.flatten() if hasattr(df["High"], 'values') else df["High"]
        l = df["Low"].values.flatten() if hasattr(df["Low"], 'values') else df["Low"]
        o = df["Open"].values.flatten() if hasattr(df["Open"], 'values') else df["Open"]
        v = df["Volume"].values.flatten() if hasattr(df["Volume"], 'values') else df["Volume"]

        close = pd.Series(c, index=df.index)
        high = pd.Series(h, index=df.index)
        low = pd.Series(l, index=df.index)
        opn = pd.Series(o, index=df.index)
        volume = pd.Series(v, index=df.index)

        feats = {}

        # 1-5: Returns
        for p in [1, 3, 5, 10, 20]:
            feats[f"return_{p}d"] = close.pct_change(p)

        # 6-8: Lagged returns
        ret_1d = close.pct_change(1)
        feats["ret_lag_1"] = ret_1d.shift(1)
        feats["ret_lag_2"] = ret_1d.shift(2)
        feats["ret_lag_3"] = ret_1d.shift(3)

        # 9: ret_lag_5 (not in original list but shift(5))
        feats["ret_lag_5"] = ret_1d.shift(5)

        # 10-13: SMA distances
        for p in [10, 20, 50, 200]:
            sma = close.rolling(p).mean()
            feats[f"sma_{p}_dist"] = (close - sma) / sma.replace(0, 1e-10)

        # 14-16: EMA distances
        for p in [10, 20, 50]:
            ema = close.ewm(span=p).mean()
            feats[f"ema_{p}_dist"] = (close - ema) / ema.replace(0, 1e-10)

        # 17-18: EMA crosses
        ema10 = close.ewm(span=10).mean()
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        feats["ema_10_20_cross"] = (ema10 - ema20) / ema20.replace(0, 1e-10)
        feats["ema_20_50_cross"] = (ema20 - ema50) / ema50.replace(0, 1e-10)

        # 19: Golden cross distance
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        feats["golden_cross_dist"] = (sma50 - sma200) / sma200.replace(0, 1e-10)

        # 20-21: RSI
        delta = close.diff()
        gain14 = delta.where(delta > 0, 0).rolling(14).mean()
        loss14 = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs14 = gain14 / loss14.replace(0, 1e-10)
        feats["rsi_14"] = 100 - (100 / (1 + rs14))

        gain7 = delta.where(delta > 0, 0).rolling(7).mean()
        loss7 = (-delta.where(delta < 0, 0)).rolling(7).mean()
        rs7 = gain7 / loss7.replace(0, 1e-10)
        feats["rsi_7"] = 100 - (100 / (1 + rs7))

        # 22-24: MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()
        feats["macd"] = macd
        feats["macd_signal"] = macd_signal
        feats["macd_hist"] = macd - macd_signal

        # 25: Williams %R
        hh14 = high.rolling(14).max()
        ll14 = low.rolling(14).min()
        feats["willr_14"] = -100 * (hh14 - close) / (hh14 - ll14).replace(0, 1e-10)

        # 26-28: ADX, DI+, DI-
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        plus_dm = high.diff().where(lambda x: x > 0, 0)
        minus_dm = (-low.diff()).where(lambda x: x > 0, 0)
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr14.replace(0, 1e-10))
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr14.replace(0, 1e-10))
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10))
        feats["adx"] = dx.rolling(14).mean()
        feats["di_plus"] = plus_di
        feats["di_minus"] = minus_di

        # 29-30: ROC
        feats["roc_10"] = close.pct_change(10) * 100
        feats["roc_20"] = close.pct_change(20) * 100

        # 31: ATR ratio
        feats["atr_ratio"] = atr14 / close.replace(0, 1e-10)

        # 32-35: Bollinger Bands
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        feats["bb_upper_dist"] = (bb_upper - close) / close.replace(0, 1e-10)
        feats["bb_lower_dist"] = (close - bb_lower) / close.replace(0, 1e-10)
        feats["bb_width"] = (bb_upper - bb_lower) / sma20.replace(0, 1e-10)
        feats["bb_pct"] = (close - bb_lower) / (bb_upper - bb_lower).replace(0, 1e-10)

        # 36-38: Realized volatility
        daily_ret = close.pct_change()
        feats["rvol_10"] = daily_ret.rolling(10).std()
        feats["rvol_20"] = daily_ret.rolling(20).std()
        feats["rvol_60"] = daily_ret.rolling(60).std()

        # 39: Vol ratio (short/long)
        feats["vol_ratio"] = feats["rvol_10"] / feats["rvol_60"].replace(0, 1e-10)

        # 40-42: Range features
        hh52 = high.rolling(252).max()
        ll52 = low.rolling(252).min()
        feats["range_ratio"] = (high - low) / close.replace(0, 1e-10)
        feats["range_position"] = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min()).replace(0, 1e-10)
        feats["range_pos_52w"] = (close - ll52) / (hh52 - ll52).replace(0, 1e-10)

        # 43-44: Volume features
        vol_sma20 = volume.rolling(20).mean()
        feats["volume_ratio"] = volume / vol_sma20.replace(0, 1e-10)
        feats["volume_change"] = volume.pct_change()

        # 45-46: Candle features
        body = (close - opn).abs()
        wick = high - low
        feats["body_ratio"] = body / wick.replace(0, 1e-10)
        feats["candle_dir"] = (close > opn).astype(float)

        # 47-48: Consecutive up/down
        up = (close > close.shift(1)).astype(float)
        down = (close < close.shift(1)).astype(float)
        consec_up = up.copy()
        consec_down = down.copy()
        for i in range(1, len(consec_up)):
            if up.iloc[i] == 1:
                consec_up.iloc[i] = consec_up.iloc[i - 1] + 1
            if down.iloc[i] == 1:
                consec_down.iloc[i] = consec_down.iloc[i - 1] + 1
        feats["consec_up"] = consec_up
        feats["consec_down"] = consec_down

        # 49-52: Time cyclical encoding
        idx = df.index.to_series()
        feats["dow_sin"] = np.sin(2 * np.pi * idx.dt.dayofweek / 5)
        feats["dow_cos"] = np.cos(2 * np.pi * idx.dt.dayofweek / 5)
        feats["month_sin"] = np.sin(2 * np.pi * idx.dt.month / 12)
        feats["month_cos"] = np.cos(2 * np.pi * idx.dt.month / 12)

        result = pd.DataFrame(feats, index=df.index)
        # Replace inf with NaN, then forward-fill and fill remaining with 0
        result = result.replace([np.inf, -np.inf], np.nan)
        result = result.ffill().fillna(0)
        # Drop only the initial warmup rows (need ~252 for 52w range)
        result = result.iloc[252:]
        return result

    def _get_observation(self, features_row, regime=0, position=0):
        """Build observation vector matching training format."""
        vals = features_row.values.astype(np.float32)
        regime_oh = np.zeros(3, dtype=np.float32)
        regime_oh[regime] = 1.0
        extra = np.array([position, 0.0, 0.0], dtype=np.float32)
        obs = np.concatenate([vals, regime_oh, extra])
        return obs

    def _ensemble_vote(self, obs):
        """Get majority vote from PPO, A2C, SAC."""
        votes = []
        details = []

        if self.ppo:
            action, _ = self.ppo.predict(obs, deterministic=True)
            a = int(action)
            vote = {0: 0, 1: 1, 2: -1}.get(a, 0)
            votes.append(vote)
            details.append({"name": "PPO", "vote": vote, "label": SIGNAL_LABELS[vote]})

        if self.a2c:
            action, _ = self.a2c.predict(obs, deterministic=True)
            a = int(action)
            vote = {0: 0, 1: 1, 2: -1}.get(a, 0)
            votes.append(vote)
            details.append({"name": "A2C", "vote": vote, "label": SIGNAL_LABELS[vote]})

        if self.sac:
            action, _ = self.sac.predict(obs, deterministic=True)
            # SAC uses continuous action space [-1, 1]
            a = float(action[0]) if hasattr(action, '__len__') else float(action)
            vote = 1 if a > 0.3 else (-1 if a < -0.3 else 0)
            votes.append(vote)
            details.append({"name": "SAC", "vote": vote, "label": SIGNAL_LABELS[vote]})

        if not votes:
            return 0, 0.0, details

        total = sum(votes)
        if total >= 2:
            signal = 1
        elif total <= -2:
            signal = -1
        else:
            signal = 0

        agreement = sum(1 for v in votes if v == signal) / len(votes)
        return signal, agreement, details

    def _compute_entry_score(self, h1_feats, signal, regime):
        """Compute H1 entry score (0-9+) with reasons."""
        if h1_feats is None or h1_feats.empty:
            return 0, ["No H1 data available"]

        row = h1_feats.iloc[-1]
        score = 0
        reasons = []

        rsi = row.get("rsi_14", 50)
        macd = row.get("macd", 0)
        bb_pct = row.get("bb_pct", 0.5)
        vol_ratio = row.get("volume_ratio", 1.0) if "volume_ratio" in row else row.get("vol_ratio", 1.0)
        ema_cross = row.get("ema_10_20_cross", 0) if "ema_10_20_cross" in row else (row.get("ema_10_dist", 0) - row.get("ema_20_dist", 0))

        if signal == 1:  # LONG
            if rsi < 40:
                score += 2; reasons.append(f"RSI {rsi:.0f} — Oversold bounce (+2)")
            elif rsi < 50:
                score += 1; reasons.append(f"RSI {rsi:.0f} — Neutral (+1)")
            if macd > 0:
                score += 1; reasons.append("MACD positive (+1)")
            if ema_cross > 0:
                score += 1; reasons.append("EMA cross bullish (+1)")
            if bb_pct < 0.3:
                score += 2; reasons.append(f"BB %B {bb_pct:.2f} — Lower band (+2)")
            elif bb_pct < 0.5:
                score += 1; reasons.append(f"BB %B {bb_pct:.2f} — Below mid (+1)")
            if regime == 0:
                score += 2; reasons.append("Uptrend regime (+2)")
            elif regime == 1:
                score -= 3; reasons.append("Downtrend regime (-3)")
        elif signal == -1:  # SHORT
            if rsi > 60:
                score += 2; reasons.append(f"RSI {rsi:.0f} — Overbought (+2)")
            elif rsi > 50:
                score += 1; reasons.append(f"RSI {rsi:.0f} — Neutral (+1)")
            if macd < 0:
                score += 1; reasons.append("MACD negative (+1)")
            if ema_cross < 0:
                score += 1; reasons.append("EMA cross bearish (+1)")
            if bb_pct > 0.7:
                score += 2; reasons.append(f"BB %B {bb_pct:.2f} — Upper band (+2)")
            elif bb_pct > 0.5:
                score += 1; reasons.append(f"BB %B {bb_pct:.2f} — Above mid (+1)")
            if regime == 1:
                score += 2; reasons.append("Downtrend regime (+2)")
            elif regime == 0:
                score -= 3; reasons.append("Uptrend regime (-3)")

        if vol_ratio > 1.2:
            score += 1; reasons.append(f"Volume ratio {vol_ratio:.2f} — Confirmed (+1)")

        now = datetime.now()
        hour = now.hour
        if 13 <= hour <= 20:
            score += 1; reasons.append("NY session active (+1)")
        elif 7 <= hour <= 16:
            score += 1; reasons.append("London session active (+1)")

        return max(score, 0), reasons

    def _compute_5d_outlook(self, daily_feats):
        """Compute 5-day directional outlook from indicator momentum."""
        if len(daily_feats) < 10:
            return {"direction": "Neutral", "strength": 50, "factors": []}

        last5 = daily_feats.iloc[-5:]
        last = daily_feats.iloc[-1]
        prev5 = daily_feats.iloc[-6] if len(daily_feats) > 5 else daily_feats.iloc[0]

        score = 0
        factors = []

        # Trend: SMA distances trending
        for sma in ["sma_20_dist", "sma_50_dist"]:
            if sma in last5.columns:
                delta = float(last[sma]) - float(prev5[sma])
                if delta > 0.005:
                    score += 10; factors.append(f"{sma.replace('_dist','').upper()} distance expanding bullish")
                elif delta < -0.005:
                    score -= 10; factors.append(f"{sma.replace('_dist','').upper()} distance expanding bearish")

        # EMA cross direction
        if "ema_10_20_cross" in last.index:
            cross = float(last["ema_10_20_cross"])
            if cross > 0.005:
                score += 15; factors.append("Short-term EMA cross bullish")
            elif cross < -0.005:
                score -= 15; factors.append("Short-term EMA cross bearish")

        if "ema_20_50_cross" in last.index:
            cross = float(last["ema_20_50_cross"])
            if cross > 0.005:
                score += 10; factors.append("Medium-term EMA cross bullish")
            elif cross < -0.005:
                score -= 10; factors.append("Medium-term EMA cross bearish")

        # RSI momentum (slope over 5 bars)
        if "rsi_14" in last5.columns:
            rsi_now = float(last["rsi_14"])
            rsi_prev = float(prev5["rsi_14"])
            rsi_delta = rsi_now - rsi_prev
            if rsi_now < 30:
                score += 15; factors.append(f"RSI {rsi_now:.0f} — Oversold, reversal likely")
            elif rsi_now > 70:
                score -= 15; factors.append(f"RSI {rsi_now:.0f} — Overbought, pullback likely")
            elif rsi_delta > 5:
                score += 8; factors.append(f"RSI rising ({rsi_delta:+.0f} over 5 bars)")
            elif rsi_delta < -5:
                score -= 8; factors.append(f"RSI falling ({rsi_delta:+.0f} over 5 bars)")

        # MACD histogram slope
        if "macd_hist" in last5.columns:
            hist_vals = last5["macd_hist"].values
            hist_slope = float(hist_vals[-1]) - float(hist_vals[0])
            if hist_slope > 0 and float(hist_vals[-1]) > 0:
                score += 12; factors.append("MACD histogram rising and positive")
            elif hist_slope < 0 and float(hist_vals[-1]) < 0:
                score -= 12; factors.append("MACD histogram falling and negative")
            elif hist_slope > 0:
                score += 6; factors.append("MACD histogram improving")
            elif hist_slope < 0:
                score -= 6; factors.append("MACD histogram deteriorating")

        # ROC direction
        if "roc_10" in last.index:
            roc = float(last["roc_10"])
            if roc > 3:
                score += 8; factors.append(f"10-day momentum strong ({roc:+.1f}%)")
            elif roc < -3:
                score -= 8; factors.append(f"10-day momentum weak ({roc:+.1f}%)")

        # Bollinger Band position
        if "bb_pct" in last.index:
            bbp = float(last["bb_pct"])
            if bbp < 0.2:
                score += 10; factors.append("Price near lower Bollinger Band — bounce potential")
            elif bbp > 0.8:
                score -= 10; factors.append("Price near upper Bollinger Band — resistance")

        # ADX trend strength
        if "adx" in last.index:
            adx = float(last["adx"])
            if adx > 25:
                factors.append(f"Strong trend (ADX {adx:.0f})")
            else:
                factors.append(f"Weak trend (ADX {adx:.0f}) — range-bound")

        # Golden cross
        if "golden_cross_dist" in last.index:
            gc = float(last["golden_cross_dist"])
            if gc > 0.01:
                score += 5; factors.append("Above golden cross — long-term bullish")
            elif gc < -0.01:
                score -= 5; factors.append("Below golden cross — long-term bearish")

        # Normalize score to 0-100 strength (50 = neutral)
        strength = max(0, min(100, 50 + score))
        if strength >= 60:
            direction = "Bullish"
        elif strength <= 40:
            direction = "Bearish"
        else:
            direction = "Neutral"

        return {
            "direction": direction,
            "strength": strength,
            "factors": factors[:6],
        }

    def _classify_volatility(self, daily_feats):
        """Classify current volatility as High/Normal/Low."""
        if "rvol_20" not in daily_feats.columns or len(daily_feats) < 60:
            return "Normal"
        current = float(daily_feats["rvol_20"].iloc[-1])
        historical = daily_feats["rvol_20"].iloc[-60:].values
        pct = (historical < current).sum() / len(historical)
        if pct > 0.75:
            return "High"
        elif pct < 0.25:
            return "Low"
        return "Normal"

    def predict(self, symbol: str) -> dict:
        """Full prediction pipeline: data → features → ensemble → score."""
        if not self.loaded:
            raise ValueError("DRL models not loaded")

        daily, h1, ticker = self._get_market_data(symbol)
        daily_feats = self._compute_features(daily)
        h1_feats = self._compute_features(h1) if not h1.empty else None

        if daily_feats.empty:
            raise ValueError(f"Insufficient data for {symbol}")

        # Regime detection
        regime = 0
        if self.hmm is not None:
            try:
                regime_features = daily_feats[["return_1d", "rvol_20"]].iloc[-60:].values
                states = self.hmm.predict(regime_features)
                regime = int(states[-1])
            except Exception:
                regime = 0

        # Build observation and get ensemble vote
        obs = self._get_observation(daily_feats.iloc[-1], regime=regime)
        signal, confidence, votes = self._ensemble_vote(obs)

        # Entry score
        entry_score, entry_reasons = self._compute_entry_score(h1_feats, signal, regime)

        # 5-day outlook
        outlook = self._compute_5d_outlook(daily_feats)

        # Current price and previous close
        close = float(daily.iloc[-1]["Close"])
        if hasattr(close, '__iter__'):
            close = float(list(close)[0])
        prev_close = float(daily.iloc[-2]["Close"]) if len(daily) > 1 else close
        if hasattr(prev_close, '__iter__'):
            prev_close = float(list(prev_close)[0])
        price_change = round(close - prev_close, 2)
        price_change_pct = round((price_change / prev_close) * 100, 2) if prev_close else 0

        # Volatility classification
        volatility_level = self._classify_volatility(daily_feats)

        # Risk levels from ATR
        atr = float(daily_feats["atr_ratio"].iloc[-1]) * close

        if signal == 1:
            sl = close - 4 * atr
            tp = close + 6 * atr
        elif signal == -1:
            sl = close + 4 * atr
            tp = close - 6 * atr
        else:
            sl = close - 4 * atr
            tp = close + 6 * atr

        # Key indicators for display
        last_row = daily_feats.iloc[-1]
        indicators = {}
        indicator_map = {
            "rsi_14": "RSI 14",
            "macd": "MACD",
            "bb_pct": "BB %B",
            "adx": "ADX",
            "ema_10_20_cross": "EMA Cross",
            "vol_ratio": "Vol Ratio",
        }
        for col, label in indicator_map.items():
            if col in last_row:
                indicators[label] = round(float(last_row[col]), 2)

        return {
            "signal": signal,
            "signal_label": SIGNAL_LABELS[signal],
            "confidence": round(confidence, 2),
            "votes": votes,
            "regime": {"state": regime, "label": REGIME_LABELS.get(regime, "Unknown")},
            "entry_score": entry_score,
            "entry_reasons": entry_reasons,
            "outlook": outlook,
            "risk": {
                "atr": round(atr, 1),
                "stop_loss": round(sl, 1),
                "take_profit": round(tp, 1),
            },
            "indicators": indicators,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "volatility_level": volatility_level,
            "events": {
                "next_event": None,
                "hours_until": None,
                "shock_active": False,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "price": round(close, 2),
        }

    def get_upcoming_events(self, currencies: list) -> list:
        """Return upcoming economic events filtered by currencies."""
        # Static event calendar (in production, fetch from API)
        from datetime import timedelta
        now = datetime.now(timezone.utc)

        STATIC_EVENTS = [
            {"title": "FOMC Rate Decision", "currency": "USD", "impact": "high", "offset_days": 12},
            {"title": "Non-Farm Payrolls", "currency": "USD", "impact": "high", "offset_days": 5},
            {"title": "CPI YoY", "currency": "USD", "impact": "high", "offset_days": 18},
            {"title": "GDP QoQ", "currency": "USD", "impact": "medium", "offset_days": 25},
            {"title": "ECB Rate Decision", "currency": "EUR", "impact": "high", "offset_days": 8},
            {"title": "BoE Rate Decision", "currency": "GBP", "impact": "high", "offset_days": 15},
            {"title": "Retail Sales MoM", "currency": "USD", "impact": "medium", "offset_days": 3},
            {"title": "Initial Jobless Claims", "currency": "USD", "impact": "medium", "offset_days": 1},
            {"title": "PMI Manufacturing", "currency": "USD", "impact": "medium", "offset_days": 7},
            {"title": "Consumer Confidence", "currency": "USD", "impact": "low", "offset_days": 10},
        ]

        events = []
        for ev in STATIC_EVENTS:
            if ev["currency"] in currencies or ev["currency"] == "USD":
                event_time = now + timedelta(days=ev["offset_days"])
                events.append({
                    "title": ev["title"],
                    "currency": ev["currency"],
                    "impact": ev["impact"],
                    "time": event_time.strftime("%b %d, %H:%M UTC"),
                    "forecast": None,
                    "previous": None,
                })

        return sorted(events, key=lambda x: x["time"])[:10]
