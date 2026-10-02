#!/bin/bash
# setup_seamless.sh — Run this INSIDE WSL2 Ubuntu after installation
# This script sets up SeamlessM4T as a backend translation API server

set -e

echo "=== Step 1: Install system dependencies ==="
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev \
    ffmpeg libsndfile1 git curl

echo "=== Step 2: Create project directory ==="
mkdir -p ~/ch2en_translator
cd ~/ch2en_translator

echo "=== Step 3: Create Python 3.11 virtual environment ==="
python3.11 -m venv venv
source venv/bin/activate

echo "=== Step 4: Install pip and core packages ==="
pip install --upgrade pip
pip install flask requests

echo "=== Step 5: Install fairseq2 (SeamlessM4T dependency) ==="
pip install fairseq2

echo "=== Step 6: Clone and install seamless_communication ==="
git clone https://github.com/facebookresearch/seamless_communication.git
cd seamless_communication
pip install .
cd ..

echo "=== Step 7: Create the Flask backend server ==="
cat > backend_server.py << 'PYEOF'
# backend_server.py — SeamlessM4T Flask API running inside WSL2
"""
This server runs inside WSL2 on port 5001.
The Windows Flask app (port 5000) forwards audio requests here.

Endpoints:
  POST /translate_audio  — accepts audio file, returns English translation
  POST /translate_text   — accepts JSON {text: "..."}, returns English translation
  GET  /health           — health check
"""

import os
import uuid
import tempfile
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

# ── Lazy model loading ──────────────────────────────────────────────────────
_translator = None

def _load_model():
    global _translator
    if _translator is not None:
        return
    logger.info("Loading SeamlessM4T v2 Large model (first time — downloads ~10 GB)...")
    from seamless_communication.models.inference import Translator
    _translator = Translator(
        model_name_or_card="seamlessM4T_v2_large",
        vocoder_name_or_card="vocoder_v2",
        device="cpu",
        dtype="float32",
    )
    logger.info("SeamlessM4T model loaded successfully!")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "seamlessM4T_v2_large"})


@app.route("/translate_audio", methods=["POST"])
def translate_audio():
    """Speech-to-text translation: Chinese audio → English text."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["audio"]
    # Save to temp file
    suffix = os.path.splitext(file.filename)[1] or ".wav"
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    file.save(temp_path)

    try:
        _load_model()
        # S2TT: Speech-to-Text Translation
        translation, _, _ = _translator.predict(
            input=temp_path,
            task_str="S2TT",
            src_lang="cmn",    # Mandarin Chinese
            tgt_lang="eng",    # English
        )
        return jsonify({"translation": str(translation[0])})
    except Exception as exc:
        logger.error(f"Translation error: {exc}", exc_info=True)
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.route("/translate_text", methods=["POST"])
def translate_text():
    """Text-to-text translation: Chinese text → English text."""
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        _load_model()
        # T2TT: Text-to-Text Translation
        translation, _, _ = _translator.predict(
            input=text,
            task_str="T2TT",
            src_lang="cmn",
            tgt_lang="eng",
        )
        return jsonify({"translation": str(translation[0])})
    except Exception as exc:
        logger.error(f"Translation error: {exc}", exc_info=True)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    logger.info("Starting SeamlessM4T backend on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=False)
PYEOF

echo ""
echo "============================================="
echo "  Setup complete!"
echo "============================================="
echo ""
echo "To start the SeamlessM4T backend server, run:"
echo "  cd ~/ch2en_translator"
echo "  source venv/bin/activate"
echo "  python backend_server.py"
echo ""
echo "The server will be available at http://localhost:5001"
echo "First request will download the model (~10 GB)."
echo "============================================="
