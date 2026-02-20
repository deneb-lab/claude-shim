FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    jq \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*
