# Recap

## Project Overview

Recap is a local, privacy-first desktop app that captures system audio from any meeting platform (Zoom, Google Meet, Teams, etc.), transcribes it in real-time with speaker identification, and generates AI-powered summaries after the meeting ends. All processing happens on-device using local ML models — no data leaves the user's machine.

## Architecture

```
┌─────────────────────────────┐
│  Tauri (native desktop app) │
│  ┌───────────────────────┐  │
│  │  React UI (webview)   │──── HTTP/WebSocket ───→ Python backend (FastAPI)
│  └───────────────────────┘  │                        port 8420
│  System tray / window mgmt  │
└─────────────────────────────┘
```

Two processes:
- **Tauri shell** — desktop window, system tray, spawns/manages the Python backend
- **Python backend** — FastAPI server handling audio capture, ML inference, storage, and API

### Data Flow — During Meeting
```
System Audio → Audio Capture (platform-specific) → Silero VAD (filter silence)
→ faster-whisper (STT) + pyannote (diarization) in parallel
→ Align text + speaker labels → WebSocket to frontend + SQLite storage
```

### Data Flow — After Meeting
```
Full transcript from DB → Unload STT/diarization models (free VRAM)
→ Ollama + Mistral/Llama 3 → Structured summary → Store in DB → Notify frontend
```

## Directory Structure

```
recap/
├── backend/                      # Python (FastAPI)
│   ├── main.py                   # Entry point, FastAPI app, lifespan events
│   ├── config.py                 # Settings: paths, model names, audio params
│   ├── requirements.txt
│   ├── audio/                    # Platform-specific audio capture
│   │   ├── capture.py            # Unified interface: start(), stop(), get_chunk()
│   │   ├── _windows.py           # WASAPI loopback via sounddevice
│   │   ├── _linux.py             # PulseAudio/PipeWire monitor
│   │   └── _macos.py             # ScreenCaptureKit via Swift helper
│   ├── vad/
│   │   └── detector.py           # Silero VAD — filter silence
│   ├── transcription/
│   │   └── transcriber.py        # faster-whisper, chunked processing
│   ├── diarization/
│   │   └── diarizer.py           # pyannote.audio, speaker segment alignment
│   ├── summarization/
│   │   └── summarizer.py         # Ollama REST client, prompt templates
│   ├── pipeline/
│   │   ├── realtime.py           # Live: audio → VAD → STT → diarize → stream
│   │   └── post_meeting.py       # Post: transcript → LLM summary → store
│   ├── storage/
│   │   ├── database.py           # SQLite setup, migrations, FTS5
│   │   ├── models.py             # Dataclasses: Meeting, Segment, Summary
│   │   └── queries.py            # CRUD, search
│   ├── api/
│   │   ├── meetings.py           # REST: list, get, delete meetings
│   │   ├── capture.py            # POST /capture/start, /capture/stop
│   │   ├── summary.py            # POST /meetings/{id}/summarize
│   │   └── ws.py                 # WebSocket: live transcript stream
│   └── utils/
│       ├── gpu.py                # VRAM monitoring, model load/unload
│       └── logger.py             # Structured logging
│
├── frontend/                     # Tauri + React + TypeScript
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── LiveSession.tsx       # Real-time transcript during meeting
│   │   │   ├── MeetingHistory.tsx    # Past meetings list
│   │   │   └── MeetingDetail.tsx     # Transcript + summary view
│   │   ├── components/
│   │   │   ├── TranscriptView.tsx
│   │   │   ├── SummaryCard.tsx
│   │   │   ├── RecordingControls.tsx
│   │   │   ├── SpeakerBadge.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── StatusIndicator.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useMeetings.ts
│   │   │   └── useRecording.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   ├── src-tauri/
│   │   ├── src/main.rs
│   │   ├── tauri.conf.json
│   │   └── Cargo.toml
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── data/                         # Runtime data (gitignored)
├── models/                       # Downloaded ML models (gitignored)
├── CLAUDE.md                     # This file
└── README.md
```

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend | Python + FastAPI | Python 3.11+, FastAPI 0.115+ |
| STT | faster-whisper (large-v3) | 1.1+ |
| VAD | Silero VAD | 5+ |
| Diarization | pyannote.audio | 3.3+ |
| LLM | Ollama + Mistral 7B (Q4_K_M) | latest |
| Storage | SQLite + FTS5 | built-in |
| Frontend | React + TypeScript | React 19, TS 5.5+ |
| Desktop shell | Tauri 2 | 2+ |
| Styling | Tailwind CSS | 4+ |
| Build | Vite | 6+ |

## Key Constraints

