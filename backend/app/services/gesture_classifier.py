import numpy as np
import joblib
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger
from collections import deque

TRAINED_DIR = Path(__file__).parent.parent.parent / "trained_models"
SKLEARN_MODEL = TRAINED_DIR / "gesture_model.joblib"
SKLEARN_META = TRAINED_DIR / "gesture_model_meta.joblib"
LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE", "DELETE", "NOTHING"]


class GestureClassifier:
    def __init__(self, smoothing_window: int = 5):
        self._model = None
        self._label_encoder = None
        self._history: deque = deque(maxlen=smoothing_window)
        self._load()

    def _load(self):
        if SKLEARN_MODEL.exists():
            try:
                self._model = joblib.load(SKLEARN_MODEL)
                if SKLEARN_META.exists():
                    meta = joblib.load(SKLEARN_META)
                    self._label_encoder = meta.get("label_encoder")
                logger.info(f"Gesture model loaded: {SKLEARN_MODEL.name}")
            except Exception as e:
                logger.warning(f"Model load failed: {e}")

    def _normalize(self, landmarks: np.ndarray) -> np.ndarray:
        # translate to wrist origin, scale by max extent
        base = landmarks[0].copy()
        lms = landmarks - base
        scale = np.max(np.abs(lms)) + 1e-8
        lms = lms / scale
        return lms.flatten()

    def predict(self, landmarks: np.ndarray) -> Tuple[str, float]:
        features = self._normalize(landmarks).reshape(1, -1)

        if self._model is not None:
            try:
                pred = self._model.predict(features)[0]
                proba = self._model.predict_proba(features)[0]
                confidence = float(np.max(proba))
                if self._label_encoder is not None:
                    label = str(self._label_encoder.inverse_transform([pred])[0])
                else:
                    label = LABELS[int(pred)] if isinstance(pred, (int, np.integer)) else str(pred)
                return label, confidence
            except Exception as e:
                logger.warning(f"Prediction error: {e}")

        return "?", 0.0

    def smooth_predict(self, landmarks: np.ndarray) -> Tuple[str, float]:
        label, conf = self.predict(landmarks)
        self._history.append(label)

        if len(self._history) < 3:
            return label, conf

        # majority vote
        from collections import Counter
        counts = Counter(self._history)
        smoothed, _ = counts.most_common(1)[0]
        return smoothed, conf
