#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "HomeAssistant-API>=5.0.3",
#   "python-dotenv>=1.0.1",
#   "typer>=0.12.0",
# ]
# ///
"""Home Assistant CLI — agent-friendly, compact by default.

Run `ha --help` for all commands, `ha <domain>` to discover entities and actions.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv
from homeassistant_api import Client as HAClient

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = typer.Typer(
    help="Home Assistant CLI — compact JSON output. Run 'ha <domain>' to list entities and actions.",
    add_completion=False,
    no_args_is_help=True,
)


class _State:
    verbose: bool = False
    human: bool = False


_st = _State()


@app.callback()
def _callback(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Full JSON output"),
    human: bool = typer.Option(
        False, "-H", "--human", help="Pretty human-readable output"
    ),
) -> None:
    _st.verbose = verbose
    _st.human = human


# ---------------------------------------------------------------------------
# Config / helpers
# ---------------------------------------------------------------------------

CONFIG_PATHS = [
    Path.cwd() / ".ha.json",
    Path.home() / ".config" / "home-assistant" / "config.json",
]


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_config() -> tuple[str, str]:
    load_dotenv()
    url = os.getenv("HA_URL", "").strip()
    token = os.getenv("HA_TOKEN", "").strip()
    if url and token:
        return url.rstrip("/"), token
    for path in CONFIG_PATHS:
        if not path.exists():
            continue
        with path.open() as f:
            data = json.load(f)
        file_url = str(data.get("url", "")).strip()
        file_token = str(data.get("token", "")).strip()
        if file_url and file_token:
            return file_url.rstrip("/"), file_token
    _die(
        "Missing config. Set HA_URL + HA_TOKEN env vars, or create .ha.json: "
        '{"url":"http://ha.local:8123","token":"..."}'
    )
    return "", ""


def normalize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return normalize(value.model_dump(mode="json"))
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    return value


def _human_print(data: Any) -> None:
    """Pretty human-readable output using rich."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if isinstance(data, dict) and "entities" in data:
        entities = data["entities"]
        if not entities:
            console.print("[dim]No entities found.[/dim]")
            return
        table = Table(show_header=True, header_style="bold")
        table.add_column("Entity ID", style="cyan")
        table.add_column("State", style="green")
        table.add_column("Name")
        sample = entities[0] if entities else {}
        extra_cols = [
            k
            for k in sample
            if k not in ("entity_id", "state", "name") and sample[k] is not None
        ]
        for col in extra_cols:
            table.add_column(col.replace("_", " ").title())
        for e in entities:
            row = [
                str(e.get("entity_id", "")),
                str(e.get("state", "")),
                str(e.get("name", "")),
            ]
            for col in extra_cols:
                row.append(str(e.get(col, "")))
            table.add_row(*row)
        console.print(table)
        if "actions" in data:
            console.print("\n[bold]Actions:[/bold]")
            actions = data["actions"]
            if isinstance(actions, dict):
                for domain_or_key, val in actions.items():
                    if isinstance(val, dict):
                        console.print(f"  [bold]{domain_or_key}:[/bold]")
                        for name, cmd in val.items():
                            console.print(f"    [dim]{name}:[/dim] {cmd}")
                    else:
                        console.print(f"  [dim]{domain_or_key}:[/dim] {val}")
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        table = Table(show_header=True, header_style="bold")
        for key in data[0]:
            table.add_column(key.replace("_", " ").title())
        for row_data in data:
            table.add_row(*[str(v) for v in row_data.values()])
        console.print(table)
    elif isinstance(data, dict) and "ok" in data:
        if data.get("ok"):
            parts = [f"[green]OK[/green] {data.get('entity_id', '')}"]
            if "action" in data:
                parts.append(f"[dim]{data['action']}[/dim]")
            extras = {
                k: v for k, v in data.items() if k not in ("ok", "entity_id", "action")
            }
            if extras:
                parts.append(str(extras))
            console.print(" ".join(parts))
        else:
            console.print(f"[red]FAIL[/red] {data}")
    else:
        console.print_json(json.dumps(data))


def out(data: Any, *, verbose: bool = False) -> None:
    if _st.human:
        _human_print(data)
    elif verbose:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data, separators=(",", ":")))


