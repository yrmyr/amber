// Автоматически определяем адрес сервера: берем текущий хост (IP или домен) и меняем порт на 8000
const API_URL = `http://${window.location.hostname}:8001/api`;

const urlInput = document.getElementById('url-input');
const fetchBtn = document.getElementById('fetch-btn');
const resultSection = document.getElementById('result-section');
const loader = document.getElementById('loader');
const errorMsg = document.getElementById('error-msg');

const videoThumbnail = document.getElementById('video-thumbnail');
const videoTitle = document.getElementById('video-title');
const videoAuthor = document.getElementById('video-author');
const videoDuration = document.getElementById('video-duration');
const qualitySelect = document.getElementById('quality-select');
const downloadBtn = document.getElementById('download-btn');

let currentVideoUrl = '';

// Функция форматирования времени (секунды -> MM:SS)
function formatDuration(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${min}:${sec < 10 ? '0' : ''}${sec}`;
}

// Получение информации о видео
async function fetchVideoInfo() {
    const url = urlInput.value.trim();
    if (!url) return;

    // Сброс состояния
    errorMsg.classList.add('hidden');
    resultSection.classList.add('hidden');
    loader.classList.remove('hidden');
    currentVideoUrl = url;

    try {
        const response = await fetch(`${API_URL}/info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Не удалось получить информацию');
        }

        const data = await response.json();
        displayResult(data);
    } catch (err) {
        showError(err.message);
    } finally {
        loader.classList.add('hidden');
    }
}

// Отображение данных видео
function displayResult(data) {
    videoThumbnail.src = data.thumbnail;
    videoTitle.textContent = data.title;
    videoAuthor.textContent = data.uploader;
    videoDuration.textContent = formatDuration(data.duration);

    // Заполнение списка форматов
    qualitySelect.innerHTML = '';
    data.formats.forEach(f => {
        const option = document.createElement('option');
        // Передаем format_id (который теперь является высотой, например "1080")
        option.value = f.format_id; 
        
        const size = f.filesize ? `(~${(f.filesize / 1024 / 1024).toFixed(1)} MB)` : '';
        // Показываем разрешение: например "1080p - MP4 (~45 MB)"
        option.textContent = `${f.resolution} - ${f.ext.toUpperCase()} ${size}`;
        qualitySelect.appendChild(option);
    });

    resultSection.classList.remove('hidden');
}

// Скачивание видео
async function downloadVideo() {
    const format_id = qualitySelect.value;
    
    downloadBtn.disabled = true;
    downloadBtn.textContent = 'Подготовка файла...';

    try {
        const response = await fetch(`${API_URL}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentVideoUrl, format_id })
        });

        if (!response.ok) throw new Error('Ошибка при скачивании');

        // Получаем файл как Blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку для скачивания
        const a = document.createElement('a');
        a.href = url;
        // Пытаемся достать имя файла из заголовков или придумываем свое
        a.download = `amber_video_${Date.now()}.mp4`; 
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (err) {
        showError('Ошибка при скачивании: ' + err.message);
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Скачать файл';
    }
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
}

// Event Listeners
fetchBtn.addEventListener('click', fetchVideoInfo);
downloadBtn.addEventListener('click', downloadVideo);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') fetchVideoInfo();
});
