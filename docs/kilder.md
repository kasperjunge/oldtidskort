# Datakilder

| Datasæt | Kilde | Adgang | Licens |
| --- | --- | --- | --- |
| Gravhøje | Fund og Fortidsminder (Slots- og Kulturstyrelsen) | WFS, punktlag findes via GetCapabilities | Offentlige data — kreditér styrelsen |
| Kirker | OpenStreetMap via Overpass | Overpass API (to spejle) | ODbL 1.0 — kreditering påkrævet |
| Runesten | Samnordisk runtextdatabas/Runor, Wikidata og Fund og Fortidsminder | REST, SPARQL og WFS | CC0-metadata + kildekreditering |

## Fund og Fortidsminder
Styrelsen har flyttet servicen mellem hosts gennem årene, så adapteren prøver
de kendte endpoints i rækkefølge og vælger punktlag ud fra GetCapabilities
frem for hardcodede lagnavne. Se hvad serveren rent faktisk tilbyder med:

```bash
uv run oldtidskort inspect fund_og_fortidsminder
```

Attributnavne varierer mellem lagene, så mapningen sker via alias-lister
(`FIELD_ALIASES`) og er case-insensitiv. Gravhøje udvælges på
`anlaegsbetegnelse` — udvid `barrow_terms`, hvis der mangler typer.

Nogle lag ignorerer `srsName` og svarer i UTM32N (EPSG:25832); det opdages på
koordinatstørrelsen og omprojiceres. Lat/lon-ombytning (kendt WFS 1.1.0-faldgrube)
rettes tilsvarende.

## Kirker
Overpass-forespørgslen tager `building=church|chapel`, `historic=church` og
kristne `place_of_worship`. Datering kommer fra `start_date`, som også kan være
et århundrede (`C12`); der bruges århundredets midte til periodebestemmelse,
mens `year_from` er århundredets første år.

Danmarks Kirker (Nationalmuseet) ville give langt bedre bygningsdatering, men
er ikke udgivet som maskinlæsbart datasæt.

## Runesten
Danmarks Runeindskrifter (runer.ku.dk) har ingen offentlig API. Wikidata-laget
henter nordiske runesten (Q24566025) i Danmark med koordinat og ofte DR-nummer (P1261).
Manglende sten kan tilføjes i `data/raw/runesten.csv` med kolonnerne
`dr_nummer,navn,lon,lat,datering,kommune,kilde_url`.
Hvis CSV og Wikidata har samme DR-nummer (uanset mellemrum og store/små
bogstaver), overskriver CSV'ens udfyldte felter Wikidata uden at skabe en dublet.

Det dokumenterede researchdatasæt bruger desuden Samnordisk runtextdatabases
officielle Runor-API, udgave 2020. Den kilde skelner mellem ældst belagte og
nuværende koordinater, oplyser proveniens, placering, bevaringsstatus og om en
placering udtrykkeligt er oprindelig. Fund og Fortidsminder importeres som
registerobservationer og sammenkobles kun med en sten via dokumenterede ID'er.

## Kildekrav
Før et datasæt publiceres: afklar licens, kreditering, opdateringskadence og et
stabilt id, der kan diffes mod forrige udgivelse.
