FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg espeak-ng fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from faster_whisper import WhisperModel; import requests" && pip check
COPY app.py .
CMD ["sh","-c","gunicorn -w 1 --threads 2 --timeout 600 -b 0.0.0.0:${PORT:-8080} app:app"]
