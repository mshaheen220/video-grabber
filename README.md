# Video Grabber (Media Downloader API)

A local Python-based Flask API that triggers video downloads (from YouTube, Dailymotion, Vimeo, etc.) via URL. The script intelligently locates existing media folders across external drives using the Seer (Overseerr/Jellyseerr) API to ensure continuity, and automates Plex-compliant naming and filing.

## Prerequisites
- **Python 3.x**
- **FFmpeg**: Must be installed and added to your system's PATH (required by yt-dlp for merging audio and video).

## Installation

1. **Clone the repository** (or copy to your target machine).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment**:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Before running the API, open `downloader.py` and configure the following variables:
- `SEER_URL`: The URL to your Overseerr/Jellyseerr instance (e.g., `http://localhost:5055/api/v1`).
- `SEER_API_KEY`: Your Seer API Key.
- `DEFAULT_DRIVE`: The fallback drive/path if Seer doesn't have a record of the show (e.g., `H:/TV Shows`).

## Usage

1. **Start the API Server**:
   ```bash
   python downloader.py
   ```
   The server will run on `http://0.0.0.0:5000`.

2. **Create the Bookmarklet**:
   Create a new bookmark in your web browser and paste the following minified JavaScript into the URL field. Replace `YOUR_WINDOWS_IP` with the IP address of the machine running this Python script.

   ```javascript
   javascript:(function(){const series=prompt("Series Name:","Cbeebies Bedtime Stories");if(!series)return;const season=prompt("Season:","1");if(!season)return;const episode=prompt("Episode:","1");if(!episode)return;const serverIp="YOUR_WINDOWS_IP";const params=new URLSearchParams({url:window.location.href,cat:series,s:season,e:episode});window.open(`http://${serverIp}:5000/dl?${params.toString()}`,'downloader','width=400,height=200');})();
   ```

3. **Trigger a Download**:
   - Navigate to a video on YouTube, Dailymotion, Vimeo, etc.
   - Click the bookmarklet.
   - Fill in the prompts (Series, Season, Episode).
   - A small popup will briefly open, triggering the download on your server and automatically formatting it for Plex (e.g., `Show Name - S01E01 - Video Title.mkv`).

## Technologies Used
- **Flask**: Lightweight web server to catch download requests.
- **yt-dlp**: Core downloading engine.
- **Requests**: To query the Seer API for path discovery.