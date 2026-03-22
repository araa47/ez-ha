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
        zsh \
        curl \
        jq \
        openvpn \
        chromium \
        nss \
        freetype \
        harfbuzz \
        ca-certificates \
        ttf-freefont \
        # Terminal enhancements
        fzf \
        eza \
        zsh-autosuggestions \
        zsh-syntax-highlighting \
    # ttyd static binary
    && ARCH="$(uname -m)" \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${ARCH}" \
    && chmod +x /usr/local/bin/ttyd \
    # Starship prompt (static binary)
    && ARCH="$(uname -m)" \
    && if [ "$ARCH" = "x86_64" ]; then STARSHIP_ARCH="x86_64-unknown-linux-musl"; \
       elif [ "$ARCH" = "aarch64" ]; then STARSHIP_ARCH="aarch64-unknown-linux-musl"; fi \
    && curl -fsSL "https://github.com/starship/starship/releases/latest/download/starship-${STARSHIP_ARCH}.tar.gz" \
       | tar xz -C /usr/local/bin \
    && chmod +x /usr/local/bin/starship \
    # zsh-history-substring-search plugin (not in Alpine repos)
    && mkdir -p /usr/share/zsh/plugins/zsh-history-substring-search \
    && curl -fsSL "https://raw.githubusercontent.com/zsh-users/zsh-history-substring-search/master/zsh-history-substring-search.zsh" \
       -o /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh \
    # Claude Code CLI + Playwright + agent-browser (use Alpine chromium, not Chrome for Testing)
    && npm install -g @anthropic-ai/claude-code playwright agent-browser \
    && npm cache clean --force \
    # Python deps for ha skill — install via pip then remove pip
    && apk add --no-cache --virtual .pip py3-pip \
    && pip3 install --no-cache-dir --no-compile --break-system-packages \
       homeassistant-api python-dotenv typer \
    && apk del .pip \
    # Download skill scripts
    && curl -fsSL \
       "https://raw.githubusercontent.com/araa47/ez-ha/main/skills/ez-ha/scripts/ha.py" \
       -o /usr/local/bin/ha \
    && chmod +x /usr/local/bin/ha \
    && mkdir -p /usr/local/lib/ez-ui \
    && curl -fsSL \
       "https://raw.githubusercontent.com/araa47/ez-ha/main/skills/ez-ui/scripts/browser-login.mjs" \
       -o /usr/local/lib/ez-ui/browser-login.mjs \
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
    /usr/local/bin/vpn-up.sh \
    /usr/local/bin/browser-login

WORKDIR /config
