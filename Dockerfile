FROM python:3.11

ENV TZ=Europe/Berlin

WORKDIR /app

COPY requirements.txt .

RUN apt-get update -qqy \
    && apt-get install -qqy curl chromium chromium-driver libffi-dev pkg-config libssl-dev \
    libx11-6 libx11-xcb1 libfontconfig1 libfreetype6 libxext6 libxrender1 libxtst6 libnss3 libnspr4 libasound2 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN pip install -r requirements.txt

COPY . .