# ---------------------------------------------------------------------------
# Slim formatters
# ---------------------------------------------------------------------------

_SLIM_KEYS: dict[str, tuple[str, ...]] = {
    "default": (
        "brightness",
        "color_temp",
        "temperature",
        "current_temperature",
        "hvac_mode",
        "media_title",
        "source",
        "unit_of_measurement",
        "percentage",
        "preset_mode",
    ),
    "media_player": (
        "media_title",
        "media_artist",
        "media_content_type",
        "source",
        "volume_level",
        "is_volume_muted",
    ),
    "cover": ("current_position", "current_tilt_position"),
    "lock": (),
    "humidifier": ("humidity", "current_humidity", "mode", "device_class"),
}


def slim(state: dict[str, Any], domain: str | None = None) -> dict[str, Any]:
    attrs = state.get("attributes", {})
    if domain is None:
        domain = state.get("entity_id", "").split(".", 1)[0]
    result: dict[str, Any] = {
        "entity_id": state.get("entity_id"),
        "state": state.get("state"),
        "name": attrs.get("friendly_name"),
    }
    for key in _SLIM_KEYS.get(domain, _SLIM_KEYS["default"]):
        if key in attrs:
            result[key] = attrs[key]
    return result


# ---------------------------------------------------------------------------
# Async API layer
# ---------------------------------------------------------------------------


def safe_run(coro: Any) -> Any:
    try:
        return asyncio.run(coro)
    except SystemExit:
        raise
    except Exception as e:
        _die(f"{type(e).__name__}: {e}")


async def get_client(base_url: str, token: str) -> HAClient:
    return HAClient(f"{base_url}/api", token, use_async=True)


async def _call_service(
    base_url: str,
    token: str,
    domain: str,
    service: str,
    data: dict[str, Any],
) -> Any:
    client = await get_client(base_url, token)
    async with client:
        result = await client.async_trigger_service(domain, service, **data)
        return normalize(result)


async def _get_states(base_url: str, token: str) -> list[dict[str, Any]]:
    client = await get_client(base_url, token)
    async with client:
        return normalize(await client.async_get_states())


async def _get_state(base_url: str, token: str, entity_id: str) -> dict[str, Any]:
    client = await get_client(base_url, token)
    async with client:
        return normalize(await client.async_get_state(entity_id=entity_id))


async def _get_config(base_url: str, token: str) -> dict[str, Any]:
    client = await get_client(base_url, token)
    async with client:
        return normalize(await client.async_get_config())


def _rest(
    base_url: str,
    token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    raw: bool = False,
) -> Any:
    import urllib.error
    import urllib.request

    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url=f"{base_url}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode()
            if raw:
                return text
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        _die(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}")
    except urllib.error.URLError as e:
        _die(f"Connection failed: {e.reason}")


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def _matches_area(entity_id: str, area: str) -> bool:
    return area.lower() in entity_id.lower()


def _filter_domain_area(
    states: list[dict[str, Any]],
    domain: str,
    area: str | None,
) -> list[dict[str, Any]]:
    filtered = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    if area:
        filtered = [s for s in filtered if _matches_area(s.get("entity_id", ""), area)]
    return filtered


def _prefix(raw: str, domain: str) -> str:
    return raw if raw.startswith(f"{domain}.") else f"{domain}.{raw}"


