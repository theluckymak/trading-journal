"""
Train Chart Pattern CNN — Full pipeline

Steps:
1. Generate labeled chart images from historical data using SMC detector
2. Train ResNet-18 transfer learning model
3. Evaluate and generate thesis figures
4. Save model + metrics

Run: cd F:\trading-journal\backend && python train_cnn.py
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = r"F:\trading-journal\backend\ai\cnn_dataset"
MODEL_DIR = r"F:\trading-journal\backend\ai\saved_models\cnn"
FIGURES_DIR = r"F:\trading-journal\backend\ai\saved_models\cnn\figures"

# Symbols — clean institutional instruments, optimal for 1H SMC detection
# Forex: 24/5 trading, zero gaps, 12k+ bars each
# Futures: near-24h, 11k+ bars each
SYMBOLS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X",  # Forex (cleanest)
    "ES=F", "NQ=F",                         # Index futures
]


def step1_generate_images():
    """Generate labeled chart images from historical data."""
    from ai.cnn.chart_generator import generate_training_dataset
    
    print("\n" + "="*60)
    print("STEP 1: Generating Training Images")
    print("="*60)
    
    stats = generate_training_dataset(
        symbols=SYMBOLS,
        output_dir=DATASET_DIR,
        window_size=60,      # 60 candles per chart (60 hours ≈ 2.5 trading days)
        step=5,              # Every 5 bars
        days_back=729,       # Max 1H history on yfinance
        interval="1h",       # Hourly timeframe — SMC patterns are frequent here
        forward_bars=10,     # Look 10 bars ahead for outcome
        swing_lookback=5,
    )
    
    print(f"\n  Dataset Statistics:")
    print(f"    Bullish: {stats.get('bullish', 0)}")
    print(f"    Bearish: {stats.get('bearish', 0)}")
    print(f"    Neutral: {stats.get('neutral', 0)}")
    print(f"    Total:   {stats.get('total', 0)}")
    print(f"    Errors:  {stats.get('errors', 0)}")
    
    return stats


def step2_train_model(resume=False):
    """Train the CNN on generated images."""
    from ai.cnn.model import train_model
    
    print("\n" + "="*60)
    print("STEP 2: Training CNN Model" + (" (RESUMING)" if resume else ""))
    print("="*60)
    
    metrics = train_model(
        data_dir=DATASET_DIR,
        save_dir=MODEL_DIR,
        epochs=50,
        batch_size=32,
        lr=0.0005,
        patience=12,
        val_split=0.15,
        test_split=0.15,
        resume=resume,
    )
    
    return metrics


def step3_generate_figures(metrics: dict):
    """Generate thesis-quality figures from training results."""
    os.makedirs(FIGURES_DIR, exist_ok=True)
    
    print("\n" + "="*60)
    print("STEP 3: Generating Thesis Figures")
    print("="*60)
    
    history = metrics["history"]
    config = metrics["config"]
    
    # Figure 1: Training/Validation Loss
    fig, ax = plt.subplots(figsize=(10, 6))
    epochs_range = range(1, len(history["train_loss"]) + 1)
    ax.plot(epochs_range, history["train_loss"], 'b-', label='Training Loss', linewidth=2)
    ax.plot(epochs_range, history["val_loss"], 'r-', label='Validation Loss', linewidth=2)
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Loss', fontsize=12)
    ax.set_title('CNN Training and Validation Loss', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "cnn_loss_curves.png"), dpi=150)
    plt.close()
    print("  ✓ Loss curves")
    
    # Figure 2: Training/Validation Accuracy
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(epochs_range, history["train_acc"], 'b-', label='Training Accuracy', linewidth=2)
    ax.plot(epochs_range, history["val_acc"], 'r-', label='Validation Accuracy', linewidth=2)
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Accuracy', fontsize=12)
    ax.set_title('CNN Training and Validation Accuracy', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "cnn_accuracy_curves.png"), dpi=150)
    plt.close()
    print("  ✓ Accuracy curves")
    
    # Figure 3: Per-class accuracy bar chart
    per_class = metrics["per_class_accuracy"]
    fig, ax = plt.subplots(figsize=(8, 5))
    classes = list(per_class.keys())
    accuracies = [per_class[c] for c in classes]
    colors = ['#ef5350', '#26a69a', '#787b86']
    bars = ax.bar(classes, accuracies, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_ylabel('Accuracy', fontsize=12)
    ax.set_title('Per-Class Test Accuracy', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(axis='y', alpha=0.3)
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{acc:.1%}', ha='center', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "cnn_per_class_accuracy.png"), dpi=150)
    plt.close()
    print("  ✓ Per-class accuracy")
    
    # Figure 4: Model summary card
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis('off')
    summary_text = (
        f"CNN Chart Pattern Classifier — Results Summary\n"
        f"{'─' * 50}\n\n"
        f"Architecture:    ResNet-18 (Transfer Learning)\n"
        f"Input:           224×224 RGB candlestick chart images\n"
        f"Classes:         Bullish / Bearish / Neutral\n"
        f"Train size:      {config['train_size']:,} images\n"
        f"Val size:        {config['val_size']:,} images\n"
        f"Test size:       {config['test_size']:,} images\n"
        f"Epochs trained:  {config['epochs_trained']}\n"
        f"Batch size:      {config['batch_size']}\n"
        f"Learning rate:   {config['lr']}\n\n"
        f"Test Accuracy:   {metrics['test_accuracy']:.1%}\n"
        f"  Bullish:       {per_class.get('bullish', 0):.1%}\n"
        f"  Bearish:       {per_class.get('bearish', 0):.1%}\n"
        f"  Neutral:       {per_class.get('neutral', 0):.1%}\n"
    )
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "cnn_summary_card.png"), dpi=150)
    plt.close()
    print("  ✓ Summary card")
    
    print(f"\n  All figures saved to {FIGURES_DIR}")


def step4_test_inference():
    """Quick inference test on a sample image."""
    from ai.cnn.model import predict_chart
    
    print("\n" + "="*60)
    print("STEP 4: Testing Inference")
    print("="*60)
    
    model_path = os.path.join(MODEL_DIR, "chart_cnn.pth")
    if not os.path.exists(model_path):
        print("  ✗ No trained model found")
        return
    
    # Find a sample image
    for cls in ["bullish", "bearish", "neutral"]:
        cls_dir = os.path.join(DATASET_DIR, cls)
        if os.path.exists(cls_dir):
            images = [f for f in os.listdir(cls_dir) if f.endswith('.png')]
            if images:
                sample = os.path.join(cls_dir, images[0])
                result = predict_chart(sample, model_path)
                print(f"  Sample ({cls}): {sample}")
                print(f"    Prediction: {result['prediction']} ({result['confidence']:.1%})")
                print(f"    Probabilities: {result['probabilities']}")
                break


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Resume training from checkpoint")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation (use existing dataset)")
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════╗")
    print("║  Chart Pattern CNN — Full Training Pipeline      ║")
    print("║  Module 2: SMC Pattern Recognition               ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # Step 1: Generate images (skip if --skip-images or --resume)
    if not args.skip_images and not args.resume:
        stats = step1_generate_images()
        total = stats.get("total", 0)
        if total < 100:
            print(f"\n  ⚠ Only {total} images generated — need more for training.")
            if total < 30:
                print("    ✗ Too few images, cannot train. Exiting.")
                return
    else:
        # Count existing images
        import glob
        total = len(glob.glob(os.path.join(DATASET_DIR, "**", "*.png"), recursive=True))
        print(f"\n  Skipping image generation. Using existing dataset: {total} images")
    
    # Step 2: Train
    metrics = step2_train_model(resume=args.resume)
    
    # Step 3: Figures
    step3_generate_figures(metrics)
    
    # Step 4: Quick test
    step4_test_inference()
    
    print("\n" + "="*60)
    print("DONE!")
    print(f"  Model:   {os.path.join(MODEL_DIR, 'chart_cnn.pth')}")
    print(f"  Metrics: {os.path.join(MODEL_DIR, 'cnn_metrics.json')}")
    print(f"  Figures: {FIGURES_DIR}")
    print("="*60)


if __name__ == "__main__":
    main()
