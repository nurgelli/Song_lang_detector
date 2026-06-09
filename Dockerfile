FROM python:3.11-slim AS worker_build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY sp_requirements.txt .

RUN python -m venv --copies /worker_venv \
    && /worker_venv/bin/pip install --upgrade pip \
    && /worker_venv/bin/pip install -r sp_requirements.txt


FROM python:3.11-slim AS app_build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt


FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=app_build /usr/local /usr/local
COPY --from=worker_build /worker_venv /worker_venv

COPY app/ ./app/
COPY main.py ./
COPY unmix_worker.py ./
COPY .env.dev ./

ARG ENV_MODE=dev
ENV ENV_MODE=${ENV_MODE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV ENABLE_UNMIX=false

ENV PYTHON_SP_VENV_PATH=/worker_venv/bin/python
ENV UNMIX_WORKER_SCRIPT=/app/unmix_worker.py
ENV TEMP_DIR=/tmp/song_processing

RUN mkdir -p ${TEMP_DIR}

EXPOSE 8000

CMD ["python", "main.py"]