### VRAM Budget (NVIDIA 5070 Ti — 16GB)
Models are loaded **sequentially, never concurrently across phases**:
- During meeting: faster-whisper large-v3 (~3GB) + pyannote (~1GB) + Silero VAD (~0.1GB) + overhead (~1GB) = ~5.1GB
- After meeting: unload all above, then Ollama Mistral 7B Q4 (~5GB)
- Implement explicit model unloading between phases in `utils/gpu.py`

### Cross-Platform Audio Capture
Each OS requires a different audio capture backend behind the unified `audio/capture.py` interface:
- **Windows**: WASAPI loopback via `sounddevice` — native, no extra software
- **Linux**: PulseAudio/PipeWire monitor source via `sounddevice`
- **macOS**: ScreenCaptureKit (macOS 13+) via a small Swift helper subprocess

Use `platform.system()` to detect OS and delegate to the correct backend. The interface must expose: `start()`, `stop()`, `get_chunk() -> np.ndarray` (PCM 16kHz mono float32).

### Audio Pipeline Params
- Sample rate: 16000 Hz
- Channels: mono
- Format: float32 PCM
- Chunk size for Whisper: 30-second sliding windows
- VAD filters chunks before sending to Whisper

### Real-Time Streaming
- Backend streams diarized transcript segments to frontend via WebSocket at `ws://localhost:8420/ws`
- Each message is JSON: `{"speaker": "Speaker 1", "text": "...", "start_time": 0.0, "end_time": 5.0, "confidence": 0.95}`
- Frontend appends to a scrolling transcript view in real-time

## Database Schema

```sql
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'recording',  -- recording | processing | completed
    audio_path TEXT
);

CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id),
    speaker TEXT NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE segments_fts USING fts5(
    text, content='segments', content_rowid='rowid'
);

CREATE TABLE summaries (
    meeting_id TEXT PRIMARY KEY REFERENCES meetings(id),
    overview TEXT NOT NULL,
    key_points TEXT NOT NULL,       -- JSON array
    action_items TEXT NOT NULL,     -- JSON array
    generated_at TEXT NOT NULL
);
```

## Coding Conventions

### Python (backend/)
- Python 3.11+ with type hints on all functions
- Use `dataclasses` for data models, not Pydantic models (Pydantic only for FastAPI request/response schemas)
- Async functions for all API routes and WebSocket handlers
- Use `logging` module with structured format, never `print()`
- Imports: stdlib → third-party → local, separated by blank lines
- Error handling: catch specific exceptions, never bare `except:`
- Docstrings on all public functions (one-liner or Google-style)
- Use `pathlib.Path` for all file paths, never string concatenation
- Config values in `config.py`, never hardcoded in modules

### TypeScript (frontend/)
- Strict TypeScript — no `any` types
- Functional components with hooks, no class components
- Custom hooks for all API interactions and WebSocket connections
- Types defined in `types/index.ts`, imported where needed
- Use Tailwind utility classes for styling, no separate CSS files
- Component files: PascalCase. Hooks: camelCase with `use` prefix
- Prefer named exports over default exports for components

### General
- Commits: conventional commits format (`feat:`, `fix:`, `refactor:`, etc.)
- No comments explaining *what* code does — only *why* when non-obvious
- Keep functions small and single-purpose
- Test files next to source: `transcriber.py` → `test_transcriber.py`

## How to Run (Development)

```bash
# Terminal 1 — Backend
cd backend
source .venv/bin/activate
python -m uvicorn main:app --reload --port 8420

# Terminal 2 — Frontend
cd frontend
npm run tauri dev
```

## Build Priority Order

When building features, follow this order — each step validates the previous:
1. Audio capture + VAD — get PCM chunks, filter silence
2. Transcription — faster-whisper producing text from chunks
3. Live WebSocket — stream transcript to barebones React page
4. Diarization — add speaker labels to segments
5. Storage — persist meetings/segments to SQLite
6. Summarization — Ollama integration, prompt engineering
7. Frontend polish — meeting history, search, full UI
8. Tauri packaging — system tray, platform installers

## Things to Avoid

- Never load STT/diarization models and LLM simultaneously — VRAM will overflow
- Never use `subprocess.run()` for long-running processes — use `asyncio.create_subprocess_exec()`
- Never hardcode model names — always reference `config.py`
- Never block the FastAPI event loop with synchronous ML inference — run in thread executor
- Never store audio as base64 — write raw WAV files to `data/recordings/`
- Do not add a vector database — SQLite FTS5 is sufficient for search
- Do not add user authentication — this is a single-user local app
- Do not create separate CSS/JS files for React components — single-file with Tailwind
