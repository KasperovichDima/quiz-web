FROM nginx:latest
# Удаляем из контейнера дефолтный конф файл
RUN rm /etc/nginx/conf.d/default.conf
# Копируем наш конф файл
COPY nginx.conf /etc/nginx/conf.d
