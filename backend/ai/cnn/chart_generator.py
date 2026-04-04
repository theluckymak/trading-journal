"""
Chart Image Generator — Creates labeled candlestick chart images for CNN training.

Pipeline:
1. Take historical OHLCV data for multiple symbols/timeframes
2. For each window of N candles, render a candlestick chart image
3. Run SMC detector on the window to find patterns
4. Label the image based on detected setup + future outcome
5. Save as PNG with label in filename

This generates thousands of labeled images automatically — no manual labeling needed.
"""
import os
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
import yfinance as yf
from datetime import datetime, timedelta
import logging

from ai.smc.detector import SMCDetector

logger = logging.getLogger(__name__)

# Chart style matching typical trading platform look
CHART_STYLE = mpf.make_mpf_style(
    base_mpf_style='charles',
    marketcolors=mpf.make_marketcolors(
        up='#26a69a', down='#ef5350',
        edge={'up': '#26a69a', 'down': '#ef5350'},
        wick={'up': '#26a69a', 'down': '#ef5350'},
        volume='in',
    ),
    gridstyle='', gridcolor='#1e1e1e',
    facecolor='#131722',
    figcolor='#131722',
    edgecolor='#131722',
    rc={
        'axes.labelcolor': '#787b86',
        'xtick.color': '#787b86',
        'ytick.color': '#787b86',
    }
)

IMAGE_SIZE = (224, 224)  # CNN input size


def generate_chart_image(
    df_window: pd.DataFrame,
    save_path: str,
    show_volume: bool = True,
    figsize: tuple = (3, 3),
    dpi: int = 75,
) -> bool:
    """
    Render a candlestick chart from OHLCV data and save as image.
    
    Args:
        df_window: OHLCV DataFrame (must have DatetimeIndex)
        save_path: Path to save the PNG
        show_volume: Include volume bars
        figsize: Figure size in inches
        dpi: Resolution (75 dpi × 3 inches = 225px ≈ 224)
    
    Returns:
        True if saved successfully
    """
    try:
        # Ensure proper index
        if not isinstance(df_window.index, pd.DatetimeIndex):
            df_window.index = pd.to_datetime(df_window.index)
        
        kwargs = {
            'type': 'candle',
            'style': CHART_STYLE,
            'volume': show_volume and 'Volume' in df_window.columns,
            'figsize': figsize,
            'savefig': dict(fname=save_path, dpi=dpi, pad_inches=0.02,
                          bbox_inches='tight', facecolor='#131722'),
            'axisoff': True,  # Remove axis labels for cleaner CNN input
            'tight_layout': True,
            'warn_too_much_data': 9999,
        }
        
        mpf.plot(df_window, **kwargs)
        plt.close('all')
        return True
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        return False


