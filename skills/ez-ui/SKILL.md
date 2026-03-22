---
name: ez-ui
description: Access the Home Assistant web UI for visual verification, dashboard inspection, and browser-based testing. Use when the user asks to check a dashboard, verify a UI change, or interact with HA visually.
---

# ez-ui — Home Assistant Web UI Access

## Local access

Home Assistant UI is available at:

```
http://<HA_HOST>:8123
```

From inside the ez-ha addon container, use:

```
http://homeassistant:8123
```

The `HA_URL` env var is set automatically inside the addon.

## Authentication

API requests use `HA_TOKEN` (set automatically inside the addon).

For browser-based access, run `browser-login` first to authenticate the browser session:

```bash
browser-login                   # Uses HA_BROWSER_USER / HA_BROWSER_PASS from addon config
browser-login <user> <pass>     # Or pass credentials explicitly
```

The session is persisted in `/data/browser-profile` via `AGENT_BROWSER_PROFILE` env var.

> **Tip:** Create a dedicated HA user without 2FA for the agent.

## Browser testing with agent-browser

```bash
# Take a screenshot of a dashboard
agent-browser screenshot http://homeassistant:8123/lovelace/0 dashboard.png

# Get the accessibility tree (for AI navigation)
agent-browser open http://homeassistant:8123/lovelace/0 && agent-browser snapshot -i

# Click elements, fill forms, etc.
agent-browser click @e5
agent-browser fill @e3 "Living Room"
```

## Key UI paths

| Path | Description |
|------|-------------|
| `/lovelace/` | Default dashboard |
| `/config/` | Settings & configuration panel |
| `/config/automation/` | Automation editor |
| `/config/script/` | Script editor |
| `/config/scene/` | Scene editor |
| `/developer-tools/` | Developer tools (services, states, templates) |
| `/developer-tools/state` | Entity state browser |
| `/developer-tools/service` | Service call tester |
| `/developer-tools/template` | Jinja2 template tester |
| `/history/` | History graphs |
| `/logbook/` | Logbook |
| `/map/` | Map view |
