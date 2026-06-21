from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.hand_tracker import HandTracker
from app.services.gesture_classifier import GestureClassifier
from app.services.text_processor import TextProcessor


async def recognition_ws(websocket: WebSocket):
    await websocket.accept()
    tracker = HandTracker()
    classifier = GestureClassifier()
    processor = TextProcessor()
    logger.info("Recognition WS connected")

    try:
        while True:
            data = await websocket.receive_text()

            landmarks = tracker.process_frame(data)
            if landmarks is None:
                await websocket.send_json({"sign": None, "confidence": 0.0, "state": processor._state()})
                continue

            label, confidence = classifier.smooth_predict(landmarks)
            state = processor.process(label)

            await websocket.send_json({
                "sign": label,
                "confidence": round(confidence, 3),
                "state": state,
            })

    except WebSocketDisconnect:
        logger.info("Recognition WS disconnected")
    except Exception as e:
        logger.error(f"Recognition WS error: {e}")
        await websocket.close(code=1011)
