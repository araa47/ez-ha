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
| `ha_username` | HA user for browser access (optional — for dashboard screenshots/testing) |
| `ha_password` | HA password for browser access (optional) |
| `ssh_host` | IP/hostname to SSH into (optional — for direct host access) |
| `ssh_port` | SSH port (default: 22) |
| `ssh_username` | SSH user (default: root) |

## SSH setup (optional)

To give Claude SSH access to the HA host:

1. Install the **SSH & Web Terminal** addon (or enable SSH on your host)
2. Set `ssh_host` in this addon's configuration to your HA host IP
3. Restart this addon — an SSH key pair is auto-generated at `/config/.ssh/id_ed25519`
4. Copy the public key into the SSH addon's authorized keys:
   - Open the **SSH & Web Terminal** addon configuration
   - Paste the contents of `/config/.ssh/id_ed25519.pub` into the `authorized_keys` list
   - Restart the SSH addon
5. The `ssh-ha` alias will now be available in the terminal

> **Note:** The generated key is persisted in `/config/.ssh/` so it survives addon restarts. You can also place your own key there instead.

## ExpressVPN (optional)

Route all addon traffic through ExpressVPN so Claude API calls originate from another country.

### Setup

1. Go to [ExpressVPN Manual Config](https://www.expressvpn.com/setup#manual) and sign in
2. Select **OpenVPN** — copy your **username** and **password** (these are *not* your account credentials)
3. Download the `.ovpn` file for your desired server location
4. Place the `.ovpn` file in `/config/expressvpn/` on your HA instance (create the folder if needed)
5. In the addon **Configuration** tab, set:

| Option | Description |
|--------|-------------|
| `expressvpn_enabled` | Set to `true` to enable VPN |
| `expressvpn_username` | OpenVPN username from step 2 |
| `expressvpn_password` | OpenVPN password from step 2 |
| `expressvpn_config` | *(optional)* Filename of the `.ovpn` file (e.g. `my_expressvpn_usa.ovpn`). If omitted, the first `.ovpn` file found is used |

6. Restart the addon

### Verify

Inside the terminal, run:

```bash
curl -s https://ipinfo.io
```

You should see the VPN server's IP and country.

## Browser testing

Chromium and `agent-browser` are pre-installed. Claude can open your HA dashboard in a headless browser, take screenshots, and verify changes visually.

### Browser login

The HA frontend requires authentication. To let the agent access dashboards:

1. **Recommended:** Create a dedicated HA user for the agent (Settings > People > Add Person) **without 2FA**
2. Set `ha_username` and `ha_password` in this addon's Configuration tab
3. Restart the addon
4. Run `browser-login` in the terminal (or the agent can run it automatically)

The browser session is persisted in `/data/browser-profile` and survives addon restarts.

> **Note:** If the HA user has 2FA enabled, `browser-login` cannot complete the login flow automatically. Create a separate user without 2FA for the agent.

## `cc` alias

The `cc` command runs `claude --dangerously-skip-permissions` — useful for fully autonomous operation without permission prompts.
