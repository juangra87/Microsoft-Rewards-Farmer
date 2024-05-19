FROM python:3.11-slim

ENV TZ=Europe/Berlin

WORKDIR /app

COPY requirements.txt .

RUN apt-get update -qqy \
    && apt-get install -qqy curl libffi-dev pkg-config libssl-dev \
    libx11-6 libx11-xcb1 libfontconfig1 libfreetype6 libxext6 libxrender1 libxtst6 libnss3 libnspr4 libasound2 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Install Chrome browser
RUN wget --no-verbose -O /usr/src/google-chrome-stable_current_amd64.deb "http://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
  dpkg -i /usr/src/google-chrome-stable_current_amd64.deb ; \
  apt-get install -f -y && \
  rm -f /usr/src/google-chrome-stable_current_amd64.deb

RUN pip install -r requirements.txt

COPY . .
