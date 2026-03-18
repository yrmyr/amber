# Используем официальный Python образ
FROM python:3.12-slim

# Установка необходимых системных утилит
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    python3-pip \
    npm \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U "yt-dlp[default]" pycryptodome

# Копируем исходный код
COPY . .

# Создаем папку для загрузок
RUN mkdir -p downloads && chmod 777 downloads

# Запуск приложения через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]