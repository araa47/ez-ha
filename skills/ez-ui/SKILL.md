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

For browser-based access, run `browser-login` (see `scripts/browser-login.mjs`) to authenticate the browser session:

```bash
browser-login                   # Uses HA_BROWSER_USER / HA_BROWSER_PASS from addon config
browser-login <user> <pass>     # Or pass credentials explicitly
```

The session is persisted in `/data/browser-profile/state.json` and can be loaded by Playwright:

```js
const context = await browser.newContext({
    storageState: "/data/browser-profile/state.json"
});
```

> **Tip:** Create a dedicated HA user without 2FA for the agent.

## Browser testing with Playwright

`browser-login` uses Playwright under the hood. Playwright pierces shadow DOM automatically via role-based selectors, which is far more reliable than manual shadow DOM traversal.

```bash
# Take a screenshot of a dashboard
npx playwright screenshot http://homeassistant:8123/lovelace/0 dashboard.png

# Use Playwright in a Node.js script
node -e '
const { chromium } = require("playwright");
(async () => {
    const browser = await chromium.launch({
        executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
        headless: true, args: ["--no-sandbox"]
    });
    const context = await browser.newContext({
        storageState: "/data/browser-profile/state.json"
    });
    const page = await context.newPage();
    await page.goto("http://homeassistant:8123/lovelace/0");
    await page.screenshot({ path: "dashboard.png" });
    await browser.close();
})();
'
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
