"""
Backtesting Engine

Simulates trading using each model's signals and computes financial performance metrics.
Compares against a buy-and-hold baseline strategy.

Metrics:
- Total Return (%)
- Sharpe Ratio (annualized, risk-free rate = 0)
- Maximum Drawdown (%)
- Win Rate of signals
- Number of trades
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Optional
import json
import logging

from ai.config import INITIAL_CAPITAL, COMMISSION_PCT, SAVED_MODELS_DIR

logger = logging.getLogger(__name__)

FIGURES_DIR = SAVED_MODELS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)


def backtest_strategy(
    prices: np.ndarray,
    predictions: np.ndarray,
    threshold: float = 0.5,
    initial_capital: float = INITIAL_CAPITAL,
    commission: float = COMMISSION_PCT,
) -> dict:
    """
    Simulate a long-only trading strategy based on model predictions.

    Strategy:
    - If prediction > threshold (UP): go long (buy)
    - If prediction <= threshold (DOWN): stay out (cash)
    - Commission charged on each entry/exit

    Args:
        prices: Array of closing prices (aligned with predictions)
        predictions: Model probability predictions (0 to 1)
        threshold: Buy threshold (default 0.5)
        initial_capital: Starting capital
        commission: Transaction cost as fraction (0.001 = 0.1%)

    Returns:
        Dictionary with performance metrics and equity curve
    """
    n = len(prices)
    signals = (predictions >= threshold).astype(int)

    # Track equity
    equity = np.zeros(n)
    equity[0] = initial_capital
    position = 0  # 0 = out, 1 = in
    trades = 0

    for i in range(1, n):
        daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]

        # Check for signal change (entry/exit)
        if signals[i] != position:
            trades += 1
            position = signals[i]
            # Apply commission
            equity[i] = equity[i - 1] * (1 - commission)
        else:
            equity[i] = equity[i - 1]

        # If in position, apply daily return
        if position == 1:
            equity[i] *= (1 + daily_return)

    # Calculate metrics
    total_return = (equity[-1] - initial_capital) / initial_capital * 100
    daily_returns = np.diff(equity) / equity[:-1]
    daily_returns = daily_returns[~np.isnan(daily_returns)]

    sharpe = _calculate_sharpe(daily_returns)
    max_drawdown = _calculate_max_drawdown(equity)

    # Signal accuracy
    actual_direction = (np.diff(prices) > 0).astype(int)
    signal_accuracy = np.mean(signals[1:] == actual_direction) if len(actual_direction) > 0 else 0

    return {
        "total_return_pct": float(total_return),
        "sharpe_ratio": float(sharpe),
        "max_drawdown_pct": float(max_drawdown),
        "total_trades": int(trades),
        "signal_accuracy": float(signal_accuracy),
        "final_equity": float(equity[-1]),
        "initial_capital": float(initial_capital),
        "equity_curve": equity.tolist(),
    }


def backtest_buy_and_hold(
    prices: np.ndarray,
    initial_capital: float = INITIAL_CAPITAL,
) -> dict:
    """Buy-and-hold baseline: buy on day 1, hold until end."""
    equity = initial_capital * (prices / prices[0])
    total_return = (equity[-1] - initial_capital) / initial_capital * 100
    daily_returns = np.diff(equity) / equity[:-1]
    sharpe = _calculate_sharpe(daily_returns)
    max_drawdown = _calculate_max_drawdown(equity)

    return {
        "total_return_pct": float(total_return),
        "sharpe_ratio": float(sharpe),
        "max_drawdown_pct": float(max_drawdown),
        "total_trades": 1,
        "final_equity": float(equity[-1]),
        "initial_capital": float(initial_capital),
        "equity_curve": equity.tolist(),
    }


def run_full_backtest(
    prices: np.ndarray,
    model_predictions: dict[str, np.ndarray],
    dates: Optional[pd.DatetimeIndex] = None,
    save: bool = True,
) -> dict:
    """
    Run backtesting for all models and the baseline.

    Args:
        prices: Test set closing prices
        model_predictions: Dict mapping model name → prediction probabilities
        dates: Optional date index for the x-axis
        save: Whether to save results and plots

    Returns:
        Dictionary with all backtest results
    """
    results = {}

    # Baseline
    baseline = backtest_buy_and_hold(prices)
    results["Buy & Hold"] = baseline
    logger.info(f"Buy & Hold: Return={baseline['total_return_pct']:.2f}% | Sharpe={baseline['sharpe_ratio']:.2f}")

    # Each model
    for name, predictions in model_predictions.items():
        # Align lengths (LSTM might have fewer predictions due to sequence windowing)
        if len(predictions) < len(prices):
            offset = len(prices) - len(predictions)
            bt = backtest_strategy(prices[offset:], predictions)
        else:
            bt = backtest_strategy(prices[:len(predictions)], predictions)

        results[name] = bt
        logger.info(f"{name}: Return={bt['total_return_pct']:.2f}% | "
                     f"Sharpe={bt['sharpe_ratio']:.2f} | "
                     f"MaxDD={bt['max_drawdown_pct']:.2f}% | "
                     f"Trades={bt['total_trades']}")

    # Plot equity curves
    if save:
        _plot_equity_curves(results, dates)
        _plot_backtest_comparison(results)
        _save_backtest_results(results)

    return results


def _calculate_sharpe(daily_returns: np.ndarray, trading_days: int = 252) -> float:
    """Annualized Sharpe Ratio (assuming risk-free rate = 0)."""
    if len(daily_returns) == 0 or np.std(daily_returns) == 0:
        return 0.0
    return float(np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(trading_days))


def _calculate_max_drawdown(equity: np.ndarray) -> float:
    """Maximum peak-to-trough decline (percentage)."""
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak * 100
    return float(np.max(drawdown))


def _plot_equity_curves(
    results: dict,
    dates: Optional[pd.DatetimeIndex] = None,
) -> plt.Figure:
    """Plot all equity curves on one chart."""
    fig, ax = plt.subplots(figsize=(14, 7))

    colors = {"Buy & Hold": "#94a3b8", "LSTM": "#2563eb", "Random Forest": "#16a34a", "XGBoost": "#dc2626"}
    linestyles = {"Buy & Hold": "--", "LSTM": "-", "Random Forest": "-", "XGBoost": "-"}

    for name, bt in results.items():
        equity = bt["equity_curve"]
        x = dates[:len(equity)] if dates is not None else range(len(equity))
        ax.plot(
            x, equity,
            label=f"{name} ({bt['total_return_pct']:+.1f}%)",
            color=colors.get(name, "#666"),
            linestyle=linestyles.get(name, "-"),
            linewidth=2,
        )

    ax.set_xlabel("Date" if dates is not None else "Trading Days")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_title("Backtesting — Equity Curves")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    if dates is not None:
        fig.autofmt_xdate()

    fig.tight_layout()

    path = FIGURES_DIR / "backtest_equity_curves.png"
    fig.savefig(path, bbox_inches="tight")
    logger.info(f"Saved: {path}")
    return fig


def _plot_backtest_comparison(results: dict) -> plt.Figure:
    """Bar chart comparing backtest metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    names = list(results.keys())
    colors = ["#94a3b8", "#2563eb", "#16a34a", "#dc2626"][:len(names)]

    # Total Return
    returns = [results[n]["total_return_pct"] for n in names]
    axes[0].bar(names, returns, color=colors)
    axes[0].set_title("Total Return (%)")
    axes[0].grid(True, axis="y", alpha=0.3)

    # Sharpe Ratio
    sharpes = [results[n]["sharpe_ratio"] for n in names]
    axes[1].bar(names, sharpes, color=colors)
    axes[1].set_title("Sharpe Ratio")
    axes[1].grid(True, axis="y", alpha=0.3)

    # Max Drawdown
    drawdowns = [results[n]["max_drawdown_pct"] for n in names]
    axes[2].bar(names, drawdowns, color=colors)
    axes[2].set_title("Max Drawdown (%)")
    axes[2].grid(True, axis="y", alpha=0.3)

    for ax in axes:
        ax.tick_params(axis="x", rotation=15)

    fig.suptitle("Backtesting Performance Comparison", fontsize=14, y=1.02)
    fig.tight_layout()

    path = FIGURES_DIR / "backtest_comparison.png"
    fig.savefig(path, bbox_inches="tight")
    logger.info(f"Saved: {path}")
    return fig


def _save_backtest_results(results: dict):
    """Save backtest results to JSON (without equity curves to save space)."""
    serializable = {}
    for name, bt in results.items():
        serializable[name] = {k: v for k, v in bt.items() if k != "equity_curve"}

    path = SAVED_MODELS_DIR / "backtest_results.json"
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)
    logger.info(f"Saved: {path}")
