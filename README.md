# 🀄 Chinese → English Web Translator (Text & Speech)

A fast, lightweight web application for translating **Chinese text and Chinese speech/audio** into English.

Built with **Flask**, **faster-whisper** (CTranslate2 INT8), **argostranslate**, and HTML5 Web APIs.

---

## ✨ Features

- 📝 **Chinese Text Translation:** Fast offline translation powered by `argostranslate`. No rate limits.
- 🎙️ **Speech & Audio Translation:** Directly translates spoken Chinese audio into English text in one step via `faster-whisper` (medium model, INT8 quantized for CPU).
- 🎤 **Live Microphone Recording:** Record Chinese speech straight from your web browser.
- 📁 **All Audio Formats Supported:** MP3, WAV, M4A, OGG, FLAC, WebM, MP4, AAC, and more.
- 🔊 **Text-to-Speech (Pronunciation):** Listen to the translated English text read aloud with a single click.
- 🔗 **1-Click Public Sharing:** Share your local app securely with anyone over the internet using `share.bat`.

---

## 🛠️ Requirements

- Python 3.10+ (tested on Python 3.13)
- [FFmpeg](https://ffmpeg.org/download.html) (for audio conversion)

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/chinese-to-english-translator.git
cd chinese-to-english-translator
```

### 2. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the web server
```powershell
python app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🌐 Sharing With Others

To share with friends or testers without deploying to a cloud server:
Run `share.bat` to launch the server and generate a free, public HTTPS link (via Cloudflare Tunnels).

---

## 📂 Project Structure

```
├── app.py                  # Main Flask application and API routes
├── translate_text.py       # Offline text translation engine
├── translate_audio.py      # Speech-to-text translation engine (faster-whisper)
├── templates/
│   └── index.html          # Modern dark-themed web interface
├── share.bat               # 1-click script to share publicly
├── requirements.txt        # Python package dependencies
└── .gitignore
```

---

## 📜 License
MIT License
