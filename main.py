import requests
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from app.lang_detect import detect_lang
from app.settings import API_TOKEN, API_BASE_URL, API_UPDATE_URL, UNMIX_WORKER_SCRIPT, PYTHON_SP_VENV_PATH
import subprocess
import os

POLLING_INTERVAL = 5
app = FastAPI()
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
    }


@app.get('/health')
def health_check():
    return {"status": "ok"}

def get_next_song():
    try:
        resp = requests.get(API_BASE_URL, headers=headers)
        resp.raise_for_status()
        song = resp.json()
        if 'audioFileUrl' not in song or 'id' not in song:
            raise KeyError("API missing url or id or both of them")
        return song
    except requests.exceptions.RequestException as e:
        print(f'Network or API error while fetching song: {e}')
        return None          
    except (ValueError, KeyError) as e:
        print(f'Error parsing JSON or missing data in API response: {e}')
        return None

def update_song_language(song_id, lang):
    update_url = f"{API_UPDATE_URL}/{song_id}"
    # print(update_url)
    try:
        resp = requests.put(
            update_url,
            headers=headers,
            json={"lang": lang}
        )
        resp.raise_for_status()
        print(resp.json())
        return resp.json()

    except requests.exceptions.RequestException as e:
        print(f"Network or API error while updating song {song_id}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f'Error parsing JSON update response for song {song_id}: {e}')

def unmix_audio_to_vocal(input_filepath, output_dir):
      
    #from .env.dev for win system
    PYTHON_VENV_PATH = PYTHON_SP_VENV_PATH 
    UNMIX_WORKER_SCRIPT = UNMIX_WORKER_SCRIPT

    UNMIX_COMMAND = [
        PYTHON_VENV_PATH, 
        UNMIX_WORKER_SCRIPT, 
        input_filepath, 
        output_dir
    ]
    
    try:
        print(f"Starting unmixing using external worker for {input_filepath}...")
        
        result = subprocess.run(UNMIX_COMMAND, check=True, capture_output=True, text=True)
        print("Unmixing complete.")
        print(f"Unmix Worker Cikti: \n{result.stdout}")

        
        vocal_filepath = os.path.join(output_dir, "vocals.wav") 
        
        if not os.path.exists(vocal_filepath):

             print(f"Unmix Worker Erorr: \n{result.stderr}") 
             raise FileNotFoundError(f"Unmix Error: Vocal file {vocal_filepath} not found.")
        return vocal_filepath

    except subprocess.CalledProcessError as e:
        print(f"Unmix worker script finished with error code. Error: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unmixing process Erorr: {e}")
        return None


def process_song():
    song = get_next_song()
    if song:
        try:
            song_id = song['id']
            audio_path = song["audioFileUrl"]
            lang = detect_lang(audio_path)
            update_song_language(song_id, lang)
            
        except Exception as e:
            print(f'Error in processing song {song.get("id", "N/A")}: {e}')

# Job_scheduling
scheduler = BackgroundScheduler()
scheduler.add_job(
    process_song,
    'interval', 
    seconds=POLLING_INTERVAL,
    max_instances=1,
    coalesce=True)

# For quitting from job_scheduler
import atexit
atexit.register(lambda: scheduler.shutdown(wait=False))

if __name__ == "__main__":
    scheduler.start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
