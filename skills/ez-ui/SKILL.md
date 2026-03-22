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

API requests use the `HA_TOKEN` (long-lived access token). For browser-based access, you may need to log in via the UI or use an auth token in the URL:

```
http://homeassistant:8123/auth/authorize?response_type=code&client_id=http://homeassistant:8123
```

## Browser testing with Playwright

If Playwright + Chromium are installed (run `install-browser` inside the addon):

```bash
# Take a screenshot of a dashboard
npx playwright screenshot http://homeassistant:8123/lovelace/default_view screenshot.png

# Or use the agent-browser skill for interactive browser automation
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
