# Bynavneendelser

Dette er et kurateret opslagsdatasæt, der oversætter en dansk bebyggelses
navneendelse til et **navnelag** og en grov datering. Det bruges af kilden
`bynavne_osm` til at give hvert bynavn en periode, så bynavne kan holdes op
mod gravhøje og runesten på kortets fælles periodeakse.

## Vigtigt forbehold

Endelsesdatering er en **tolkning, ikke et facit**. Den daterer navnetypen —
ikke nødvendigvis den bebyggelse, der bærer navnet i dag: en landsby kan være
ældre end sit navn, navnet kan være flyttet, og enkelte navne er sene
efterligninger af et gammelt mønster. Dateringerne følger hovedlinjen i dansk
navneforskning (Hald, Jørgensen, Danmarks Stednavne), men grænserne er
omdiskuterede og angives derfor bredt.

Hver endelse har derfor et `confidence`-felt:

- `high` — veletableret navnelag med bred faglig enighed (`-lev`, `-torp`, `-by`)
- `medium` — anerkendt lag, men med usikker afgrænsning eller betydning
- `low` — endelsen bruges også i unge navne; alderen kan ikke antages

## Tabeller

`suffixes.csv` — én række pr. endelsesform. Flere former hører til samme
`family` (fx `-torp`, `-rup`, `-drup`, `-strup`, `-trup`, `-arp`), som er den
enhed kortet filtrerer på. `horizon` er det navnehistoriske lag, `period`
oversætter til projektets fælles `Period`, og `year_from`/`year_to` er grove
yderpunkter.

`exceptions.csv` — navne hvor den automatiske endelsesmatch er forkert.
`decision` er enten en `family` fra `suffixes.csv` eller `none`, når navnet
ikke skal dateres. Listen er kort med vilje: den skal vokse med dokumenterede
enkelttilfælde, ikke med gæt.

`sources.csv` — de værker klassifikationen hviler på. Værkerne er
ophavsretligt beskyttede og refereres kun; ingen tekst er kopieret hertil.

## Sådan matches en endelse

1. Navnets sidste ord bruges (`Store Heddinge` → `Heddinge`).
2. Står navnet i `exceptions.csv`, gælder den beslutning.
3. Ellers vælges den **længste** endelse fra `suffixes.csv`, der passer.
4. Der skal være mindst to bogstaver stamme tilbage foran endelsen, så korte
   navne ikke fejlmatches.
5. Uden match får bynavnet `period = ukendt` og ingen `family`.
