<p align="center">
  <h1 align="center">ez-ha</h1>
  <p align="center">
    <strong>Home Assistant, meet your AI agent.</strong>
  </p>
  <p align="center">
    <a href="#ez-ha--the-skill">Skill</a> &bull;
    <a href="#ez-ha--the-addon">Addon</a> &bull;
    <a href="https://github.com/araa47/ez-ha/issues">Issues</a> &bull;
    <a href="CONTRIBUTING.md">Contributing</a>
  </p>
  <p align="center">
    <a href="https://github.com/araa47/ez-ha/actions"><img src="https://img.shields.io/github/actions/workflow/status/araa47/ez-ha/on-pr.yml?branch=main&style=flat-square" alt="CI"></a>
    <a href="https://github.com/araa47/ez-ha/blob/main/LICENSE"><img src="https://img.shields.io/github/license/araa47/ez-ha?style=flat-square" alt="License"></a>
    <a href="https://github.com/araa47/ez-ha/stargazers"><img src="https://img.shields.io/github/stars/araa47/ez-ha?style=flat-square" alt="Stars"></a>
  </p>
</p>

---

`ez-ha` is two things in one repo:

| | **The Skill** | **The Addon** |
|:--|:--|:--|
| **What** | CLI that lets any AI agent control your HA | Full Claude Code environment running inside HAOS |
| **Where** | Your laptop / server — give agents remote access to your HA | Home Assistant sidebar via web terminal |
| **For** | Adding HA superpowers to Claude Code, Cursor, Codex, etc. from anywhere | Editing configs, debugging, and testing directly in HA |
| **Install** | `npx skills add araa47/ez-ha` | Add repo URL in HA addon store |

---

## ez-ha -- The Skill

> Give any AI agent the ability to talk to Home Assistant -- query entities, call services, check automations, and debug issues.

```bash
npx skills add araa47/ez-ha
```

<details>
<summary><strong>Why ez-ha?</strong></summary>

<br>

Most HA integrations hand agents a flat list of API endpoints and hope for the best. **ez-ha is built for agents from the ground up:**

- **Self-discovering** -- `ha search <room>` returns matching entities *and* the exact commands to control them. No guessing, no hallucinated entity IDs.
- **Two-step workflow** -- discover, then act. `ha fan` lists all fans with actions like `ha fan speed bedroom 60`. The agent always knows what it can do before doing it.
- **Compact output** -- minimal JSON by default, saving tokens. Add `-v` for full detail or `-H` for human-readable tables.
- **Fuzzy matching** -- `ha scene movie` finds `scene.movie_night`. `ha script bassdrive` finds the right script. No exact IDs needed.
- **Every domain** -- lights, fans, covers, locks, switches, climate, humidifiers, media players, scenes, scripts, automations, weather, buttons, and natural language via Assist.

Agents can chain complex multi-step actions (e.g. *"set the bedroom to movie mode: dim lights to 20 %, close the blinds, turn on the AC to 22 C, and play the movie night scene"*) by discovering what's available and composing commands -- no hardcoded knowledge needed.

</details>

### Quick start

```bash
# 1. Discover what's in the bedroom
ha search bedroom
# => {"entities": [...], "actions": {"light": {"on": "ha light on [area]", ...}, "fan": {...}}}

# 2. Act
ha on light.bedroom --brightness 50
ha fan speed fan.bedroom 60
ha cover close cover.bedroom_blinds
```

> **Requires:** a running Home Assistant instance with a long-lived access token.
> Set `HA_URL` and `HA_TOKEN` in your environment (or `.env` file).

---

## ez-ha -- The Addon

> A Home Assistant addon that runs **Claude Code** directly inside HAOS -- full config access, Supervisor API, and a web terminal in your sidebar.

The addon runs as an HA ingress panel — it serves a ttyd web terminal through HA's built-in reverse proxy, so it appears as a sidebar tab in your HA UI. The terminal is a full Linux shell (you can use it for anything), but it's purpose-built for running Claude Code against your HA instance.

### Highlights

| Feature | Details |
|:--------|:--------|
| **Web terminal** | ttyd + tmux in your HA sidebar -- persistent sessions survive page reloads |
| **Claude Code** | Pre-installed -- run `claude` and start asking questions |
| **Config access** | Full read/write to `/config/` -- automations, scripts, scenes, custom components |
| **`ha` CLI** | The same ez-ha skill, auto-configured with your HA credentials |
| **`ha-supervisor`** | Restart HA, validate configs, reload automations, view logs |
| **Browser testing** | Playwright + Chromium pre-installed — `browser-login` authenticates the session |
| **SSH** | Auto-generated key pair, optional direct host access for advanced debugging |
| **`cc` alias** | `claude --dangerously-skip-permissions` for fully autonomous operation |

### Install

1. **Settings** -> **Add-ons** -> **Add-on Store**
2. **...** -> **Repositories** -> paste:
   ```
   https://github.com/araa47/ez-ha
   ```
3. Find **ez-ha Claude Agent** and click **Install**
4. *(Optional)* Set your Anthropic API key in the **Configuration** tab
5. **Start** the addon -> open **Claude Agent** from the sidebar
6. Run `claude` in the terminal

### Configuration

| Option | Description |
|:-------|:------------|
| `anthropic_api_key` | Anthropic API key *(or run `claude auth` in the terminal)* |
| `ha_username` | HA user for browser access *(optional — see below)* |
| `ha_password` | HA password for browser access *(optional — see below)* |
| `ssh_host` | IP / hostname to SSH into the HA host *(optional)* |
| `ssh_port` | SSH port *(default: 22)* |
| `ssh_username` | SSH user *(default: root)* |
| `expressvpn_enabled` | Enable OpenVPN tunnel *(default: false)* |
| `expressvpn_username` | OpenVPN username (e.g. from ExpressVPN manual setup) |
| `expressvpn_password` | OpenVPN password |
| `expressvpn_config` | `.ovpn` filename in `/config/expressvpn/` *(optional — uses first found)* |

### Browser access user

To let the agent interact with the HA web UI (take screenshots, verify dashboards, test UI changes), create a dedicated local user:

1. **Settings** -> **People** -> **Add Person** -> **Allow person to login**
2. Set a username/password (e.g. `claude` / `claude`)
3. **Important:** set the user to **Local access only** — this account never needs internet access
4. **Do not enable 2FA** — the agent logs in headlessly via Playwright
5. Enter the credentials in the addon config (`ha_username` / `ha_password`)

The agent uses `browser-login` to authenticate a headless Chromium session. The session is persisted so it only needs to log in once.

### VPN

The addon has an optional built-in OpenVPN client. This is useful if the agent needs outbound internet access through a VPN (e.g. for API calls, package installs, or web browsing). It works with any provider that supplies `.ovpn` config files — ExpressVPN, NordVPN, Surfshark, etc.

1. Drop your `.ovpn` file into `/config/expressvpn/`
2. Set `expressvpn_enabled: true` and your OpenVPN credentials in the addon config
3. Verify with `curl -s https://ipinfo.io` in the terminal

### What the agent can do

```text
ha search bedroom                     # discover entities
ha light on bedroom --brightness 50   # control devices
ha-supervisor check                   # validate YAML config
ha-supervisor reload automations      # reload without restart
ha-supervisor restart                 # full HA restart
ha-supervisor logs 50                 # tail core logs
browser-login                         # authenticate Playwright session for HA UI
playwright                            # browser automation (Chromium pre-installed)
ssh-ha                                # SSH to host (if configured)
cc                                    # claude --dangerously-skip-permissions
curl -s https://ipinfo.io             # verify VPN country (if enabled)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) for details.
