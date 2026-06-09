import os
import shutil
import subprocess
import uuid

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.lang_detect import analyze_audio
from app.settings import (
    ENABLE_UNMIX,
    PYTHON_SP_VENV_PATH,
    TEMP_DIR,
    UNMIX_WORKER_SCRIPT,
)

app = FastAPI(
    title="Audio Language Detector",
    description=(
        "Upload Song => detect language & transcribe lyrics.\n\n"
        "**How to use:** send song to the `POST /detect` endpoint, "
        "get detected language + lyrics as JSON."
    ),
    version="3.0.0",
)

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".mp4", ".webm"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "unmix_enabled": ENABLE_UNMIX,
    }


def unmix_audio_to_vocal(input_filepath: str, output_dir: str) -> str | None:
    command = [
        PYTHON_SP_VENV_PATH,
        UNMIX_WORKER_SCRIPT,
        input_filepath,
        output_dir,
    ]
    try:
        print(f"[unmix] Starting.. {input_filepath}")
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
        print(f"[unmix] Done:\n{result.stdout}")

        vocal_path = os.path.join(output_dir, "vocals.wav")
        if not os.path.exists(vocal_path):
            print(f"[unmix] Error - vocals.wav not found. Stderr:\n{result.stderr}")
            return None

        return vocal_path

    except subprocess.TimeoutExpired:
        print("[unmix] Timeout: process 300 second pass.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[unmix] Worker error return:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"[unmix] unexpected error: {e}")
        return None


@app.post("/detect", tags=["Detection"])
async def detect_language(
    file: UploadFile = File(..., description="Target audio file"),
    enable_unmix: bool = Form(default=False, description="Apply vocal isolation before analysis"),
):
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: '{ext}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    job_id  = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    input_path = os.path.join(job_dir, f"input{ext}")

    try:
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"[detect] New request => job_id={job_id}, file={filename} ({len(content):,} bytes), unmix={enable_unmix}")

        audio_path    = input_path
        unmix_applied = False

        if enable_unmix:
            vocal_path = unmix_audio_to_vocal(input_path, job_dir)
            if vocal_path:
                audio_path    = vocal_path
                unmix_applied = True
            else:
                print("[detect] Unmix failed, using original audio.")

        result = analyze_audio(audio_path)

        return JSONResponse(content={
            "filename":          filename,
            "detected_language": result["language"],
            "transcription":     result["transcription"],
            "unmix_applied":     unmix_applied,
            "job_id":            job_id,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)


if __name__ == "__main__":
    os.makedirs(TEMP_DIR, exist_ok=True)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")