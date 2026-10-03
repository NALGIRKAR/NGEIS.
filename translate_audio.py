# translate_audio.py
"""
Chinese audio → English text.

Optimized Pipeline:
  1. High-accuracy ASR: faster-whisper (medium INT8) transcribes Chinese speech
     with beam_size=5, deterministic temperature=0.0, and a Mandarin context prompt.
  2. Accurate Translation: The recognized Chinese text is translated to English
     using translate_text (argostranslate / SeamlessM4T).
  3. Returns both the recognized Chinese speech and the English translation.
"""

import os
import logging
import requests as http_requests

logger = logging.getLogger(__name__)

# ── Inject ffmpeg into PATH (Windows local fallback) ───────────────────────
FFMPEG_DIR = r"C:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin"
if os.path.isdir(FFMPEG_DIR) and FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# SeamlessM4T backend URL (running inside WSL2 if enabled)
SEAMLESS_URL = "http://localhost:5001"


# ── SeamlessM4T backend (WSL2) ─────────────────────────────────────────────

def _seamless_available() -> bool:
    """Check if the SeamlessM4T backend is running."""
    try:
        r = http_requests.get(f"{SEAMLESS_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _translate_via_seamless(file_path: str) -> dict:
    """Send audio to SeamlessM4T backend for translation."""
    with open(file_path, "rb") as f:
        files = {"audio": (os.path.basename(file_path), f)}
        r = http_requests.post(
            f"{SEAMLESS_URL}/translate_audio",
            files=files,
            timeout=300,
        )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"SeamlessM4T error: {data['error']}")
    return {
        "translation": data["translation"],
        "original": data.get("original", ""),
    }


# ── High-Accuracy faster-whisper (local Windows CPU) ─────────────────────────

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


def _translate_via_whisper(file_path: str) -> dict:
    """Transcribe Chinese speech with high accuracy, then translate to English."""
    from translate_text import translate_text

    _load_whisper()

    # Step 1: High-accuracy Chinese Speech Recognition
    # Setting initial_prompt primes Whisper for standard Mandarin vocabulary and tones
    segments, info = _whisper_model.transcribe(
        file_path,
        language="zh",
        task="transcribe",
        beam_size=5,          # Beam 5 for superior recognition accuracy
        best_of=5,
        temperature=0.0,      # Deterministic decoding prevents hallucinated words
        initial_prompt="这是一段标准中文普通话对话，发音清晰。",
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400, threshold=0.4),
    )

    chinese_text = " ".join(seg.text.strip() for seg in segments).strip()

    if not chinese_text:
        return {
            "translation": "No clear speech detected. Please speak closer to the microphone and try again.",
            "original": "",
        }

    # Step 2: Accurate translation of recognized Chinese text to English
    english_translation = translate_text(chinese_text)

    return {
        "translation": english_translation,
        "original": chinese_text,
    }


# ── Public API ──────────────────────────────────────────────────────────────

def translate_audio(file_path: str) -> dict:
    """Translate Chinese speech to English text.

    Tries SeamlessM4T (WSL2 backend) first for best quality.
    Falls back to high-accuracy faster-whisper pipeline locally.

    Args:
        file_path: Path to the audio file.
    Returns:
        dict with {"translation": str, "original": str}
    """
    if _seamless_available():
        logger.info("Using SeamlessM4T backend (WSL2)")
        try:
            return _translate_via_seamless(file_path)
        except Exception as exc:
            logger.warning(f"SeamlessM4T failed ({exc}), falling back to faster-whisper…")

    logger.info("Using high-accuracy faster-whisper pipeline (local CPU)")
    return _translate_via_whisper(file_path)
