ARG BUILD_FROM
FROM ${BUILD_FROM}

# Single layer: install all system deps, Node.js, Python, tools, then cleanup
RUN apk add --no-cache \
        nodejs \
        npm \
        python3 \
        py3-pip \
        git \
        tmux \
        openssh-client \
        bash \
        curl \
        jq \
    # Install ttyd static binary
    && ARCH="$(uname -m)" \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${ARCH}" \
    && chmod +x /usr/local/bin/ttyd \
    # Install Claude Code CLI
    && npm install -g @anthropic-ai/claude-code \
    && npm cache clean --force \
    # Install Python deps for ha skill (minimal)
    && pip3 install --no-cache-dir --break-system-packages \
       homeassistant-api python-dotenv typer \
    # Download ha.py skill
    && curl -fsSL \
       "https://raw.githubusercontent.com/araa47/ez-ha/main/skills/ez-ha/scripts/ha.py" \
       -o /usr/local/bin/ha \
    && chmod +x /usr/local/bin/ha \
    # Cleanup
    && rm -rf /tmp/* /root/.cache /root/.npm

# Copy rootfs overlay (init scripts, services, helpers)
COPY rootfs/ /

WORKDIR /config
