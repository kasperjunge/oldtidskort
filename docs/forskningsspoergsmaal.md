# Åbne forskningsspørgsmål, som Oldtidskort kan angribe

Status: researchnotat, 2026-09-07. Formålet er at identificere spørgsmål i
vikingetids- og landskabsarkæologien, der (a) er reelt ubesvarede i
litteraturen, (b) er følsomme over for netop den slags data, projektet allerede
har, og (c) kan afgøres eller sandsynliggøres med aggregering, datatilføjelse
eller agentbaseret læsning af fundbeskrivelser.

Prioriteringen er efter nyhedsværdi divideret med indsats. Spørgsmål 1 er efter
min vurdering det stærkeste kort, projektet sidder på, fordi datamodellen
allerede indeholder den skelnen, feltet mangler.

---

## 0. Hvad vi faktisk har (målt på det aktuelle datasæt)

Tal fra `data/curated/runestones/`, kørt 2026-09-07:

| Mål | Antal |
| --- | --- |
| Sten i datasættet | 193 |
| Med DR-nummer / Runor-kobling | 190 / 190 |
| Sten med **dokumenteret oprindeligt opstillingssted** | **4** |
| Sten med dokumenteret fundsted | 12 |
| Sten med nuværende koordinat | 55 (110 lokationsrækker) |
| Sten med "ældst belagte" koordinat | 185 |
| Lokationsrækker `reviewed` / `needs_review` | 199 / 510 |
| Bevaringsstatus extant / lost / unknown | 167 / 21 / 5 |

Sammenlign med den samlede bestand: Imer (2014) opgør ca. **260 runesten** i
det gamle danske område inkl. Skåne, Halland, Blekinge og Slesvig. Datasættet
dækker altså formentlig ~75 % af de sten, der ligger inden for nutidens
Danmark, men **2 % af dem har et fagligt dokumenteret oprindeligt
opstillingssted.**

Målt på de 48 sten, hvor både "ældst belagt" og "nuværende" koordinat findes:

- median forskydning: **11 m**
- 54 % er flyttet > 10 m, 27 % > 100 m, 21 % > 500 m, 19 % > 1 km
- ekstremer: DR400 6,4 km · DR155 6,0 km · DR370 4,2 km · DR191 143 km
  (museumsflytning — skal håndteres som egen kategori, ikke som outlier)

Det er grundlaget for spørgsmål 1.

---

## 1. Hvor meget af "runestenenes geografi" er i virkeligheden kirkernes og museernes geografi?

**Status i feltet.** Alle fordelingskort over danske runesten — inklusive Imers
periodekort (Helnæs-, Gørlev-, førkonverterings-, efterkonverterings- og
Bornholmsgruppen) — plottes på de punkter, vi *har*. Men Danmarks
Runeindskrifter og formidlingslitteraturen er enige om, at kun et fåtal står på
eller nær deres oprindelige plads; mange blev genanvendt i de over 1.500
stenkirker bygget fra 1100-tallet til reformationen, og for mange vil det
oprindelige sted aldrig kunne fastslås. Imer noterer desuden, at **Randbøl er
den eneste danske runesten fundet i forbindelse med en samtidig grav.**

**Hvorfor det er åbent.** Ingen har, så vidt jeg kan finde, publiceret en
systematisk kvantificering af *forskydningen*: hvor stor en andel af bestanden
har kendt oprindelsessted, hvor langt er resten flyttet, og hvordan påvirker
det de regionale mønstre, konklusionerne bygger på. Litteraturen behandler
forskydning som en kvalitativ forbeholdssætning i indledningen — ikke som en
målt størrelse med en fejlmodel.

**Det novelle bidrag.** Et *forskydningskorrigeret fordelingskort* med
eksplicit usikkerhedsbudget pr. sten:

1. Klassificér hver sten i en flyttekategori: in situ (sandsynlig), flyttet
   inden for lokaliteten, genanvendt i kirke, flyttet til kirkegård i nyere
   tid, museumsflyttet, tabt, ukendt.
