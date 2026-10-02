# app.py
"""
Chinese-to-English Translator — Flask entry point.

Supports:
  - /              GET  → serves the HTML UI
  - /translate     POST → translates Chinese text to English
  - /translate_audio POST → accepts an audio file, runs SeamlessM4T to
                            produce an English translation directly
"""

import os
import uuid
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from translate_text import translate_text
from translate_audio import translate_audio, _seamless_available

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "mp3", "wav", "m4a", "ogg", "flac", "webm", "mp4",
    "aac", "wma", "opus"
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/status", methods=["GET"])
def status_route():
    """Check which backends are available."""
    seamless = _seamless_available()
    return jsonify({
        "seamless_m4t": seamless,
        "backend_audio": "SeamlessM4T (WSL2)" if seamless else "faster-whisper (local CPU)",
        "backend_text": "SeamlessM4T (WSL2)" if seamless else "argostranslate (offline)",
    })


@app.route("/translate", methods=["POST"])
def text_route():
    data = request.get_json(force=True, silent=True) or {}
    chinese = (data.get("text") or "").strip()
    if not chinese:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = translate_text(chinese)
        return jsonify({"translation": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/translate_audio", methods=["POST"])
def audio_route():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided (field name: 'audio')"}), 400
    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not _allowed(file.filename):
        return jsonify({"error": f"Unsupported format. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
    file.save(temp_path)
    try:
        result = translate_audio(temp_path)
        if isinstance(result, dict):
            return jsonify(result)
        return jsonify({"translation": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
