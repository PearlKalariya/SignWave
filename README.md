# SignWave

**Accessible video meetings** — real-time American Sign Language (ASL) recognition and speech transcription, shared as a live captioned transcript, with AI-generated meeting summaries you can chat with.

SignWave lets deaf/hard-of-hearing and hearing participants share one meeting: signers' gestures become text, speakers' voices become text, and everything streams into a single live transcript that's persisted and summarized.

---

## Features

- **Sign → Text** — webcam frames run through MediaPipe hand-landmark detection + a trained gesture classifier (A–Z + `SPACE`/`DELETE`), assembled into words/sentences.
- **Speech → Text** — microphone audio transcribed by OpenAI Whisper.
- **Live rooms** — Socket.IO rooms broadcast every caption to all participants in real time; each line is persisted to MongoDB.
- **AI summaries** — on meeting end, Claude (`claude-sonnet-4-6`) generates decisions, action items, risks, and an overview.
- **Transcript Q&A** — ask natural-language questions about a finished meeting (RAG over the stored transcript).

---

## Architecture

```
┌────────────────────────┐         ┌─────────────────────────────────────┐
│   Frontend (Next.js)    │         │           Backend (FastAPI)         │
│                         │         │                                     │
│  Lobby / Meeting / Summ │         │  REST  /api/meetings|transcripts|   │
│                         │         │        summaries                    │
│  WebcamRecognizer  ─────┼──ws────▶│  /ws/recognize  → HandTracker +     │
│  (JPEG frames)          │         │                   GestureClassifier │
│                         │         │                   + TextProcessor   │
│  SpeechCapture     ─────┼──ws────▶│  /ws/speech     → WhisperService    │
│  (webm audio clips)     │         │                                     │
│                         │         │  Socket.IO rooms (join/subtitle)    │
│  Socket.IO client  ◀────┼─socket─▶│   → persists Transcript to Mongo    │
└────────────────────────┘         │                                     │
                                    │  SummaryService → Anthropic Claude  │
                                    └──────────────┬──────────────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │   MongoDB   │
                                            └─────────────┘
```

**Stack**
- Frontend: Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · socket.io-client
- Backend: FastAPI · python-socketio · Motor/Beanie (MongoDB ODM)
- ML/Vision: MediaPipe Hand Landmarker · scikit-learn gesture model · OpenAI Whisper
- LLM: Anthropic Claude (`claude-sonnet-4-6`)
- Database: MongoDB

---

## Prerequisites

- **Python 3.9+** and **Node.js 20+**
- **MongoDB** running locally (or a connection URI)
- **ffmpeg** on `PATH` — required by Whisper to decode audio
- An **Anthropic API key** for summaries/chat

---

## Setup

### 1. MongoDB

Easiest via Docker:

```bash
docker run -d --name signwave-mongo -p 27017:27017 mongo:7
```

### 2. ffmpeg

Whisper shells out to `ffmpeg`. Install one of:

```bash
brew install ffmpeg                       # Homebrew
conda install -c conda-forge ffmpeg       # conda
```

Verify: `ffmpeg -version`.

### 3. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt

# Download the MediaPipe hand-landmark model (one-time)
python scripts/download_hand_landmarker.py

cp .env.example .env        # then edit values (see below)
uvicorn app.main:app --reload --port 8000
```

> **Note:** `openai-whisper` builds from source. If install fails with
> `No module named 'pkg_resources'`, upgrade setuptools first then install
> without build isolation:
> `pip install -U setuptools && pip install openai-whisper==20240930 --no-build-isolation`

Backend serves on `http://localhost:8000`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend serves on `http://localhost:3000`.

---

## Environment variables

`backend/.env`:

| Variable            | Default                      | Purpose                              |
|---------------------|------------------------------|--------------------------------------|
| `MONGODB_URL`       | `mongodb://localhost:27017`  | MongoDB connection URI               |
| `MONGODB_DB_NAME`   | `signwave_meeting`           | Database name                        |
| `ANTHROPIC_API_KEY` | _(empty)_                    | Claude key for summaries + chat      |
| `SECRET_KEY`        | `dev-secret-change-in-prod`  | App secret                           |
| `BACKEND_PORT`      | `8010`                       | Port hint                            |
| `CORS_ORIGINS`      | `["http://localhost:3000"]`  | Allowed frontend origins             |
| `WHISPER_MODEL`     | `base`                       | Whisper model size (`tiny`…`large`)  |

`frontend/.env.local`:

| Variable               | Default                 | Purpose                                  |
|------------------------|-------------------------|------------------------------------------|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | Backend base URL (REST + WS + Socket.IO) |

