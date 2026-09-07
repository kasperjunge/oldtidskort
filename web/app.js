/* global maplibregl */
const number = new Intl.NumberFormat("da-DK");
const periodNames = { stenalder: "Stenalder", bronzealder: "Bronzealder", jernalder: "Jernalder", vikingetid: "Vikingetid", middelalder: "Middelalder", renaessance: "Renæssance", ukendt: "Oldtid / ukendt" };
const typeNames = { gravhoej: "Gravminde", runesten: "Runesten" };
let data;

function expandCompact(payload) {
  return {
    type: "FeatureCollection",
    features: payload.features.map(row => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: row.slice(0, 2) },
      properties: {
        id: row[2],
        source_id: row[2], site_type: row[3], name: row[4], description: row[5],
        period: row[6], period_raw: row[7], url: row[8], extra: row[9], municipality: row[10],
      },
    })),
  };
}

async function loadData() {
  const staticResponse = await fetch("./data/lokaliteter.json");
  if (staticResponse.ok) return expandCompact(await staticResponse.json());
  const sources = ["../data/processed/fund_og_fortidsminder.geojson", "../data/processed/runesten_lokationer.geojson"];
  const responses = await Promise.all(sources.map(url => fetch(url)));
  if (responses.some(response => !response.ok)) throw new Error("Kortdata blev ikke fundet");
  const payloads = await Promise.all(responses.map(response => response.json()));
  return { type: "FeatureCollection", features: payloads.flatMap(payload => payload.features) };
}

