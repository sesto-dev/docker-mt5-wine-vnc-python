# Stage 1: Base image with apt packages
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbullseye AS base

ENV TITLE=MetaTrader
ENV WINEARCH=win64
ENV WINEPREFIX="/config/.wine"
ENV WINEDEBUG=-all,err-toolbar,fixme-all
ENV DISPLAY=:0
ENV metatrader_version=5.0.36

# Copy scripts
COPY scripts /scripts
RUN chmod +x /scripts/*.sh

# Setup environment
RUN /scripts/01-setup-environment.sh

# Stage 2: Final image
FROM base

# Copy application files
COPY app /app
COPY /root /

# Setup Wine
RUN /scripts/02-setup-wine.sh

# Setup logging
RUN touch /var/log/mt5_setup.log && \
    chown abc:abc /var/log/mt5_setup.log && \
    chmod 644 /var/log/mt5_setup.log

EXPOSE 3000 5000 8001 18812
VOLUME /config

# Set the entrypoint to run as the abc user
ENTRYPOINT ["/bin/bash", "-c", "su abc -c '/scripts/03-entrypoint.sh'"]