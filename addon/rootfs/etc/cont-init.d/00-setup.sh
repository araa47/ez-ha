#!/usr/bin/with-contenv bashio
# One-time setup: env vars, persistent config, SSH

# ---------------------------------------------------------------------------
# Persist Claude Code config (auth, settings) across container restarts
# ---------------------------------------------------------------------------
mkdir -p /data/claude-config
# If .claude exists as a real dir (not symlink), migrate contents to persistent storage
if [ -d /root/.claude ] && [ ! -L /root/.claude ]; then
    cp -a /root/.claude/. /data/claude-config/ 2>/dev/null || true
fi
# Always (re)create the symlink — handles fresh containers and stale symlinks
rm -rf /root/.claude
ln -sf /data/claude-config /root/.claude

# ---------------------------------------------------------------------------
# Build /etc/profile.d/ha-env.sh (overwrite each start — do NOT append)
# ---------------------------------------------------------------------------
cat > /etc/profile.d/ha-env.sh <<ENVEOF
export HA_URL=http://homeassistant:8123
export HA_TOKEN=${SUPERVISOR_TOKEN}
export SUPERVISOR_TOKEN=${SUPERVISOR_TOKEN}
export IS_SANDBOX=1
ENVEOF

# Anthropic API key (from addon options)
api_key=$(bashio::config 'anthropic_api_key' '')
if [ -n "$api_key" ]; then
    echo "export ANTHROPIC_API_KEY=${api_key}" >> /etc/profile.d/ha-env.sh
fi

# ---------------------------------------------------------------------------
# SSH setup (optional — only if user configured ssh_host)
# ---------------------------------------------------------------------------
ssh_host=$(bashio::config 'ssh_host' '')
if [ -n "$ssh_host" ]; then
    ssh_port=$(bashio::config 'ssh_port' '22')
    ssh_user=$(bashio::config 'ssh_username' 'root')

    mkdir -p /root/.ssh
    chmod 700 /root/.ssh

    # Generate SSH key pair if none exists (persisted in /config/.ssh/)
    mkdir -p /config/.ssh
    if [ ! -f /config/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -f /config/.ssh/id_ed25519 -N "" -C "ez-ha-addon"
        bashio::log.info "Generated SSH key pair. Add this public key to your SSH addon's authorized_keys:"
        bashio::log.info "$(cat /config/.ssh/id_ed25519.pub)"
    fi

    # Copy key into container
    cp /config/.ssh/id_ed25519 /root/.ssh/id_ed25519
    chmod 600 /root/.ssh/id_ed25519
    if [ -f /config/.ssh/id_ed25519.pub ]; then
        cp /config/.ssh/id_ed25519.pub /root/.ssh/id_ed25519.pub
    fi

    # Also support user-provided RSA key
    if [ -f /config/.ssh/id_rsa ]; then
        cp /config/.ssh/id_rsa /root/.ssh/id_rsa
        chmod 600 /root/.ssh/id_rsa
    fi

    cat >> /etc/profile.d/ha-env.sh <<SSHEOF
export HA_SSH_HOST=${ssh_host}
export HA_SSH_PORT=${ssh_port}
export HA_SSH_USER=${ssh_user}
alias ssh-ha='ssh -o StrictHostKeyChecking=no -p ${ssh_port} ${ssh_user}@${ssh_host}'
SSHEOF
fi

# cc alias — claude with no permission prompts
echo "alias cc='claude --dangerously-skip-permissions'" >> /etc/profile.d/ha-env.sh

chmod +x /etc/profile.d/ha-env.sh

# ---------------------------------------------------------------------------
# Copy CLAUDE.md into /config if not already there
# ---------------------------------------------------------------------------
if [ ! -f /config/CLAUDE.md ]; then
    cp /root/CLAUDE.md /config/CLAUDE.md
fi

bashio::log.info "ez-ha Claude Agent setup complete"
