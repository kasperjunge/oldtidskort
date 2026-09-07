/* global maplibregl */
const number = new Intl.NumberFormat("da-DK");
const periodNames = { stenalder: "Stenalder", bronzealder: "Bronzealder", jernalder: "Jernalder", vikingetid: "Vikingetid", middelalder: "Middelalder", renaessance: "1536 og senere", ukendt: "Oldtid / ukendt" };
const typeNames = { gravhoej: "Gravhøj", runesten: "Runesten", bynavn: "Bynavn", kirke: "Kirke" };
const locationRoles = { earliest_known_location: "Ældst kendte sted", findspot: "Fundsted", original_location: "Oprindeligt sted", current_location: "Nuværende placering" };
const confidenceNames = { high: "Veletableret navnelag", medium: "Anerkendt, men usikkert afgrænset", low: "Bruges også i unge navne" };
const confidenceRank = { high: 3, medium: 2, low: 1 };
// Bynavne farves efter periode, så de kan aflæses mod fundenes kronologi.
const periodColors = { jernalder: "#6f5f92", vikingetid: "#a8762a", middelalder: "#4f7a52", ukendt: "#8b8579" };

let data;

/* ---------- lag ---------- */

/** Ét datalag: hvilke features det ejer, hvordan det filtreres, og hvilke
 *  MapLibre-lag det tegner. Panelet har ét kort pr. lag. */
const LAYERS = {
  kirker: { siteType: "kirke", mapLayers: ["churches"], controls: [], matches() { return true; } },
  gravhoeje: {
    siteType: "gravhoej",
    mapLayers: ["mounds"],
    controls: ["#protection"],
    matches(p) {
      const protection = value("#protection");
      return protection === "all" || p.protected === (protection === "protected");
    },
  },
  runesten: {
    siteType: "runesten",
    mapLayers: ["runestones"],
    controls: ["#runestone-location"],
    matches(p) {
      const role = value("#runestone-location");
      return role === "all" || p.location_role === role;
    },
  },
  bynavne: {
    siteType: "bynavn",
    mapLayers: ["placename-dots", "placename-labels"],
    controls: ["#suffix", "#suffix-confidence"],
    matches(p) {
      const suffix = value("#suffix");
      const confidence = value("#suffix-confidence");
      if (suffix === "dated" && !p.suffix_family) return false;
      if (suffix !== "all" && suffix !== "dated" && p.suffix_family !== suffix) return false;
      if (confidence !== "all" && (confidenceRank[p.confidence] || 0) < confidenceRank[confidence]) return false;
      return true;
    },
  },
};

function value(selector) {
  return document.querySelector(selector).value;
}

function enabled(key) {
  return document.querySelector(`#layer-${key}`).checked;
}

function extra(properties) {
  if (properties.extra && typeof properties.extra === "object") return properties.extra;
  try { return JSON.parse(properties.extra || "{}"); } catch { return {}; }
}

/* ---------- data ---------- */

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
  const sources = [
    "../data/processed/fund_og_fortidsminder.geojson",
    "../data/processed/runesten_lokationer.geojson",
    "../data/processed/bynavne_osm.geojson",
    "../data/processed/kirker_osm.geojson",
  ];
  const responses = await Promise.all(sources.map(url => fetch(url)));
  if (!responses.some(response => response.ok)) throw new Error("Kortdata blev ikke fundet");
  const payloads = await Promise.all(responses.filter(response => response.ok).map(response => response.json()));
  return { type: "FeatureCollection", features: payloads.flatMap(payload => payload.features) };
}

/** Flader `extra` ud til de felter filtrene og kortlagene slår op på. */
function prepare(features) {
  for (const feature of features) {
    const p = feature.properties;
    const details = extra(p);
    p.protected = p.site_type === "gravhoej" ? Boolean(details.fredet) : null;
    p.location_role = details.location_role || null;
    p.suffix_family = details.suffix_family || null;
    p.suffix_label = details.suffix_label || null;
    p.confidence = details.confidence || null;
  }
}

/** Endelsesvælgeren bygges af data, så det kuraterede datasæt er eneste facit. */
function fillSuffixOptions(features) {
  const select = document.querySelector("#suffix");
  const labels = new Map();
  for (const feature of features) {
    const p = feature.properties;
    if (p.site_type === "bynavn" && p.suffix_family) labels.set(p.suffix_family, p.suffix_label);
  }
  for (const [family, label] of [...labels].sort((a, b) => a[1].localeCompare(b[1], "da"))) {
    const option = document.createElement("option");
    option.value = family;
    option.textContent = label;
    select.append(option);
  }
}

/* ---------- kort ---------- */