def generate_training_dataset(
    symbols: list[str],
    output_dir: str,
    window_size: int = 60,
    step: int = 5,
    days_back: int = 729,
    interval: str = "1h",
    forward_bars: int = 10,
    swing_lookback: int = 5,
) -> dict:
    """
    Generate a complete labeled image dataset for CNN training.
    
    For each symbol:
    1. Fetch historical 1H (or other interval) data
    2. Slide a window across the data
    3. For each window: detect SMC patterns, determine label, render chart
    4. Save chart image in class-specific subfolder
    
    Args:
        symbols: List of ticker symbols
        output_dir: Root directory for dataset
        window_size: Number of candles per chart image
        step: Slide step (every N bars)
        days_back: How many days of history (max 729 for 1H on yfinance)
        interval: Data interval ("1h", "1d", etc.)
        forward_bars: Bars to look ahead for outcome labeling
        swing_lookback: Bars for swing detection
    
    Returns:
        Statistics dict
    """
    # Create class directories
    for cls in ["bullish", "bearish", "neutral"]:
        os.makedirs(os.path.join(output_dir, cls), exist_ok=True)
    
    stats = {"bullish": 0, "bearish": 0, "neutral": 0, "errors": 0, "total": 0}
    
    for symbol in symbols:
        print(f"  Processing {symbol}...")
        
        try:
            # Fetch data — 1H interval, up to 729 days back (yfinance limit)
            end = datetime.now()
            start = end - timedelta(days=days_back)
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start.strftime("%Y-%m-%d"),
                              end=end.strftime("%Y-%m-%d"),
                              interval=interval, auto_adjust=True)
            
            if df.empty or len(df) < window_size + forward_bars + 50:
                print(f"    ✗ Insufficient data ({len(df)} rows)")
                continue
            
            df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df = df.sort_index().ffill().dropna()
            
            # Run SMC detection on full dataset (pass timeframe for threshold scaling)
            detector = SMCDetector(df, swing_lookback=swing_lookback, timeframe=interval)
            detector.detect_all()
            
            # Print pattern counts for debugging
            summary = detector.summary()
            print(f"    Patterns found: {summary}")
            
            # Slide window
            n_windows = 0
            for start_idx in range(0, len(df) - window_size - forward_bars, step):
                end_idx = start_idx + window_size
                window = df.iloc[start_idx:end_idx].copy()
                
                # Get label from SMC detector
                label = detector.get_label_for_bar(end_idx - 1, forward_bars)
                if label is None:
                    continue
                
                # Generate image
                fname = f"{symbol}_{start_idx:05d}.png"
                save_path = os.path.join(output_dir, label, fname)
                
                if generate_chart_image(window, save_path):
                    stats[label] += 1
                    stats["total"] += 1
                    n_windows += 1
                else:
                    stats["errors"] += 1
            
            print(f"    ✓ Generated {n_windows} images")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            stats["errors"] += 1
    
    return stats


def generate_balanced_dataset(
    symbols: list[str],
    output_dir: str,
    target_per_class: int = 500,
    window_size: int = 80,
    years: int = 7,
    forward_bars: int = 10,
) -> dict:
    """
    Generate a balanced dataset (equal samples per class).
    Keeps generating until we have target_per_class for each class,
    or runs out of data.
    """
    for cls in ["bullish", "bearish", "neutral"]:
        os.makedirs(os.path.join(output_dir, cls), exist_ok=True)
    
    counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    max_neutral = target_per_class  # Cap neutral class
    
    for symbol in symbols:
        print(f"  Processing {symbol}...")
        
        try:
            end = datetime.now()
            start = end - timedelta(days=years * 365)
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start.strftime("%Y-%m-%d"),
                              end=end.strftime("%Y-%m-%d"),
                              interval="1d", auto_adjust=True)
            
            if df.empty or len(df) < window_size + forward_bars + 50:
                continue
            
            df = df.drop(columns=["Dividends", "Stock Splits"], errors="ignore")
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df = df.sort_index().ffill().dropna()
            
            detector = SMCDetector(df, swing_lookback=5)
            detector.detect_all()
            
            # Random order to avoid temporal bias in what gets sampled
            indices = list(range(0, len(df) - window_size - forward_bars, 2))
            np.random.shuffle(indices)
            
            for start_idx in indices:
                # Check if we have enough
                if all(counts[c] >= target_per_class for c in ["bullish", "bearish"]):
                    break
                
                end_idx = start_idx + window_size
                label = detector.get_label_for_bar(end_idx - 1, forward_bars)
                if label is None:
                    continue
                
                # Skip if this class is full
                if label == "neutral" and counts["neutral"] >= max_neutral:
                    continue
                if counts.get(label, 0) >= target_per_class:
                    continue
                
                window = df.iloc[start_idx:end_idx].copy()
                fname = f"{symbol}_{start_idx:05d}.png"
                save_path = os.path.join(output_dir, label, fname)
                
                if generate_chart_image(window, save_path):
                    counts[label] += 1
            
            print(f"    ✓ Counts so far: {counts}")
            
        except Exception as e:
            print(f"    ✗ {e}")
    
    return counts
