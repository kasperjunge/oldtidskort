#!/usr/bin/env python3
"""Build the committed GitHub Pages site locally from processed data."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "data" / "processed" / "fund_og_fortidsminder.geojson",
    ROOT / "data" / "processed" / "runesten_lokationer.geojson",
    ROOT / "data" / "processed" / "bynavne_osm.geojson",
    ROOT / "data" / "processed" / "kirker_osm.geojson",
)
WEB = ROOT / "web"
DATA_URL = "./data/lokaliteter.json"
SITE_URL = "https://kasperjunge.github.io/oldtidskort/"
PAGES = ROOT / ".pages-dist"


def compact_feature(feature: dict) -> list:
    props = feature["properties"]
    details = props.get("extra") or {}
    if isinstance(details, str):
        details = json.loads(details)
    record_id = props["id"]
    return [
        *[round(value, 6) for value in feature["geometry"]["coordinates"][:2]],
        record_id,
        props.get("site_type"),
        props.get("name"),
        details.get("anlaegsbetegnelse") or props.get("description"),
        props.get("period", "ukendt"),
        props.get("period_raw"),
        props.get("url"),
        details,
        props.get("municipality"),
    ]


def build(sources: tuple[Path, ...] = SOURCES, destination: Path = PAGES) -> tuple[int, Path]:
    missing = [source for source in sources if not source.exists()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise SystemExit(
            f"Mangler {names}. Kør først: uv run oldtidskort build fund_og_fortidsminder "
            "&& uv run oldtidskort build bynavne_osm "
            "&& uv run oldtidskort build kirker_osm "
            "&& uv run python scripts/build_runestone_research.py"
        )

    features = []
    for source in sources:
        payload = json.loads(source.read_text(encoding="utf-8"))
        features.extend(compact_feature(feature) for feature in payload["features"])

    payload = json.dumps(
        {"format": "oldtidskort-v2", "features": features},
        ensure_ascii=False,
        separators=(",", ":"),
    )

    index_html = (WEB / "index.html").read_text(encoding="utf-8")
    style_css = (WEB / "style.css").read_text(encoding="utf-8")
    app_js = (WEB / "app.js").read_text(encoding="utf-8")

    # index.html, app.js og datafilen skal skifte i takt. Uden en version i
    # URL'en kan en browser genbruge en cachet app.js sammen med en ny
    # index.html — så tegner kortet, men panelets elementer er skiftet ud, og
    # scriptet fejler. Stemplet ændrer sig, når som helst en af delene ændrer sig.
    stamp = hashlib.sha256(
        f"{payload}{index_html}{style_css}{app_js}".encode()
    ).hexdigest()[:10]
    app_js = app_js.replace(DATA_URL, f"{DATA_URL}?v={stamp}")
    index_html = index_html.replace("./style.css", f"./style.css?v={stamp}")
    index_html = index_html.replace("./app.js", f"./app.js?v={stamp}")

    if destination.exists():
        shutil.rmtree(destination)
    (destination / "data").mkdir(parents=True)
    (destination / "index.html").write_text(index_html, encoding="utf-8")
    (destination / "style.css").write_text(style_css, encoding="utf-8")
    (destination / "app.js").write_text(app_js, encoding="utf-8")
    (destination / ".nojekyll").touch()
    shutil.copyfile(WEB / "og.jpg", destination / "og.jpg")

    # Sitet er én side, så robots.txt og sitemap.xml kan skrives direkte her
    # frem for at ligge som statiske filer, der skal holdes i sync i hånden.
    (destination / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8"
    )
    (destination / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}</loc>"
        f"<lastmod>{datetime.now(UTC).date().isoformat()}</lastmod>"
        "<changefreq>monthly</changefreq></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )

    # Selve filnavnet holdes uændret; deploy-scriptet verificerer denne sti.
    target = destination / "data" / "lokaliteter.json"
    target.write_text(payload, encoding="utf-8")
    return len(features), target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", dest="sources")
    parser.add_argument("--destination", type=Path, default=PAGES)
    args = parser.parse_args()
    count, target = build(tuple(args.sources) if args.sources else SOURCES, args.destination)
    print(f"Byggede {count:,} punkter → {target.relative_to(ROOT)} ({target.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
