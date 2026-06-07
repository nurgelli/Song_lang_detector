FROM python:3.11-slim AS worker_deps

WORKDIR /worker_env

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY sp_requirements.txt .
RUN pip install --no-cache-dir -r sp_requirements.txt



FROM python:3.11-slim AS app_deps

WORKDIR /app_env


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Environment Variables
ARG ENV_MODE=prod
ENV ENV_MODE=${ENV_MODE}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/tmp/song_processing 

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*


COPY --from=app_deps /usr/local/ /usr/local/

ENV PYTHON_SP_VENV_PATH=/worker_venv
RUN mkdir -p ${PYTHON_SP_VENV_PATH}
COPY --from=worker_deps /usr/local/ ${PYTHON_SP_VENV_PATH}

COPY . .

ENV PYTHON_SP_VENV_PATH=${PYTHON_SP_VENV_PATH}/bin/python
ENV UNMIX_WORKER_SCRIPT=/app/unmix_worker.py

EXPOSE 8000

RUN mkdir -p $TEMP_DIR


CMD ["python", "main.py"]