DOMAIN_ACTIONS: dict[str, dict[str, str]] = {
    "light": {
        "on": "ha light on [area]",
        "off": "ha light off [area]",
        "power": "ha on/off/toggle <entity_id> [--brightness N]",
    },
    "fan": {
        "speed": "ha fan speed <entity_id> <0-100>",
        "preset": "ha fan preset <entity_id> <mode>",
        "oscillate": "ha fan oscillate <entity_id> on|off",
        "power": "ha on/off/toggle <entity_id>",
    },
    "cover": {
        "open": "ha cover open <entity_id>",
        "close": "ha cover close <entity_id>",
        "stop": "ha cover stop <entity_id>",
        "position": "ha cover position <entity_id> <0-100>",
    },
    "lock": {
        "lock": "ha lock lock <entity_id>",
        "unlock": "ha lock unlock <entity_id>",
    },
    "switch": {"power": "ha on/off/toggle <entity_id>"},
    "media_player": {
        "play": "ha media play <entity_id>",
        "pause": "ha media pause <entity_id>",
        "stop": "ha media stop <entity_id>",
        "next": "ha media next <entity_id>",
        "prev": "ha media prev <entity_id>",
        "volume": "ha media volume <entity_id> <0-100>",
    },
    "climate": {
        "set": "ha climate set <entity_id> [--temperature N] [--hvac-mode cool|heat|off|...]",
    },
    "humidifier": {
        "set": "ha humidifier set <entity_id> [--humidity N] [--mode MODE]",
        "power": "ha on/off <entity_id>",
    },
    "automation": {
        "trigger": "ha automation trigger <entity_id>",
        "on": "ha automation on <entity_id>",
        "off": "ha automation off <entity_id>",
    },
    "scene": {"activate": "ha scene <name>"},
    "script": {"run": "ha script <name>"},
    "button": {"press": "ha button <entity_id>"},
    "weather": {"show": "ha weather <entity_id>"},
}


def _actions_for_domains(domains: set[str]) -> dict[str, dict[str, str]]:
    """Return action hints for the given domains."""
    return {d: DOMAIN_ACTIONS[d] for d in sorted(domains) if d in DOMAIN_ACTIONS}


def _list_domain(
    domain: str, area: str | None, actions: dict[str, str] | None = None
) -> None:
    """List entities for a domain with action hints for discoverability."""
    base_url, token = load_config()
    states = safe_run(_get_states(base_url, token))
    entities = _filter_domain_area(states, domain, area)
    v = _st.verbose
    result: dict[str, Any] = {
        "entities": entities if v else [slim(s, domain) for s in entities],
    }
    if actions:
        result["actions"] = actions
    out(result, verbose=v)


def _fuzzy_find(states: list[dict[str, Any]], domain: str, raw: str) -> str | None:
    exact_id = _prefix(raw, domain)
    pool = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    if any(s.get("entity_id") == exact_id for s in pool):
        return exact_id
    q = raw.lower()
    matches = [
        s
        for s in pool
        if q in str(s.get("entity_id", "")).lower()
        or q in str(s.get("attributes", {}).get("friendly_name", "")).lower()
    ]
    if len(matches) == 1:
        return matches[0].get("entity_id")
    if not matches:
        _die(f"No {domain} matching '{raw}'")
    else:
        out(
            {
                "error": "ambiguous",
                "query": raw,
                "matches": [s.get("entity_id") for s in matches],
            }
        )
    return None


async def _bulk_service(
    base_url: str,
    token: str,
    domain: str,
    service: str,
    area: str | None,
) -> list[dict[str, Any]]:
    client = await get_client(base_url, token)
    async with client:
        states = normalize(await client.async_get_states())
        targets = _filter_domain_area(states, domain, area)
        results = []
        for entity in targets:
            eid = entity.get("entity_id", "")
            try:
                await client.async_trigger_service(domain, service, entity_id=eid)
                results.append({"entity_id": eid, "ok": True})
            except Exception as e:
                results.append({"entity_id": eid, "ok": False, "error": str(e)})
        return results


def _done(result: Any, entity_id: str, action: str, **extra: Any) -> None:
    if _st.verbose:
        out(result, verbose=True)
    else:
        out({"ok": True, "entity_id": entity_id, "action": action, **extra})


def _bulk_done(
    results: list[dict[str, Any]], action: str, domain: str, area: str | None
) -> None:
    if _st.verbose:
        out(results, verbose=True)
    else:
        ok = sum(1 for r in results if r.get("ok"))
        out(
            {
                "action": action,
                "domain": domain,
                "area": area or "all",
                "total": len(results),
                "ok": ok,
            }
        )


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


@app.command()
def info() -> None:
    """Connection info and HA version."""
    base_url, token = load_config()
    data = safe_run(_get_config(base_url, token))
    v = _st.verbose
    if v:
        out(data, verbose=True)
    else:
        out(
            {
                "version": data.get("version"),
                "location": data.get("location_name"),
                "units": data.get("unit_system", {}).get("temperature"),
            }
        )


