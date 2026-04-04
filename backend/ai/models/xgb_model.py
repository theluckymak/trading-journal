"""
XGBoost Classifier — Extreme Gradient Boosting

Theory (for thesis):
    XGBoost is a gradient boosting framework that builds an ensemble of weak learners
    (decision trees) sequentially. Each tree corrects the errors of the previous ensemble.

    Key concepts:
    - Gradient Boosting: minimizes loss by adding trees that follow the negative gradient
    - Regularization: L1 (Lasso) and L2 (Ridge) penalties prevent overfitting
    - Pruning: max_depth limits tree complexity
    - Learning Rate (eta): controls contribution of each tree (shrinkage)
    - Column Subsampling: like Random Forest, randomly selects features per tree

    Why XGBoost for financial data:
    - Handles missing values natively
    - Built-in regularization prevents overfitting to noise
    - SHAP (SHapley Additive exPlanations) values provide model-agnostic explainability
    - Consistently top-performing in structured/tabular data competitions

References:
    Chen, T. & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System."
    Proceedings of the 22nd ACM SIGKDD, 785-794.

    Lundberg, S.M. & Lee, S.I. (2017). "A Unified Approach to Interpreting Model Predictions."
    Advances in Neural Information Processing Systems (NeurIPS).
"""
import numpy as np
import joblib
import json
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
import logging

from ai.config import XGB_CONFIG, SAVED_MODELS_DIR

logger = logging.getLogger(__name__)

MODEL_PATH = SAVED_MODELS_DIR / "xgb_model.json"


def build_xgb_model() -> XGBClassifier:
    """Create a base XGBoost classifier."""
    return XGBClassifier(
        random_state=XGB_CONFIG["random_state"],
        eval_metric=XGB_CONFIG["eval_metric"],
        use_label_encoder=False,
        n_jobs=XGB_CONFIG["n_jobs"],
        verbosity=0,
    )


def train_xgb(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str] = None,
    tune_hyperparams: bool = True,
    save: bool = True,
) -> dict:
    """
    Train XGBoost with optional hyperparameter tuning.

    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        feature_names: Feature column names (for importance and SHAP)
        tune_hyperparams: Run GridSearchCV or use defaults
        save: Save model to disk

    Returns:
        Dictionary with metrics, best params, feature importance, and SHAP data
    """
    if tune_hyperparams:
        logger.info("Running GridSearchCV for XGBoost...")
        logger.info(f"  Parameter grid: {XGB_CONFIG['param_grid']}")

        cv = TimeSeriesSplit(n_splits=XGB_CONFIG["cv_folds"])

        grid_search = GridSearchCV(
            estimator=build_xgb_model(),
            param_grid=XGB_CONFIG["param_grid"],
            cv=cv,
            scoring="accuracy",
            n_jobs=XGB_CONFIG["n_jobs"],
            verbose=1,
        )
        grid_search.fit(X_train, y_train)

        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        cv_score = grid_search.best_score_

        logger.info(f"  Best params: {best_params}")
        logger.info(f"  Best CV accuracy: {cv_score:.4f}")
    else:
        logger.info("Training XGBoost with default params...")
        best_model = build_xgb_model()
        best_model.set_params(n_estimators=300, max_depth=6, learning_rate=0.05)
        best_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        best_params = best_model.get_params()
        cv_score = None

    # Evaluate
    val_accuracy = best_model.score(X_val, y_val)
    train_accuracy = best_model.score(X_train, y_train)
    logger.info(f"  Train accuracy: {train_accuracy:.4f}")
    logger.info(f"  Val accuracy: {val_accuracy:.4f}")

    # Feature importance (gain-based)
    importance = best_model.feature_importances_
    if feature_names is not None:
        feature_importance = dict(zip(feature_names, [float(v) for v in importance]))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    else:
        feature_importance = {f"feature_{i}": float(v) for i, v in enumerate(importance)}

    # SHAP values for explainability
    shap_values = None
    try:
        import shap
        explainer = shap.TreeExplainer(best_model)
        sv = explainer.shap_values(X_val[:200])  # Compute on subset for speed
        if feature_names is not None:
            shap_importance = dict(zip(
                feature_names,
                [float(v) for v in np.abs(sv).mean(axis=0)]
            ))
            shap_importance = dict(sorted(shap_importance.items(), key=lambda x: x[1], reverse=True))
            shap_values = shap_importance
        logger.info("  SHAP values computed successfully")
    except Exception as e:
        logger.warning(f"  SHAP computation failed: {e}")

    if save:
        best_model.save_model(str(MODEL_PATH))
        logger.info(f"  Model saved to {MODEL_PATH}")

    return {
        "best_params": {k: v for k, v in best_params.items()
                        if k in ["n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree"]},
        "cv_score": float(cv_score) if cv_score else None,
        "train_accuracy": float(train_accuracy),
        "val_accuracy": float(val_accuracy),
        "feature_importance": feature_importance,
        "shap_importance": shap_values,
    }


def predict_xgb(X: np.ndarray) -> np.ndarray:
    """Load saved model and predict probabilities."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained XGBoost model found at {MODEL_PATH}.")
    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))
    probabilities = model.predict_proba(X)[:, 1]
    return probabilities


def load_xgb_model():
    """Load the saved XGBoost model into memory."""
    if not MODEL_PATH.exists():
        return None
    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))
    return model
