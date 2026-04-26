# Recap

A local, privacy-first desktop app that captures system audio from any meeting platform, transcribes it in real-time with speaker identification, and generates AI-powered summaries — entirely on-device. No data leaves your machine.

## Features

- **System audio capture** — works with Zoom, Google Meet, Teams, and any other platform
- **Real-time transcription** — live transcript streamed to the UI as you speak
- **Speaker diarization** — automatically labels who said what
- **AI summaries** — overview, key points, and action items generated after the meeting
- **Full-text search** — find any meeting by keyword
- **Cross-platform** — Windows, macOS, Linux

## System Design

```
┌──────────────────────────────────────────────────────────────────────┐
│                        User's Machine                                │
│                                                                      │
│  ┌─────────────────────────────┐        ┌───────────────────────┐   │
│  │   Tauri Desktop Shell       │        │   Python Backend       │   │
│  │  ┌───────────────────────┐  │        │   (FastAPI :8420)      │   │
│  │  │   React UI (webview)  │◄─┼──WS────┤                       │   │
│  │  │                       │  │        │  ┌─────────────────┐  │   │
│  │  │  LiveSession.tsx      │  │        │  │  Audio Capture  │  │   │
│  │  │  MeetingHistory.tsx   │──┼─HTTP──►│  │  (WASAPI/Pulse/ │  │   │
│  │  │  MeetingDetail.tsx    │  │        │  │   SCKit)        │  │   │
│  │  └───────────────────────┘  │        │  └────────┬────────┘  │   │
│  │  System tray / window mgmt  │        │           │            │   │
│  └─────────────────────────────┘        │           ▼            │   │
│                                         │  ┌─────────────────┐  │   │
│                                         │  │  Silero VAD     │  │   │
│                                         │  │  (silence filter│  │   │
│                                         │  └────────┬────────┘  │   │
│                                         │           │            │   │
│                                         │     ┌─────┴──────┐    │   │
│                                         │     │            │    │   │
│                                         │     ▼            ▼    │   │
│                                         │  ┌──────┐  ┌────────┐ │   │
│                                         │  │Whispr│  │pyannote│ │   │
│                                         │  │large │  │  3.3   │ │   │
│                                         │  │  v3  │  │(diariz)│ │   │
│                                         │  └──┬───┘  └───┬────┘ │   │
│                                         │     │          │      │   │
│                                         │     └────┬─────┘      │   │
│                                         │          │             │   │
│                                         │          ▼             │   │
│                                         │  ┌─────────────────┐  │   │
│                                         │  │  Align text +   │  │   │
│                                         │  │  speaker labels │  │   │
│                                         │  └────────┬────────┘  │   │
│                                         │           │            │   │
│                                         │     ┌─────┴──────┐    │   │
│                                         │     │            │    │   │
│                                         │     ▼            ▼    │   │
│                                         │  ┌──────┐  ┌────────┐ │   │
│                                         │  │  WS  │  │SQLite  │ │   │
│                                         │  │stream│  │  +FTS5 │ │   │
│                                         │  └──────┘  └────────┘ │   │
│                                         │                        │   │
│                                         │  ── meeting ends ──    │   │
│                                         │  unload Whisper+pyann  │   │
│                                         │           │             │   │
│                                         │           ▼             │   │
│                                         │  ┌─────────────────┐  │   │
│                                         │  │  Ollama         │  │   │
│                                         │  │  Mistral 7B Q4  │  │   │
│                                         │  │  (summary)      │  │   │
│                                         │  └────────┬────────┘  │   │
│                                         │           │            │   │
│                                         │           ▼            │   │
│                                         │  ┌─────────────────┐  │   │
│                                         │  │  SQLite summary │  │   │
│                                         │  │  → notify UI    │  │   │
│                                         │  └─────────────────┘  │   │
│                                         └───────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### VRAM Budget (NVIDIA GPU — 16 GB)

Models are loaded **sequentially, never concurrently across phases**:

| Phase | Models active | VRAM |
|---|---|---|
| During meeting | Silero VAD + Whisper large-v3 + pyannote 3.3 | ~5.1 GB |
| After meeting | Ollama Mistral 7B Q4_K_M | ~5 GB |

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop shell | Tauri 2 |
| Frontend | React 19 + TypeScript 5.5 + Tailwind CSS 4 |
| Backend | Python 3.11 + FastAPI |
| Speech-to-text | faster-whisper (large-v3) |
| Speaker diarization | pyannote.audio 3.3 |
| Voice activity detection | Silero VAD 5 |
| LLM (summaries) | Ollama + Mistral 7B Q4_K_M |
| Storage | SQLite + FTS5 |
| Build | Vite 6 |

## Prerequisites

- Python 3.11+
- Node.js 20+
- Rust (for Tauri)
- NVIDIA GPU with 6+ GB VRAM recommended (CPU fallback works but is slow)
- [Ollama](https://ollama.com) installed and running
- A [HuggingFace](https://huggingface.co) account with access granted to:
  - [pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
  - [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
  - [pyannote/speaker-diarization-community-1](https://hf.co/pyannote/speaker-diarization-community-1)

## Getting Started

```bash
# Clone the repo
git clone https://github.com/your-username/recap.git
cd recap

# Backend
cd backend
python -m venv .venv

# Activate the virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell (if you get an execution policy error, first run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser)
.venv\Scripts\activate

pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Environment Variables

Create a `.env` file in `backend/` or set these in your shell before starting:

| Variable | Required | Description |
|---|---|---|
| `HF_TOKEN` | Yes | HuggingFace token with read access — needed to download pyannote models |

```powershell
# Windows PowerShell
$env:HF_TOKEN="hf_your_token_here"
```

Get a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (Read access is sufficient).

## Development

```bash
# Terminal 1 — Backend
cd backend
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m uvicorn main:app --reload --port 8420

# Terminal 2 — Frontend + Tauri
cd frontend
npm run tauri dev
```

On first run, pyannote and Whisper models are downloaded automatically and cached in `~/.cache/huggingface/`. This can take a few minutes depending on your connection.

## Ollama Setup

```bash
ollama pull mistral
```

Ollama must be running before starting the backend. The summarization step after each meeting calls it at `http://localhost:11434`.

## Privacy

All ML inference runs locally:
- faster-whisper and pyannote run on your GPU/CPU
- Summaries are generated by Ollama (local LLM runtime)
- Audio recordings are saved to `data/recordings/` on your machine only
- No telemetry, no cloud API calls, no accounts required

## License

MIT
