# 💎 Project Amber: YT-DLP Web Downloader

**Amber** — это современный, минималистичный веб-сервис для скачивания медиа-контента с различных платформ (YouTube, TikTok, Twitter и др.), вдохновленный дизайном `cobalt.tools`.

> [!info] Ключевая особенность
> В отличие от многих онлайн-сервисов, Amber поддерживает скачивание видео в высоком качестве (1080p, 2K, 4K) путем автоматической склейки видео и аудио потоков на стороне сервера через FFmpeg.

## ✨ Особенности

- 🌌 **Glassmorphism UI**: Эстетичный темный интерфейс с неоновыми акцентами и размытием.
- 🎬 **High Quality Support**: Поддержка всех доступных разрешений (от 144p до 4K).
- 📦 **Docker Ready**: Возможность развернуть проект одной командой.
- 🧹 **Auto-Cleanup**: Автоматическое удаление временных файлов после скачивания.

## 🛠 Технологический стек

- **Core**: `yt-dlp` + `FFmpeg`
- **Backend**: `Python 3.12`, `FastAPI`
- **Frontend**: `Vanilla HTML5`, `CSS3`, `JavaScript (ES6)`, `Nginx`
- **Deployment**: `Docker`, `Docker Compose`

## 🐳 Запуск через Docker (Рекомендуется)

Это самый простой способ запустить проект со всеми зависимостями.

### 1. Установка Docker
Убедитесь, что у вас установлены `docker` и `docker-compose`.

### 2. Запуск проекта
Перейдите в корневую папку проекта и выполните:
```bash
docker-compose up --build -d
```
*   **Интерфейс** будет доступен по адресу: `http://localhost:3000`
*   **API** будет работать по адресу: `http://localhost:8000`

### 3. Остановка проекта
```bash
docker-compose down
```

## 🚀 Ручной запуск (без Docker)

### 1. Запуск Бэкенда (API)
Перейдите в папку бэкенда и запустите сервер:
```bash
cd src/backend
./venv/bin/python main.py
```
*API будет доступно по адресу: `http://localhost:8000`*

### 2. Запуск Фронтенда (UI)
```bash
cd src/frontend
python3 -m http.server 3000
```
*Интерфейс будет доступен по адресу: `http://localhost:3000`*

## 📁 Структура проекта

```text
amber/
├── docker-compose.yml   # Конфигурация запуска Docker
└── src/
    ├── backend/         # FastAPI API
    │   ├── Dockerfile   # Образ бэкенда с FFmpeg
    │   └── main.py      # Код сервера
    └── frontend/        # Веб-интерфейс
        ├── Dockerfile   # Образ фронтенда с Nginx
        └── index.html   # Разметка
```

---
*Проект разработан в рамках базы знаний Obsidian.*
