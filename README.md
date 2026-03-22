<p align="center">
  <h1 align="center">ez-ha</h1>
  <p align="center">
    <strong>Home Assistant, meet your AI agent.</strong>
  </p>
  <p align="center">
    <a href="#ez-ha--the-skill">Skill</a> &bull;
    <a href="#ez-ha--the-addon-beta">Addon</a> &bull;
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
| **Where** | Your laptop / server, alongside your agent | Home Assistant sidebar via web terminal |
| **For** | Adding HA superpowers to Claude Code, Cursor, Codex, etc. | Editing configs, debugging, and testing directly in HA |
| **Install** | `npx skills add araa47/ez-ha` | Add repo URL in HA addon store |
| **Status** | Stable | **BETA** |

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

## ez-ha -- The Addon *(BETA)*

> A Home Assistant addon that runs **Claude Code** directly inside HAOS -- full config access, Supervisor API, and a web terminal in your sidebar.

> [!WARNING]
> This addon is under active development. Expect rough edges. [Report issues here.](https://github.com/araa47/ez-ha/issues)

### Highlights

| Feature | Details |
|:--------|:--------|
| **Web terminal** | ttyd + tmux in your HA sidebar -- persistent sessions survive page reloads |
| **Claude Code** | Pre-installed -- run `claude` and start asking questions |
| **Config access** | Full read/write to `/config/` -- automations, scripts, scenes, custom components |
| **`ha` CLI** | The same ez-ha skill, auto-configured with your HA credentials |
| **`ha-supervisor`** | Restart HA, validate configs, reload automations, view logs |
| **Browser testing** | agent-browser + Chrome for Testing pre-installed |
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
| `ssh_host` | IP / hostname to SSH into the HA host *(optional)* |
| `ssh_port` | SSH port *(default: 22)* |
| `ssh_username` | SSH user *(default: root)* |
| `expressvpn_enabled` | Enable ExpressVPN tunnel *(default: false)* |
| `expressvpn_username` | OpenVPN username from ExpressVPN manual setup |
| `expressvpn_password` | OpenVPN password from ExpressVPN manual setup |
| `expressvpn_config` | `.ovpn` filename in `/config/expressvpn/` *(optional — uses first found)* |

### What the agent can do

```text
ha search bedroom                     # discover entities
ha light on bedroom --brightness 50   # control devices
ha-supervisor check                   # validate YAML config
ha-supervisor reload automations      # reload without restart
ha-supervisor restart                 # full HA restart
ha-supervisor logs 50                 # tail core logs
agent-browser                         # browser automation (Chrome pre-installed)
ssh-ha                                # SSH to host (if configured)
cc                                    # claude --dangerously-skip-permissions
curl -s https://ipinfo.io             # verify VPN country (if enabled)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) for details.
