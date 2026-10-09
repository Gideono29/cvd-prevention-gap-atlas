"use strict";

const DARK = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
const NODATA = DARK ? "#3a4148" : "#c9ced4";
const TRACT_MINZOOM = 6.5;

const METRICS = {
  gap_national: { label: "Gap (national)", diverging: true },
  gap_stratum: { label: "Gap (within group)", diverging: true },
  gap_no_hpsa: { label: "Gap without HPSA", diverging: true, countyOnly: true },
  burden: { label: "Burden percentile", diverging: false },
  capacity: { label: "Capacity percentile", diverging: false },
  svi: { label: "SVI", diverging: false, svi: true },
};
// SVI is stored on 0..1 and scaled to 0..100 for colouring. Diverging (blue = capacity ahead of burden, red = burden ahead of capacity) and sequential ramps
const DIV = [[-100, "#2b6cb0"], [-50, "#90b8e0"], [0, DARK ? "#2a2f35" : "#f2f2f2"], [50, "#f0a58c"], [100, "#c0392b"]];
const SEQ = [[0, DARK ? "#2a2f35" : "#f4eedf"], [50, "#e9a95b"], [100, "#7a2e0e"]];

let metric = "gap_national";
const loaded = new Set();
let states = {};
let activePopup = null;

function ramp(m) {
  return { stops: METRICS[m].diverging ? DIV : SEQ };
}

function colorExpr(m) {
  const { stops } = ramp(m);
  const v = ["to-number", ["get", m], -9999];
  const interp = ["interpolate", ["linear"], m === "svi" ? ["*", v, 100] : v];
  stops.forEach(([x, c]) => interp.push(x, c));
  return ["case", ["any", ["!", ["has", m]], ["==", ["get", m], null]], NODATA, interp];
}

function legend() {
  const { stops } = ramp(metric);
  const grad = stops.map(([x, c], i) => `${c} ${(i / (stops.length - 1)) * 100}%`).join(",");
  const cfg = METRICS[metric];
  const lo = cfg.diverging ? "Capacity ahead (-100)" : "Low (0)";
  const hi = cfg.diverging ? "Burden ahead (+100)" : "High (100)";
  document.getElementById("legend").innerHTML =
    `<div class="bar" style="background:linear-gradient(90deg,${grad})"></div>` +
    `<div class="ticks"><span>${lo}</span><span>${hi}</span></div>` +
    `<div class="nodata"><i></i> No data</div>`;
}

