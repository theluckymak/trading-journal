"""
Random Forest Classifier

Theory (for thesis):
    Random Forest is an ensemble learning method that constructs multiple decision trees
    during training and outputs the mode of their predictions (majority vote).

    Key concepts:
    - Bagging (Bootstrap Aggregation): each tree is trained on a random subset of data
    - Feature randomness: each split considers a random subset of features
    - This decorrelates individual trees, reducing overfitting
    - Feature importance is computed via Mean Decrease in Gini Impurity

    Advantages for financial prediction:
    - Handles non-linear relationships between indicators
    - Robust to outliers and noisy data
    - No need for feature scaling (though we scale for consistency)
    - Built-in feature importance ranking

Reference:
    Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
"""
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
import logging

from ai.config import RF_CONFIG, SAVED_MODELS_DIR

logger = logging.getLogger(__name__)

MODEL_PATH = SAVED_MODELS_DIR / "rf_model.pkl"


def build_rf_model() -> RandomForestClassifier:
    """Create a base Random Forest classifier."""
    return RandomForestClassifier(
        random_state=RF_CONFIG["random_state"],
        n_jobs=RF_CONFIG["n_jobs"],
        class_weight="balanced",  # Handle class imbalance
    )


def train_rf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str] = None,
    tune_hyperparams: bool = True,
    save: bool = True,
) -> dict:
    """
    Train Random Forest with optional hyperparameter tuning via GridSearchCV.

    Uses TimeSeriesSplit for cross-validation (respects temporal order).

    Args:
        X_train: Training features, shape (n_samples, n_features)
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        feature_names: List of feature column names (for importance)
        tune_hyperparams: Whether to run GridSearchCV
        save: Whether to save the model

    Returns:
        Dictionary with model metrics and feature importance
    """
    if tune_hyperparams:
        logger.info("Running GridSearchCV for Random Forest...")
        logger.info(f"  Parameter grid: {RF_CONFIG['param_grid']}")

        # TimeSeriesSplit preserves temporal order in cross-validation
        cv = TimeSeriesSplit(n_splits=RF_CONFIG["cv_folds"])

        grid_search = GridSearchCV(
            estimator=build_rf_model(),
            param_grid=RF_CONFIG["param_grid"],
            cv=cv,
            scoring="accuracy",
            n_jobs=RF_CONFIG["n_jobs"],
            verbose=1,
        )
        grid_search.fit(X_train, y_train)

        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        cv_score = grid_search.best_score_

        logger.info(f"  Best params: {best_params}")
        logger.info(f"  Best CV accuracy: {cv_score:.4f}")
    else:
        logger.info("Training Random Forest with default params...")
        best_model = build_rf_model()
        best_model.set_params(n_estimators=200, max_depth=20)
        best_model.fit(X_train, y_train)
        best_params = best_model.get_params()
        cv_score = None

    # Evaluate on validation set
    val_accuracy = best_model.score(X_val, y_val)
    train_accuracy = best_model.score(X_train, y_train)
    logger.info(f"  Train accuracy: {train_accuracy:.4f}")
    logger.info(f"  Val accuracy: {val_accuracy:.4f}")

    # Feature importance
    importance = best_model.feature_importances_
    if feature_names is not None:
        feature_importance = dict(zip(feature_names, [float(v) for v in importance]))
        # Sort by importance descending
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    else:
        feature_importance = {f"feature_{i}": float(v) for i, v in enumerate(importance)}

    if save:
        joblib.dump(best_model, MODEL_PATH)
        logger.info(f"  Model saved to {MODEL_PATH}")

    return {
        "best_params": best_params,
        "cv_score": float(cv_score) if cv_score else None,
        "train_accuracy": float(train_accuracy),
        "val_accuracy": float(val_accuracy),
        "feature_importance": feature_importance,
        "n_estimators": best_model.n_estimators,
    }


def predict_rf(X: np.ndarray) -> np.ndarray:
    """Load saved model and predict probabilities."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained RF model found at {MODEL_PATH}.")
    model = joblib.load(MODEL_PATH)
    # Return probability of class 1 (UP)
    probabilities = model.predict_proba(X)[:, 1]
    return probabilities


def load_rf_model():
    """Load the saved RF model into memory."""
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)