2. Beregn forskydningsfordelingen pr. kategori (48 par i dag, formentlig 150+
   efter agentlæsning af DR-teksterne).
3. Genkør Imers periodefordelinger som **sandsynlighedsflader** i stedet for
   punkter: hver sten bidrager med en kerne, hvis radius er dens
   forskydningsusikkerhed.
4. Test: holder den kronologiske tyngdepunktsforskydning — Fyn/Sjælland i
   700–900-tallet → Jylland i 900-tallet → Nordøstjylland og skånsk kyst
   omkring år 1000 → Bornholm efter 1025 — når man tager højde for, at
   observationsmønstret er filtreret gennem middelalderens kirkebyggeri?

**Falsificerbar test.** Hvis kirketætheden i et område forudsiger
runestenstætheden bedre end nogen vikingetidsvariabel gør, er en del af det
etablerede fordelingsmønster et bevaringsartefakt. Projektet har allerede et
kirkelag fra OSM, så nulmodellen kan bygges i dag.

**Indsats.** Lav–middel. Data findes; det tunge er kategoriseringen, se
spørgsmål 6.

---

## 2. Stod runestenene ved vejene? En dansk pendant til de skånske least-cost-path-studier

**Status i feltet.** For **Skåne** — det gamle østdanske område — findes
publicerede GIS-studier, der kombinerer klyngestatistik og least-cost-path for
at teste, om runesten står langs vikingetidens færdselsårer; konklusionen er,
at stenene grupperer sig langs veje, vandløb, gravpladser og regionale grænser.
Tilsvarende argumenter fremføres løbende for det øvrige Danmark
(broindskrifter, "hvor mange kom forbi"), men **uden en tilsvarende kvantitativ
analyse for Jylland, Fyn, Sjælland og Bornholm.**

**Hvorfor det er åbent.** Den skånske metode er aldrig replikeret på nutidens
Danmark. Det er en veldefineret, ubesat plads i litteraturen — ikke et
spørgsmål om at opfinde en metode, men om at anvende en eksisterende metode på
et datasæt, der først nu er ved at findes maskinlæsbart.

**Det novelle bidrag.** Byg en friktionsflade fra Danmarks Højdemodel plus
historisk vådområdekortlægning, generér least-cost-korridorer mellem kendte
vikingetidsknudepunkter (Jelling, Hedeby, ringborgene, tidlige byer,
tingsteder), og mål afstanden fra hver runesten til nærmeste korridor mod en
Monte Carlo-nulmodel af tilfældige punkter med samme landskabsbetingelser.

**Kritisk forbehold.** Analysen er kun meningsfuld på sten med kendt
oprindeligt sted. Med 4 sådanne sten i dag er svaret ikke tilgængeligt. Det er
præcis derfor, forskydningsarbejdet er den egentlige flaskehals i feltet — og
hvorfor projektet kan levere noget, andre ikke har.

**Variant med lavere risiko:** vend spørgsmålet om. I stedet for "står stenene
ved vejene", spørg **"forudsiger runestenene, hvor vejene gik?"** — brug de
sten, der *har* sikkert oprindelsessted, plus broindskrifterne som
kontrolpunkter for at validere et rekonstrueret vikingetidsvejnet, og publicér
vejnettet som selvstændigt datalag.

---

## 3. Genbrugte vikingetiden bevidst bronzealderhøjene — og kan det måles på landsplan?

**Status i feltet.** Genbrug af ældre høje til vikingetidsgrave er kendt fra
mange enkeltlokaliteter (Jelling Nordhøj er bygget over en bronzealderhøj;
Bække kobler skibssætning, høj og runesten), men litteraturen konstaterer, at
fænomenet **ikke er diskuteret i bredt perspektiv eller på lang tidsskala**, og
at det er omstridt, om genbrug var arbejdsbesparelse eller
legitimeringsstrategi.

**Hvorfor det er åbent.** Argumenterne er anekdotiske, fordi ingen har haft et
landsdækkende, ensartet datasæt over både høje og vikingetidsaktivitet.
Oldtidskort har høje for hele landet.

