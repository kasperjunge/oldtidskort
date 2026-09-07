# Datamodel

Alt normaliseres til `Site` (`core/models.py`): ét punkt med `id`, `source`,
`site_type`, koordinater i WGS84, periode (kildens fritekst i `period_raw` +
vores normaliserede `period`), administrativ kontekst og licens.

Designvalg:
- **Ét fladt skema for alle typer.** Kortet skal kunne lægge gravhøje, kirker og
  runesten i samme lag og filtrere på `site_type` og `period`. Kildespecifikke
  felter lever i `extra` (serialiseres som JSON-tekst i GeoJSON).
- **Kildens id bevares** i `source_id`, så en genkørsel kan diffe mod forrige version.
- **WGS84 i datamodellen**; projektion og lat/lon-oprydning sker ved indlæsning
  (`core/geo.py`).
- **To formater ud**: GeoJSON til kortlag, Parquet til analyse.

## Perioder
`Period` er bevidst grov (stenalder → renæssance), fordi det er den opløsning
kortets tidsfilter skal bruge. To veje ind:
- `parse_period(tekst)` for kildernes fritekstdatering.
- `period_for_year(år)` for numeriske årstal, med danske grænser
  (vikingetid ca. 750-1050, middelalder til reformationen 1536).

## Validering
`pipeline.validate` frasorterer dubletter på `id` og punkter uden for et groft
Danmarks-bbox — sidstnævnte fanger fejlprojektioner, der ellers ville lande i
Nordsøen eller Vestafrika. `BuildReport` tæller, hvad der blev smidt væk, så en
kilde ikke stille skrumper efter en skemaændring hos udbyderen.
