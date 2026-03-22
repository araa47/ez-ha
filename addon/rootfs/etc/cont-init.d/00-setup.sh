#!/usr/bin/with-contenv bashio
# One-time setup: env vars, persistent config, SSH

# ---------------------------------------------------------------------------
# Persist Claude Code config across container restarts
# ---------------------------------------------------------------------------
mkdir -p /data/claude-config
if [ ! -d /root/.claude ]; then
    ln -sf /data/claude-config /root/.claude
fi

# ---------------------------------------------------------------------------
# Build /etc/profile.d/ha-env.sh (overwrite each start — do NOT append)
# ---------------------------------------------------------------------------
cat > /etc/profile.d/ha-env.sh <<ENVEOF
export HA_URL=http://homeassistant:8123
export HA_TOKEN=${SUPERVISOR_TOKEN}
export SUPERVISOR_TOKEN=${SUPERVISOR_TOKEN}
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

    # If user placed a key in /config/.ssh/, use it
    if [ -f /config/.ssh/id_rsa ]; then
        cp /config/.ssh/id_rsa /root/.ssh/id_rsa
        chmod 600 /root/.ssh/id_rsa
    fi
    if [ -f /config/.ssh/id_ed25519 ]; then
        cp /config/.ssh/id_ed25519 /root/.ssh/id_ed25519
        chmod 600 /root/.ssh/id_ed25519
    fi

    cat >> /etc/profile.d/ha-env.sh <<SSHEOF
export SSH_HOST=${ssh_host}
export SSH_PORT=${ssh_port}
export SSH_USER=${ssh_user}
alias ssh-ha='ssh -o StrictHostKeyChecking=no -p ${ssh_port} ${ssh_user}@${ssh_host}'
SSHEOF
fi

chmod +x /etc/profile.d/ha-env.sh

# ---------------------------------------------------------------------------
# Copy CLAUDE.md into /config if not already there
# ---------------------------------------------------------------------------
if [ ! -f /config/CLAUDE.md ]; then
    cp /root/CLAUDE.md /config/CLAUDE.md
fi

bashio::log.info "ez-ha Claude Agent setup complete"