const map = new maplibregl.Map({
  container: "map", center: [10.3, 56.15], zoom: 6.25, minZoom: 5.5, maxZoom: 17,
  style: {
    version: 8,
    glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
    sources: { base: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap-bidragsydere" } },
    layers: [{ id: "base", type: "raster", source: "base", paint: { "raster-saturation": -0.86, "raster-contrast": -0.08, "raster-brightness-min": 0.18, "raster-brightness-max": 0.95, "raster-opacity": 0.72 } }],
  },
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

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

const periodColor = ["match", ["get", "period"], ...Object.entries(periodColors).flat(), periodColors.ukendt];

function addLayers() {
  for (const key of Object.keys(LAYERS)) {
    map.addSource(key, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  }

  map.addLayer({
    id: "mounds", type: "circle", source: "gravhoeje",
    paint: {
      "circle-color": ["case", ["get", "protected"], "#9c563e", "#b89466"],
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5.5, .7, 7, 1, 9, 1.8, 12, 4.5, 16, 7],
      "circle-opacity": ["interpolate", ["linear"], ["zoom"], 5.5, .52, 8, .68, 12, .88],
      "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 0, 12, 1], "circle-stroke-color": "#fff4e6",
    },
  });

  // Bynavne under fundene: de er kontekst, ikke registreringer.
  map.addLayer({
    id: "placename-dots", type: "circle", source: "bynavne",
    paint: {
      "circle-color": periodColor,
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5.5, 1.6, 9, 2.6, 13, 4],
      "circle-opacity": .85,
      "circle-stroke-width": 1, "circle-stroke-color": "#f8f5ed",
    },
  }, "mounds");

  map.addLayer({
    id: "placename-labels", type: "symbol", source: "bynavne", minzoom: 8,
    layout: {
      "text-field": ["get", "name"],
      "text-font": ["Noto Sans Regular"],
      "text-size": ["interpolate", ["linear"], ["zoom"], 8, 10, 13, 13],
      "text-offset": [0, 0.9], "text-anchor": "top", "text-padding": 4,
    },
    paint: { "text-color": periodColor, "text-halo-color": "#f8f5ed", "text-halo-width": 1.4 },
  });

  addRunestoneIcon("runestone-history", "#315d69", false);
  addRunestoneIcon("runestone-current", "#315d69", true);
  map.addLayer({
    id: "runestones", type: "symbol", source: "runesten",
    layout: {
      "icon-image": ["case", ["==", ["get", "location_role"], "current_location"], "runestone-current", "runestone-history"],
      "icon-allow-overlap": true, "icon-size": ["interpolate", ["linear"], ["zoom"], 5.5, .55, 9, .75, 13, 1],
    },
  });
  map.addLayer({
    id: "churches", type: "circle", source: "kirker",
    paint: {
      "circle-color": "#75608a", "circle-stroke-color": "#faf8f2", "circle-stroke-width": 1.5,
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5.5, 2.5, 10, 4, 15, 7],
    },
  });
}

/* ---------- filtrering ---------- */

function matching(key) {
  const layer = LAYERS[key];
  if (!enabled(key)) return [];
  const period = value(`#period-${key}`);
  return data.features.filter(feature => {
    const p = feature.properties;
    return p.site_type === layer.siteType &&
      (period === "all" || p.period === period) &&
      layer.matches(p);
  });
}

function filter() {
  let total = 0;
  const bounds = map.getBounds();
  for (const key of Object.keys(LAYERS)) {
    const features = matching(key);
    map.getSource(key).setData({ type: "FeatureCollection", features });
    const visible = features.filter(feature => bounds.contains(feature.geometry.coordinates));
    document.querySelector(`#count-${key}`).textContent = number.format(visible.length);
    const tab = document.querySelector(`#tab-${key}`);
    tab.classList.toggle("enabled", enabled(key));
    tab.querySelector(".tab-status").textContent = enabled(key) ? "Til" : "Fra";
    total += visible.length;
  }
  document.querySelector("#visible-count").textContent = number.format(total);
}

/** Panorering ændrer kun tællerne, ikke hvilke features der er tegnet. */
function updateCounts() {
  if (!map.getSource("gravhoeje")) return;
  const bounds = map.getBounds();
  let total = 0;
  for (const key of Object.keys(LAYERS)) {
    const visible = matching(key).filter(feature => bounds.contains(feature.geometry.coordinates));
    document.querySelector(`#count-${key}`).textContent = number.format(visible.length);
    total += visible.length;
  }
  document.querySelector("#visible-count").textContent = number.format(total);
}

/* ---------- detaljer ---------- */

function setDetails(rows) {
  const list = document.querySelector("#detail-fields");
  list.replaceChildren();
  for (const [label, val] of rows) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = val || "Ikke angivet";
    list.append(term, description);
  }
}