**Det novelle bidrag.** En landsdækkende nabolagsanalyse: for hver
vikingetidsmarkør (runesten med sikkert sted, vikingetidsgravplads,
detektorfundskoncentration fra DIME) — er afstanden til nærmeste
bronzealderhøj mindre end forventet under en nulmodel, der kontrollerer for, at
høje selv klumper på tørre, højtliggende jorder? Holder effekten efter
terrænkontrol, er arbejdsbesparelsesforklaringen svækket: arbejdsbesparelse
forudsiger ikke, *hvilke* høje der vælges — det gør synlighed og placering ved
færdselsårer.

**Ekstra vinkel med reel nyhedsværdi:** test *synlighed* frem for afstand.
Beregn viewshed fra genbrugte vs. ikke-genbrugte høje. Hypotesen "genbrug
handlede om at blive set fra vejen" er aldrig testet systematisk i Danmark.

---

## 4. Hvor mange høje mangler i registret — og hvor systematisk mangler de?

**Status i feltet.** Ca. 86.000 gravhøje er registreret i Danmark, heraf ca.
20.000 dateret til bronzealderen, og hovedparten er helt eller delvist ødelagt
— genanvendt som byggemateriale og vejfyld. For dysser og jættestuer anslås
det, at kun omkring en tiendedel er bevaret. LiDAR-baseret automatisk detektion
af høje, stendiger og vikingetidsborge er en moden metode; i Danmark er den
bl.a. brugt til at reducere 202.048 cirkulære LiDAR-features til 199
ringborgkandidater.

**Hvorfor det er åbent.** Det interessante er ikke "find flere høje" — det gør
detektionslitteraturen allerede. Det åbne spørgsmål er **registrets bias**: er
manglerne tilfældige, eller systematisk korreleret med jordbund,
dyrkningsintensitet, kommunegrænser og registreringshistorik? Enhver
fordelingsanalyse i dansk arkæologi — inklusive punkt 1–3 ovenfor — hviler på
en antagelse om, at Fund og Fortidsminder er en ensartet stikprøve. Den
antagelse er aldrig kvantificeret.

**Det novelle bidrag.** Et **bias-kort over Fund og Fortidsminder**: modellér
registreringssandsynlighed som funktion af arealanvendelse, fredningsstatus,
undersøgelseshistorik og administrativ enhed, og udgiv residualfladen som åbent
lag. Det er et metodebidrag, hele feltet kan bruge, det kræver ingen ny
feltarkæologi, og det er det resultat, der bedst kan stå alene som publikation
fra et dataprojekt.

---

## 5. Holder arvehypotesen geografisk?

**Status i feltet.** Birgit Sawyers hypotese (2000) er, at runesten primært er
arvekrav: rejseren markerer sin ret til den dødes ejendom, og de regionale
forskelle i indskrifternes slægtsformler afspejler forskellige arveregler
mellem vest/syd og øst. Hypotesen er indflydelsesrig og samtidig kritiseret
for, at de selvsikre konklusioner ikke er tilstrækkeligt underbyggede.

**Hvorfor det er åbent.** Kritikken har været filologisk og historiografisk.
Den geografiske konsekvens af hypotesen er derimod aldrig skarpt testet: hvis
stenene er ejendomskrav, bør de klumpe ved **bebyggelsesgrænser og
godsstrukturer**, ikke ved centrale samlingspunkter — og det er en rumlig
forudsigelse, der kan afvises.

**Det novelle bidrag.** Kombinér runestenslaget med **stednavnelaget**:
Danmarks Stednavne rummer over 210.000 navne med historiske former, og
bebyggelsesnavnetyper (-lev, -inge, -sted, -torp) er den bedst etablerede proxy
for bebyggelsens relative kronologi. Test: falder runestenene
overrepræsenteret i ældre navnelag (-lev/-inge, tidlige storgårde) eller i
udflytterlaget (-torp)? Sawyers ejendomstolkning forudsiger det første; en "ny
elite, der skal legitimere sig" forudsiger snarere en blanding. Testen er
aldrig kørt, fordi de to datasæt aldrig er lagt sammen maskinelt.

