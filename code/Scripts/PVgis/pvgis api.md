Hier is een samenvatting van de betekenis van de velden in de ruwe JSON-response van PVGIS, vertaald naar het Nederlands en gegroepeerd per sectie.

### 1. `inputs` (De instellingen die jij hebt gestuurd)
Dit bevestigt de parameters die de berekening heeft gebruikt. Handig om te controleren of je request goed is aangekomen.

| Pad | Veld | Betekenis | Eenheid / Waarde |
| :--- | :--- | :--- | :--- |
| `location` | `latitude` / `longitude` | De geografische coördinaten van het punt. | Graden (decimaal) |
| | `elevation` | De hoogte boven zeeniveau. | Meter (m) |
| `meteo_data` | `radiation_db` | De gebruikte database voor zonnestraling. | Bijv. "PVGIS-SARAH3" |
| | `meteo_db` | De database voor andere weerdata (temperatuur, wind). | Bijv. "ERA5" |
| | `year_min` / `year_max` | De periode waarover het gemiddelde is berekend. | Jaar (bijv. 2005-2023) |
| | `use_horizon` | Of er rekening is gehouden met schaduw van de omgeving (bergen). | `true` / `false` |
| `mounting_system` | `slope` | De hellingshoek van de panelen. | Graden (0° = plat, 90° = verticaal) |
| | `azimuth` | De richting van de panelen. | Graden (0° = Zuid, -90° = Oost, 90° = West) |
| `pv_module` | `technology` | Het type zonnecel. | "c-Si" (Kristallijn Silicium) |
| | `peak_power` | Het piekvermogen van het systeem. | kWp (Kilowatt-piek) |
| | `system_loss` | Het standaard verlies door kabels, omvormer, stof, etc. | Percentage (%) |

---

### 2. `outputs` (De berekende resultaten)
Dit is de kern van je analyse. De data is hier onderverdeeld in **maandgemiddelden** en **jaartotalen**.

#### A. `monthly.fixed` (Maandelijkse data)
Een lijst met 12 objecten (januari t/m december).

| Veld | Betekenis | Eenheid | Toelichting |
| :--- | :--- | :--- | :--- |
| `month` | De maand. | 1-12 | 1 = Januari, 12 = December |
| `E_d` | Gemiddelde **dag**opbrengst. | kWh/d | Hoeveel stroom het systeem gemiddeld per dag produceert in die maand. |
| `E_m` | Gemiddelde **maand**opbrengst. | kWh/maand | Hoeveel stroom het systeem gemiddeld per maand produceert. |
| `H(i)_d` | Gemiddelde **dag**elijke instraling. | kWh/m²/d | Hoeveel zonlicht er per m² op het paneel valt (nog geen stroom). |
| `H(i)_m` | Gemiddelde **maand**elijke instraling. | kWh/m²/maand | Totale zonlichtinstraling per m² voor de hele maand. |
| `SD_m` | Standaardafwijking. | kWh | Geeft aan hoe sterk de opbrengst per jaar kan variëren door weersverschillen. |

#### B. `totals.fixed` (Jaartotalen & Verliezen)
De samenvatting van het hele jaar.

| Veld | Betekenis | Eenheid | Toelichting |
| :--- | :--- | :--- | :--- |
| `E_y` | **Totale jaaropbrengst**. | kWh/jaar | **Belangrijkste getal:** Totaal geproduceerde stroom per jaar. |
| `E_d` | Gemiddelde dagopbrengst (over het hele jaar). | kWh/d | Gemiddelde over alle dagen van het jaar. |
| `H(i)_y` | Totale jaarlijkse instraling. | kWh/m²/jaar | Totaal zonlicht dat op de panelen valt per m². |
| `l_aoi` | Verlies door invalshoek. | % | Verlies doordat de zon niet altijd loodrecht op het paneel schijnt. |
| `l_spec` | Spectraal verlies. | % | Verlies door specifieke golflengten van het licht. |
| `l_tg` | Verlies door temperatuur & lage straling. | % | Panelen werken minder goed als ze heel heet worden. |
| `l_total` | **Totaal systeemverlies**. | % | De som van alle verliezen (inclusief de 14% die je als input gaf). |

---

### 3. `meta` (Documentatie)
Dit deel bevat puur tekstuele uitleg over de variabelen en eenheden.
*   Dit is nuttig als je de tool dynamisch wilt maken en de eenheden automatisch in je rapport wilt tonen.
*   Voor je analyse hoef je dit deel meestal **niet** te parsen, omdat de eenheden altijd gelijk zijn (kWh, %, graden).

### Samenvattend voor je code:
Als je **één getal** nodig hebt voor de potentie van een locatie, gebruik dan:
`outputs['totals']['fixed']['E_y']` (De totale kWh per jaar).

Als je een **grafiek** wilt maken per maand, gebruik dan de lijst:
`outputs['monthly']['fixed']` (Haal hier `E_m` uit voor de Y-as en `month` voor de X-as).