const map = new maplibregl.Map({
  container: "map",
  style: { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": DARK ? "#14171a" : "#f6f7f9" } }] },
  bounds: [[-125, 24], [-66, 50]],
  fitBoundsOptions: { padding: { left: 340, top: 20, right: 20, bottom: 20 } },
  maxZoom: 12,
  attributionControl: { customAttribution: "CDC PLACES 2025, CDC/ATSDR SVI 2022, HRSA, USDA ERS RUCA 2020, Census cartographic boundaries" },
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

function setStatus(t) { document.getElementById("status").textContent = t; }

function paint() {
  const expr = colorExpr(metric);
  if (map.getLayer("counties")) map.setPaintProperty("counties", "fill-color", expr);
  loaded.forEach((st) => map.setPaintProperty(`t-${st}`, "fill-color", expr));
  legend();
  const co = METRICS[metric].countyOnly;
  setStatus(co ? "County view only: HPSA data are not available for tracts." : "");
  const tractOpacity = co ? 0 : 1;
  loaded.forEach((st) => {
    map.setPaintProperty(`t-${st}`, "fill-opacity", tractOpacity);
    map.setPaintProperty(`t-${st}-line`, "line-opacity", tractOpacity * 0.8);
  });
  map.setPaintProperty("counties", "fill-opacity", ["interpolate", ["linear"], ["zoom"], TRACT_MINZOOM, 1, TRACT_MINZOOM + 1, co ? 1 : 0.15]);
}

function topFilter(on) {
  const w = on ? 1.4 : 0;
  if (map.getLayer("counties-top")) map.setPaintProperty("counties-top", "line-width", w);
  loaded.forEach((st) => map.setPaintProperty(`t-${st}-top`, "line-width", w));
}

function loadTractState(st) {
  if (loaded.has(st)) return;
  loaded.add(st);
  map.addSource(`t-${st}`, { type: "geojson", data: `data/tracts/${st}.geojson` });
  map.addLayer({ id: `t-${st}`, type: "fill", source: `t-${st}`, minzoom: TRACT_MINZOOM - 0.5,
    paint: { "fill-color": colorExpr(metric), "fill-opacity": METRICS[metric].countyOnly ? 0 : 1, "fill-outline-color": "rgba(0,0,0,0)" } });
  map.addLayer({ id: `t-${st}-line`, type: "line", source: `t-${st}`, minzoom: 8.5,
    paint: { "line-color": DARK ? "#14171a" : "#ffffff", "line-width": 0.5,
      "line-opacity": METRICS[metric].countyOnly ? 0 : 0.8 } });
  map.addLayer({ id: `t-${st}-top`, type: "line", source: `t-${st}`, minzoom: TRACT_MINZOOM - 0.5,
    filter: ["==", ["get", "top_decile_gap"], 1],
    paint: { "line-color": "#111", "line-width": document.getElementById("top").checked ? 1.2 : 0 } });
}

function updateTracts() {
  if (map.getZoom() < TRACT_MINZOOM - 0.5) return;
  const b = map.getBounds();
  for (const [st, [w, s, e, n]] of Object.entries(states)) {
    if (e >= b.getWest() && w <= b.getEast() && n >= b.getSouth() && s <= b.getNorth()) loadTractState(st);
  }
}

function fmt(v, d = 0) { return v === null || v === undefined ? "n/a" : Number(v).toFixed(d); }

function popup(e) {
  const f = e.features && e.features[0];
  if (!f) return;
  const p = f.properties;
  const isTract = f.layer.id.startsWith("t-");
  const title = isTract ? `Tract ${p.fips}` : `${p.NAME}, ${p.STUSPS}`;
  const rows = [["Gap (national)", fmt(p.gap_national)], ["Gap (within group)", fmt(p.gap_stratum)]];
  if (!isTract) rows.push(["Gap without HPSA", fmt(p.gap_no_hpsa)]);
  rows.push(["Burden pct.", fmt(p.burden)], ["Capacity pct.", fmt(p.capacity)],
    ["SVI (0-1)", fmt(p.svi, 2)]);
  if (!isTract) rows.push(["HPSA score", fmt(p.hpsa_score)]);
  rows.push(["Rural-urban group", p.stratum || "n/a"]);
  const html = `<div class="pop"><b>${title}</b><table>${rows.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join("")}</table></div>`;
  if (activePopup) activePopup.remove();
  activePopup = new maplibregl.Popup({ closeButton: false, maxWidth: "260px" }).setLngLat(e.lngLat).setHTML(html).addTo(map);
}

map.on("load", async () => {
  states = await (await fetch("data/states.json")).json();
  map.addSource("counties", { type: "geojson", data: "data/counties.geojson" });
  map.addLayer({ id: "counties", type: "fill", source: "counties",
    paint: { "fill-color": colorExpr(metric), "fill-outline-color": DARK ? "#14171a" : "#ffffff" } });
  map.addLayer({ id: "counties-top", type: "line", source: "counties",
    filter: ["==", ["get", "top_decile_gap"], 1], paint: { "line-color": "#111", "line-width": 0 } });
  legend();
  paint();
  map.on("moveend", updateTracts);
  map.on("click", (e) => {
    const ids = [...loaded].map((s) => `t-${s}`).filter((id) => map.getLayer(id) && map.getPaintProperty(id, "fill-opacity") !== 0);
    const hit = map.queryRenderedFeatures(e.point, { layers: [...ids, "counties"] });
    popup({ features: hit, lngLat: e.lngLat });
  });
  map.on("mousemove", () => { map.getCanvas().style.cursor = "pointer"; });
});

document.getElementById("metric").addEventListener("change", (e) => { metric = e.target.value; paint(); });
document.getElementById("top").addEventListener("change", (e) => topFilter(e.target.checked));
