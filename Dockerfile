# Используем конкретную версию Python
FROM python:3.9

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev

# Установка Python-зависимостей
WORKDIR /usr/src/app
COPY req.txt ./
RUN pip install --upgrade pip
RUN pip install -r req.txt


WORKDIR /usr/src/app

COPY req.txt ./

RUN pip install -r req.txt