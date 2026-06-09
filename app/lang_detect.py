import whisper
import warnings
import os

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

def get_whisper_model():
    env_mode   = os.getenv("ENV_MODE", "dev")
    model_name = "tiny" if env_mode == "dev" else "turbo"
    print(f"[whisper] Loading model: {model_name}")
    return whisper.load_model(model_name)


model = get_whisper_model()


def analyze_audio(audio_path: str) -> dict:
    try:
        print(f"[whisper] Analyzing: {audio_path}")
        result = model.transcribe(audio_path)

        lang        = result.get("language", "unknown")
        transcription = result.get("text", "").strip()
        confidence  = round(result.get("language_probability", 0) * 100, 1)

        print(f"[whisper] Lang: {lang} ({confidence}%) | {len(transcription)} chars transcribed")
        return {"language": lang, "transcription": transcription}

    except Exception as e:
        print(f"[whisper] Analysis error: {e}")
        return {"language": "unknown", "transcription": ""}


def detect_lang(audio_path: str) -> str:
    return analyze_audio(audio_path)["language"]