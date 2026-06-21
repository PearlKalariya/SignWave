#!/usr/bin/env python3
"""
CLI entry point for ASL gesture model training.

Usage:
  python scripts/train_gesture_model.py --dataset /path/to/asl_alphabet_train
  python scripts/train_gesture_model.py --dataset data/asl --model rf
  python scripts/train_gesture_model.py --verify
  python scripts/train_gesture_model.py --demo /path/to/image.jpg

Kaggle dataset:
  https://www.kaggle.com/datasets/grassknoted/asl-alphabet
  Download → extract → pass top-level folder with A/ B/ ... Z/ space/ del/ nothing/ subdirs
"""

import argparse
import sys
from pathlib import Path

# Allow running from repo root or scripts/ dir
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.training_pipeline import train, verify_model, extract_features, _normalize, _init_hands, OUTPUT_MODEL

import cv2
import numpy as np


def demo_single_image(img_path: str) -> None:
    """Run sign prediction on a single image using trained model."""
    import joblib

    if not OUTPUT_MODEL.exists():
        print(f"Model not found at {OUTPUT_MODEL}. Train first.")
        sys.exit(1)

    meta_path = OUTPUT_MODEL.parent / "gesture_model_meta.joblib"
    pipe = joblib.load(OUTPUT_MODEL)
    meta = joblib.load(meta_path)
    le = meta["label_encoder"]

    img = cv2.imread(img_path)
    if img is None:
        print(f"Cannot read image: {img_path}")
        sys.exit(1)

    detector = _init_hands()
    from app.ml.training_pipeline import _extract_landmarks
    lm = _extract_landmarks(detector, img)
    detector.close()

    if lm is None:
        print("No hand detected in image.")
        sys.exit(1)

    features = _normalize(lm).reshape(1, -1)
    pred = pipe.predict(features)[0]
    proba = pipe.predict_proba(features)[0]
    label = le.inverse_transform([pred])[0]
    confidence = float(np.max(proba))
    print(f"Predicted: {label}  (confidence: {confidence:.3f})")


def main():
    parser = argparse.ArgumentParser(description="ASL gesture model trainer")
    parser.add_argument("--dataset", type=str, help="Path to ASL dataset root dir")
    parser.add_argument(
        "--model", type=str, default="mlp", choices=["mlp", "rf"],
        help="Model type: mlp (MLP neural net) or rf (Random Forest). Default: mlp"
    )
    parser.add_argument(
        "--max-per-class", type=int, default=3000,
        help="Max images per class (default 3000, set lower for fast test)"
    )
    parser.add_argument(
        "--test-size", type=float, default=0.15,
        help="Validation split fraction (default 0.15)"
    )
    parser.add_argument("--verify", action="store_true", help="Verify existing model works")
    parser.add_argument("--demo", type=str, help="Run prediction on single image")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    if args.verify:
        verify_model()
        return

    if args.demo:
        demo_single_image(args.demo)
        return

    if not args.dataset:
        parser.print_help()
        print("\nERROR: --dataset required for training.\n")
        print("To download dataset:")
        print("  pip install kaggle")
        print("  kaggle datasets download -d grassknoted/asl-alphabet")
        print("  unzip asl-alphabet.zip")
        print("  python scripts/train_gesture_model.py --dataset asl_alphabet_train/asl_alphabet_train")
        sys.exit(1)

    metrics = train(
        dataset_dir=args.dataset,
        model_type=args.model,
        max_per_class=args.max_per_class,
        test_size=args.test_size,
        verbose=not args.quiet,
    )
    print(f"\nDone. Val accuracy: {metrics['val_accuracy']:.4f}")


if __name__ == "__main__":
    main()
