FROM python:3.11-slim

# Install system dependencies (ffmpeg is required for audio transcription)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs as user with UID 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860

WORKDIR $HOME/app

# Install Python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download argostranslate Chinese->English package during build
RUN python -c "import argostranslate.package; argostranslate.package.update_package_index(); available = argostranslate.package.get_available_packages(); pkg = next((p for p in available if p.from_code == 'zh' and p.to_code == 'en'), None); argostranslate.package.install_from_path(pkg.download()) if pkg else None"

# Copy project files
COPY --chown=user:user . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

CMD ["python", "app.py"]
