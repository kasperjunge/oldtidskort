/* global maplibregl */
const number = new Intl.NumberFormat("da-DK");
const periodNames = { stenalder: "Stenalder", bronzealder: "Bronzealder", jernalder: "Jernalder", vikingetid: "Vikingetid", ukendt: "Oldtid / ukendt" };
let data;

async function loadData() {
  const candidates = [
    "./data/gravhoeje.json",
    "../data/processed/fund_og_fortidsminder.geojson",
  ];
  for (const url of candidates) {
    const response = await fetch(url);
    if (!response.ok) continue;
    const payload = await response.json();
    if (payload.format === "oldtidskort-v1") {
      return {
        type: "FeatureCollection",
        features: payload.features.map(row => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: row.slice(0, 2) },
          properties: {
            id: `fund_og_fortidsminder:${row[2]}`,
            name: null,
            description: row[3],
            period: row[4],
            period_raw: row[5],
            url: `https://www.kulturarv.dk/fundogfortidsminder/Lokalitet/${row[2]}`,
            extra: { anlaegsbetegnelse: row[3], fredet: row[6], stednr: row[7] },
          },
        })),
      };
    }
    return payload;
  }
  throw new Error("Gravhøjsdata blev ikke fundet");
}

const map = new maplibregl.Map({
  container: "map",
  center: [10.3, 56.15],
  zoom: 6.25,
  minZoom: 5.5,
  maxZoom: 17,
  style: {
    version: 8,
    sources: { base: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap-bidragsydere" } },
    layers: [{ id: "base", type: "raster", source: "base", paint: { "raster-saturation": -0.86, "raster-contrast": -0.08, "raster-brightness-min": 0.18, "raster-brightness-max": 0.95, "raster-opacity": 0.72 } }]
  }
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

function extra(properties) {
  if (properties.extra && typeof properties.extra === "object") return properties.extra;
  try { return JSON.parse(properties.extra || "{}"); } catch { return {}; }
}

function filter() {
  const period = document.querySelector("#period").value;
  const protection = document.querySelector("#protection").value;
  const features = data.features.filter(feature => {
    const p = feature.properties;
    return (period === "all" || p.period === period) &&
      (protection === "all" || p.protected === (protection === "protected"));
  });
  map.getSource("mounds").setData({ type: "FeatureCollection", features });
  updateCount();
}

function updateCount() {
  if (!map.getLayer("mounds")) return;
  const bounds = map.getBounds();
  const period = document.querySelector("#period").value;
  const protection = document.querySelector("#protection").value;
  const visible = data.features.filter(feature => {
    const [lon, lat] = feature.geometry.coordinates;
    const p = feature.properties;
    return bounds.contains([lon, lat]) &&
      (period === "all" || p.period === period) &&
      (protection === "all" || p.protected === (protection === "protected"));
  });
  document.querySelector("#visible-count").textContent = number.format(visible.length);
}

function showDetail(feature) {
  const p = feature.properties;
  const details = extra(p);
  document.querySelector("#detail-period").textContent = periodNames[p.period] || p.period_raw || "Ukendt periode";
  document.querySelector("#detail-title").textContent = p.name || details.anlaegsbetegnelse || "Gravhøj";
  document.querySelector("#detail-fields").innerHTML = `
    <dt>Type</dt><dd>${details.anlaegsbetegnelse || p.description || "Gravminde"}</dd>
    <dt>Datering</dt><dd>${p.period_raw || "Ikke angivet"}</dd>
    <dt>Status</dt><dd>${p.protected ? "Fredet" : "Ikke fredet"}</dd>
    <dt>Stednr.</dt><dd>${details.stednr || "Ikke angivet"}</dd>`;
  const link = document.querySelector("#detail-link");
  link.href = p.url || "https://www.kulturarv.dk/fundogfortidsminder/";
  document.querySelector("#detail").hidden = false;
}

map.on("load", async () => {
  try {
    data = await loadData();
    for (const feature of data.features) {
      feature.properties.protected = Boolean(extra(feature.properties).fredet);
    }
    map.addSource("mounds", { type: "geojson", data, cluster: true, clusterRadius: 35, clusterMaxZoom: 10 });
    map.addLayer({ id: "clusters", type: "circle", source: "mounds", filter: ["has", "point_count"], paint: { "circle-color": ["step", ["get", "point_count"], "#78866d", 100, "#607257", 1000, "#41533f"], "circle-radius": ["step", ["get", "point_count"], 14, 100, 18, 1000, 24], "circle-stroke-width": 1, "circle-stroke-color": "#f2efe7" } });
    map.addLayer({ id: "cluster-count", type: "symbol", source: "mounds", filter: ["has", "point_count"], layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 10 }, paint: { "text-color": "#fff" } });
    map.addLayer({ id: "mounds", type: "circle", source: "mounds", filter: ["!", ["has", "point_count"]], paint: { "circle-color": ["case", ["get", "protected"], "#9c563e", "#b89466"], "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 2.2, 12, 5], "circle-opacity": .88, "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 7, 0, 12, 1], "circle-stroke-color": "#fff4e6" } });
    document.querySelector("#loading").hidden = true;
    document.querySelector("#total-count").textContent = `${number.format(data.features.length)} registreringer i hele Danmark`;
    updateCount();
  } catch (error) {
    document.querySelector("#loading").hidden = true;
    document.querySelector("#error").hidden = false;
    console.error(error);
  }
});

map.on("click", "clusters", async event => {
  const feature = map.queryRenderedFeatures(event.point, { layers: ["clusters"] })[0];
  const zoom = await map.getSource("mounds").getClusterExpansionZoom(feature.properties.cluster_id);
  map.easeTo({ center: feature.geometry.coordinates, zoom });
});
map.on("click", "mounds", event => showDetail(event.features[0]));
for (const layer of ["clusters", "mounds"]) {
  map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
}
map.on("moveend", updateCount);
document.querySelector("#period").addEventListener("change", filter);
document.querySelector("#protection").addEventListener("change", filter);
document.querySelector("#detail-close").addEventListener("click", () => { document.querySelector("#detail").hidden = true; });
