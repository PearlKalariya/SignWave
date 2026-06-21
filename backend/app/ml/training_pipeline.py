"""
ASL gesture model training pipeline.

Dataset expected layout (Kaggle ASL Alphabet):
  <dataset_dir>/
    A/  B/  C/ ... Z/   <- letter folders (images)
    space/               <- maps to SPACE
    del/                 <- maps to DELETE
    nothing/             <- maps to NOTHING

Each folder contains .jpg/.png images of that gesture.

Output: backend/trained_models/gesture_model.joblib
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision as mp_vision
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

MODEL_ASSET_PATH = Path(__file__).parent.parent.parent / "models" / "hand_landmarker.task"

LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE", "DELETE", "NOTHING"]

# Folder name → canonical label
FOLDER_LABEL_MAP = {letter: letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
FOLDER_LABEL_MAP.update({
    "SPACE": "SPACE",
    "DEL": "DELETE",
    "NOTHING": "NOTHING",
})

TRAINED_MODELS_DIR = Path(__file__).parent.parent.parent / "trained_models"
OUTPUT_MODEL = TRAINED_MODELS_DIR / "gesture_model.joblib"
OUTPUT_META = TRAINED_MODELS_DIR / "gesture_model_meta.joblib"


def _init_hands():
    if not MP_AVAILABLE:
        raise RuntimeError("mediapipe not installed. Run: pip install mediapipe")
    if not MODEL_ASSET_PATH.exists():
        raise FileNotFoundError(
            f"Hand landmarker model not found: {MODEL_ASSET_PATH}\n"
            "Run: python scripts/download_hand_landmarker.py"
        )
    options = mp_vision.HandLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(MODEL_ASSET_PATH)),
        num_hands=1,
        running_mode=mp_vision.RunningMode.IMAGE,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return mp_vision.HandLandmarker.create_from_options(options)


def _extract_landmarks(detector, img_bgr: np.ndarray) -> Optional[np.ndarray]:
    """Return (21, 3) array or None if no hand detected."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    result = detector.detect(mp_image)
    if not result.hand_landmarks:
        return None
    lm = result.hand_landmarks[0]
    pts = np.array([[l.x, l.y, l.z] for l in lm], dtype=np.float32)
    return pts


def _normalize(landmarks: np.ndarray) -> np.ndarray:
    """Wrist-origin translate, scale by max extent → 63-float vector."""
    base = landmarks[0].copy()
    lms = landmarks - base
    scale = np.max(np.abs(lms)) + 1e-8
    lms = lms / scale
    return lms.flatten()


