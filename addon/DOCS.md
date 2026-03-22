# ez-ha Claude Agent

Run an AI coding agent inside Home Assistant — edit configs, debug automations, and control devices from a web terminal.

## How it works

This addon runs a web terminal (via ttyd + tmux) accessible from your HA sidebar. Inside, you launch **Claude Code** which has:

- **Direct access to your HA config files** — edit `automations.yaml`, `scripts.yaml`, `configuration.yaml`, etc.
- **`ha` CLI** — query and control entities (lights, fans, covers, climate, scenes, etc.)
- **`ha-supervisor` helper** — restart HA, validate configs, reload automations, view logs
- **SSH access** (optional) — connect to the HA host if configured
- **Persistent sessions** — tmux keeps your session alive when you navigate away

## First-time setup

1. Start the addon and open it from the sidebar
2. In the terminal, run `claude` to start Claude Code
3. Authenticate with your Anthropic API key (or set it in addon Configuration)
4. Start asking Claude to help with your Home Assistant setup

## Configuration

| Option | Description |
|--------|-------------|
| `anthropic_api_key` | Your Anthropic API key (optional — you can also auth inside the terminal) |
| `ssh_host` | IP/hostname to SSH into (optional — for direct host access) |
| `ssh_port` | SSH port (default: 22) |
| `ssh_username` | SSH user (default: root) |

## SSH setup (optional)

To give Claude SSH access to the HA host:

1. Install the **SSH & Web Terminal** addon (or enable SSH on your host)
2. Place your SSH key at `/config/.ssh/id_ed25519` (or `id_rsa`)
3. Set `ssh_host` in this addon's configuration to your HA host IP
4. Restart this addon — the `ssh-ha` alias will be available in the terminal

## Browser testing (optional)

For users with more resources (8GB+ RAM), you can install Playwright inside the container:

```bash
apk add chromium
npm install -g playwright
npx playwright install chromium
```

This lets Claude open your HA dashboard in a headless browser and verify changes visually.