**Bemærk licensen.** Stednavnedatabasens vilkår skal afklares, før laget
publiceres — følg projektets egne kildekrav i `docs/kilder.md`.

---

## 6. Metodespørgsmålet: kan agenter læse fundbeskrivelser og producere efterprøvelige stedvurderinger?

Ikke et arkæologisk spørgsmål, men det, der gør 1–5 gennemførlige — og
selvstændigt publicerbart.

**Status i feltet.** NLP og LLM'er bruges i stigende grad til at udtrække
struktureret information fra arkæologisk grålitteratur — kronologier,
kulturtaksonomier, genstandstyper — fra udgravningsberetninger, og
oversigtslitteraturen fra 2025 peger på, at moderne modeller kan bygge
databaser ud af ustruktureret legacy-litteratur.

**Hvorfor det er åbent i dansk sammenhæng.** Danmarks Runeindskrifter
(runer.ku.dk) har ingen offentlig API, og Fund og Fortidsminders beskrivelser
er fritekst. Ingen har systematisk konverteret de danske fundbeskrivelser til
**stedvurderinger med rolle, metode, usikkerhedsradius og kildecitat** — præcis
det skema, `data/curated/runestones/` allerede definerer med `role`,
`coordinate_method`, `uncertainty_m` og `evidence.csv`.

**Det novelle bidrag.** En agentpipeline, der for hver sten læser
DR-beskrivelsen og Fund og Fortidsminder-teksten og udskriver:

- rolle (oprindeligt sted / fundsted / nuværende / registreret)
- flyttekategori (kirkegenbrug, museumsflytning, flyttet i marken …)
- usikkerhedsradius med begrundelse
- ordret kildecitat i `evidence.source_statement`
- `review_status = needs_review`, indtil et menneske har set på det

Og — afgørende for troværdigheden — **et guldsæt**: 40–60 sten håndkodet af en
fagperson, som agentens output måles mod, med rapporteret præcision og recall
pr. rolle. Uden det er det databerigelse; med det er det et metodebidrag til
digital arkæologi.

**Hvad der gør det til et bidrag frem for bare pænt arbejde:** datasættets
eksisterende designvalg — at et manglende sted bevares som en eksplicit
`unknown`-række, og at fundsted aldrig automatisk læses som oprindeligt sted —
er nøjagtigt den disciplin, agentbaseret ekstraktion normalt bryder. At vise,
at en agent kan arbejde inden for et skema, der tvinger den til at sige "det
ved vi ikke", er et resultat i sig selv.

---

## Anbefalet rækkefølge

1. **Spørgsmål 6** (agentpipeline + guldsæt) — låser alt andet op ved at løfte
   de 4 kendte oprindelsessteder mod noget brugbart.
2. **Spørgsmål 1** (forskydningskorrigeret fordeling) — det stærkeste
   selvstændige resultat, og det eneste sted, hvor projektets datamodel er
   forud for litteraturen.
3. **Spørgsmål 4** (bias-kortet) — kan køres parallelt, kræver intet
   runestensarbejde, og er nyttigt for hele feltet.
4. **Spørgsmål 3 og 5** — kræver ét nyt datalag hver (høj-genbrug hhv.
   stednavne).
5. **Spørgsmål 2** — mest ambitiøst, og reelt først muligt efter 1.

## Datasæt, der bør tilføjes

| Lag | Formål | Adgang | Vær opmærksom på |
| --- | --- | --- | --- |
| Danmarks Højdemodel (DHM) | friktionsflader, viewshed, LiDAR-detektion | Datafordeleren, åbne data | stor datamængde, kræver tiling |
| Danmarks Stednavne | bebyggelseskronologi (sp. 5) | navn.ku.dk / nors.ku.dk | licens skal afklares før publicering |
| DIME (detektorfund) | vikingetidsaktivitet uafhængigt af gravminder | metaldetektorfund.dk | stærk indsamlingsbias — brug som aktivitetsproxy, ikke som fordeling |
| Sten- og jorddiger | historiske skel (sp. 5) | Slots- og Kulturstyrelsen | |
| Historisk vådområde/kystlinje | friktionsflade (sp. 2) | Videnskabernes Selskabs kort, høje målebordsblade | georeferering er selv en fejlkilde |
| Danmarks Runeindskrifter, fuldtekst | sp. 1 og 6 | ingen API — kræver aftale | afklar vilkår med KU/Nationalmuseet først |