def extract_features(
    dataset_dir: str,
    max_per_class: int = 3000,
    verbose: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Walk dataset_dir, extract MediaPipe landmarks for each image.
    Returns (X, y) where X.shape = (N, 63) and y = label strings.
    """
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset dir not found: {dataset_path}")

    detector = _init_hands()
    X, y = [], []
    skipped = 0

    img_exts = {".jpg", ".jpeg", ".png", ".bmp"}

    for folder in sorted(dataset_path.iterdir()):
        if not folder.is_dir():
            continue
        folder_name = folder.name.strip()
        label = FOLDER_LABEL_MAP.get(folder_name.upper(), None)
        if label is None:
            if verbose:
                print(f"  skip unknown folder: {folder_name}")
            continue

        images = [p for p in folder.iterdir() if p.suffix.lower() in img_exts]
        if max_per_class and len(images) > max_per_class:
            rng = np.random.default_rng(42)
            images = [images[i] for i in rng.choice(len(images), max_per_class, replace=False)]

        class_ok = 0
        for img_path in images:
            img = cv2.imread(str(img_path))
            if img is None:
                skipped += 1
                continue
            lm = _extract_landmarks(detector, img)
            if lm is None:
                skipped += 1
                continue
            X.append(_normalize(lm))
            y.append(label)
            class_ok += 1

        if verbose:
            print(f"  {label:8s}: {class_ok:4d} samples")

    detector.close()

    if verbose:
        print(f"\nTotal: {len(X)} samples, {skipped} skipped (no hand detected)")

    return np.array(X, dtype=np.float32), np.array(y)


def train(
    dataset_dir: str,
    model_type: str = "mlp",
    max_per_class: int = 3000,
    test_size: float = 0.15,
    verbose: bool = True,
) -> dict:
    """
    Full training run. Returns metrics dict.
    model_type: 'mlp' | 'rf'
    """
    TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Feature extraction from {dataset_dir} ===")
    t0 = time.time()
    X, y = extract_features(dataset_dir, max_per_class=max_per_class, verbose=verbose)
    print(f"Extraction done in {time.time() - t0:.1f}s")

    if len(X) == 0:
        raise ValueError("No samples extracted. Check dataset path and MediaPipe installation.")

    # Drop classes with fewer than 2 samples (can't stratify-split them)
    from collections import Counter
    counts = Counter(y)
    rare = {lbl for lbl, cnt in counts.items() if cnt < 2}
    if rare:
        print(f"Dropping rare classes (< 2 samples): {rare}")
        mask = np.array([lbl not in rare for lbl in y])
        X, y = X[mask], y[mask]

    le = LabelEncoder()
    le.fit(LABELS)
    y_enc = le.transform(y)

    # Use stratify only when all remaining classes have enough samples
    min_count = min(counts[lbl] for lbl in np.unique(y))
    use_stratify = min_count >= max(2, int(1 / test_size))
    X_train, X_val, y_train, y_val = train_test_split(
        X, y_enc, test_size=test_size, random_state=42,
        stratify=y_enc if use_stratify else None,
    )
    print(f"Train: {len(X_train)}  Val: {len(X_val)}")

    if model_type == "mlp":
        clf = MLPClassifier(
            hidden_layer_sizes=(512, 256, 128),
            activation="relu",
            solver="adam",
            batch_size=256,
            learning_rate_init=1e-3,
            max_iter=200,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=15,
            random_state=42,
            verbose=verbose,
        )
    else:  # rf
        clf = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=42,
            verbose=1 if verbose else 0,
        )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", clf),
    ])

    print(f"\n=== Training {model_type.upper()} ===")
    t1 = time.time()
    pipe.fit(X_train, y_train)
    print(f"Training done in {time.time() - t1:.1f}s")

    val_preds = pipe.predict(X_val)
    val_acc = np.mean(val_preds == y_val)
    print(f"\nVal accuracy: {val_acc:.4f}")

    present_classes = sorted(np.unique(y_enc))
    present_names = le.inverse_transform(present_classes)
    print("\n" + classification_report(y_val, val_preds, labels=present_classes, target_names=present_names))

    # Save
    joblib.dump(pipe, OUTPUT_MODEL, compress=3)
    joblib.dump({"label_encoder": le, "labels": LABELS, "model_type": model_type}, OUTPUT_META)
    print(f"\nModel saved → {OUTPUT_MODEL}")
    print(f"Meta  saved → {OUTPUT_META}")

    return {"val_accuracy": val_acc, "n_train": len(X_train), "n_val": len(X_val)}


def verify_model(n_random: int = 5) -> None:
    """Quick sanity check: load model, run N random feature vectors."""
    if not OUTPUT_MODEL.exists():
        print("No model found. Train first.")
        return

    pipe = joblib.load(OUTPUT_MODEL)
    meta = joblib.load(OUTPUT_META)
    le: LabelEncoder = meta["label_encoder"]

    rng = np.random.default_rng(0)
    X_fake = rng.random((n_random, 63)).astype(np.float32)
    preds = pipe.predict(X_fake)
    labels = le.inverse_transform(preds)
    print(f"Model loaded. Sample predictions on random input: {labels.tolist()}")
    print("Model OK.")
