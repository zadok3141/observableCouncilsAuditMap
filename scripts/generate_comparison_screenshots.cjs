#!/usr/bin/env node
/**
 * Generate comparison map screenshots for councils where current and
 * address-geocoded coordinates differ by more than 10m.
 *
 * Reads:  scripts/geocode-comparison.json
 * Writes: scripts/comparison_screenshots/{council-name}.png
 *
 * Usage:
 *   yarn node scripts/generate_comparison_screenshots.cjs
 */

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");

const SCRIPT_DIR = __dirname;
const COMPARISON_JSON = path.join(SCRIPT_DIR, "geocode-comparison.json");
const MAP_HTML = path.join(SCRIPT_DIR, "geocode-comparison-map.html");
const SCREENSHOTS_DIR = path.join(SCRIPT_DIR, "comparison_screenshots");

function sanitizeFilename(name) {
  return name
    .replace(/['']/g, "")
    .replace(/[^a-zA-Z0-9-_ ]/g, "")
    .replace(/\s+/g, "_");
}

async function main() {
  if (!fs.existsSync(COMPARISON_JSON)) {
    console.error("Error: geocode-comparison.json not found.");
    console.error("Run geocode_addresses.py first.");
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(COMPARISON_JSON, "utf-8"));

  // Filter to amber + red + failed-with-current (distance > 10m or no geocoded result)
  const toScreenshot = data.filter(
    (d) => d.status === "amber" || d.status === "red"
  );

  if (toScreenshot.length === 0) {
    console.log("No councils need screenshots (all within 10m).");
    return;
  }

  console.log(
    `Generating screenshots for ${toScreenshot.length} councils...`
  );

  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

  const mapUrl = "file://" + MAP_HTML;

  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  for (let i = 0; i < toScreenshot.length; i++) {
    const d = toScreenshot[i];
    const filename = sanitizeFilename(d.council) + ".png";
    const filepath = path.join(SCREENSHOTS_DIR, filename);

    const params = new URLSearchParams();
    if (d.current) {
      params.set("lat1", d.current.lat);
      params.set("lng1", d.current.lng);
    }
    if (d.address_geocoded) {
      params.set("lat2", d.address_geocoded.lat);
      params.set("lng2", d.address_geocoded.lng);
    }
    params.set("name", d.council);
    if (d.distance_m != null) {
      params.set("dist", Math.round(d.distance_m));
    }

    const page = await browser.newPage();
    await page.setViewport({ width: 600, height: 400 });

    try {
      await page.goto(mapUrl + "?" + params.toString(), {
        waitUntil: "networkidle0",
        timeout: 15000,
      });

      // Wait for map tiles to load
      await page.waitForFunction(
        () => document.body.getAttribute("data-map-ready") === "true",
        { timeout: 10000 }
      );

      // Extra pause for tile rendering
      await new Promise((r) => setTimeout(r, 500));

      await page.screenshot({ path: filepath });
      console.log(
        `  [${i + 1}/${toScreenshot.length}] ${d.council} → ${filename}`
      );
    } catch (err) {
      console.error(
        `  [${i + 1}/${toScreenshot.length}] ${d.council} FAILED: ${err.message}`
      );
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log(`\nDone. Screenshots saved to ${SCREENSHOTS_DIR}/`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
