import os
import threading
import requests
import yt_dlp
from flask import Flask, request
from yt_dlp.utils import sanitize_filename

app = Flask(__name__)

# CONFIGURATION
SEER_URL = "http://localhost:5055/api/v1"
SEER_API_KEY = "YOUR_SEER_API_KEY"
DEFAULT_DRIVE = "H:/TV Shows"

def get_path_from_seer(title):
    headers = {"X-Api-Key": SEER_API_KEY}
    try:
        search = requests.get(f"{SEER_URL}/search?query={title}", headers=headers).json()
        if not search.get('results'): return None
        
        media_id = search['results'][0]['id']
        m_type = search['results'][0]['mediaType']
        details = requests.get(f"{SEER_URL}/{m_type}/{media_id}", headers=headers).json()
        
        if 'mediaInfo' in details and details['mediaInfo'].get('plexPath'):
            return os.path.dirname(details['mediaInfo']['plexPath'])
    except requests.RequestException as e:
        print(f"Error querying Seer: {e}")
        return None
    return None

def download_task(url, series_name, season, episode):
    season_pad = str(season).zfill(2)
    episode_pad = str(episode).zfill(2)
    safe_series_name = sanitize_filename(series_name)
    
    base_dir = get_path_from_seer(series_name) or os.path.join(DEFAULT_DRIVE, safe_series_name)
    target_dir = os.path.join(base_dir, f"Season {season_pad}")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Plex Naming: Series - S01E01 - Title.mkv
    output_template = os.path.join(target_dir, f"{safe_series_name} - S{season_pad}E{episode_pad} - %(title)s.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mkv',
        'outtmpl': output_template,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/dl')
def trigger():
    video_url = request.args.get('url')
    series_name = request.args.get('cat')
    season = request.args.get('s')
    episode = request.args.get('e')
    
    if not all([video_url, series_name, season, episode]):
        return "Missing required parameters.", 400
    
    threading.Thread(target=download_task, args=(video_url, series_name, season, episode)).start()
    return f"Processing {series_name} S{str(season).zfill(2)}E{str(episode).zfill(2)}..."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)