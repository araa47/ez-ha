# ez-ha

**Home Assistant, meet your AI agent.**

`ez-ha` is two things in one repo:

1. **An agent skill** — gives any AI agent (OpenClaw, Claude, Codex, Cursor, ...) the ability to query and control your Home Assistant instance

2. **A Home Assistant addon** — runs a full AI coding agent inside HAOS with file access, shell, and a browser to view and validate your dashboards end-to-end

---

## Part 1 — Add the HA Skill to Your Agent

Give your agent the ability to talk to Home Assistant — query entities, call services, check automations, and debug issues.

```bash
npx skills add araa47/ez-ha
```

Your agent can now:
- Query entity states and attributes
- Call services and control devices
- List automations, areas, and devices
- Check logs and history
- Render and test Jinja2 templates

> **Requires:** A running Home Assistant instance with a long-lived access token. Set `HA_URL` and `HA_TOKEN` in your environment.

---

## Part 2 — Coming Soon: The ez-ha Home Assistant Addon

A Home Assistant addon that runs an AI coding agent directly inside your HAOS instance — with full system access, shell, and a headless browser to verify changes visually.

### What it does

- Runs **Claude Code** in your HA sidebar (Codex and Cursor support coming)
- Full read/write access to your HA config files via shell
- Headless **Playwright browser** — the agent can open your dashboards and verify things actually look right
- Config changes recommended to be **git-backed** (the agent will commit after edits)
- Persistent sessions via tmux — navigate away, come back, still running

### Install

1. Go to **Settings → Add-ons → Add-on Store**
2. Click ⋮ → **Repositories** → add:
   ```
   https://github.com/araa47/ez-ha
   ```
3. Find **ez-ha** in the store and install
4. Set some variables in the Configuration tab
5. Start the addon → open from the sidebar

### What the agent can do

- Edit `automations.yaml`, `scripts.yaml`, `configuration.yaml`, custom components
- Reload or restart HA after changes
- Open a real browser and navigate to your dashboard to visually verify changes
- Debug why an automation isn't triggering
- Write and test new integrations end-to-end



-
