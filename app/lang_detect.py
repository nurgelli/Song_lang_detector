import whisper
import os

def get_whisper_model():
    ENV_MODE = os.getenv('ENV_MODE', 'dev')
    model_name = "tiny" if ENV_MODE == 'dev' else "turbo"
    print(f'Loading whisper model: {model_name}')
    return whisper.load_model(model_name)

model = get_whisper_model()   

def detect_lang(audio_path):
    try:
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)
        _, probs = model.detect_language(mel)
        detected_lang = max(probs, key=probs.get) 
        print(f"Detected Language for {audio_path}: {detected_lang}")
        return detected_lang
            
    except Exception as e:
        print(f'Error during lang detection: {e}')
        return 'unknown'