## Faldgruber, der bør stå eksplicit i enhver publikation herfra

- **Fundsted er ikke opstillingssted.** Datasættet håndhæver det allerede;
  analysen skal gøre det samme.
- **Kun én dansk runesten (Randbøl) er fundet ved en samtidig grav.** Enhver
  "runesten = gravmarkør"-antagelse skal derfor begrundes, ikke forudsættes.
- **Fund og Fortidsminder er et historisk register**, ikke en observation af
  nutidens landskab — en høj i registret er ikke nødvendigvis en høj i marken.
- **En lokalitet ≠ en sten.** Datamodellens adskillelse af
  `registered_observations` og `stones` skal fastholdes i aggregeringer, ellers
  overtælles Bornholm systematisk.
- **Datering er typologisk.** Imers fem grupper er typologiske grupper med
  overlap, ikke absolutte intervaller; usikkerheden skal med i tidsanimationer,
  ellers foregøgler kortet en præcision, runologien ikke har.

## Kilder

- Imer, L. M. (2014), "The Danish runestones – when and where?",
  *Danish Journal of Archaeology* 3(2), 164–174.
  https://tidsskrift.dk/dja/article/view/124929
- Sawyer, B. (2000), *The Viking-Age Rune-Stones: Custom and Commemoration in
  Early Medieval Scandinavia*, OUP.
  https://global.oup.com/academic/product/the-viking-age-rune-stones-9780198206439
  — kritisk anmeldelse: https://scholarworks.iu.edu/journals/index.php/tmr/article/view/15274
- "The spatiotemporal distribution of Late Viking Age Swedish runestones",
  *Journal of Archaeological Science: Reports*.
  https://www.sciencedirect.com/science/article/abs/pii/S2352409X18305285
- "The Spatial Order of the Scanian Runestones. Analysing Runestone Clustering
  and Pathways through GIS". https://www.academia.edu/14916999/
- "In 100 meters turn left by the runestone — least cost path and spatial
  statistics study of the Scanian runestones".
  https://www.academia.edu/73235087/
- "Ancient mounds for new graves – an aspect of Viking-age burial customs in
  southern Scandinavia". https://www.academia.edu/4148958/
- "Kerbing Relations through Time: Reuse, Connectivity and Folded Time in the
  Viking Age", *Cambridge Archaeological Journal*.
  https://www.cambridge.org/core/journals/cambridge-archaeological-journal/article/kerbing-relations-through-time-reuse-connectivity-and-folded-time-in-the-viking-age/107860E57C87AF191894D902D99DA4E4
- "Searching for Viking Age Fortresses with Automatic Landscape Classification
  and Feature Detection", *Remote Sensing* 11(16), 1881.
  https://www.mdpi.com/2072-4292/11/16/1881
- "Detecting Neolithic Burial Mounds from LiDAR-Derived Elevation Data Using a
  Multi-Scale Approach and Machine Learning Techniques", *Remote Sensing*
  10(2), 225. https://www.mdpi.com/2072-4292/10/2/225
- Dobat, A. & Jessen, M., "The DIME project", *Danish Journal of Archaeology*.
  https://tidsskrift.dk/dja/article/view/111422
- "Large Language and Multimodal Models in Archaeological Science: A Review",
  *Electronics* 14(22), 4507. https://doi.org/10.3390/electronics14224507
- Nationalmuseet om runesten:
  https://en.natmus.dk/historical-knowledge/denmark/prehistoric-period-until-1050-ad/the-viking-age/power-and-aristocracy/rune-stones/
- Danmarks Stednavne / Arkiv for Navneforskning, KU:
  https://nors.ku.dk/forskning/samlinger/stednavnesamlinger/digitale_samlinger/
