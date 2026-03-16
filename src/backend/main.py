import os
import asyncio
import uuid
import glob
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from typing import List, Optional

# Настройка логирования для Docker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amber")

app = FastAPI(title="Amber API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ПРОВЕРКА КУКОВ ПРИ ЗАПУСКЕ
COOKIES_PATH = os.path.join(os.path.dirname(__file__), "cookies.txt")
if os.path.exists(COOKIES_PATH):
    logger.info(f"✅ COOKIES FOUND: {COOKIES_PATH}")
else:
    logger.warning(f"❌ NO COOKIES FOUND AT: {COOKIES_PATH}")

class VideoRequest(BaseModel):
    url: str
    format_id: Optional[str] = "best"

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    quality: Optional[str] = None

class VideoInfo(BaseModel):
    id: str
    title: str
    thumbnail: str
    duration: int
    uploader: str
    formats: List[VideoFormat]

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Error removing file {path}: {e}")

def get_ydl_opts(custom_opts=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # ВКЛЮЧАЕМ ВСЕ ВОЗМОЖНЫЕ ПОТОКИ
        'youtube_include_dash_manifest': True,
        'youtube_include_hls_manifest': True,
        'check_formats': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web', 'android', 'tv'],
                'player_skip': [],
            }
        },
    }
    if os.path.exists(COOKIES_PATH):
        opts['cookiefile'] = COOKIES_PATH
    if custom_opts:
        opts.update(custom_opts)
    return opts

def extract_info(url: str) -> dict:
    with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
        return ydl.extract_info(url, download=False)

def download_video(url: str, format_val: str, output_path: str) -> str:
    if format_val.isdigit():
        height = format_val
        ydl_format = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        ydl_opts = get_ydl_opts({
            'format': ydl_format,
            'outtmpl': f"{output_path}.%(ext)s",
            'merge_output_format': 'mp4',
        })
    elif format_val == 'bestaudio':
        ydl_opts = get_ydl_opts({
            'format': 'bestaudio/best',
            'outtmpl': f"{output_path}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts = get_ydl_opts({
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f"{output_path}.%(ext)s",
            'merge_output_format': 'mp4',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        actual_files = glob.glob(f"{output_path}.*")
        if actual_files:
            return actual_files[0]
        raise Exception("File not found after download")

@app.post("/api/info", response_model=VideoInfo)
async def get_video_info(request: VideoRequest):
    try:
        logger.info(f"Fetching info for: {request.url}")
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info, request.url)
        
        formats = []
        seen_heights = set()
        
        for f in info.get('formats', []):
            h = f.get('height')
            if not h or f.get('vcodec') == 'none':
                continue
            
            if h not in seen_heights:
                formats.append({
                    'format_id': str(h),
                    'ext': 'mp4',
                    'resolution': f"{h}p",
                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                    'quality': f.get('format_note') or f"{h}p"
                })
                seen_heights.add(h)

        formats.append({
            'format_id': 'bestaudio',
            'ext': 'mp3',
            'resolution': 'Audio Only',
            'filesize': None,
            'quality': 'MP3 192kbps'
        })

        formats.sort(key=lambda x: int(x['resolution'].split('p')[0]) if 'p' in x['resolution'] else 0, reverse=True)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "formats": formats
        }
    except Exception as e:
        logger.error(f"Error fetching info: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def start_download(request: VideoRequest, background_tasks: BackgroundTasks):
    try:
        file_uuid = str(uuid.uuid4())
        output_base = os.path.join(DOWNLOAD_DIR, file_uuid)
        
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None, download_video, request.url, request.format_id, output_base
        )
        
        background_tasks.add_task(remove_file, file_path)
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "amber-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