---

## Usage

1. Open `http://localhost:3000`, enter your name.
2. **Create & host** a meeting (gives you a room code) or **Join** with a code.
3. In the room:
   - **Start camera** → sign letters; hold a sign ~8 frames to commit it. Build a sentence, then **Send to meeting**.
   - **Start microphone** → speech is transcribed in 4-second clips and broadcast.
   - All captions appear in the live transcript, tagged `sign` or `speech`.
4. Host clicks **End & summarize** → redirected to the summary page.
5. On the summary page: view decisions / action items / risks, and **ask questions** about the meeting.

---

## API reference

### REST (`/api`)

| Method | Path                                | Description                                  |
|--------|-------------------------------------|----------------------------------------------|
| POST   | `/meetings/`                        | Create meeting `{title, host_id, host_name}` |
| GET    | `/meetings/`                        | List meetings (`?host_id=` filter)           |
| GET    | `/meetings/{id}`                    | Get meeting by id                            |
| GET    | `/meetings/room/{room_code}`        | Get meeting by room code                     |
| POST   | `/meetings/{id}/end`                | End meeting `{generate_summary}`             |
| GET    | `/meetings/{id}/transcripts`        | All transcript lines for a meeting           |
| POST   | `/transcripts/`                     | Add a transcript line                        |
| GET    | `/transcripts/search?q=`            | Full-text transcript search                  |
| GET    | `/summaries/{meeting_id}`           | Get summary                                  |
| POST   | `/summaries/{meeting_id}/regenerate`| Rebuild summary                              |
| POST   | `/summaries/{meeting_id}/chat`      | Ask `{question}` about the meeting           |
| GET    | `/health`                           | Health check                                 |

### WebSockets

- **`/ws/recognize`** — send base64 JPEG data-URL frames (text). Receives
  `{sign, confidence, state:{current_letter, current_word, sentence}}`.
- **`/ws/speech`** — send JSON metadata `{speaker_id, speaker_name, meeting_id}`
  first, then binary audio clips. Receives `{text, speaker_id, speaker_name, ...}`.

### Socket.IO events

| Event                | Direction | Payload                                                          |
|----------------------|-----------|------------------------------------------------------------------|
| `join_room`          | C → S     | `{room_code, user_id, user_name}`                                |
| `leave_room`         | C → S     | `{room_code}`                                                    |
| `new_subtitle`       | C → S     | `{room_code, meeting_id, speaker_id, speaker_name, text, source}`|
| `subtitle_received`  | S → C     | persisted line broadcast to the room                             |
| `participant_joined` | S → C     | `{user_id, user_name, joined_at}`                                |
| `participant_left`   | S → C     | `{user_id, user_name}`                                           |

---

## Training the gesture model

A trained model ships in `backend/trained_models/`. To retrain from the
ASL alphabet dataset (`asl_alphabet_train/`, not committed):

```bash
cd backend
python scripts/train_gesture_model.py
```

Labels: `A`–`Z`, plus `SPACE`, `DELETE`, `NOTHING`.

---

## Project structure

```
SignWave/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI + Socket.IO ASGI app
│   │   ├── api/
│   │   │   ├── routes/             # meetings, transcripts, summaries, health
│   │   │   └── websocket/          # recognition.py, speech.py
│   │   ├── services/               # hand_tracker, gesture_classifier,
│   │   │   │                       # text_processor, whisper_service,
│   │   │   │                       # summary_service, room_manager
│   │   ├── models/                 # Beanie documents
│   │   └── core/                   # config, database, logging
│   ├── models/                     # hand_landmarker.task
│   ├── trained_models/             # gesture_model.joblib (+ meta)
│   ├── scripts/                    # download_hand_landmarker, train_gesture_model
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/                    # lobby, meeting/[roomCode], summary/[meetingId]
        ├── components/             # WebcamRecognizer, SpeechCapture, TranscriptPanel
        └── lib/                    # api, socket, identity, types
```

---

## Troubleshooting

- **Backend hangs at "Waiting for application startup"** — MongoDB isn't reachable. Start it (see step 1).
- **Speech does nothing / Whisper errors** — `ffmpeg` not on `PATH`, or `torch`/`openai-whisper` not installed. See steps 2–3.
- **Camera/mic denied** — browsers require `localhost` or HTTPS for `getUserMedia`; allow permissions.
- **CORS errors** — ensure the frontend origin is in `CORS_ORIGINS`.
- **Signs not recognized** — confirm `scripts/download_hand_landmarker.py` ran and `backend/models/hand_landmarker.task` exists.
