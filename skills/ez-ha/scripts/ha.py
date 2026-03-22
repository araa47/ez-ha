#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "HomeAssistant-API>=5.0.3",
#   "python-dotenv>=1.0.1",
# ]
# ///
"""Home Assistant CLI — agent-friendly, compact by default.

Convention:
  singular = action   ha light on bedroom, ha cover open curtains
  plural   = list     ha lights, ha covers
  generic  = any      ha on <entity_id>, ha off <entity_id>

Usage: ha <command> [options]
       uv run skills/ha/scripts/ha.py <command> [options]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from homeassistant_api import Client as HAClient

CONFIG_PATHS = [
    Path.cwd() / ".ha.json",
    Path.home() / ".config" / "home-assistant" / "config.json",
]


# ---------------------------------------------------------------------------
# Config / helpers
# ---------------------------------------------------------------------------


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


def out(data: Any, *, verbose: bool = False) -> None:
    if verbose:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data, separators=(",", ":")))


# ---------------------------------------------------------------------------
# Slim formatters (compact entity representations)
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
    """Compact entity representation. Domain-aware key selection."""
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
    """Unified REST helper. Returns parsed JSON by default, raw text if raw=True."""
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
    """Ensure entity_id has domain prefix."""
    return raw if raw.startswith(f"{domain}.") else f"{domain}.{raw}"


def _fuzzy_run(
    args: argparse.Namespace,
    domain: str,
    service: str,
    id_attr: str,
) -> None:
    """Run a service with fuzzy entity matching. Exact > single fuzzy > ambiguous error."""
    base_url, token = load_config()
    raw = getattr(args, id_attr)
    exact_id = _prefix(raw, domain)
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    pool = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]

    # Exact match
    if any(s.get("entity_id") == exact_id for s in pool):
        result = safe_run(
            _call_service(base_url, token, domain, service, {"entity_id": exact_id})
        )
        if args.verbose:
            out(result, verbose=True)
        else:
            out({"ok": True, "entity_id": exact_id, "action": service})
        return

    # Fuzzy substring match
    q = raw.lower()
    matches = [
        s
        for s in pool
        if q in str(s.get("entity_id", "")).lower()
        or q in str(s.get("attributes", {}).get("friendly_name", "")).lower()
    ]
    if len(matches) == 1:
        eid = matches[0].get("entity_id")
        result = safe_run(
            _call_service(base_url, token, domain, service, {"entity_id": eid})
        )
        if args.verbose:
            out(result, verbose=True)
        else:
            out({"ok": True, "entity_id": eid, "action": service})
    elif not matches:
        _die(f"No {domain} matching '{raw}'")
    else:
        out(
            {
                "error": "ambiguous",
                "query": raw,
                "matches": [s.get("entity_id") for s in matches],
            }
        )


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


def _bulk_result(
    results: list[dict[str, Any]],
    action: str,
    domain: str,
    area: str | None,
    verbose: bool,
) -> None:
    """Format bulk operation output."""
    if verbose:
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
# Commands — query / inspect
# ---------------------------------------------------------------------------


def cmd_info(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    data = safe_run(_get_config(base_url, token))
    if args.verbose:
        out(data, verbose=True)
    else:
        out(
            {
                "version": data.get("version"),
                "location": data.get("location_name"),
                "units": data.get("unit_system", {}).get("temperature"),
            }
        )


def cmd_entities(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    if args.domain:
        states = [
            s for s in states if s.get("entity_id", "").startswith(f"{args.domain}.")
        ]
    if args.ids_only:
        out([s.get("entity_id") for s in states], verbose=args.verbose)
    elif args.verbose:
        out(states, verbose=True)
    else:
        out([slim(s) for s in states])


def cmd_search(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    q = args.query.lower()
    hits = [
        s
        for s in states
        if q in str(s.get("entity_id", "")).lower()
        or q in str(s.get("attributes", {}).get("friendly_name", "")).lower()
    ]
    out(hits if args.verbose else [slim(s) for s in hits], verbose=args.verbose)


def cmd_state(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    data = safe_run(_get_state(base_url, token, args.entity_id))
    out(data if args.verbose else slim(data), verbose=args.verbose)


def cmd_areas(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    ids_raw = _rest(
        base_url,
        token,
        "POST",
        "/api/template",
        {"template": "{{ areas() | join('\\n') }}"},
        raw=True,
    )
    if not ids_raw or not ids_raw.strip():
        out([], verbose=args.verbose)
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
    out(result, verbose=args.verbose)


def cmd_history(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    from datetime import datetime, timedelta, timezone

    start = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    ts = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    path = f"/api/history/period/{ts}?filter_entity_id={args.entity_id}&minimal_response&no_attributes"
    data = _rest(base_url, token, "GET", path)
    if not data or not isinstance(data, list) or not data[0]:
        out([], verbose=args.verbose)
        return
    entries = data[0][-args.count :]
    if args.verbose:
        out(entries, verbose=True)
    else:
        out(
            [
                {"state": e.get("state"), "changed": e.get("last_changed")}
                for e in entries
            ]
        )


def cmd_snapshot(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    domains = (
        tuple(d.strip() for d in args.domains.split(","))
        if args.domains
        else (
            "light",
            "climate",
            "media_player",
            "fan",
            "cover",
            "lock",
        )
    )
    result: dict[str, Any] = {}
    for domain in domains:
        entities = [
            s for s in states if s.get("entity_id", "").startswith(f"{domain}.")
        ]
        result[domain] = (
            entities if args.verbose else [slim(s, domain) for s in entities]
        )
    out(result, verbose=args.verbose)


def cmd_weather(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = (
        _prefix(args.entity_id, "weather")
        if args.entity_id
        else "weather.forecast_home"
    )
    data = safe_run(_get_state(base_url, token, eid))
    if args.verbose:
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


# ---------------------------------------------------------------------------
# Commands — generic entity control (any domain)
# ---------------------------------------------------------------------------


def _entity_service(
    args: argparse.Namespace, service: str, extra: dict[str, Any] | None = None
) -> None:
    base_url, token = load_config()
    domain = args.entity_id.split(".", 1)[0]
    payload: dict[str, Any] = {"entity_id": args.entity_id}
    if extra:
        payload.update(extra)
    result = safe_run(_call_service(base_url, token, domain, service, payload))
    if args.verbose:
        out(result, verbose=True)
    else:
        out({"ok": True, "entity_id": args.entity_id, "action": service})


def cmd_on(args: argparse.Namespace) -> None:
    extra: dict[str, Any] = {}
    if args.brightness is not None:
        extra["brightness"] = args.brightness
    if args.transition is not None:
        extra["transition"] = args.transition
    _entity_service(args, "turn_on", extra)


def cmd_off(args: argparse.Namespace) -> None:
    _entity_service(args, "turn_off")


def cmd_toggle(args: argparse.Namespace) -> None:
    _entity_service(args, "toggle")


def cmd_call(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    payload: dict[str, Any] = json.loads(args.json) if args.json else {}
    result = safe_run(
        _call_service(base_url, token, args.domain, args.service, payload)
    )
    out(result, verbose=args.verbose)


# ---------------------------------------------------------------------------
# Commands — domain: light (singular=bulk action, plural=list)
# ---------------------------------------------------------------------------


def cmd_light(args: argparse.Namespace) -> None:
    """ha light on|off [area]"""
    base_url, token = load_config()
    service = "turn_on" if args.action == "on" else "turn_off"
    results = safe_run(_bulk_service(base_url, token, "light", service, args.area))
    _bulk_result(results, service, "light", args.area, args.verbose)


def cmd_lights(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    lights = _filter_domain_area(states, "light", args.area)
    out(
        lights if args.verbose else [slim(s, "light") for s in lights],
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Commands — domain: cover
# ---------------------------------------------------------------------------


def cmd_cover(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "cover")
    if args.action == "position":
        if args.value is None:
            _die("cover position requires a value (0-100)")
            return
        result = safe_run(
            _call_service(
                base_url,
                token,
                "cover",
                "set_cover_position",
                {"entity_id": eid, "position": args.value},
            )
        )
        out(
            (
                result
                if args.verbose
                else {"ok": True, "entity_id": eid, "position": args.value}
            ),
            verbose=args.verbose,
        )
        return
    service_map = {"open": "open_cover", "close": "close_cover", "stop": "stop_cover"}
    service = service_map[args.action]
    result = safe_run(
        _call_service(base_url, token, "cover", service, {"entity_id": eid})
    )
    out(
        result if args.verbose else {"ok": True, "entity_id": eid, "action": service},
        verbose=args.verbose,
    )


def cmd_covers(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    covers = _filter_domain_area(states, "cover", args.area)
    out(
        covers if args.verbose else [slim(s, "cover") for s in covers],
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Commands — domain: lock
# ---------------------------------------------------------------------------


def cmd_lock(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "lock")
    result = safe_run(
        _call_service(base_url, token, "lock", args.action, {"entity_id": eid})
    )
    out(
        (
            result
            if args.verbose
            else {"ok": True, "entity_id": eid, "action": args.action}
        ),
        verbose=args.verbose,
    )


def cmd_locks(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    locks = [s for s in states if s.get("entity_id", "").startswith("lock.")]
    out(
        locks if args.verbose else [slim(s, "lock") for s in locks],
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Commands — domain: switch (list only — use ha on/off/toggle for control)
# ---------------------------------------------------------------------------


def cmd_switches(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    switches = _filter_domain_area(states, "switch", args.area)
    out(switches if args.verbose else [slim(s) for s in switches], verbose=args.verbose)


# ---------------------------------------------------------------------------
# Commands — domain: media_player
# ---------------------------------------------------------------------------


def cmd_media(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "media_player")
    service_map = {
        "play": "media_play",
        "pause": "media_pause",
        "stop": "media_stop",
        "next": "media_next_track",
        "prev": "media_previous_track",
    }
    service = service_map[args.action]
    result = safe_run(
        _call_service(base_url, token, "media_player", service, {"entity_id": eid})
    )
    out(
        result if args.verbose else {"ok": True, "entity_id": eid, "action": service},
        verbose=args.verbose,
    )


def cmd_volume(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "media_player")
    result = safe_run(
        _call_service(
            base_url,
            token,
            "media_player",
            "volume_set",
            {"entity_id": eid, "volume_level": args.level / 100.0},
        )
    )
    out(
        (
            result
            if args.verbose
            else {"ok": True, "entity_id": eid, "volume": args.level}
        ),
        verbose=args.verbose,
    )


def cmd_players(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    players = [s for s in states if s.get("entity_id", "").startswith("media_player.")]
    out(
        players if args.verbose else [slim(s, "media_player") for s in players],
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Commands — domain: fan
# ---------------------------------------------------------------------------


def cmd_fan(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "fan")
    action = args.action
    if action == "speed":
        if args.value is None:
            _die("fan speed requires a value (0-100)")
            return
        result = safe_run(
            _call_service(
                base_url,
                token,
                "fan",
                "set_percentage",
                {"entity_id": eid, "percentage": args.value},
            )
        )
        label = {"ok": True, "entity_id": eid, "percentage": args.value}
    elif action == "preset":
        if args.value is None:
            _die("fan preset requires a mode name")
            return
        result = safe_run(
            _call_service(
                base_url,
                token,
                "fan",
                "set_preset_mode",
                {"entity_id": eid, "preset_mode": args.value},
            )
        )
        label = {"ok": True, "entity_id": eid, "preset_mode": args.value}
    elif action == "oscillate":
        val = str(args.value).lower() in ("on", "true", "1")
        result = safe_run(
            _call_service(
                base_url,
                token,
                "fan",
                "oscillate",
                {"entity_id": eid, "oscillating": val},
            )
        )
        label = {"ok": True, "entity_id": eid, "oscillating": val}
    else:
        _die(f"Unknown fan action: {action}")
        return
    out(result if args.verbose else label, verbose=args.verbose)


def cmd_fans(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    fans = [s for s in states if s.get("entity_id", "").startswith("fan.")]
    out(fans if args.verbose else [slim(s) for s in fans], verbose=args.verbose)


# ---------------------------------------------------------------------------
# Commands — domain: climate
# ---------------------------------------------------------------------------


def cmd_climate(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    payload: dict[str, Any] = {"entity_id": args.entity_id}
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.hvac_mode:
        payload["hvac_mode"] = args.hvac_mode
    if "temperature" in payload:
        service = "set_temperature"
    elif "hvac_mode" in payload:
        service = "set_hvac_mode"
    else:
        _die("Specify --temperature and/or --hvac-mode")
        return
    result = safe_run(_call_service(base_url, token, "climate", service, payload))
    if args.verbose:
        out(result, verbose=True)
    else:
        out(
            {
                "ok": True,
                "entity_id": args.entity_id,
                "action": service,
                **{k: v for k, v in payload.items() if k != "entity_id"},
            }
        )


# ---------------------------------------------------------------------------
# Commands — domain: humidifier
# ---------------------------------------------------------------------------


def cmd_humidifier(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "humidifier")
    payload: dict[str, Any] = {"entity_id": eid}
    if args.humidity is not None:
        payload["humidity"] = args.humidity
    if args.mode:
        payload["mode"] = args.mode
    if "humidity" in payload:
        result = safe_run(
            _call_service(base_url, token, "humidifier", "set_humidity", payload)
        )
        if args.mode:
            safe_run(
                _call_service(
                    base_url,
                    token,
                    "humidifier",
                    "set_mode",
                    {"entity_id": eid, "mode": args.mode},
                )
            )
    elif "mode" in payload:
        result = safe_run(
            _call_service(base_url, token, "humidifier", "set_mode", payload)
        )
    else:
        _die("Specify --humidity and/or --mode")
        return
    if args.verbose:
        out(result, verbose=True)
    else:
        out(
            {
                "ok": True,
                "entity_id": eid,
                **{k: v for k, v in payload.items() if k != "entity_id"},
            }
        )


def cmd_humidifiers(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    states: list[dict[str, Any]] = safe_run(_get_states(base_url, token))
    humids = [s for s in states if s.get("entity_id", "").startswith("humidifier.")]
    out(
        humids if args.verbose else [slim(s, "humidifier") for s in humids],
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Commands — scene, script (fuzzy), automation, assist, button
# ---------------------------------------------------------------------------


def cmd_scene(args: argparse.Namespace) -> None:
    _fuzzy_run(args, "scene", "turn_on", "scene")


def cmd_script(args: argparse.Namespace) -> None:
    _fuzzy_run(args, "script", "turn_on", "script")


def cmd_automation(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.automation, "automation")
    result = safe_run(
        _call_service(base_url, token, "automation", args.action, {"entity_id": eid})
    )
    out(
        (
            result
            if args.verbose
            else {"ok": True, "entity_id": eid, "action": args.action}
        ),
        verbose=args.verbose,
    )


def cmd_assist(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    result = _rest(
        base_url,
        token,
        "POST",
        "/api/conversation/process",
        {"text": args.text, "language": args.language},
    )
    if args.verbose:
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


def cmd_button(args: argparse.Namespace) -> None:
    base_url, token = load_config()
    eid = _prefix(args.entity_id, "button")
    result = safe_run(
        _call_service(base_url, token, "button", "press", {"entity_id": eid})
    )
    out(
        result if args.verbose else {"ok": True, "entity_id": eid, "action": "press"},
        verbose=args.verbose,
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ha", description="Home Assistant CLI (compact output by default)"
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Full JSON output")
    sub = p.add_subparsers(dest="command", required=True)

    # -- Query / inspect --
    sub.add_parser("info", help="Connection info")

    e = sub.add_parser("entities", help="List entities")
    e.add_argument("--domain", help="Filter by domain (light, switch, ...)")
    e.add_argument("--ids-only", action="store_true")

    s = sub.add_parser("search", help="Search entities by id/name")
    s.add_argument("query")

    st = sub.add_parser("state", help="Get entity state")
    st.add_argument("entity_id")

    sub.add_parser("areas", help="List all HA areas")

    hi = sub.add_parser("history", help="Last N state changes for an entity")
    hi.add_argument("entity_id")
    hi.add_argument(
        "-n", "--count", type=int, default=10, help="Number of entries (default 10)"
    )
    hi.add_argument(
        "--hours", type=int, default=24, help="Look-back window in hours (default 24)"
    )

    sn = sub.add_parser("snapshot", help="Current state of key domains")
    sn.add_argument(
        "--domains",
        help="Comma-separated (default: light,climate,media_player,fan,cover,lock)",
    )

    wt = sub.add_parser("weather", help="Current weather conditions")
    wt.add_argument(
        "entity_id", nargs="?", help="weather.x (default: weather.forecast_home)"
    )

    # -- Generic entity control --
    on = sub.add_parser("on", help="Turn on entity")
    on.add_argument("entity_id")
    on.add_argument("--brightness", type=int, help="0-255")
    on.add_argument("--transition", type=float, help="Seconds")

    off = sub.add_parser("off", help="Turn off entity")
    off.add_argument("entity_id")

    tg = sub.add_parser("toggle", help="Toggle entity")
    tg.add_argument("entity_id")

    c = sub.add_parser("call", help="Raw service call")
    c.add_argument("domain")
    c.add_argument("service")
    c.add_argument("--json", help="JSON payload")

    # -- Light (singular=bulk action, plural=list) --
    lt = sub.add_parser("light", help="Bulk light control by area")
    lt.add_argument("action", choices=["on", "off"])
    lt.add_argument("area", nargs="?", help="Area name (bedroom, hall, kitchen, ...)")

    ll = sub.add_parser("lights", help="List lights (or by area)")
    ll.add_argument("area", nargs="?", help="Area name")

    # -- Cover --
    cv = sub.add_parser("cover", help="Cover control (open/close/stop/position)")
    cv.add_argument("action", choices=["open", "close", "stop", "position"])
    cv.add_argument("entity_id", help="cover.x or x")
    cv.add_argument("value", nargs="?", type=int, help="Position 0-100 (for position)")

    cvl = sub.add_parser("covers", help="List covers (or by area)")
    cvl.add_argument("area", nargs="?", help="Area name")

    # -- Lock --
    lk = sub.add_parser("lock", help="Lock/unlock")
    lk.add_argument("action", choices=["lock", "unlock"])
    lk.add_argument("entity_id", help="lock.x or x")

    sub.add_parser("locks", help="List all locks")

    # -- Switch --
    sw = sub.add_parser("switches", help="List switches (or by area)")
    sw.add_argument("area", nargs="?", help="Area name")

    # -- Media player --
    md = sub.add_parser("media", help="Media control (play/pause/stop/next/prev)")
    md.add_argument("action", choices=["play", "pause", "stop", "next", "prev"])
    md.add_argument("entity_id", help="media_player.x or x")

    vol = sub.add_parser("volume", help="Set media player volume (0-100)")
    vol.add_argument("entity_id", help="media_player.x or x")
    vol.add_argument("level", type=int, help="Volume 0-100")

    sub.add_parser("players", help="List all media players")

    # -- Fan --
    fn = sub.add_parser("fan", help="Fan control (speed/preset/oscillate)")
    fn.add_argument("action", choices=["speed", "preset", "oscillate"])
    fn.add_argument("entity_id", help="fan.x or x")
    fn.add_argument("value", nargs="?", help="Speed 0-100, preset name, or on/off")

    sub.add_parser("fans", help="List all fans")

    # -- Climate --
    cl = sub.add_parser("climate", help="Climate control")
    cl.add_argument("entity_id")
    cl.add_argument("--temperature", type=float)
    cl.add_argument(
        "--hvac-mode",
        choices=["off", "heat", "cool", "heat_cool", "auto", "dry", "fan_only"],
    )

    # -- Humidifier --
    hm = sub.add_parser("humidifier", help="Set humidifier target humidity or mode")
    hm.add_argument("entity_id", help="humidifier.x or x")
    hm.add_argument("--humidity", type=int, help="Target humidity 0-100")
    hm.add_argument("--mode", help="Mode (SMART, FAST, CILENT, IONIZER, ...)")

    sub.add_parser("humidifiers", help="List all humidifiers/dehumidifiers")

    # -- Scene / script / automation / assist / button --
    sc = sub.add_parser("scene", help="Activate scene (fuzzy match)")
    sc.add_argument("scene", help="scene.x or x or substring")

    sr = sub.add_parser("script", help="Run script (fuzzy match)")
    sr.add_argument("script", help="script.x or x or substring")

    au = sub.add_parser("automation", help="Trigger/enable/disable automation")
    au.add_argument("action", choices=["trigger", "turn_on", "turn_off"])
    au.add_argument("automation", help="automation.x or x")

    a = sub.add_parser("assist", help="Natural language via Assist API")
    a.add_argument("text")
    a.add_argument("--language", default="en")

    bt = sub.add_parser("button", help="Press a button entity")
    bt.add_argument("entity_id", help="button.x or x")

    return p


COMMANDS = {
    "info": cmd_info,
    "entities": cmd_entities,
    "search": cmd_search,
    "state": cmd_state,
    "areas": cmd_areas,
    "history": cmd_history,
    "snapshot": cmd_snapshot,
    "weather": cmd_weather,
    "on": cmd_on,
    "off": cmd_off,
    "toggle": cmd_toggle,
    "call": cmd_call,
    "light": cmd_light,
    "lights": cmd_lights,
    "cover": cmd_cover,
    "covers": cmd_covers,
    "lock": cmd_lock,
    "locks": cmd_locks,
    "switches": cmd_switches,
    "media": cmd_media,
    "volume": cmd_volume,
    "players": cmd_players,
    "fan": cmd_fan,
    "fans": cmd_fans,
    "climate": cmd_climate,
    "humidifier": cmd_humidifier,
    "humidifiers": cmd_humidifiers,
    "scene": cmd_scene,
    "script": cmd_script,
    "automation": cmd_automation,
    "assist": cmd_assist,
    "button": cmd_button,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
