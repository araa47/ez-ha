ARG BUILD_FROM
FROM ${BUILD_FROM}

# Single layer: system deps, Node.js, Python, tools, then aggressive cleanup
RUN apk add --no-cache \
        nodejs \
        npm \
        python3 \
        git \
        tmux \
        openssh-client \
        bash \
        curl \
        jq \
        openvpn \
        chromium \
        nss \
        freetype \
        harfbuzz \
        ca-certificates \
        ttf-freefont \
    # ttyd static binary
    && ARCH="$(uname -m)" \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${ARCH}" \
    && chmod +x /usr/local/bin/ttyd \
    # Claude Code CLI + Playwright + agent-browser (use Alpine chromium, not Chrome for Testing)
    && npm install -g @anthropic-ai/claude-code playwright agent-browser \
    && npm cache clean --force \
    # Python deps for ha skill — install via pip then remove pip
    && apk add --no-cache --virtual .pip py3-pip \
    && pip3 install --no-cache-dir --no-compile --break-system-packages \
       homeassistant-api python-dotenv typer \
    && apk del .pip \
    # Download ha.py skill
    && curl -fsSL \
       "https://raw.githubusercontent.com/araa47/ez-ha/main/skills/ez-ha/scripts/ha.py" \
       -o /usr/local/bin/ha \
    && chmod +x /usr/local/bin/ha \
    # Cleanup
    && rm -rf /tmp/* /root/.cache /root/.npm /var/cache/apk/*

# Point Playwright + agent-browser at Alpine's chromium (no glibc Chrome for Testing)
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Copy rootfs overlay (init scripts, services, helpers)
COPY rootfs/ /

# Ensure all scripts are executable
RUN chmod +x \
    /etc/cont-init.d/01-vpn-setup.sh \
    /etc/services.d/openvpn/run \
    /etc/services.d/openvpn/finish \
    /usr/local/bin/vpn-up.sh

WORKDIR /config
