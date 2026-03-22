---
name: ez-ha
description: Control Home Assistant — lights, fans, covers, locks, switches, climate, humidifiers, media players, scenes, scripts, automations, weather, buttons, and Assist. Compact output by default (use -v for full JSON).
---

# ha — Home Assistant Skill

## Convention

- **singular = action** → `ha light on bedroom`, `ha cover open curtains`, `ha media play radio`
- **plural = list** → `ha lights`, `ha covers`, `ha players`
- **generic = any domain** → `ha on <entity_id>`, `ha off <entity_id>`, `ha toggle <entity_id>`

## Setup

Env vars `HA_URL` and `HA_TOKEN` must be set (or in `.env`):

```env
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your-long-lived-access-token
```

### Alias (recommended)

Add to shell profile so the LLM can just run `ha`:

```bash
alias ha='uv run ~/.openclaw/skills/ha/scripts/ha.py'
```

## Output

**Compact by default** — minimal JSON, fewest tokens. Add `-v` for full verbose JSON when you need all attributes.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `ha info` | Connection + version check |
| `ha state light.hall` | Get entity state |
| `ha search kitchen` | Find entities by id/name |
| `ha entities --domain light --ids-only` | List all light entity IDs |

### Control single entity

| Command | What it does |
|---------|-------------|
| `ha on light.hall` | Turn on |
| `ha on light.hall --brightness 200` | Turn on at brightness (0-255) |
| `ha off light.hall` | Turn off |
| `ha toggle fan.upstairs` | Toggle on/off |

### Bulk lights (by area or all)

| Command | What it does |
|---------|-------------|
| `ha lights` | List all lights with state |
| `ha lights bedroom` | List bedroom lights only |
| `ha light on` | Turn on ALL lights |
| `ha light on bedroom` | Turn on bedroom lights |
| `ha light off` | Turn off ALL lights |
| `ha light off balcony` | Turn off balcony lights |

Areas: `bedroom`, `hall`, `kitchen`, `toilet`, `balcony`, `desk`, `upstairs` (or any substring match).

### Climate / AC

| Command | What it does |
|---------|-------------|
| `ha climate climate.bedroomac --temperature 24 --hvac-mode cool` | Set AC to 24C cool |
| `ha climate climate.bedroomac --hvac-mode off` | Turn AC off |

### Media players

| Command | What it does |
|---------|-------------|
| `ha players` | List all media players + state/volume |
| `ha media play media_player.toilettes_2` | Play |
| `ha media pause media_player.toilettes_2` | Pause |
| `ha media stop toilettes_2` | Stop (auto-prefixes `media_player.`) |
| `ha media next toilettes_2` | Next track |
| `ha media prev toilettes_2` | Previous track |
| `ha volume toilettes_2 40` | Set volume to 40% (0-100) |

### Scenes, scripts, automations (fuzzy match)

| Command | What it does |
|---------|-------------|
| `ha scene movie_night` | Activate scene (exact match) |
| `ha scene movie` | Activate scene (fuzzy — finds `scene.movie_night`) |
| `ha script play_radio_bassdrive` | Run script (exact match) |
| `ha script bassdrive` | Run script (fuzzy — finds matching script) |
| `ha automation trigger motion_lights` | Trigger automation |

Fuzzy matching: if the name isn't an exact `domain.id`, it searches all entities in that domain by substring. If exactly one matches, it runs it. If multiple match, it returns the list so you can pick.

### Natural language (Assist API)

| Command | What it does |
|---------|-------------|
| `ha assist "turn on the desk light"` | Voice-style command via HA Assist |

### Covers (blinds, awnings, garage doors)

| Command | What it does |
|---------|-------------|
| `ha covers` | List all covers with state/position |
| `ha covers balcony` | List covers in area |
| `ha cover open balcony_awning` | Open cover |
| `ha cover close balcony_awning` | Close cover |
| `ha cover stop balcony_awning` | Stop cover movement |
| `ha cover position balcony_awning 50` | Set position (0=closed, 100=open) |

### Locks

| Command | What it does |
|---------|-------------|
| `ha locks` | List all locks with state |
| `ha lock lock front_door` | Lock |
| `ha lock unlock front_door` | Unlock |

### Switches

| Command | What it does |
|---------|-------------|
| `ha switches` | List all switches |
| `ha switches bedroom` | List switches in area |

Use `ha on`/`ha off`/`ha toggle` to control individual switches (e.g. `ha toggle switch.bedroom_plug`).

### Fans

| Command | What it does |
|---------|-------------|
| `ha fans` | List all fans with state/speed/preset |
| `ha fan speed upstairs 60` | Set fan speed (0-100) |
| `ha fan preset upstairs Normal` | Set fan preset mode |
| `ha fan oscillate upstairs on` | Toggle oscillation (on/off) |

Use `ha on`/`ha off`/`ha toggle` to turn fans on/off.

### Humidifiers / dehumidifiers

| Command | What it does |
|---------|-------------|
| `ha humidifiers` | List all humidifiers with state/humidity/mode |
| `ha humidifier dehumidifier --humidity 50` | Set target humidity |
| `ha humidifier dehumidifier --mode SMART` | Set mode (SMART, FAST, CILENT, IONIZER, ...) |
| `ha on humidifier.dehumidifier` | Turn on |
| `ha off humidifier.dehumidifier` | Turn off |

### Buttons

| Command | What it does |
|---------|-------------|
| `ha button u7_pro_xg_restart` | Press a button entity |

### Weather

| Command | What it does |
|---------|-------------|
| `ha weather` | Current weather (default: weather.forecast_home) |
| `ha weather shau_kei_wan` | Weather for specific entity |

### Inspection / debugging

| Command | What it does |
|---------|-------------|
| `ha areas` | List all HA areas with id and name |
| `ha snapshot` | Current state of lights, climate, media, fans, covers, locks |
| `ha snapshot --domains light,switch` | Snapshot specific domains only |
| `ha history light.hall` | Last 10 state changes (24h window) |
| `ha history light.hall -n 20 --hours 48` | Last 20 changes in 48h window |

### Raw service call

| Command | What it does |
|---------|-------------|
| `ha call light turn_on --json '{"entity_id":"light.desk","brightness":200}'` | Any HA service |

## Flags

| Flag | Effect |
|------|--------|
| `-v` / `--verbose` | Full JSON with all attributes (default is compact) |
