# Runestensdatasættet

Dette er et åbent researchdatasæt over runesten med tilknytning til det
nuværende Danmark. Formålet er at skelne mellem:

- stenens oprindelige opstillingssted (`original_location`)
- stedet hvor stenen blev fundet (`findspot`)
- stenens nuværende placering (`current_location`)
- kildens ældst belagte placering (`earliest_known_location`)
- et koordinat i et offentligt register, hvis den historiske rolle endnu ikke
  er afgjort (`registered_location`)

Et manglende sted er bevaret som en eksplicit række med metoden `unknown`.
Det gør både dækningsgrad og manglende research synlig. Et fundsted bliver
aldrig automatisk fortolket som det oprindelige opstillingssted.

## Tabeller

`stones.csv` indeholder én foreløbig identitet pr. sten. Fund og Fortidsminders
punkter ligger separat i `registered_observations.csv`, fordi én lokalitet kan
rumme flere sten og én sten kan have flere historiske lokaliteter.
`identity_links.csv` indeholder kun dokumenterede koblinger mellem observation
og sten. `locations.csv`
indeholder alle stedvurderinger og den fulde metodebegrundelse. `evidence.csv`
knytter kildeudsagn og vores fortolkning til en stedvurdering. `sources.csv`
indeholder kilder, udgiver, licens og dato for opslag.

Tabellerne kobles således:

```text
stones.stone_id <- locations.stone_id
stones.stone_id <- identity_links.stone_id
registered_observations.observation_id <- identity_links.observation_id
locations.location_id <- evidence.location_id
sources.source_id <- evidence.source_id
```

## Betydningen af koordinatmetoder

| Metode | Betydning |
| --- | --- |
| `source_coordinate` | Kilden angiver koordinatet direkte for stenen eller registerposten. |
| `related_place_coordinate` | Kilden navngiver et sted; koordinatet tilhører stedobjektet. |
| `geocoded` | Et kildenavn er slået op i et dokumenteret stedregister. |
| `estimated` | Koordinatet er en fagligt begrundet tilnærmelse. |
| `unknown` | Der publiceres ikke et koordinat. |

`uncertainty_m` er en radius, ikke en statistisk standardafvigelse. Estimerede
punkter skal vises med usikkerhed på kortet og må ikke fremstilles som præcise
fundkoordinater.

## Status og begrænsninger

Den første maskinelle import er bevidst mærket `needs_review`. Wikidata P625
behandles foreløbigt som nuværende placering, men med en klar advarsel i
`rationale`. Fund og Fortidsminders WFS-punkter bevares som
`registered_location`, indtil beskrivelse og undersøgelseshistorie er læst.
Samnordisk runtextdatabases egne `oldest_known`- og `current`-koordinater er
markeret `reviewed`, fordi deres semantiske rolle er eksplicit; det er ikke en
påstand om, at `oldest_known` nødvendigvis er det oprindelige opstillingssted.

Datasættet må derfor filtreres på `review_status=reviewed`, hvis det skal bruges
til konklusioner om historiske steder. Alle øvrige rækker er åbne
researchhypoteser, ikke færdige faglige konklusioner.

## Reproduktion

```bash
uv run python scripts/build_runestone_research.py --refresh
```

Importlogikken og valideringsreglerne ligger i
`src/oldtidskort/research/`. Wikidata er CC0. Data fra Fund og Fortidsminder
skal krediteres Slots- og Kulturstyrelsen og følger kildens egne vilkår.