@app.command()
def entities(
    domain: str = typer.Option(None, help="Filter by domain (light, switch, ...)"),
    ids_only: bool = typer.Option(False, "--ids-only", help="Show only entity IDs"),
) -> None:
    """List all entities."""
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    if domain:
        states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
    v = _st.verbose
    if ids_only:
        out([s.get("entity_id") for s in states], verbose=v)
    elif v:
        out(states, verbose=True)
    else:
        out([slim(s) for s in states])


@app.command()
def search(query: str) -> None:
    """Search entities by id or friendly name. Shows matching entities and available actions."""
    base_url, token = load_config()
    states = safe_run(_get_states(base_url, token))
    q = query.lower()
    hits = [
        s
        for s in states
        if q in str(s.get("entity_id", "")).lower()
        or q in str(s.get("attributes", {}).get("friendly_name", "")).lower()
    ]
    v = _st.verbose
    domains = {str(s.get("entity_id", "")).split(".", 1)[0] for s in hits}
    result: dict[str, Any] = {
        "entities": hits if v else [slim(s) for s in hits],
        "actions": _actions_for_domains(domains),
    }
    out(result, verbose=v)


@app.command()
def state(entity_id: str) -> None:
    """Get current state of an entity."""
    base_url, token = load_config()
    data = safe_run(_get_state(base_url, token, entity_id))
    v = _st.verbose
    out(data if v else slim(data), verbose=v)


@app.command()
def areas() -> None:
    """List all HA areas."""
    base_url, token = load_config()
    ids_raw = _rest(
        base_url,
        token,
        "POST",
        "/api/template",
        {"template": "{{ areas() | join('\\n') }}"},
        raw=True,
    )
    v = _st.verbose
    if not ids_raw or not ids_raw.strip():
        out([], verbose=v)
        return
    area_ids = [a.strip() for a in ids_raw.strip().split("\n") if a.strip()]
    parts = [f"{aid}|{{{{ area_name('{aid}') }}}}" for aid in area_ids]
    names_raw = _rest(
        base_url,
        token,
        "POST",
        "/api/template",
        {"template": "\n".join(parts)},
        raw=True,
    )
    result = []
    for line in names_raw.strip().split("\n"):
        if "|" in line:
            aid, name = line.split("|", 1)
            result.append({"id": aid.strip(), "name": name.strip()})
    out(result, verbose=v)


@app.command()
def history(
    entity_id: str,
    count: int = typer.Option(10, "-n", "--count", help="Number of entries"),
    hours: int = typer.Option(24, "--hours", help="Look-back window in hours"),
) -> None:
    """Last N state changes for an entity."""
    from datetime import datetime, timedelta, timezone

    base_url, token = load_config()
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    ts = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    path = f"/api/history/period/{ts}?filter_entity_id={entity_id}&minimal_response&no_attributes"
    data = _rest(base_url, token, "GET", path)
    v = _st.verbose
    if not data or not isinstance(data, list) or not data[0]:
        out([], verbose=v)
        return
    entries = data[0][-count:]
    if v:
        out(entries, verbose=True)
    else:
        out(
            [
                {"state": e.get("state"), "changed": e.get("last_changed")}
                for e in entries
            ]
        )


@app.command()
def snapshot(
    domains: str = typer.Option(
        None,
        help="Comma-separated domains (default: light,climate,media_player,fan,cover,lock)",
    ),
) -> None:
    """Current state of key domains."""
    base_url, token = load_config()
    states = safe_run(_get_states(base_url, token))
    domain_list = (
        tuple(d.strip() for d in domains.split(","))
        if domains
        else ("light", "climate", "media_player", "fan", "cover", "lock")
    )
    v = _st.verbose
    result: dict[str, Any] = {}
    for d in domain_list:
        ents = [s for s in states if s.get("entity_id", "").startswith(f"{d}.")]
        result[d] = ents if v else [slim(s, d) for s in ents]
    out(result, verbose=v)


