---
name: ez-ssh
description: SSH into a Home Assistant host and access config files, logs, and system commands. Use when the user asks to connect to HA over SSH, inspect host-level files, or debug the underlying OS.
---

# ez-ssh — SSH to Home Assistant

## Setup

Requires SSH access to the HA host. Set these env vars (or `.env` file):

| Var | Description |
|-----|-------------|
| `HA_SSH_HOST` | IP or hostname of the HA machine |
| `HA_SSH_PORT` | SSH port (default: `22`) |
| `HA_SSH_USER` | SSH user (default: `root`) |

An SSH key must be available (e.g. `~/.ssh/id_ed25519` or `~/.ssh/id_rsa`).

## Quick connect

```bash
ssh -o StrictHostKeyChecking=no -p ${HA_SSH_PORT:-22} ${HA_SSH_USER:-root}@${HA_SSH_HOST}
```

Inside the ez-ha addon the alias `ssh-ha` does this automatically.

## Common HA host paths

| Path | Description |
|------|-------------|
| `/root/config/` or `/config/` | Main HA config directory (automations.yaml, scripts.yaml, etc.) |
| `/root/config/custom_components/` | HACS / custom integrations |
| `/root/config/.storage/` | HA internal storage (entity registry, device registry) |
| `/root/config/secrets.yaml` | Secrets — never expose values |
| `/mnt/data/supervisor/` | Supervisor data (addon configs, backups) |
| `/mnt/data/supervisor/addons/local/` | Local addon source |

## Useful host commands

```bash
ha core restart          # Restart HA core
ha core logs             # Tail HA core logs
ha host info             # Host OS info
ha network info          # Network config
ha addons list           # List installed addons
journalctl -f            # Follow system journal
docker ps                # Running containers (HAOS uses Docker)
```

## Tips

- Always read a file before editing it.
- Back up before making large changes: `cp file file.bak`
- After editing YAML configs, validate before restarting.
- Do NOT expose values from `secrets.yaml`.
