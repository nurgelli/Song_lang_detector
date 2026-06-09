import argparse
import os
import shutil
import subprocess
import tempfile
import traceback

import torch
import torchaudio
from openunmix import predict



SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL_DIR = os.path.join(SCRIPT_DIR, "models", "umxhq")


UMXHQ_TARGET_FILES = {
    "vocals": "vocals-b62c91ce.pth",
    # "drums":  "drums-9619578f.pth",
    # "bass":   "bass-8d85a5bd.pth",
    # "other":  "other-b52fbbf7.pth",
}


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found

    fallback_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
    ]
    for path in fallback_paths:
        if os.path.isfile(path):
            return path

    raise RuntimeError("ffmpeg not found.\n")


def convert_to_wav(input_file: str) -> str:
    ffmpeg = find_ffmpeg()
    print(f"[worker] ffmpeg found: {ffmpeg}")

    fd, out_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    cmd = [
        ffmpeg, "-y",
        "-i", input_file,
        "-ar", "44100",
        "-ac", "2",
        "-acodec", "pcm_s16le",
        "-f", "wav",
        out_path,
    ]

    print(f"[worker] Converting to WAV: {os.path.basename(input_file)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        os.unlink(out_path)
        raise RuntimeError(f"ffmpeg conversion failed:\n{result.stderr}")

    size = os.path.getsize(out_path)
    if size < 44:
        os.unlink(out_path)
        raise RuntimeError(f"ffmpeg produced a suspiciously small WAV ({size} bytes).")

    print(f"[worker] Conversion done: {out_path}  ({size:,} bytes)")
    return out_path


def load_audio_robust(path: str):
    try:
        audio, rate = torchaudio.load(path)
        print(f"[worker] torchaudio.load OK — shape={audio.shape}, rate={rate}")
        return audio, rate
    except Exception as primary_err:
        print(f"[worker] torchaudio.load failed ({primary_err}), trying ffmpeg pipe fallback...")

    ffmpeg = find_ffmpeg()
    rate = 44100

    probe_cmd = [
        ffmpeg, "-i", path,
        "-ar", str(rate), "-ac", "2",
        "-f", "f32le", "-acodec", "pcm_f32le",
        "pipe:1",
    ]
    proc = subprocess.run(probe_cmd, capture_output=True)
    if len(proc.stdout) == 0:
        raise RuntimeError(
            f"ffmpeg pipe fallback produced no data.\nstderr:\n{proc.stderr.decode(errors='replace')}"
        )

    import numpy as np
    samples = np.frombuffer(proc.stdout, dtype=np.float32).copy()
    audio = torch.from_numpy(samples.reshape(-1, 2).T)
    print(f"[worker] Fallback load OK — {audio.shape[1]} samples @ {rate} Hz")
    return audio, rate


def get_model_path_or_name(target: str, model_name: str) -> str:
    """
    Lokal models/umxhq/ klasöründe ilgili .pth varsa tam path döner.
    Yoksa model_name string'ini döner (torch.hub'dan indirir).
    """
    if model_name == "umxhq" and target in UMXHQ_TARGET_FILES:
        fname      = UMXHQ_TARGET_FILES[target]
        local_path = os.path.join(LOCAL_MODEL_DIR, fname)
        if os.path.isfile(local_path):
            size = os.path.getsize(local_path)
            print(f"[worker] Using local model: {local_path}  ({size:,} bytes)")
            return local_path
        else:
            print(f"[worker] Local model NOT found at {local_path}")
            print(f"[worker] Will attempt torch.hub download")

    return model_name  # fallback: hub string


def run_unmix(input_file: str, output_dir: str) -> str | None:
    tmp_wav = None

    try:
        target     = "vocals"
        model_name = "umxhq"

        ext = os.path.splitext(input_file)[1].lower()
        if ext != ".wav":
            tmp_wav   = convert_to_wav(input_file)
            load_path = tmp_wav
        else:
            load_path = input_file

        print(f"[worker] Loading audio: {load_path}")
        audio, rate = load_audio_robust(load_path)

        if audio.shape[0] == 1:
            audio = audio.repeat(2, 1)
        elif audio.shape[0] > 2:
            audio = audio[:2, :]

        audio_batch = audio.unsqueeze(0)

        model_str = get_model_path_or_name(target, model_name)

        print(f"[worker] Separating vocals (model={model_str})...")
        with torch.no_grad():
            estimates = predict.separate(
                audio=audio_batch,
                rate=rate,
                model_str_or_path=model_str,
                targets=[target],
                residual=True,
            )

        vocal_tensor = estimates[target].squeeze(0)

        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"{target}.wav")

        torchaudio.save(output_filepath, vocal_tensor, rate)
        print(f"[worker] Vocal saved: {output_filepath}")
        return output_filepath

    except Exception as e:
        print(f"[worker] error: {e}")
        traceback.print_exc()
        return None

    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            os.unlink(tmp_wav)
            print(f"[worker] Temp file cleaned: {tmp_wav}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open-Unmix Vocal Separator Worker")
    parser.add_argument("input_file",  type=str, help="Input music file (wav/mp3/flac...)")
    parser.add_argument("output_dir",  type=str, help="Output folder (vocals.wav saved here)")
    args = parser.parse_args()

    result = run_unmix(args.input_file, args.output_dir)
    if result is None:
        print("[worker] Separation failed.")
        raise SystemExit(1)