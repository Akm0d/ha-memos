import assert from "node:assert/strict";
import { chromium } from "playwright";

const prefix = "/api/hassio_ingress/ci_session";
const origin = "http://127.0.0.1:19899";
const errors = [];
const failedAssets = [];
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  page.on("pageerror", error => errors.push(error.message));
  page.on("response", response => {
    const path = new URL(response.url()).pathname;
    if (response.status() >= 400 && (path.includes("/assets/") || path.includes("/api/"))) {
      // Memos may legitimately return 401 for unauthenticated API calls.
      if (response.status() !== 401 && response.status() !== 403) {
        failedAssets.push(response.status() + " " + path);
      }
    }
  });

  await page.goto(origin + prefix + "/", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForFunction(
    () => document.querySelector("#root")?.childElementCount > 0,
    undefined,
    { timeout: 25000 },
  );
  await page.waitForTimeout(1500);

  const first = await page.evaluate(() => ({
    base: window.__MEMOS_INGRESS_BASE__,
    url: location.pathname,
    body: document.body.innerText.trim(),
    script: document.querySelector('script[type="module"]')?.src ?? "",
  }));
  assert.equal(first.base, prefix, "missing ingress bootstrap");
  assert.ok(first.url.startsWith(prefix), "SPA escaped Home Assistant ingress");
  assert.ok(first.body.length >= 8, "Memos SPA rendered a white/empty page");
  assert.ok(first.script.includes(prefix + "/assets/"), "module script did not use ingress base");

  // A nested URL must still resolve frontend assets and render the SPA.
  await page.goto(origin + prefix + "/auth/signup", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForFunction(
    () => document.querySelector("#root")?.childElementCount > 0,
    undefined,
    { timeout: 25000 },
  );
  await page.waitForTimeout(1000);

  assert.deepEqual(errors, [], "browser JavaScript crashed");
  assert.deepEqual(failedAssets, [], "assets or API escaped the ingress path");

  console.log("Memos browser ingress rendered successfully:", first.body.slice(0, 180));
} finally {
  await browser.close();
}
