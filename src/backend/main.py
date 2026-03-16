import os
import asyncio
import uuid
import glob
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from typing import List, Optional

app = FastAPI(title="Amber API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь для хранения скачанных файлов
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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
    """Фоновая задача для удаления файла после скачивания."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing file {path}: {e}")

def extract_info(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_video(url: str, format_id: str, output_path: str) -> str:
    """Синхронная функция скачивания. Склеивает видео с аудио для высокого качества."""
    
    # Если это аудио, настраиваем конвертацию в mp3
    if format_id == 'bestaudio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{output_path}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
    else:
        # Для видео просим склеить выбранный видео-поток с лучшим аудио
        ydl_opts = {
            'format': f"{format_id}+bestaudio/best",
            'outtmpl': f"{output_path}.%(ext)s",
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        actual_files = glob.glob(f"{output_path}.*")
        if actual_files:
            return actual_files[0]
        raise Exception("File not found after download")

@app.post("/api/info", response_model=VideoInfo)
async def get_video_info(request: VideoRequest):
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info, request.url)
        
        formats = []
        seen_resolutions = set()
        
        # Собираем видео-форматы разных разрешений
        for f in info.get('formats', []):
            height = f.get('height')
            if not height or f.get('vcodec') == 'none':
                continue
            
            res_str = f"{height}p"
            if res_str not in seen_resolutions:
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': 'mp4', # Мы будем принудительно мержить в mp4
                    'resolution': res_str,
                    'filesize': f.get('filesize'),
                    'quality': f.get('format_note')
                })
                seen_resolutions.add(res_str)

        # Добавляем аудио-формат
        formats.append({
            'format_id': 'bestaudio',
            'ext': 'mp3',
            'resolution': 'Audio Only',
            'filesize': None,
            'quality': 'MP3 192kbps'
        })

        # Сортируем: сначала самое высокое качество
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "amber-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
