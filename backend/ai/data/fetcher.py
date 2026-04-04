"""
Data Fetcher — Downloads historical OHLCV data from Yahoo Finance.

Data source: Yahoo Finance via yfinance library
Citation: "Yahoo Finance historical market data, accessed via yfinance (Aroussi, 2024)"
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def fetch_ohlcv(
    symbol: str,
    years: int = 5,
    interval: str = "1d",
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a given symbol.

    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'EURUSD=X', 'BTC-USD')
        years: Number of years of historical data
        interval: Data interval ('1d' for daily, '1h' for hourly, etc.)
        end_date: End date string 'YYYY-MM-DD'. Defaults to today.

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, plus metadata
    """
    if end_date is None:
        end = datetime.now()
    else:
        end = datetime.strptime(end_date, "%Y-%m-%d")

    start = end - timedelta(days=years * 365)

    logger.info(f"Fetching {symbol} data from {start.date()} to {end.date()}")

    ticker = yf.Ticker(symbol)
    df = ticker.history(
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval=interval,
        auto_adjust=True,   # Adjust for splits/dividends
    )

    if df.empty:
        raise ValueError(f"No data returned for symbol '{symbol}'. Check if symbol is valid.")

    # Clean up
    df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)  # Remove timezone for consistency
    df = df.sort_index()

    # Forward-fill missing values (standard financial convention)
    df = df.ffill()

    # Drop any remaining NaN rows (e.g., at the very start)
    df = df.dropna()

    logger.info(f"Fetched {len(df)} rows for {symbol} ({df.index[0].date()} → {df.index[-1].date()})")

    return df


def fetch_multiple_symbols(
    symbols: list[str],
    years: int = 5,
    interval: str = "1d",
) -> dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for multiple symbols.

    Returns:
        Dictionary mapping symbol → DataFrame
    """
    data = {}
    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, years=years, interval=interval)
            data[symbol] = df
            logger.info(f"✓ {symbol}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"✗ {symbol}: {e}")
    return data


def get_symbol_info(symbol: str) -> dict:
    """
    Get metadata about a symbol (name, currency, exchange, etc.)
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "symbol": symbol,
        "name": info.get("longName", info.get("shortName", symbol)),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", "Unknown"),
        "type": info.get("quoteType", "Unknown"),
    }
