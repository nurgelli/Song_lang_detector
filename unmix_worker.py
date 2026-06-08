import argparse
import os

import torch
import torchaudio
from openunmix import predict


def run_unmix(input_file: str, output_dir: str) -> str | None:
    try:
        target     = "vocals"
        model_name = "umxhq"   

        print(f"[worker] Music loading: {input_file}")
        audio, rate = torchaudio.load(input_file)

        if audio.shape[0] == 1:
            audio = audio.repeat(2, 1)      
        elif audio.shape[0] > 2:
            audio = audio[:2, :]            

        audio_batch = audio.unsqueeze(0)

        print(f"[worker] vocal seperating ({model_name})...")
        with torch.no_grad():
            estimates = predict.separate(
                audio=audio_batch,
                rate=rate,
                model_str_or_path=model_name,
                targets=[target],
                residual=False,
            )

        vocal_tensor = estimates[target].squeeze(0)   

        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"{target}.wav")

        torchaudio.save(output_filepath, vocal_tensor, rate)
        print(f"[worker] Vocal saved: {output_filepath}")
        return output_filepath

    except Exception as e:
        print(f"[worker] error: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open-Unmix Vocal Separator Worker")
    parser.add_argument("input_file", type=str, help="Input music file (wav/mp3/flac...)")
    parser.add_argument("output_dir", type=str, help="output folder (vocals.wav buraya yazılır)")
    args = parser.parse_args()

    result = run_unmix(args.input_file, args.output_dir)
    if result is None:
        print("[worker] Seperation failed.")
        raise SystemExit(1)
