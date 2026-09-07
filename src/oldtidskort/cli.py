from __future__ import annotations

import functools
import http.server
import webbrowser
from pathlib import Path

import typer
from rich.console import Console

from .core.http import client
from .core.io import PROCESSED_DIR, RAW_DIR
from .core.wfs import capabilities
from .pipeline import build, build_all
from .research.runestones import (
    build_dataset as build_runestone_research,
)
from .research.runestones import (
    fetch as fetch_runestone_research,
)
from .research.runestones import (
    fetch_runor,
    write_location_geojson,
)
from .research.runestones import (
    validate_foreign_keys as validate_runestone_research,
)
from .research.runestones import (
    write_dataset as write_runestone_research,
)
from .sources import REGISTRY

app = typer.Typer(help="Byg danske historiske datasæt til kortvisualisering.", no_args_is_help=True)
console = Console()
PROJECT_DIR = Path(__file__).resolve().parents[2]
CURATED_RUNESTONES = PROJECT_DIR / "data" / "curated" / "runestones"


@app.command("list")
def list_sources() -> None:
    """Vis tilgængelige datakilder."""
    for name, source in REGISTRY.items():
        console.print(f"[bold]{name}[/bold]\n  licens: {source.license}\n  kilde:  {source.homepage}")


@app.command("build")
def build_command(
    source: str = typer.Argument(..., help="Kildenavn, eller 'all' for alle + samlet datasæt"),
    refresh: bool = typer.Option(False, "--refresh", help="Hent kildedata på ny."),
) -> None:
    """Hent, normalisér og skriv datasæt til data/processed/."""
    if source == "all":
        reports, paths = build_all(RAW_DIR, PROCESSED_DIR, refresh=refresh)
        for report in reports:
            console.print(report.summary())
        for path in paths:
            console.print(f"skrev {path}")
        return
    if source not in REGISTRY:
        raise typer.BadParameter(f"ukendt kilde: {source}. Se 'oldtidskort list'.")
    report = build(source, RAW_DIR, PROCESSED_DIR, refresh=refresh)
    console.print(report.summary())
    for path in report.paths:
        console.print(f"skrev {path}")


@app.command("map")
def map_command(
    port: int = typer.Option(8000, min=1, max=65535, help="Lokal port til kortet."),
    refresh: bool = typer.Option(False, "--refresh", help="Hent og byg kildedata på ny."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Åbn kortet i browseren."),
) -> None:
    """Byg data ved behov og vis det interaktive oldtidskort."""
    mounds = PROCESSED_DIR / "fund_og_fortidsminder.geojson"
    if refresh or not mounds.exists():
        console.print("Bygger kortlaget fund_og_fortidsminder …")
        report = build("fund_og_fortidsminder", RAW_DIR, PROCESSED_DIR, refresh=refresh)
        console.print(report.summary())

    research_geojson = PROCESSED_DIR / "runesten_lokationer.geojson"
    if refresh or not research_geojson.exists():
        console.print("Bygger det dokumenterede runestenslag …")
        wikidata = fetch_runestone_research(
            RAW_DIR / "runestone_research.json", refresh=refresh
        )
        runor = fetch_runor(RAW_DIR / "runor_api_2020.json", refresh=refresh)
        research = build_runestone_research(
            wikidata, RAW_DIR / "fund_og_fortidsminder.json", runor
        )
        validate_runestone_research(research)
        write_runestone_research(research, CURATED_RUNESTONES)
        feature_count = write_location_geojson(research, research_geojson)
        console.print(f"runesten: {feature_count} dokumenterede stedvurderinger")

    url = f"http://127.0.0.1:{port}/web/"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PROJECT_DIR)
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as error:
        raise typer.BadParameter(f"port {port} kan ikke bruges: {error}") from error

    console.print(f"[bold green]Kortet er klar:[/bold green] {url}")
    console.print("Tryk Ctrl+C for at stoppe serveren.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\nKortserveren er stoppet.")
    finally:
        server.server_close()


@app.command("inspect")
def inspect_command(source: str = typer.Argument("fund_og_fortidsminder")) -> None:
    """Vis hvilke WFS-lag en kilde faktisk tilbyder (til fejlsøgning)."""
    adapter = REGISTRY[source]
    if not hasattr(adapter, "endpoints"):
        raise typer.BadParameter(f"{source} er ikke en WFS-kilde")
    with client() as http:
        for endpoint in adapter.endpoints():
            console.print(f"[bold]{endpoint}[/bold]")
            try:
                for feature_type in capabilities(http, endpoint):
                    console.print(f"  {feature_type.name}  ({feature_type.srs})  {feature_type.title}")
            except Exception as error:  # noqa: BLE001 — diagnostik skal vise alt
                console.print(f"  [red]{error}[/red]")
