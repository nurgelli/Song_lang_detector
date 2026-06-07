import os
import argparse
import torchaudio
import openunmix

def run_unmix(input_file, output_dir):
    try:
        target = "vocals"
        model = "umxhq" 

        print(f"Song is loading: {input_file}")
        
      
        audio, rate = torchaudio.load(input_file)
        
        print(f"Vocal seperating starting ({model} model)...")
        estimates = openunmix.model.separate_audio(
            audio, 
            rate, 
            targets=[target], 
            model_name=model
        )

        output_filepath = os.path.join(output_dir, f"{target}.wav")

        os.makedirs(output_dir, exist_ok=True)
        

        vocal_track = estimates[0, ...]


        torchaudio.save(output_filepath, vocal_track, rate)
        
        print(f"Vocal successfully got: {output_filepath}")
        return output_filepath

    except Exception as e:
        print(f"Error in starting Open-Unmix: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Audio file input")
    parser.add_argument("output_dir", type=str, help="Output folder")
    
    args = parser.parse_args()
    
    run_unmix(args.input_file, args.output_dir)