import requests
# import threading
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from fastapi import FastAPI
from app.lang_detect import detect_lang
from app.settings import API_TOKEN, API_BASE_URL, API_UPDATE_URL

POLLING_INTERVAL = 5
app = FastAPI()
headers = {"Authorization": f"Bearer {API_TOKEN}"}

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
    try:
        resp = requests.put(
            update_url,
            headers=headers,
            json={"lang": lang}
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Network or API error while updating song {song_id}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f'Error parsing JSON update response for song {song_id}: {e}')

def process_song(song):
    song = get_next_song()
    if song:
        try:
            audio_path = song["audioFileUrl"]
            song_id = song['id']
            lang = detect_lang(audio_path)
            update_song_language(song_id, lang)
            print(f"Song Updated {song_id} with language {lang}")
        except Exception as e:
            print(f'Error in processing song {song.get("id", "N/A")}: {e}')

scheduler = BackgroundScheduler()
scheduler.add_job(
    process_song,
    'interval', 
    seconds=POLLING_INTERVAL,
    max_instances=1,
    coalesce=True,
    id="job_proc"
    )

atexit.register(lambda: scheduler.shutdown(wait=False))

if __name__ == "__main__":
    scheduler.start()
    uvicorn.run(app, port=8000, host="0.0.0.0", log_level="info")
