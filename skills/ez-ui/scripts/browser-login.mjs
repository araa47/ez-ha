#!/usr/bin/env node
// Log into Home Assistant via Playwright.
// Persists session state so subsequent Playwright calls are already authenticated.
//
// Usage:
//   browser-login                    # uses HA_BROWSER_USER / HA_BROWSER_PASS env vars
//   browser-login <username> <pass>  # explicit credentials
//
// Env vars:
//   HA_BROWSER_URL     — HA base URL (default: http://homeassistant:8123)
//   HA_BROWSER_PROFILE — directory to save session state (default: /data/browser-profile)
//   PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH — path to chromium binary

import { chromium } from "playwright";
import { mkdirSync } from "fs";

const user = process.argv[2] || process.env.HA_BROWSER_USER;
const pass = process.argv[3] || process.env.HA_BROWSER_PASS;

if (!user || !pass) {
    console.error("Usage: browser-login <username> <password>");
    console.error("  Or set HA_BROWSER_USER and HA_BROWSER_PASS env vars.");
    console.error("");
    console.error("Tip: Create a dedicated HA user without 2FA for the agent.");
    process.exit(1);
}

const ha = process.env.HA_BROWSER_URL || "http://homeassistant:8123";
const profile = process.env.HA_BROWSER_PROFILE || "/data/browser-profile";

console.log(`Logging into Home Assistant at ${ha} ...`);

const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
});

try {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto(ha, { waitUntil: "networkidle", timeout: 30000 });

    // Playwright pierces shadow DOM automatically with role selectors
    const usernameField = page.getByRole("textbox", { name: /username/i });
    await usernameField.waitFor({ timeout: 15000 });
    await usernameField.fill(user);

    await page.getByRole("textbox", { name: /password/i }).fill(pass);
    await page.getByRole("button", { name: /log in/i }).click();

    // Wait for navigation away from auth page
    await page.waitForURL((url) => !url.pathname.includes("/auth/"), {
        timeout: 15000,
    });

    console.log(`Login successful! Redirected to: ${page.url()}`);

    // Save browser session state
    mkdirSync(profile, { recursive: true });
    const statePath = `${profile}/state.json`;
    await context.storageState({ path: statePath });
    console.log(`Session saved to ${statePath}`);
} finally {
    await browser.close();
}
