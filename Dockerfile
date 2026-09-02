FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-core \
        fonts-liberation \
        fonts-dejavu-core \
        xvfb \
        xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY document-converter/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY document-converter/app.py ./app.py

EXPOSE 10000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
