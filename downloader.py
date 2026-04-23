import os
import threading
import requests
import yt_dlp
from flask import Flask, request
from yt_dlp.utils import sanitize_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CONFIGURATION
# Set these variables in a local .env file.
SEER_URL = os.getenv("SEER_URL", "http://localhost:5055/api/v1")
SEER_API_KEY = os.getenv("SEER_API_KEY", "")
DEFAULT_DRIVE = os.getenv("DEFAULT_DRIVE", "H:/TV Shows")

def get_path_from_seer(title):
    """
    Queries the Seer (Overseerr/Jellyseerr) API to find where a show is currently stored.
    This ensures that new episodes are downloaded to the same drive as existing ones.
    """
    headers = {"X-Api-Key": SEER_API_KEY}
    try:
        # Search for the series by title
        search = requests.get(f"{SEER_URL}/search?query={title}", headers=headers).json()
        if not search.get('results'): return None
        
        # Get detailed info for the first search result
        media_id = search['results'][0]['id']
        m_type = search['results'][0]['mediaType']
        details = requests.get(f"{SEER_URL}/{m_type}/{media_id}", headers=headers).json()
        
        # Extract the directory path if Seer knows about this media in Plex
        if 'mediaInfo' in details and details['mediaInfo'].get('plexPath'):
            return os.path.dirname(details['mediaInfo']['plexPath'])
    except requests.RequestException as e:
        print(f"Error querying Seer: {e}")
        return None
    return None

def download_task(url, series_name, season, episode):
    """
    Background task that handles the actual downloading via yt-dlp.
    It formats the file paths and names to strictly comply with Plex standards.
    """
    # Zero-pad season and episode (e.g., 1 -> 01)
    season_pad = str(season).zfill(2)
    episode_pad = str(episode).zfill(2)
    
    # Remove characters that Windows forbids in folder/file names (like :, ?, etc.)
    safe_series_name = sanitize_filename(series_name)
    
    # Determine the base directory from Seer, or fallback to the default drive
    base_dir = get_path_from_seer(series_name) or os.path.join(DEFAULT_DRIVE, safe_series_name)
    target_dir = os.path.join(base_dir, f"Season {season_pad}")
    
    # Create the season folder if it doesn't exist yet
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Plex Naming standard: Series - S01E01 - Title.mkv
    output_template = os.path.join(target_dir, f"{safe_series_name} - S{season_pad}E{episode_pad} - %(title)s.%(ext)s")

    # yt-dlp configuration options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # Grab highest quality streams
        'format_sort': [
            'vcodec:h264',                    # Prioritize H.264 video codec for Plex Direct Play (fixes rewinding/seeking issues)
            'acodec:aac'                      # Prioritize AAC audio codec for maximum compatibility
        ],
        'merge_output_format': 'mkv',         # Merge video/audio into MKV container
        'outtmpl': output_template,           # Set the output path/filename pattern
        'postprocessors': [{
            'key': 'FFmpegMetadata',          # Embed proper timestamps and metadata (crucial for Plex timeline seeking)
            'add_chapters': True              # Adds YouTube chapters to the Plex timeline if available
        }]
    }

    # Execute the download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/dl')
def trigger():
    """
    Flask endpoint triggered by the JavaScript bookmarklet.
    Expects URL query parameters: url, cat (series), s (season), e (episode).
    """
    video_url = request.args.get('url')
    series_name = request.args.get('cat')
    season = request.args.get('s')
    episode = request.args.get('e')
    
    # Validate that all required parameters were provided
    if not all([video_url, series_name, season, episode]):
        return "Missing required parameters.", 400
    
    # Start the download process in a background thread so the browser request finishes immediately
    threading.Thread(target=download_task, args=(video_url, series_name, season, episode)).start()
    
    # Return a quick confirmation to the user
    return f"Processing {series_name} S{str(season).zfill(2)}E{str(episode).zfill(2)}..."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)