#!/usr/bin/env python3
"""Download MediaPipe hand landmarker model."""
import urllib.request
from pathlib import Path

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
OUT = Path(__file__).parent.parent / "models" / "hand_landmarker.task"

OUT.parent.mkdir(exist_ok=True)
print(f"Downloading to {OUT} ...")
urllib.request.urlretrieve(URL, OUT)
print("Done.")