@app.command()
def weather(
    entity_id: str = typer.Argument(
        None, help="weather.x (default: weather.forecast_home)"
    ),
) -> None:
    """Current weather — omit entity to list all weather entities."""
    base_url, token = load_config()
    if entity_id is None:
        states = safe_run(_get_states(base_url, token))
        weathers = _filter_domain_area(states, "weather", None)
        v = _st.verbose
        out(
            {
                "entities": weathers if v else [slim(s) for s in weathers],
                "actions": DOMAIN_ACTIONS["weather"],
            },
            verbose=v,
        )
        return
    eid = _prefix(entity_id, "weather")
    data = safe_run(_get_state(base_url, token, eid))
    v = _st.verbose
    if v:
        out(data, verbose=True)
    else:
        attrs = data.get("attributes", {})
        out(
            {
                "state": data.get("state"),
                "name": attrs.get("friendly_name"),
                "temperature": attrs.get("temperature"),
                "humidity": attrs.get("humidity"),
                "wind_speed": attrs.get("wind_speed"),
                "wind_bearing": attrs.get("wind_bearing"),
                "pressure": attrs.get("pressure"),
                "uv_index": attrs.get("uv_index"),
            }
        )


# -- Generic entity control --


@app.command()
def on(
    entity_id: str,
    brightness: int = typer.Option(None, help="Brightness 0-255 (lights)"),
    transition: float = typer.Option(None, help="Transition seconds (lights)"),
) -> None:
    """Turn on any entity."""
    base_url, token = load_config()
    domain = entity_id.split(".", 1)[0]
    payload: dict[str, Any] = {"entity_id": entity_id}
    if brightness is not None:
        payload["brightness"] = brightness
    if transition is not None:
        payload["transition"] = transition
    result = safe_run(_call_service(base_url, token, domain, "turn_on", payload))
    _done(result, entity_id, "turn_on")


@app.command()
def off(entity_id: str) -> None:
    """Turn off any entity."""
    base_url, token = load_config()
    domain = entity_id.split(".", 1)[0]
    result = safe_run(
        _call_service(base_url, token, domain, "turn_off", {"entity_id": entity_id})
    )
    _done(result, entity_id, "turn_off")


@app.command()
def toggle(entity_id: str) -> None:
    """Toggle any entity on/off."""
    base_url, token = load_config()
    domain = entity_id.split(".", 1)[0]
    result = safe_run(
        _call_service(base_url, token, domain, "toggle", {"entity_id": entity_id})
    )
    _done(result, entity_id, "toggle")


@app.command()
def call(
    domain: str,
    service: str,
    json_payload: str = typer.Option(None, "--json", help="JSON payload"),
) -> None:
    """Raw service call."""
    base_url, token = load_config()
    payload: dict[str, Any] = json.loads(json_payload) if json_payload else {}
    result = safe_run(_call_service(base_url, token, domain, service, payload))
    out(result, verbose=_st.verbose)


@app.command()
def assist(
    text: str,
    language: str = typer.Option("en", help="Language code"),
) -> None:
    """Natural language command via HA Assist API."""
    base_url, token = load_config()
    result = _rest(
        base_url,
        token,
        "POST",
        "/api/conversation/process",
        {"text": text, "language": language},
    )
    v = _st.verbose
    if v:
        out(result, verbose=True)
    elif isinstance(result, dict):
        speech = (
            result.get("response", {})
            .get("speech", {})
            .get("plain", {})
            .get("speech", "")
        )
        out({"speech": speech})
    else:
        out(result)


@app.command()
def scene(
    name: str = typer.Argument(None, help="Scene name (fuzzy) — omit to list"),
) -> None:
    """Activate a scene, or list all scenes."""
    base_url, token = load_config()
    states = safe_run(_get_states(base_url, token))
    if name is None:
        scenes = _filter_domain_area(states, "scene", None)
        v = _st.verbose
        out(
            {
                "entities": scenes if v else [slim(s) for s in scenes],
                "actions": DOMAIN_ACTIONS["scene"],
            },
            verbose=v,
        )
        return
    eid = _fuzzy_find(states, "scene", name)
    if not eid:
        return
    result = safe_run(
        _call_service(base_url, token, "scene", "turn_on", {"entity_id": eid})
    )
    _done(result, eid, "turn_on")


