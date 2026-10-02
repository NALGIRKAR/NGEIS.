# translate_audio.py
"""
Chinese audio → English text.

Architecture:
  PRIMARY:  SeamlessM4T running inside WSL2 on port 5001
            (best quality, supports S2TT, S2ST, T2TT)
  FALLBACK: faster-whisper running locally on Windows
            (if WSL2 backend is not available)

The code automatically detects which backend is available.
"""

import os
import logging
import requests as http_requests

logger = logging.getLogger(__name__)

# ── Inject ffmpeg into PATH ────────────────────────────────────────────────
FFMPEG_DIR = r"C:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin"
if FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# SeamlessM4T backend URL (running inside WSL2)
SEAMLESS_URL = "http://localhost:5001"


# ── SeamlessM4T backend (WSL2) ─────────────────────────────────────────────

def _seamless_available() -> bool:
    """Check if the SeamlessM4T backend is running."""
    try:
        r = http_requests.get(f"{SEAMLESS_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _translate_via_seamless(file_path: str) -> str:
    """Send audio to SeamlessM4T backend for translation."""
    with open(file_path, "rb") as f:
        files = {"audio": (os.path.basename(file_path), f)}
        r = http_requests.post(
            f"{SEAMLESS_URL}/translate_audio",
            files=files,
            timeout=300,  # model can take a while on CPU
        )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"SeamlessM4T error: {data['error']}")
    return data["translation"]


# ── faster-whisper fallback (local Windows) ─────────────────────────────────

_whisper_model = None


def _load_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return
    from faster_whisper import WhisperModel
    logger.info("Loading faster-whisper 'medium' model (INT8, CPU)…")
    _whisper_model = WhisperModel(
        "medium",
        device="cpu",
        compute_type="int8",
        cpu_threads=0,
        num_workers=2,
    )
    logger.info("faster-whisper ready.")


def _translate_via_whisper(file_path: str) -> str:
    """Translate audio using local faster-whisper."""
    _load_whisper()
    segments, info = _whisper_model.transcribe(
        file_path,
        language="zh",
        task="translate",
        beam_size=3,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    return " ".join(seg.text.strip() for seg in segments).strip()


# ── Public API ──────────────────────────────────────────────────────────────

def translate_audio(file_path: str) -> str:
    """Translate Chinese speech to English text.

    Tries SeamlessM4T (WSL2 backend) first for best quality.
    Falls back to faster-whisper (local) if the backend is unavailable.

    Args:
        file_path: Path to the audio file.
    Returns:
        English translation string.
    """
    # Try SeamlessM4T first
    if _seamless_available():
        logger.info("Using SeamlessM4T backend (WSL2)")
        try:
            return _translate_via_seamless(file_path)
        except Exception as exc:
            logger.warning(f"SeamlessM4T failed ({exc}), falling back to faster-whisper…")

    # Fallback: faster-whisper
    logger.info("Using faster-whisper (local CPU)")
    return _translate_via_whisper(file_path)
