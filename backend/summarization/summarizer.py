import json

import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT = """\
You are a meeting assistant. Given the following transcript, produce a structured summary.

Transcript:
{transcript}

Respond with valid JSON in exactly this format:
{{
  "overview": "A 2-3 sentence overview of the meeting",
  "key_points": ["point 1", "point 2", "point 3"],
  "action_items": ["action 1", "action 2"]
}}\
"""


async def summarize(transcript: str) -> dict:
    """Send the transcript to Ollama and return the parsed summary dict."""
    prompt = _PROMPT.format(transcript=transcript)
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()

    text: str = response.json()["response"]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in Ollama response: {text[:200]}")
    return json.loads(text[start:end])
