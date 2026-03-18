# Используем легкий Nginx на базе Alpine
FROM nginx:alpine

# Копируем все статические файлы в директорию nginx
COPY . /usr/share/nginx/html

# По умолчанию nginx работает на 80 порту
EXPOSE 80

# Nginx запустится автоматически
CMD ["nginx", "-g", "daemon off;"]
