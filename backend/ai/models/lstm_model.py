"""
LSTM Model — Long Short-Term Memory Neural Network

Architecture:
    Input → LSTM(128) → Dropout(0.2) → LSTM(64) → Dropout(0.2) → Dense(32, ReLU) → Dense(1, Sigmoid)

Theory (for thesis):
    LSTMs solve the vanishing gradient problem in traditional RNNs through gating mechanisms:
    - Forget Gate: decides what information to discard from cell state
    - Input Gate: decides what new information to store in cell state
    - Output Gate: decides what to output based on cell state

    This makes LSTMs particularly suitable for financial time series where
    long-term dependencies (e.g., multi-week trends) influence short-term movements.

Reference:
    Hochreiter, S. & Schmidhuber, J. (1997). "Long Short-Term Memory."
    Neural Computation, 9(8), 1735-1780.
"""
import numpy as np
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TF info messages

from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import logging

from ai.config import LSTM_CONFIG, SAVED_MODELS_DIR

logger = logging.getLogger(__name__)

MODEL_PATH = SAVED_MODELS_DIR / "lstm_model.h5"


def build_lstm_model(input_shape: tuple) -> Sequential:
    """
    Build the LSTM architecture.

    Args:
        input_shape: (sequence_length, n_features) e.g., (60, 35)

    Returns:
        Compiled Keras Sequential model
    """
    model = Sequential([
        Input(shape=input_shape),

        # First LSTM layer with return_sequences=True to feed next LSTM
        LSTM(
            units=LSTM_CONFIG["units_layer1"],
            return_sequences=True,
        ),
        Dropout(LSTM_CONFIG["dropout"]),

        # Second LSTM layer
        LSTM(
            units=LSTM_CONFIG["units_layer2"],
            return_sequences=False,
        ),
        Dropout(LSTM_CONFIG["dropout"]),

        # Fully connected layers
        Dense(LSTM_CONFIG["dense_units"], activation="relu"),

        # Output: sigmoid for binary classification (probability of UP)
        Dense(1, activation="sigmoid"),
    ])

    model.compile(
        optimizer=Adam(learning_rate=LSTM_CONFIG["learning_rate"]),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    return model


def train_lstm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    save: bool = True,
) -> dict:
    """
    Train the LSTM model.

    Args:
        X_train: Training sequences, shape (n, seq_len, features)
        y_train: Training labels
        X_val: Validation sequences
        y_val: Validation labels
        save: Whether to save the trained model

    Returns:
        Dictionary with training history and metrics
    """
    logger.info("Building LSTM model...")
    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    model.summary(print_fn=logger.info)

    # Callbacks for training optimization
    callbacks = [
        # Stop if validation loss doesn't improve for 'patience' epochs
        EarlyStopping(
            monitor="val_loss",
            patience=LSTM_CONFIG["patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        # Reduce learning rate when loss plateaus
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=7,
            min_lr=1e-6,
            verbose=1,
        ),
        # Save best model during training
        ModelCheckpoint(
            str(MODEL_PATH),
            monitor="val_loss",
            save_best_only=True,
            verbose=0,
        ),
    ]

    logger.info("Training LSTM...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=LSTM_CONFIG["epochs"],
        batch_size=LSTM_CONFIG["batch_size"],
        callbacks=callbacks,
        verbose=1,
    )

    if save:
        model.save(MODEL_PATH)
        logger.info(f"Model saved to {MODEL_PATH}")

    return {
        "history": {
            "loss": [float(v) for v in history.history["loss"]],
            "val_loss": [float(v) for v in history.history["val_loss"]],
            "accuracy": [float(v) for v in history.history["accuracy"]],
            "val_accuracy": [float(v) for v in history.history["val_accuracy"]],
        },
        "epochs_trained": len(history.history["loss"]),
        "best_val_loss": float(min(history.history["val_loss"])),
        "best_val_accuracy": float(max(history.history["val_accuracy"])),
    }


def predict_lstm(X: np.ndarray) -> np.ndarray:
    """Load saved model and predict."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained LSTM model found at {MODEL_PATH}. Train the model first.")
    model = load_model(MODEL_PATH)
    probabilities = model.predict(X, verbose=0).flatten()
    return probabilities


def load_lstm_model():
    """Load the saved LSTM model into memory."""
    if not MODEL_PATH.exists():
        return None
    return load_model(MODEL_PATH)