function detailRows(p, details) {
  if (p.site_type === "kirke") {
    return [["Type", "Kirke / kapel"], ["Datering", p.period_raw], ["Trossamfund", details.denomination], ["Kilde", "OpenStreetMap"]];
  }
  if (p.site_type === "runesten") {
    return [
      ["Type", "Runesten"], ["DR-nr.", details.katalognummer],
      ["Stedtype", locationRoles[details.location_role]],
      ["Sted", details.location_label], ["Sikkerhed", details.confidence],
      ["Metode", details.coordinate_method],
      ["Datastatus", details.review_status === "reviewed" ? "Kilderolle kontrolleret" : "Kræver individuel kontrol"],
      ["Usikkerhed", details.uncertainty_m == null ? null : `ca. ${number.format(details.uncertainty_m)} m`],
      ["Vurdering", details.rationale],
    ];
  }
  if (p.site_type === "bynavn") {
    return [
      ["Endelse", details.suffix_label ? `${details.suffix_label} (-${details.suffix})` : "Ingen dateret endelse"],
      ["Betydning", details.gloss],
      ["Navnelag", details.suffix_label ? periodNames[p.period] : null],
      ["Datering", details.suffix_label ? aarstal(p) : null],
      ["Sikkerhed", confidenceNames[details.confidence]],
      ["Bebyggelse", ({ city: "By", town: "Købstad / større by", village: "Landsby", hamlet: "Lille bebyggelse", suburb: "Bydel" })[details.place_rank]],
      ["Indbyggere", details.population == null ? null : number.format(details.population)],
      ["Forbehold", "Endelsen daterer navnetypen, ikke nødvendigvis bebyggelsen."],
    ];
  }
  return [
    ["Type", details.anlaegsbetegnelse || p.description || "Gravhøj"], ["Datering", p.period_raw],
    ["Status", p.protected ? "Fredet" : "Ikke fredet"], ["Stednr.", details.stednr],
  ];
}

function aarstal(p) {
  const from = p.year_from ?? null;
  const to = p.year_to ?? null;
  if (from == null && to == null) return null;
  return `ca. ${from ?? "?"}–${to ?? "?"} e.Kr.`;
}

function showDetail(feature) {
  const p = feature.properties;
  const details = extra(p);
  const links = {
    runesten: ["Se posten på Wikidata ↗", "https://www.wikidata.org/"],
    bynavn: ["Se stedet i OpenStreetMap ↗", "https://www.openstreetmap.org/"],
    gravhoej: ["Se i Fund og Fortidsminder ↗", "https://www.kulturarv.dk/fundogfortidsminder/"],
  }[p.site_type] || ["Se kilden ↗", "https://www.openstreetmap.org/"];

  document.querySelector("#detail-period").textContent =
    p.site_type === "bynavn" && !details.suffix_label ? "Udateret navn" : periodNames[p.period] || p.period_raw || "Ukendt periode";
  document.querySelector("#detail-title").textContent = p.name || details.anlaegsbetegnelse || typeNames[p.site_type] || "Historisk lokalitet";
  setDetails(detailRows(p, details));
  const link = document.querySelector("#detail-link");
  link.href = p.url || links[1];
  link.textContent = links[0];
  document.querySelector("#detail").hidden = false;
}

/* ---------- opstart ---------- */

map.on("load", async () => {
  try {
    data = await loadData();
    prepare(data.features);
    fillSuffixOptions(data.features);
    addLayers();

    for (const key of Object.keys(LAYERS)) {
      for (const mapLayer of LAYERS[key].mapLayers) {
        map.on("click", mapLayer, event => showDetail(event.features[0]));
        map.on("mouseenter", mapLayer, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", mapLayer, () => { map.getCanvas().style.cursor = ""; });
      }
      document.querySelector(`#layer-${key}`).addEventListener("change", filter);
      for (const control of [...LAYERS[key].controls, `#period-${key}`]) document.querySelector(control).addEventListener("change", filter);
    }


    document.querySelector("#loading").hidden = true;
    document.querySelector("#total-count").textContent = `${number.format(data.features.length)} registreringer i hele Danmark`;
    filter();
  } catch (error) {
    document.querySelector("#loading").hidden = true; document.querySelector("#error").hidden = false; console.error(error);
  }
});

map.on("moveend", updateCounts);
document.querySelector("#detail-close").addEventListener("click", () => { document.querySelector("#detail").hidden = true; });

// Fanens fokus og datalagets synlighed er uafhængige.
const tabs = [...document.querySelectorAll('[role="tab"]')];
function selectTab(tab) {
  for (const item of tabs) {
    const selected = item === tab;
    item.setAttribute("aria-selected", String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute("aria-controls")).hidden = !selected;
  }
}
for (const [index, tab] of tabs.entries()) {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", event => {
    const next = { ArrowRight: (index + 1) % tabs.length, ArrowLeft: (index + tabs.length - 1) % tabs.length, Home: 0, End: tabs.length - 1 }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    selectTab(tabs[next]);
    tabs[next].focus();
  });
}
