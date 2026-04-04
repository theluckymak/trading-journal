"""
Model Evaluation & Comparison Suite

Generates all metrics and visualizations needed for the thesis:
- Classification metrics (accuracy, precision, recall, F1, AUC-ROC)
- Confusion matrices
- ROC curves
- Model comparison tables
- Training loss curves (LSTM)
- Feature importance charts
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve,
)
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
import json
import logging

from ai.config import SAVED_MODELS_DIR

logger = logging.getLogger(__name__)

FIGURES_DIR = SAVED_MODELS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Consistent styling for thesis figures
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "figure.dpi": 150,
})


def evaluate_model(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    model_name: str,
    threshold: float = 0.5,
) -> dict:
    """
    Compute all classification metrics for a single model.

    Args:
        y_true: True labels (0/1)
        y_pred_proba: Predicted probabilities of class 1 (UP)
        model_name: Name of the model (for display)
        threshold: Classification threshold (default 0.5)

    Returns:
        Dictionary with all metrics
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    metrics = {
        "model": model_name,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc_roc": float(roc_auc_score(y_true, y_pred_proba)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(y_true, y_pred, output_dict=True),
        "total_predictions": len(y_true),
        "positive_predictions": int(y_pred.sum()),
        "negative_predictions": int((1 - y_pred).sum()),
    }

    logger.info(f"\n{'='*50}")
    logger.info(f"  {model_name} Evaluation Results:")
    logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
    logger.info(f"  Precision: {metrics['precision']:.4f}")
    logger.info(f"  Recall:    {metrics['recall']:.4f}")
    logger.info(f"  F1 Score:  {metrics['f1_score']:.4f}")
    logger.info(f"  AUC-ROC:   {metrics['auc_roc']:.4f}")
    logger.info(f"{'='*50}")

    return metrics


def compare_models(results: dict[str, dict]) -> pd.DataFrame:
    """
    Create a comparison table of all models.

    Args:
        results: Dict mapping model name → metrics dict

    Returns:
        DataFrame with comparison table
    """
    rows = []
    for name, metrics in results.items():
        rows.append({
            "Model": name,
            "Accuracy": f"{metrics['accuracy']:.4f}",
            "Precision": f"{metrics['precision']:.4f}",
            "Recall": f"{metrics['recall']:.4f}",
            "F1 Score": f"{metrics['f1_score']:.4f}",
            "AUC-ROC": f"{metrics['auc_roc']:.4f}",
        })

    df = pd.DataFrame(rows)
    logger.info(f"\nModel Comparison:\n{df.to_string(index=False)}")
    return df


# ============================================================
# Visualization Functions (for thesis figures)
# ============================================================

