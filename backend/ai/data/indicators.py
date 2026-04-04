"""
Technical Indicators Calculator

Computes 15+ technical indicators from OHLCV data using the 'ta' library.
Each indicator has a well-defined mathematical formula suitable for academic citation.

References:
- Wilder, J.W. (1978). New Concepts in Technical Trading Systems. (RSI, ATR, ADX)
- Appel, G. (2005). Technical Analysis: Power Tools for Active Investors. (MACD)
- Bollinger, J. (2002). Bollinger on Bollinger Bands. (BB)
- Lane, G.C. (1984). Lane's Stochastics. (Stochastic Oscillator)
- Granville, J. (1963). Granville's New Key to Stock Market Profits. (OBV)
"""
import pandas as pd
import numpy as np
from ta import trend, momentum, volatility, volume
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to an OHLCV DataFrame.

    Args:
        df: DataFrame with Open, High, Low, Close, Volume columns

    Returns:
        DataFrame with original columns + all technical indicator columns
    """
    df = df.copy()

    # Ensure required columns exist
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    logger.info("Computing technical indicators...")

    # --- Moving Averages (Trend) ---
    df = _add_moving_averages(df)

    # --- RSI (Momentum) ---
    df = _add_rsi(df)

    # --- MACD (Trend/Momentum) ---
    df = _add_macd(df)

    # --- Bollinger Bands (Volatility) ---
    df = _add_bollinger_bands(df)

    # --- ATR (Volatility) ---
    df = _add_atr(df)

    # --- Stochastic Oscillator (Momentum) ---
    df = _add_stochastic(df)

    # --- On-Balance Volume (Volume) ---
    df = _add_obv(df)

    # --- ADX (Trend Strength) ---
    df = _add_adx(df)

    # --- CCI (Cyclical) ---
    df = _add_cci(df)

    # --- Williams %R (Momentum) ---
    df = _add_williams_r(df)

    # --- Rate of Change (Momentum) ---
    df = _add_roc(df)

    indicator_cols = [c for c in df.columns if c not in required]
    logger.info(f"Added {len(indicator_cols)} indicator columns")

    return df


def _add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Simple Moving Averages (SMA) and Exponential Moving Averages (EMA)"""
    close = df["Close"]

    # SMA: arithmetic mean over a rolling window
    for period in [5, 10, 20, 50, 200]:
        df[f"sma_{period}"] = close.rolling(window=period).mean()

    # EMA: exponentially weighted mean (more weight to recent prices)
    for period in [12, 26]:
        df[f"ema_{period}"] = close.ewm(span=period, adjust=False).mean()

    return df


def _add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Relative Strength Index (Wilder, 1978)
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss over 'period' days
    Range: 0-100. >70 = overbought, <30 = oversold
    """
    rsi_indicator = momentum.RSIIndicator(close=df["Close"], window=period)
    df["rsi_14"] = rsi_indicator.rsi()
    return df


def _add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Moving Average Convergence Divergence (Appel, 2005)
    MACD Line = EMA(12) - EMA(26)
    Signal Line = EMA(9) of MACD Line
    Histogram = MACD Line - Signal Line
    """
    macd_indicator = trend.MACD(
        close=df["Close"],
        window_slow=26,
        window_fast=12,
        window_sign=9,
    )
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_hist"] = macd_indicator.macd_diff()
    return df


def _add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Bollinger Bands (Bollinger, 2002)
    Middle Band = SMA(20)
    Upper Band = Middle + 2σ
    Lower Band = Middle - 2σ
    Width = (Upper - Lower) / Middle
    %B = (Price - Lower) / (Upper - Lower)
    """
    bb = volatility.BollingerBands(
        close=df["Close"],
        window=period,
        window_dev=std_dev,
    )
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()
    df["bb_pct"] = bb.bollinger_pband()
    return df


def _add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Average True Range (Wilder, 1978)
    True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    ATR = SMA(True Range, period)
    Measures market volatility.
    """
    atr_indicator = volatility.AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=period,
    )
    df["atr_14"] = atr_indicator.average_true_range()
    return df


def _add_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """
    Stochastic Oscillator (Lane, 1984)
    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA(%K, 3)
    Range: 0-100. >80 = overbought, <20 = oversold
    """
    stoch = momentum.StochasticOscillator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=k_period,
        smooth_window=d_period,
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    return df


def _add_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    On-Balance Volume (Granville, 1963)
    OBV += Volume if Close > PrevClose, else OBV -= Volume
    Relates volume flow to price changes.
    """
    obv_indicator = volume.OnBalanceVolumeIndicator(
        close=df["Close"],
        volume=df["Volume"],
    )
    df["obv"] = obv_indicator.on_balance_volume()
    return df


def _add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Average Directional Index (Wilder, 1978)
    Measures trend strength regardless of direction.
    Range: 0-100. >25 = trending, <20 = ranging
    """
    adx_indicator = trend.ADXIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=period,
    )
    df["adx_14"] = adx_indicator.adx()
    df["di_plus"] = adx_indicator.adx_pos()
    df["di_minus"] = adx_indicator.adx_neg()
    return df


def _add_cci(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Commodity Channel Index (Lambert, 1980)
    CCI = (Typical Price - SMA(TP)) / (0.015 * Mean Deviation)
    Measures deviation from statistical mean. >100 = overbought, <-100 = oversold
    """
    cci_indicator = trend.CCIIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=period,
    )
    df["cci_20"] = cci_indicator.cci()
    return df


def _add_williams_r(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Williams %R (Williams, 1979)
    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    Range: -100 to 0. <-80 = oversold, >-20 = overbought
    """
    willr = momentum.WilliamsRIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        lbp=period,
    )
    df["willr_14"] = willr.williams_r()
    return df


def _add_roc(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """
    Rate of Change (Price Momentum)
    ROC = ((Close - Close_n) / Close_n) * 100
    Measures percentage price change over n periods.
    """
    roc_indicator = momentum.ROCIndicator(
        close=df["Close"],
        window=period,
    )
    df["roc_10"] = roc_indicator.roc()
    return df
