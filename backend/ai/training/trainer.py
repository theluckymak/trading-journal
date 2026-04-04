"""
Unified Training Pipeline

Orchestrates the full training workflow:
1. Fetch data → 2. Engineer features → 3. Train all 3 models → 4. Evaluate → 5. Save
"""
import numpy as np
import json
import logging
from typing import Optional

from ai.data.fetcher import fetch_ohlcv
from ai.data.indicators import add_all_indicators
from ai.features.engineer import (
    build_features, create_target, get_feature_columns,
    time_series_split, scale_features,
    create_lstm_sequences, create_flat_features,
)
from ai.models.lstm_model import train_lstm
from ai.models.rf_model import train_rf
from ai.models.xgb_model import train_xgb
from ai.training.evaluate import (
    evaluate_model, compare_models, save_all_metrics,
    plot_confusion_matrices, plot_roc_curves,
    plot_feature_importance, plot_lstm_training_history,
    plot_model_comparison_bar, plot_correlation_heatmap,
)
from ai.config import SAVED_MODELS_DIR, DATA_YEARS, SEQUENCE_LENGTH

logger = logging.getLogger(__name__)


def train_all_models(
    symbol: str = "EURUSD=X",
    years: int = DATA_YEARS,
    tune_hyperparams: bool = True,
    generate_plots: bool = True,
) -> dict:
    """
    Complete training pipeline for all 3 models.

    Args:
        symbol: Trading symbol to train on
        years: Years of historical data
        tune_hyperparams: Run GridSearchCV for RF and XGBoost
        generate_plots: Generate thesis figures

    Returns:
        Dictionary with all training results and metrics
    """
    results = {}

    # ================================================================
    # Step 1: Fetch & Prepare Data
    # ================================================================
    logger.info(f"\n{'='*60}")
    logger.info(f"TRAINING PIPELINE — {symbol}")
    logger.info(f"{'='*60}")

    df = fetch_ohlcv(symbol, years=years)
    df = add_all_indicators(df)
    df = build_features(df)
    df = create_target(df)
    df = df.dropna()

    feature_columns = get_feature_columns(df)
    logger.info(f"Features: {len(feature_columns)} columns")
    logger.info(f"Dataset: {len(df)} rows")
    logger.info(f"Class balance: UP={df['target'].mean():.2%}")

    # Correlation heatmap (EDA)
    if generate_plots:
        plot_correlation_heatmap(df)

    # ================================================================
    # Step 2: Split & Scale
    # ================================================================
    train_df, val_df, test_df = time_series_split(df)
    train_df, val_df, test_df, scaler = scale_features(
        train_df, val_df, test_df, feature_columns
    )

    # ================================================================
    # Step 3: Train LSTM
    # ================================================================
    logger.info(f"\n{'='*40}")
    logger.info("Training Model 1/3: LSTM")
    logger.info(f"{'='*40}")

    X_train_seq, y_train_seq = create_lstm_sequences(train_df, feature_columns)
    X_val_seq, y_val_seq = create_lstm_sequences(val_df, feature_columns)
    X_test_seq, y_test_seq = create_lstm_sequences(test_df, feature_columns)

    lstm_train_result = train_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq)

    # Predict on test set
    from ai.models.lstm_model import predict_lstm
    lstm_test_proba = predict_lstm(X_test_seq)
    lstm_metrics = evaluate_model(y_test_seq, lstm_test_proba, "LSTM")
    results["LSTM"] = lstm_metrics

    if generate_plots:
        plot_lstm_training_history(lstm_train_result["history"])

    # ================================================================
    # Step 4: Train Random Forest
    # ================================================================
    logger.info(f"\n{'='*40}")
    logger.info("Training Model 2/3: Random Forest")
    logger.info(f"{'='*40}")

    X_train_flat, y_train_flat = create_flat_features(train_df, feature_columns)
    X_val_flat, y_val_flat = create_flat_features(val_df, feature_columns)
    X_test_flat, y_test_flat = create_flat_features(test_df, feature_columns)

    rf_train_result = train_rf(
        X_train_flat, y_train_flat,
        X_val_flat, y_val_flat,
        feature_names=feature_columns,
        tune_hyperparams=tune_hyperparams,
    )

    from ai.models.rf_model import predict_rf
    rf_test_proba = predict_rf(X_test_flat)
    rf_metrics = evaluate_model(y_test_flat, rf_test_proba, "Random Forest")
    results["Random Forest"] = rf_metrics

    if generate_plots:
        plot_feature_importance(rf_train_result["feature_importance"], "Random Forest")

    # ================================================================
    # Step 5: Train XGBoost
    # ================================================================
    logger.info(f"\n{'='*40}")
    logger.info("Training Model 3/3: XGBoost")
    logger.info(f"{'='*40}")

    xgb_train_result = train_xgb(
        X_train_flat, y_train_flat,
        X_val_flat, y_val_flat,
        feature_names=feature_columns,
        tune_hyperparams=tune_hyperparams,
    )

    from ai.models.xgb_model import predict_xgb
    xgb_test_proba = predict_xgb(X_test_flat)
    xgb_metrics = evaluate_model(y_test_flat, xgb_test_proba, "XGBoost")
    results["XGBoost"] = xgb_metrics

    if generate_plots:
        plot_feature_importance(xgb_train_result["feature_importance"], "XGBoost")
        if xgb_train_result.get("shap_importance"):
            plot_feature_importance(xgb_train_result["shap_importance"], "XGBoost SHAP")

    # ================================================================
    # Step 6: Compare & Save
    # ================================================================
    logger.info(f"\n{'='*40}")
    logger.info("Model Comparison")
    logger.info(f"{'='*40}")

    comparison_df = compare_models(results)

    if generate_plots:
        # Note: LSTM uses different test set (due to sequence windowing)
        # For ROC, use the flat test set predictions (RF and XGB share it)
        plot_confusion_matrices(results)
        plot_roc_curves(
            y_test_flat,
            {
                "LSTM": predict_lstm(X_test_seq)[:len(y_test_flat)]
                        if len(y_test_seq) >= len(y_test_flat)
                        else np.pad(lstm_test_proba, (len(y_test_flat) - len(lstm_test_proba), 0), constant_values=0.5),
                "Random Forest": rf_test_proba,
                "XGBoost": xgb_test_proba,
            },
        )
        plot_model_comparison_bar(results)

    # Save all metrics
    save_all_metrics(results)

    # Save training metadata
    metadata = {
        "symbol": symbol,
        "years": years,
        "total_rows": len(df),
        "n_features": len(feature_columns),
        "feature_columns": feature_columns,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "sequence_length": SEQUENCE_LENGTH,
        "lstm_train_result": {
            "epochs_trained": lstm_train_result["epochs_trained"],
            "best_val_loss": lstm_train_result["best_val_loss"],
            "best_val_accuracy": lstm_train_result["best_val_accuracy"],
        },
        "rf_train_result": {
            "best_params": rf_train_result["best_params"],
            "cv_score": rf_train_result["cv_score"],
        },
        "xgb_train_result": {
            "best_params": xgb_train_result["best_params"],
            "cv_score": xgb_train_result["cv_score"],
        },
    }
    with open(SAVED_MODELS_DIR / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"\n{'='*60}")
    logger.info("TRAINING COMPLETE")
    logger.info(f"Models saved to: {SAVED_MODELS_DIR}")
    logger.info(f"{'='*60}")

    return {
        "results": results,
        "comparison": comparison_df.to_dict("records"),
        "metadata": metadata,
    }
