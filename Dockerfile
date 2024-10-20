FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbullseye

ENV TITLE=mt
ENV WINEPREFIX="/config/.wine"

# Update package lists and upgrade packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y dos2unix

# Copy the metatrader directory and convert start.sh to Unix format
COPY metatrader /metatrader
RUN dos2unix /metatrader/start.sh

# Install required packages including PyXDG
RUN apt-get install -y \
    python3-pip \
    wget \
    python3-pyxdg \
    && pip3 install --upgrade pip

# Add WineHQ repository key and APT source
RUN wget -q https://dl.winehq.org/wine-builds/winehq.key \
    && apt-key add winehq.key \
    && add-apt-repository 'deb https://dl.winehq.org/wine-builds/debian/ bullseye main' \
    && rm winehq.key

# Add i386 architecture and update package lists
RUN dpkg --add-architecture i386 \
    && apt-get update

# Install WineHQ stable package and dependencies
RUN apt-get install --install-recommends -y \
    winehq-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY /root /
RUN chmod +x /metatrader/start.sh

EXPOSE 3000 8001
VOLUME /config
