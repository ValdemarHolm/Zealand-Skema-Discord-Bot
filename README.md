# Zealand TimeEdit Discord Bot 📅🤖

En automatiseret Discord-bot skrevet i Python, der synkroniserer, overvåger og visualiserer ugeskemaer direkte fra **Zealands TimeEdit (ICS-feed)**. 

Botten genererer et flot, læsbart tabelfoto (PNG) af skemaet og opdaterer automatisk en dedikeret Discord-kanal, hvis der sker ændringer i undervisningen (f.eks. lokaleændringer eller aflysninger).

## 🚀 Funktioner

* **Automatisk overvågning:** Tjekker TimeEdit hvert 20. minut for ændringer ved hjælp af MD5-hashing.
* **Visuel skematabel:** Genererer automatisk et farvekodet skemabillede via `matplotlib` med automatiske tekstombrydninger for et rent og professionelt udtryk.
* **Selvrensende kanal:** Ved skemaændringer redigeres den eksisterende besked med det nye billede, og eventuelle gamle, overflødige bot-beskeder slettes automatisk.
* **Varslingssystem:** Sender en alarmbesked i en separat kanal (f.eks. `#varsler`), når der registreres ændringer på TimeEdit.
* **Slash-kommandoer (App Commands):**
  * `/schedule [uge]`: Vis ugeskemaet som et billede for den nuværende eller en specifik historisk uge.
  * `/schedule-info`: Giver et hurtigt overblik over, hvilke uger der er tastet undervisning ind for, samt vigtige disclaimers.

## 🛠️ Forudsætninger og installation

### 1. Installer afhængigheder
Projektet kræver en række eksterne biblioteker til at håndtere Discord, hente kalenderdata og tegne tabellen. Du kan installere dem via din terminal:

```bash
pip install discord.py requests icalendar pytz matplotlib
```

### 2. Konfiguration direkte i koden
Åbn din Python-fil (f.eks. `bot.py`) og indsæt dine egne ID'er og links i konfigurationssektionen i toppen af filen:

```python
# Discord Konfiguration
TOKEN = 'INDTAST_DIN_BOT_TOKEN_HER'
GUILD_ID = discord.Object(id=123456789012345678) # Dit Server ID

# Kanal-ID'er (rent tal uden '#' eller '@')
SKEMA_CHANNEL_ID = 123456789012345678        # Kanalen hvor skemabilledet altid står (f.eks. #skema)
NOTIF_CHANNEL_ID = 123456789012345678        # Kanalen hvor botten pinger ved ændringer (f.eks. #varsler)

# Dit direkte TimeEdit-link fra Zealand
ICS_URL = 'https://timeedit.net...'
```

*⚠️ **Vigtigt:** Hvis du deler din kode med andre eller lægger den på et offentligt sted (som GitHub), skal du huske at fjerne din `TOKEN` og dine ID'er igen, så andre ikke kan misbruge din bot.*

## 🏃‍♂️ Sådan køres botten

Når du har indtastet dine oplysninger i toppen af filen, kan du starte botten fra din terminal:

```bash
python bot.py
```

Når botten logger på, vil den automatisk synkronisere sine slash-kommandoer til din Discord-server og starte baggrundstjekket med det samme.

## 📦 Teknologier brugt

* **[discord.py](https://github.com):** API-wrapper til interaktion med Discord og håndtering af app-kommandoer.
* **[matplotlib](https://matplotlib.org):** Bruges til at tegne og generere skematabellen som et PNG-billede.
* **[icalendar](https://readthedocs.io):** Til at parre og læse det rå `.ics` feed fra TimeEdit.
* **[pytz](https://pypi.org):** Sikrer korrekt tidszonehåndtering i forhold til dansk tid (`Europe/Copenhagen`).

## ⚠️ Ansvarsfraskrivelse
Dette værktøj henter data automatisk og er udelukkende vejledende. Tjek altid officielle platforme som Moodle for de seneste officielle opdateringer og beskeder fra Zealand.