def plot_confusion_matrices(results: dict[str, dict], save: bool = True) -> plt.Figure:
    """Plot confusion matrices for all 3 models side-by-side."""
    n_models = len(results)
    fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5))
    if n_models == 1:
        axes = [axes]

    for ax, (name, metrics) in zip(axes, results.items()):
        cm = np.array(metrics["confusion_matrix"])
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["DOWN", "UP"],
            yticklabels=["DOWN", "UP"],
            ax=ax,
        )
        ax.set_title(f"{name}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    fig.suptitle("Confusion Matrices — Model Comparison", fontsize=16, y=1.02)
    fig.tight_layout()

    if save:
        path = FIGURES_DIR / "confusion_matrices.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def plot_roc_curves(
    y_true: np.ndarray,
    predictions: dict[str, np.ndarray],
    save: bool = True,
) -> plt.Figure:
    """
    Plot ROC curves for all models overlaid on one chart.
    Includes AUC score in the legend.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = ["#2563eb", "#16a34a", "#dc2626"]
    for (name, y_proba), color in zip(predictions.items(), colors):
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        auc = roc_auc_score(y_true, y_proba)
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc:.4f})", color=color, linewidth=2)

    # Random baseline
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Random (AUC = 0.5)")

    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves — Model Comparison")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    if save:
        path = FIGURES_DIR / "roc_curves.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def plot_feature_importance(
    importance: dict[str, float],
    model_name: str,
    top_n: int = 15,
    save: bool = True,
) -> plt.Figure:
    """Plot horizontal bar chart of feature importance (top N features)."""
    sorted_feats = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
    names = [f[0] for f in sorted_feats][::-1]
    values = [f[1] for f in sorted_feats][::-1]

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.4)))
    bars = ax.barh(names, values, color="#2563eb", alpha=0.8)

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9)

    ax.set_xlabel("Importance")
    ax.set_title(f"Feature Importance — {model_name} (Top {top_n})")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()

    if save:
        path = FIGURES_DIR / f"feature_importance_{model_name.lower().replace(' ', '_')}.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def plot_lstm_training_history(history: dict, save: bool = True) -> plt.Figure:
    """Plot LSTM training and validation loss/accuracy curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    epochs = range(1, len(history["loss"]) + 1)

    # Loss curves
    ax1.plot(epochs, history["loss"], "b-", label="Training Loss", linewidth=2)
    ax1.plot(epochs, history["val_loss"], "r-", label="Validation Loss", linewidth=2)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss (Binary Cross-Entropy)")
    ax1.set_title("LSTM Training — Loss Curves")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Accuracy curves
    ax2.plot(epochs, history["accuracy"], "b-", label="Training Accuracy", linewidth=2)
    ax2.plot(epochs, history["val_accuracy"], "r-", label="Validation Accuracy", linewidth=2)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.set_title("LSTM Training — Accuracy Curves")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()

    if save:
        path = FIGURES_DIR / "lstm_training_history.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def plot_model_comparison_bar(results: dict[str, dict], save: bool = True) -> plt.Figure:
    """Bar chart comparing all metrics across models."""
    metrics_names = ["accuracy", "precision", "recall", "f1_score", "auc_roc"]
    display_names = ["Accuracy", "Precision", "Recall", "F1 Score", "AUC-ROC"]

    model_names = list(results.keys())
    x = np.arange(len(display_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#2563eb", "#16a34a", "#dc2626"]

    for i, (name, metrics) in enumerate(results.items()):
        values = [metrics[m] for m in metrics_names]
        ax.bar(x + i * width, values, width, label=name, color=colors[i], alpha=0.85)

    ax.set_ylabel("Score")
    ax.set_title("Model Performance Comparison")
    ax.set_xticks(x + width)
    ax.set_xticklabels(display_names)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(0.4, 0.75)

    fig.tight_layout()

    if save:
        path = FIGURES_DIR / "model_comparison_bar.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def plot_correlation_heatmap(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Correlation heatmap of all features (for EDA section of thesis)."""
    # Select numeric columns only, limit to key features
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Limit to avoid huge unreadable heatmap
    if len(numeric_cols) > 25:
        numeric_cols = numeric_cols[:25]

    corr = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(14, 12))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="RdBu_r", center=0, vmin=-1, vmax=1,
        square=True, linewidths=0.5, ax=ax,
        annot_kws={"size": 7},
    )
    ax.set_title("Feature Correlation Heatmap")
    fig.tight_layout()

    if save:
        path = FIGURES_DIR / "correlation_heatmap.png"
        fig.savefig(path, bbox_inches="tight")
        logger.info(f"Saved: {path}")

    return fig


def save_all_metrics(results: dict[str, dict], save_path: Optional[Path] = None):
    """Save all model metrics to JSON for API serving."""
    if save_path is None:
        save_path = SAVED_MODELS_DIR / "training_metrics.json"

    # Make JSON-serializable
    serializable = {}
    for name, metrics in results.items():
        serializable[name] = {
            k: v for k, v in metrics.items()
            if k != "classification_report"  # Too verbose for API
        }

    with open(save_path, "w") as f:
        json.dump(serializable, f, indent=2)

    logger.info(f"All metrics saved to {save_path}")
