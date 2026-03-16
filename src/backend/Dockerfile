# Используем официальный Python образ
FROM python:3.12-slim

# Установка необходимых системных утилит (ffmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY main.py .

# Создаем папку для загрузок
RUN mkdir -p downloads && chmod 777 downloads

# Запуск приложения через uvicorn
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]
