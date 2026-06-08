import whisper
import os


def get_whisper_model():
    env_mode   = os.getenv("ENV_MODE", "dev")
    model_name = "tiny" if env_mode == "dev" else "turbo"
    print(f"[whisper] Loading model: {model_name}")
    return whisper.load_model(model_name)


model = get_whisper_model()


def detect_lang(audio_path: str) -> str:
    try:
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel   = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)

        _, probs       = model.detect_language(mel)
        detected_lang  = max(probs, key=probs.get)
        confidence     = round(probs[detected_lang] * 100, 1)

        print(f"[whisper] Detected Lang: {detected_lang} ({confidence}% confident)")
        return detected_lang

    except Exception as e:
        print(f"[whisper] Lang detection error: {e}")
        return "unknown"
