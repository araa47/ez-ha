# ez-ha Claude Agent — Home Assistant Addon

You are running inside a Home Assistant addon container with full access to the HA config and APIs.

## Available Tools

### `ha` — Home Assistant CLI (ez-ha skill)
Query and control entities. Run `ha --help` for all commands.
```bash
ha search bedroom          # Find entities in a room
ha light on bedroom        # Turn on lights
ha fan speed bedroom 60    # Set fan speed
ha scene movie             # Activate a scene
ha automation              # List automations
```
Environment is pre-configured: `HA_URL` and `HA_TOKEN` are set automatically.

### `ha-supervisor` — Supervisor API helper
Manage HA core via the Supervisor API.
```bash
ha-supervisor check            # Validate config
ha-supervisor restart          # Restart HA core
ha-supervisor logs 50          # Last 50 lines of HA logs
ha-supervisor reload automations  # Reload automations
ha-supervisor reload scripts      # Reload scripts
ha-supervisor info             # HA version & info
ha-supervisor addons           # List installed addons
ha-supervisor host-info        # Host system info
```

### SSH (if configured)
If the user set up SSH in addon options, connect with:
```bash
ssh-ha        # Alias for SSH to HA host
```

### Browser Testing (optional — requires `install-browser` first)
Playwright is pre-installed but the browser binary is not (to save space).
To enable browser testing, run `install-browser` in the terminal (needs ~400MB disk, 8GB+ RAM recommended).
Once installed, you can open HA dashboards and verify changes visually.

## File Locations

- `/config/configuration.yaml` — Main HA config
- `/config/automations.yaml` — Automations
- `/config/scripts.yaml` — Scripts
- `/config/scenes.yaml` — Scenes
- `/config/customize.yaml` — Entity customizations
- `/config/secrets.yaml` — Secrets (do not expose values)
- `/config/custom_components/` — Custom integrations
- `/config/.storage/` — HA internal storage (read-only recommended)

## Workflow

1. **Read before editing** — always read the current file before making changes
2. **Validate after editing** — run `ha-supervisor check` after modifying YAML configs
3. **Reload when possible** — use `ha-supervisor reload automations` instead of full restart
4. **Full restart only when needed** — `ha-supervisor restart` for config changes that require it

## Important Notes

- The `/config` directory is the live HA configuration — edits take effect after reload/restart
- Always back up before large changes: `cp /config/automations.yaml /config/automations.yaml.bak`
- YAML indentation matters — use 2 spaces, no tabs
- Do NOT expose values from `secrets.yaml` to the user