const map = new maplibregl.Map({
  container: "map", center: [10.3, 56.15], zoom: 6.25, minZoom: 5.5, maxZoom: 17,
  style: {
    version: 8,
    sources: { base: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap-bidragsydere" } },
    layers: [{ id: "base", type: "raster", source: "base", paint: { "raster-saturation": -0.86, "raster-contrast": -0.08, "raster-brightness-min": 0.18, "raster-brightness-max": 0.95, "raster-opacity": 0.72 } }],
  },
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

function extra(properties) {
  if (properties.extra && typeof properties.extra === "object") return properties.extra;
  try { return JSON.parse(properties.extra || "{}"); } catch { return {}; }
}

function matchesFilters(feature) {
  const p = feature.properties;
  const type = document.querySelector("#site-type").value;
  const period = document.querySelector("#period").value;
  const protection = document.querySelector("#protection").value;
  const runestoneLocation = document.querySelector("#runestone-location").value;
  return (type === "all" || p.site_type === type) &&
    (period === "all" || p.period === period) &&
    (protection === "all" || p.site_type !== "gravhoej" || p.protected === (protection === "protected")) &&
    (p.site_type !== "runesten" || runestoneLocation === "all" || extra(p).location_role === runestoneLocation);
}

function filter() {
  const features = data.features.filter(matchesFilters);
  map.getSource("sites").setData({ type: "FeatureCollection", features });
  updateCount();
}

function updateCount() {
  if (!map.getSource("sites")) return;
  const bounds = map.getBounds();
  const visible = data.features.filter(feature => bounds.contains(feature.geometry.coordinates) && matchesFilters(feature));
  document.querySelector("#visible-count").textContent = number.format(visible.length);
}

function setDetails(rows) {
  const list = document.querySelector("#detail-fields");
  list.replaceChildren();
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value || "Ikke angivet";
    list.append(term, description);
  }
}

function showDetail(feature) {
  const p = feature.properties;
  const details = extra(p);
  const isRunestone = p.site_type === "runesten";
  document.querySelector("#detail-period").textContent = periodNames[p.period] || p.period_raw || "Ukendt periode";
  document.querySelector("#detail-title").textContent = p.name || details.anlaegsbetegnelse || typeNames[p.site_type] || "Historisk lokalitet";
  setDetails(isRunestone ? [
    ["Type", "Runesten"], ["DR-nr.", details.katalognummer],
    ["Stedtype", ({ earliest_known_location: "Ældst kendte sted", findspot: "Fundsted", original_location: "Oprindeligt sted", current_location: "Nuværende placering" })[details.location_role]],
    ["Sted", details.location_label], ["Sikkerhed", details.confidence],
    ["Metode", details.coordinate_method],
    ["Datastatus", details.review_status === "reviewed" ? "Kilderolle kontrolleret" : "Kræver individuel kontrol"],
    ["Usikkerhed", details.uncertainty_m == null ? null : `ca. ${number.format(details.uncertainty_m)} m`],
    ["Vurdering", details.rationale],
  ] : [
    ["Type", details.anlaegsbetegnelse || p.description || "Gravminde"], ["Datering", p.period_raw],
    ["Status", p.protected ? "Fredet" : "Ikke fredet"], ["Stednr.", details.stednr],
  ]);
  const link = document.querySelector("#detail-link");
  link.href = p.url || (isRunestone ? "https://www.wikidata.org/" : "https://www.kulturarv.dk/fundogfortidsminder/");
  link.textContent = isRunestone ? "Se posten på Wikidata ↗" : "Se i Fund og Fortidsminder ↗";
  document.querySelector("#detail").hidden = false;
}

function addRunestoneIcon(name, color, filled) {
  const size = 32;
  const canvas = document.createElement("canvas");
  canvas.width = size; canvas.height = size;
  const context = canvas.getContext("2d");
  context.translate(size / 2, size / 2); context.rotate(Math.PI / 4);
  context.fillStyle = filled ? color : "#f8f5ed"; context.strokeStyle = color; context.lineWidth = 3;
  context.fillRect(-7, -7, 14, 14); context.strokeRect(-7, -7, 14, 14);
  map.addImage(name, context.getImageData(0, 0, size, size), { pixelRatio: 2 });
}

map.on("load", async () => {
  try {
    data = await loadData();
    for (const feature of data.features) {
      const p = feature.properties;
      p.protected = p.site_type === "gravhoej" ? Boolean(extra(p).fredet) : null;
      p.location_role = extra(p).location_role || null;
    }
    map.addSource("sites", { type: "geojson", data });
    map.addLayer({
      id: "mounds", type: "circle", source: "sites", filter: ["==", ["get", "site_type"], "gravhoej"],
      paint: {
        "circle-color": ["case", ["get", "protected"], "#9c563e", "#b89466"],
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 5.5, .7, 7, 1, 9, 1.8, 12, 4.5, 16, 7],
        "circle-opacity": ["interpolate", ["linear"], ["zoom"], 5.5, .52, 8, .68, 12, .88],
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 0, 12, 1], "circle-stroke-color": "#fff4e6",
      },
    });
    addRunestoneIcon("runestone-history", "#315d69", false);
    addRunestoneIcon("runestone-current", "#315d69", true);
    map.addLayer({
      id: "runestones", type: "symbol", source: "sites", filter: ["==", ["get", "site_type"], "runesten"],
      layout: {
        "icon-image": ["case", ["==", ["get", "location_role"], "current_location"], "runestone-current", "runestone-history"],
        "icon-allow-overlap": true, "icon-size": ["interpolate", ["linear"], ["zoom"], 5.5, .55, 9, .75, 13, 1],
      },
    });
    document.querySelector("#loading").hidden = true;
    document.querySelector("#total-count").textContent = `${number.format(data.features.length)} registreringer i hele Danmark`;
    filter();
  } catch (error) {
    document.querySelector("#loading").hidden = true; document.querySelector("#error").hidden = false; console.error(error);
  }
});

for (const layer of ["mounds", "runestones"]) {
  map.on("click", layer, event => showDetail(event.features[0]));
  map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
}
map.on("moveend", updateCount);
for (const selector of ["#site-type", "#period", "#protection", "#runestone-location"]) document.querySelector(selector).addEventListener("change", filter);
document.querySelector("#detail-close").addEventListener("click", () => { document.querySelector("#detail").hidden = true; });
