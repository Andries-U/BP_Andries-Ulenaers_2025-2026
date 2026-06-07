# Tekst te gebruiken

## Inleiding tot je onderzoeksvraag: wat is het doel van je onderzoek?

### Inleiding: Tekst

De Einstein Telescope is een toekomstige, ultragevoelige zwaartekrachtgolfdetector die mogelijk in de Euregio Maas-Rijn komt. Deze telescoop heeft een enorme energiebehoefte, vergelijkbaar met die van UZ Leuven of CERN, en stelt hoge eisen aan betrouwbaarheid, duurzaamheid en trillingsvrijheid. Mijn onderzoek ontwikkelt een GIS-analysetool die onderzoekers ondersteunt bij het analyseren van geografische data, zoals landbouwgebieden, stortplaatsen of waterlichamen. Zo kunnen de onderzoekers snel en nauwkeurig bepalen waar en hoeveel capaciteit voor duurzame energiebronnen (bijv. zonnepanelen op landbouwgrond of water) beschikbaar is.

## Achtergrondinformatie: waarom is jouw onderzoeksvraag relevant?

### Achtergrondinformatie: Tekst

De Einstein Telescope zal een enorme impact hebben, zowel wetenschappelijk (nieuwe inzichten in zwaartekrachtgolven, fundamentele natuurkunde en randontwikkelingen) als regionaal. Voor de Euregio Maas-Rijn (EMR) betekent de komst van de ET:

- Economische groei: jobcreatie en technologische innovatie.
- Maatschappelijke impact: extra bewoners, bedrijvigheid en economische dynamiek. Wat mogelijk weerstand kan oproepen.

Om de locatie in de EMR te winnen, moet een haalbaar energieplan worden voorgelegd. Dit plan moet rekening houden met:

- Technische eisen: trillingsvrije en duurzame energie.
- Ecologische beperkingen: Natura2000-gebieden en verantwoord landgebruik.
- Maatschappelijke wensen: lokale betrokkenheid, innovatieve oplossingen zoals AgriPV (zonnepanelen boven landbouwgrond).

## Methode: hoe zoek je naar een antwoord op je onderzoeksvraag?

### Methode: Tekst

Om een bruikbare tool te creëren, doorliep ik vier fasen:

1. **Vereistenanalyse**: Wat zijn de behoeften van de ET-onderzoekers? Welke datasets zijn beschikbaar?
2. **Vergelijking** GIS-tools (bijv. QGIS, ArcGIS) en bibliotheken. QGIS gekozen omwille van zijn open-source aard, populariteit en Python-integratie.
3. **Ontwikkelen Proof-of-Concept**: Een tool die:
   - **Automatisch zoekgebieden** genereert rond ET-hoekpunten.
   - **Datasets filtert** op basis van onderzoeksgebied en specifieke wensen
   - **Resultaten** visualiseert en beschikbaar stelt in kaarten en rapporten.
4. **Benoemen Risico's**: Beperkingen identificeren, zoals risico op dubbele telling van locaties of afhankelijkheid van datakwaliteit.

## Resultaten: wat kwam voort uit je onderzoek?

### Resultaten: Tekst

**Resultaten**
Met de tool kunnen ET-onderzoekers:

- **Snel locaties identificeren**: Bijv. hoeveel hectare landbouwgrond geschikt is voor AgriPV.
  - **Volledige analyse**: Welke data heeft de dataset en hoeveel oppervlakte per categorie.
  - **Gedeeltelijke analyse**: Filter de dataset op specifieke waarden.
- **Resultaten delen**: Via PDF-rapporten met kaarten en tabellen, datalagen voor QGIS en ruwe data als CSV-bestanden.

**Toekomstige uitbreidingen**:

- Integratie van **energiepotentieel berekeningen** (bijv. hoeveel kW kan een perceel opwekken?).
- **Multi-criteria analyse**: Combineren van objectieve data (oppervlakte) met subjectieve criteria (maatschappelijke acceptatie).

## Conclusie: wat impliceren je resultaten? Wat besluit je hieruit?

### Conclusie: Tekst

**Wat neem je mee?**
Dit onderzoek bewijst dat **open-source GIS-tools** zoals QGIS, gecombineerd met Python, krachtige oplossingen kunnen bieden voor complexe uitdagingen. De ontwikkelde tool:

- **Ondersteunt** Einstein Telescope onderzoekers bij het vinden van geschikte locaties voor duurzame energie.
- **Maakt analyse toegankelijk**  voor onderzoekers, zelfs met beperkte technische kennis.
- **Biedt een startpunt** voor verdere uitbreidingen, zoals automatische energiepotentieelberekeningen.

**Lessons learned**:

- **Samenwerking** met stakeholders (onderzoekers, overheden) is cruciaal voor succes.
- **Flexibiliteit** in de tool is essentieel, omdat vereisten kunnen veranderen.
- **Benoemen van beperkingen en risico's** (bijv. datakwaliteit, dubbele telling) is essentieel voor realistische verwachtingen.