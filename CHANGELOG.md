# Changelog

## 0.0.6

- **Fix:** `ha` CLI 401 Unauthorized — `SUPERVISOR_TOKEN` only works via the Supervisor proxy, not direct to `http://homeassistant:8123`. Changed `HA_URL` from `http://homeassistant:8123` to `http://supervisor/core` so API calls go through the Supervisor proxy where the token is valid.
- **New:** `browser-login` helper — authenticates agent-browser for HA dashboard access. Session persists in `/data/browser-profile` across restarts via `AGENT_BROWSER_PROFILE` env var.
- **New:** `ha_username` / `ha_password` addon config options for browser auth. Create a dedicated HA user without 2FA for the agent.
- Removed BETA label from the addon

## 0.0.5

- **Fix:** `cc` alias (`claude --dangerously-skip-permissions`) now works as root — set `IS_SANDBOX=1` since the addon container is a sandbox
- **Fix:** Terminal now opens in `/root` (home dir) instead of `/config`
- **Fix:** Claude Code auth (subscription login) now persists across addon restarts — improved `~/.claude` symlink handling to `/data/claude-config`

## 0.0.4

- **Fix:** Use Alpine's `chromium` package instead of Chrome for Testing (glibc) — fixes Docker build failure on Alpine/musl
- Set `AGENT_BROWSER_EXECUTABLE_PATH` and `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` env vars so both tools find chromium automatically
- Chromium + font/rendering deps now baked into the image (no more `install-browser` needed)

## 0.0.3

- **New skill:** `ez-ssh` — teaches agents how to SSH to the HA host, common paths, and host commands
- **New skill:** `ez-ui` — teaches agents how to access the HA web UI and use browser automation
- **New:** `agent-browser` pre-installed for headless browser automation
- **New:** `cc` alias — runs `claude --dangerously-skip-permissions`
- **New:** Auto-generate SSH key pair on first start; logs public key for easy setup with the SSH addon
- Renamed SSH env vars to `HA_SSH_HOST` / `HA_SSH_PORT` / `HA_SSH_USER` to avoid conflicts

## 0.0.2

- Add ExpressVPN support
- Rename addon to ez-ha

## 0.0.1

- Initial release — Home Assistant addon with Claude Code web terminal