@app.command()
def script(
    name: str = typer.Argument(None, help="Script name (fuzzy) — omit to list"),
) -> None:
    """Run a script, or list all scripts."""
    base_url, token = load_config()
    states = safe_run(_get_states(base_url, token))
    if name is None:
        scripts = _filter_domain_area(states, "script", None)
        v = _st.verbose
        out(
            {
                "entities": scripts if v else [slim(s) for s in scripts],
                "actions": DOMAIN_ACTIONS["script"],
            },
            verbose=v,
        )
        return
    eid = _fuzzy_find(states, "script", name)
    if not eid:
        return
    result = safe_run(
        _call_service(base_url, token, "script", "turn_on", {"entity_id": eid})
    )
    _done(result, eid, "turn_on")


@app.command()
def button(
    entity_id: str = typer.Argument(None, help="button.x or x — omit to list"),
) -> None:
    """Press a button entity, or list all buttons."""
    if entity_id is None:
        _list_domain("button", None, DOMAIN_ACTIONS["button"])
        return
    base_url, token = load_config()
    eid = _prefix(entity_id, "button")
    result = safe_run(
        _call_service(base_url, token, "button", "press", {"entity_id": eid})
    )
    _done(result, eid, "press")


# ---------------------------------------------------------------------------
# Domain: light
# ---------------------------------------------------------------------------

light_app = typer.Typer(
    help="Light control — list or bulk on/off by area.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(light_app, name="light")


@light_app.callback(invoke_without_command=True)
def _light_list(
    ctx: typer.Context,
    area: str = typer.Option(None, help="Filter by area"),
) -> None:
    """List all lights and available actions."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("light", area, DOMAIN_ACTIONS["light"])


@light_app.command("on")
def light_on(
    area: str = typer.Argument(None, help="Area name"),
) -> None:
    """Turn on all lights (or by area)."""
    base_url, token = load_config()
    results = safe_run(_bulk_service(base_url, token, "light", "turn_on", area))
    _bulk_done(results, "turn_on", "light", area)


@light_app.command("off")
def light_off(
    area: str = typer.Argument(None, help="Area name"),
) -> None:
    """Turn off all lights (or by area)."""
    base_url, token = load_config()
    results = safe_run(_bulk_service(base_url, token, "light", "turn_off", area))
    _bulk_done(results, "turn_off", "light", area)


# ---------------------------------------------------------------------------
# Domain: fan
# ---------------------------------------------------------------------------

fan_app = typer.Typer(
    help="Fan control — list or set speed/preset/oscillate.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(fan_app, name="fan")


@fan_app.callback(invoke_without_command=True)
def _fan_list(ctx: typer.Context) -> None:
    """List all fans and available controls."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("fan", None, DOMAIN_ACTIONS["fan"])


@fan_app.command()
def speed(
    entity_id: str,
    value: int = typer.Argument(..., help="Speed percentage 0-100"),
) -> None:
    """Set fan speed percentage."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "fan")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "fan",
            "set_percentage",
            {"entity_id": eid, "percentage": value},
        )
    )
    _done(result, eid, "set_percentage", percentage=value)


@fan_app.command()
def preset(entity_id: str, mode: str) -> None:
    """Set fan preset mode."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "fan")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "fan",
            "set_preset_mode",
            {"entity_id": eid, "preset_mode": mode},
        )
    )
    _done(result, eid, "set_preset_mode", preset_mode=mode)


@fan_app.command()
def oscillate(
    entity_id: str,
    value: str = typer.Argument(..., help="on or off"),
) -> None:
    """Toggle fan oscillation."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "fan")
    val = value.lower() in ("on", "true", "1")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "fan",
            "oscillate",
            {"entity_id": eid, "oscillating": val},
        )
    )
    _done(result, eid, "oscillate", oscillating=val)


# ---------------------------------------------------------------------------
# Domain: cover
# ---------------------------------------------------------------------------

cover_app = typer.Typer(
    help="Cover control — open/close/stop/position.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(cover_app, name="cover")


@cover_app.callback(invoke_without_command=True)
def _cover_list(
    ctx: typer.Context,
    area: str = typer.Option(None, help="Filter by area"),
) -> None:
    """List all covers and available actions."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("cover", area, DOMAIN_ACTIONS["cover"])


