// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8941; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles, labels and fonts are blocked here.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs"); fs.mkdirSync("qa", { recursive: true });
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic|openfreemap/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8941) + "/index.html", { waitUntil: "load" });
    for (let k = 0; k < 60 && !(await p.evaluate(() => !!window.map && document.getElementById("loading") === null)); k++) await p.waitForTimeout(500);
    console.log(nm, "map ready:", await p.evaluate(() => !!window.map && document.getElementById("loading") === null));
    await p.waitForTimeout(2000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png`, timeout: 90000 }); };
    const drawn = async (l) => p.evaluate(l => map.queryRenderedFeatures({ layers: [l] }).length, l);
    await shot("#atlas", "map");
    console.log(nm, "stage lines drawn:", await drawn("men"), "towns:", await drawn("towns"), "labels:", await p.evaluate(() => document.querySelectorAll(".tl").length));
    // one Tour, animated
    await p.evaluate(() => setYear(1926)); await p.waitForFunction(() => S.anim === null && S.k === null, null, { timeout: 60000 }); await p.waitForTimeout(500); await shot("#atlas", "map_1926");
    console.log(nm, "1926 yellow segments:", await drawn("sel"), "label:", await p.textContent("#yv"));
    await p.evaluate(() => setYear(2024)); await p.waitForFunction(() => S.anim === null && S.k === null, null, { timeout: 60000 }); await p.waitForTimeout(500); await shot("#atlas", "map_2024");
    // play for a few seconds
    await p.evaluate(() => setYear(null)); await p.click("#play"); await p.waitForTimeout(3000); console.log(nm, "playing, year:", await p.textContent("#yv")); await p.click("#play");
    await p.evaluate(() => setYear(null));
    // heat, women, transfers
    await p.click('#showRow [data-k="heat"]'); await p.waitForTimeout(1200); await shot("#atlas", "heat"); await p.click('#showRow [data-k="heat"]');
    await p.click('#showRow [data-k="women"]'); await p.click('#showRow [data-k="men"]'); await p.waitForTimeout(1000); await shot("#atlas", "women");
    await p.click('#showRow [data-k="men"]'); await p.click('#showRow [data-k="women"]');
    await p.click('#decRow .dec:nth-of-type(3)'); await p.waitForTimeout(800); await shot("#atlas", "decade_1920s"); await p.click('#decRow .btn:last-child');
    // search and popup
    await p.fill("#q", "Alpe"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_alpe");
    console.log(nm, "popup:", (await p.textContent(".maplibregl-popup-content").catch(() => "none")).slice(0, 160));
    await p.fill("#q", "Pau"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_pau");
    // layers panel
    await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(1200);
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.evaluate(() => { const c = document.querySelector('.lyrPanel [data-k="deps"]'); c.checked = true; c.dispatchEvent(new Event("change")); });
    await p.evaluate(() => { const c = document.querySelector('.lyrPanel [data-k="base"]'); c.value = "relief"; c.dispatchEvent(new Event("change")); });
    await p.waitForTimeout(900); await shot("#mapbox", "layers_panel");
    console.log(nm, "layers state:", await p.evaluate(() => JSON.stringify({ base: LY.base, deps: map.getLayoutProperty("depfill", "visibility"), relief: map.getLayoutProperty("relief", "visibility") })));
    await p.click(".lyrPanel .reset"); await p.click(".lyrBtn");
    for (const c of ["loopChart", "distChart", "townTable", "abroadChart", "gdTable", "winChart", "womenTable"]) await shot("#" + c, c);
    if (nm === "phone") { await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#distChart", "dark_dist"); await p.click("#theme"); }
    await p.locator("#mapbox").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500);
    console.log(nm, "fullscreen:", await p.evaluate(() => !!(document.fullscreenElement || document.querySelector(".mfs-fake"))), "map h:", await p.evaluate(() => document.getElementById("map").clientHeight));
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.click(".mfs-btn"); await p.waitForTimeout(500);
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  // graceful degradation: no map library at all
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.route(/arcgisonline|googleapis|gstatic|openfreemap|maplibre/, r => r.abort());
  p.on("pageerror", e => errs.push("nomap pageerror: " + e.message));
  await p.goto("http://localhost:" + (process.env.PORT || 8941) + "/index.html", { waitUntil: "load" }); await p.waitForTimeout(1500);
  await p.locator("#atlas").screenshot({ path: "qa/nomap_fallback.png" });
  console.log("no map library: fallback shown:", await p.evaluate(() => getComputedStyle(document.getElementById("fallback")).display), "charts:", await p.evaluate(() => document.querySelectorAll(".chart svg").length));
  await p.close();
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
