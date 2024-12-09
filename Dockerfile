# Задаём базовый образ
FROM tiangolo/uwsgi-nginx-flask:latest
# Копируем содержимое папки ./app в рабочую директорию контейнера
COPY ./app ./
# Копируем файл requirements.txt в рабочую директорию контейнера
COPY ./requirements.txt ./
# Копируем файл uwsgi.ini в рабочую директорию контейнера
COPY ./uwsgi.ini ./

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && apt-get clean

# Запускаем установку необходимых зависимостей
RUN pip install -r requirements.txt