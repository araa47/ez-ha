---
name: ez-ha
description: Control Home Assistant — lights, fans, covers, locks, switches, climate, humidifiers, media players, scenes, scripts, automations, weather, buttons, and Assist. Run `ha <domain>` to discover entities and actions.
---

# ha — Home Assistant CLI

## Setup

Set `HA_URL` and `HA_TOKEN` env vars (or `.env` file).

## Usage

1. **Find entities first** — if the user mentions a device/room, run `ha search <name>` or `ha <domain>` to discover real entity IDs before acting.
2. **Act** — `ha <domain> <action> <entity_id> [args]` (e.g. `ha fan speed bedroom 60`, `ha cover open balcony_awning`)
3. **Generic power** — `ha on|off|toggle <entity_id>` works for any entity.
4. **Fuzzy match** — `ha scene|script|button [name]` — omit name to list, provide name to activate (substring match).
5. Add `-v` for verbose JSON output.