@cover_app.command("open")
def cover_open(entity_id: str) -> None:
    """Open a cover."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "cover")
    result = safe_run(
        _call_service(base_url, token, "cover", "open_cover", {"entity_id": eid})
    )
    _done(result, eid, "open_cover")


@cover_app.command("close")
def cover_close(entity_id: str) -> None:
    """Close a cover."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "cover")
    result = safe_run(
        _call_service(base_url, token, "cover", "close_cover", {"entity_id": eid})
    )
    _done(result, eid, "close_cover")


@cover_app.command("stop")
def cover_stop(entity_id: str) -> None:
    """Stop cover movement."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "cover")
    result = safe_run(
        _call_service(base_url, token, "cover", "stop_cover", {"entity_id": eid})
    )
    _done(result, eid, "stop_cover")


@cover_app.command()
def position(
    entity_id: str,
    value: int = typer.Argument(..., help="Position 0=closed, 100=open"),
) -> None:
    """Set cover position."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "cover")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "cover",
            "set_cover_position",
            {"entity_id": eid, "position": value},
        )
    )
    _done(result, eid, "set_cover_position", position=value)


# ---------------------------------------------------------------------------
# Domain: lock
# ---------------------------------------------------------------------------

lock_app = typer.Typer(
    help="Lock control.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(lock_app, name="lock")


@lock_app.callback(invoke_without_command=True)
def _lock_list(ctx: typer.Context) -> None:
    """List all locks and available actions."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("lock", None, DOMAIN_ACTIONS["lock"])


@lock_app.command("lock")
def lock_lock(entity_id: str) -> None:
    """Lock a lock."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "lock")
    result = safe_run(
        _call_service(base_url, token, "lock", "lock", {"entity_id": eid})
    )
    _done(result, eid, "lock")


@lock_app.command("unlock")
def lock_unlock(entity_id: str) -> None:
    """Unlock a lock."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "lock")
    result = safe_run(
        _call_service(base_url, token, "lock", "unlock", {"entity_id": eid})
    )
    _done(result, eid, "unlock")


# ---------------------------------------------------------------------------
# Domain: switch
# ---------------------------------------------------------------------------


@app.command("switch")
def switch_list(
    area: str = typer.Argument(None, help="Filter by area"),
) -> None:
    """List switches. Use `ha on/off/toggle <entity_id>` to control."""
    _list_domain("switch", area, DOMAIN_ACTIONS["switch"])


# ---------------------------------------------------------------------------
# Domain: media
# ---------------------------------------------------------------------------

media_app = typer.Typer(
    help="Media player control — play/pause/stop/next/prev/volume.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(media_app, name="media")


@media_app.callback(invoke_without_command=True)
def _media_list(ctx: typer.Context) -> None:
    """List all media players and available controls."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("media_player", None, DOMAIN_ACTIONS["media_player"])


def _media_action(entity_id: str, service: str) -> None:
    base_url, token = load_config()
    eid = _prefix(entity_id, "media_player")
    result = safe_run(
        _call_service(base_url, token, "media_player", service, {"entity_id": eid})
    )
    _done(result, eid, service)


@media_app.command()
def play(entity_id: str) -> None:
    """Play."""
    _media_action(entity_id, "media_play")


@media_app.command()
def pause(entity_id: str) -> None:
    """Pause."""
    _media_action(entity_id, "media_pause")


@media_app.command("stop")
def media_stop(entity_id: str) -> None:
    """Stop playback."""
    _media_action(entity_id, "media_stop")


@media_app.command("next")
def media_next(entity_id: str) -> None:
    """Next track."""
    _media_action(entity_id, "media_next_track")


@media_app.command()
def prev(entity_id: str) -> None:
    """Previous track."""
    _media_action(entity_id, "media_previous_track")


@media_app.command()
def volume(
    entity_id: str,
    level: int = typer.Argument(..., help="Volume 0-100"),
) -> None:
    """Set volume (0-100)."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "media_player")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "media_player",
            "volume_set",
            {"entity_id": eid, "volume_level": level / 100.0},
        )
    )
    _done(result, eid, "volume_set", volume=level)


# ---------------------------------------------------------------------------
# Domain: climate
# ---------------------------------------------------------------------------

climate_app = typer.Typer(
    help="Climate/AC control.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(climate_app, name="climate")


@climate_app.callback(invoke_without_command=True)
def _climate_list(ctx: typer.Context) -> None:
    """List all climate entities and available controls."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("climate", None, DOMAIN_ACTIONS["climate"])


@climate_app.command("set")
def climate_set(
    entity_id: str,
    temperature: float = typer.Option(None, help="Target temperature"),
    hvac_mode: str = typer.Option(
        None,
        "--hvac-mode",
        help="off|heat|cool|heat_cool|auto|dry|fan_only",
    ),
) -> None:
    """Set climate temperature and/or HVAC mode."""
    base_url, token = load_config()
    payload: dict[str, Any] = {"entity_id": entity_id}
    if temperature is not None:
        payload["temperature"] = temperature
    if hvac_mode:
        payload["hvac_mode"] = hvac_mode
    if "temperature" in payload:
        service = "set_temperature"
    elif "hvac_mode" in payload:
        service = "set_hvac_mode"
    else:
        _die("Specify --temperature and/or --hvac-mode")
        return
    result = safe_run(_call_service(base_url, token, "climate", service, payload))
    _done(
        result,
        entity_id,
        service,
        **{k: v for k, v in payload.items() if k != "entity_id"},
    )


# ---------------------------------------------------------------------------
# Domain: humidifier
# ---------------------------------------------------------------------------

humidifier_app = typer.Typer(
    help="Humidifier/dehumidifier control.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(humidifier_app, name="humidifier")


@humidifier_app.callback(invoke_without_command=True)
def _humidifier_list(ctx: typer.Context) -> None:
    """List all humidifiers and available controls."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("humidifier", None, DOMAIN_ACTIONS["humidifier"])


@humidifier_app.command("set")
def humidifier_set(
    entity_id: str,
    humidity: int = typer.Option(None, help="Target humidity 0-100"),
    mode: str = typer.Option(None, help="Mode (SMART, FAST, CILENT, IONIZER, ...)"),
) -> None:
    """Set humidifier target humidity and/or mode."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "humidifier")
    payload: dict[str, Any] = {"entity_id": eid}
    if humidity is not None:
        payload["humidity"] = humidity
    if mode:
        payload["mode"] = mode
    if "humidity" in payload:
        result = safe_run(
            _call_service(base_url, token, "humidifier", "set_humidity", payload)
        )
        if mode:
            safe_run(
                _call_service(
                    base_url,
                    token,
                    "humidifier",
                    "set_mode",
                    {"entity_id": eid, "mode": mode},
                )
            )
    elif "mode" in payload:
        result = safe_run(
            _call_service(base_url, token, "humidifier", "set_mode", payload)
        )
    else:
        _die("Specify --humidity and/or --mode")
        return
    _done(
        result,
        eid,
        "set",
        **{k: v for k, v in payload.items() if k != "entity_id"},
    )


# ---------------------------------------------------------------------------
# Domain: automation
# ---------------------------------------------------------------------------

auto_app = typer.Typer(
    help="Automation control — trigger/enable/disable.",
    invoke_without_command=True,
    no_args_is_help=False,
)
app.add_typer(auto_app, name="automation")


@auto_app.callback(invoke_without_command=True)
def _auto_list(ctx: typer.Context) -> None:
    """List all automations and available controls."""
    if ctx.invoked_subcommand is not None:
        return
    _list_domain("automation", None, DOMAIN_ACTIONS["automation"])


@auto_app.command()
def trigger(entity_id: str) -> None:
    """Trigger an automation."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "automation")
    result = safe_run(
        _call_service(base_url, token, "automation", "trigger", {"entity_id": eid})
    )
    _done(result, eid, "trigger")


@auto_app.command("on")
def auto_on(entity_id: str) -> None:
    """Enable an automation."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "automation")
    result = safe_run(
        _call_service(base_url, token, "automation", "turn_on", {"entity_id": eid})
    )
    _done(result, eid, "turn_on")


@auto_app.command("off")
def auto_off(entity_id: str) -> None:
    """Disable an automation."""
    base_url, token = load_config()
    eid = _prefix(entity_id, "automation")
    result = safe_run(
        _call_service(base_url, token, "automation", "turn_off", {"entity_id": eid})
    )
    _done(result, eid, "turn_off")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
