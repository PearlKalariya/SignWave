import socketio
from loguru import logger
from datetime import datetime
from app.models.transcript import Transcript


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

# sid -> {room_code, user_id, user_name}
_connections: dict[str, dict] = {}


@sio.event
async def connect(sid, environ, auth):
    logger.info(f"Socket connected: {sid}")


@sio.event
async def disconnect(sid):
    info = _connections.pop(sid, None)
    if info:
        room = info["room_code"]
        await sio.leave_room(sid, room)
        await sio.emit("participant_left", {
            "user_id": info["user_id"],
            "user_name": info["user_name"],
        }, room=room)
        logger.info(f"{info['user_name']} left room {room}")


@sio.event
async def join_room(sid, data: dict):
    room_code = data.get("room_code", "")
    user_id = data.get("user_id", sid)
    user_name = data.get("user_name", "Anonymous")

    _connections[sid] = {"room_code": room_code, "user_id": user_id, "user_name": user_name}
    await sio.enter_room(sid, room_code)
    await sio.emit("participant_joined", {
        "user_id": user_id,
        "user_name": user_name,
        "joined_at": datetime.utcnow().isoformat(),
    }, room=room_code)
    logger.info(f"{user_name} joined room {room_code}")


@sio.event
async def leave_room(sid, data: dict):
    room_code = data.get("room_code", "")
    info = _connections.pop(sid, None)
    if info:
        await sio.leave_room(sid, room_code)
        await sio.emit("participant_left", {
            "user_id": info["user_id"],
            "user_name": info["user_name"],
        }, room=room_code)


@sio.event
async def new_subtitle(sid, data: dict):
    """
    Broadcast a subtitle to the room and persist to MongoDB.
    data: {room_code, meeting_id, speaker_id, speaker_name, text, source}
    """
    room_code = data.get("room_code", "")
    meeting_id = data.get("meeting_id", "")
    speaker_id = data.get("speaker_id", "")
    speaker_name = data.get("speaker_name", "")
    text = data.get("text", "").strip()
    source = data.get("source", "speech")

    if not text:
        return

    ts = Transcript(
        meeting_id=meeting_id,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        text=text,
        source=source,
    )
    await ts.insert()

    await sio.emit("subtitle_received", {
        "id": str(ts.id),
        "speaker_id": speaker_id,
        "speaker_name": speaker_name,
        "text": text,
        "source": source,
        "timestamp": ts.timestamp.isoformat(),
    }, room=room_code)
