import cv2
import numpy as np
import base64
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from pathlib import Path
from loguru import logger
from typing import Optional


LANDMARK_MODEL = Path(__file__).parent.parent.parent / "models" / "hand_landmarker.task"


class HandTracker:
    def __init__(self):
        self._landmarker: Optional[mp_vision.HandLandmarker] = None
        self._init()

    def _init(self):
        if not LANDMARK_MODEL.exists():
            logger.warning(
                f"Hand landmarker model not found: {LANDMARK_MODEL}. "
                "Run: python scripts/download_hand_landmarker.py"
            )
            return
        try:
            opts = mp_vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(LANDMARK_MODEL)),
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp_vision.HandLandmarker.create_from_options(opts)
            logger.info("HandLandmarker (Tasks API) ready")
        except Exception as e:
            logger.warning(f"HandLandmarker init failed: {e}")

    def decode_frame(self, b64_data: str) -> Optional[np.ndarray]:
        try:
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            raw = base64.b64decode(b64_data)
            arr = np.frombuffer(raw, np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.error(f"Frame decode error: {e}")
            return None

    def extract_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        if not self._landmarker:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.hand_landmarks:
            return None
        lms = result.hand_landmarks[0]
        return np.array([[lm.x, lm.y, lm.z] for lm in lms], dtype=np.float32)

    def process_frame(self, b64_data: str) -> Optional[np.ndarray]:
        frame = self.decode_frame(b64_data)
        if frame is None:
            return None
        return self.extract_landmarks(frame)
