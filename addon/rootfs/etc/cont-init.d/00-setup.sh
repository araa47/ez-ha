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
# HA environment for the ez-ha skill
# ---------------------------------------------------------------------------
{
    echo "export HA_URL=http://homeassistant:8123"
    echo "export HA_TOKEN=${SUPERVISOR_TOKEN}"
} >> /etc/profile.d/ha-env.sh

# Anthropic API key (from addon options)
api_key=$(bashio::config 'anthropic_api_key' '')
if [ -n "$api_key" ]; then
    echo "export ANTHROPIC_API_KEY=${api_key}" >> /etc/profile.d/ha-env.sh
fi

# Supervisor token for ha-supervisor helper
echo "export SUPERVISOR_TOKEN=${SUPERVISOR_TOKEN}" >> /etc/profile.d/ha-env.sh

chmod +x /etc/profile.d/ha-env.sh

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

    # Convenience alias
    {
        echo "export SSH_HOST=${ssh_host}"
        echo "export SSH_PORT=${ssh_port}"
        echo "export SSH_USER=${ssh_user}"
        echo "alias ssh-ha='ssh -o StrictHostKeyChecking=no -p ${ssh_port} ${ssh_user}@${ssh_host}'"
    } >> /etc/profile.d/ha-env.sh
fi

# ---------------------------------------------------------------------------
# Copy CLAUDE.md into /config if not already there
# ---------------------------------------------------------------------------
if [ ! -f /config/CLAUDE.md ]; then
    cp /root/CLAUDE.md /config/CLAUDE.md
fi

bashio::log.info "ez-ha Claude Agent setup complete"
