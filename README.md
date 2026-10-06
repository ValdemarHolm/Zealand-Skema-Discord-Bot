# Zealand Discord Skemabot 📅

En automatiseret Discord-bot bygget i Python (`bot.py`), der henter skemadata live fra Zealand (TimeEdit via `.ics`-link) og genererer et flot, letlæseligt tabelfoto direkte i en dedikeret tekstkanal.

Botten holder automatisk øje med ændringer i skemaet og opdaterer sig selv i baggrunden, så de studerende altid har det nyeste ugeskema lige ved hånden.

## 🚀 Funktioner

* **Automatisk Live-opdatering**: Tjekker TimeEdit hvert 20. minut. Hvis der sker ændringer i den nuværende uge, opdateres skemabilledet automatisk.
* **Varslingssystem (`#varsler`)**: Sender en ping-notifikation i en separat varslingskanal, så snart der registreres en ændring (f.eks. aflysninger eller lokaleændringer).
* **Automatisk Opstart**: Når botten tændes eller genstartes, søger den selv efter sin tidligere besked i skemakanalen og opdaterer den i fuldstændig stilhed.
* **Privat Skemaviser (`/skema`)**: Henter et øjebliksbillede af skemaet som en privat besked (`ephemeral`), som kun du kan se. Understøtter også specifikke ugenumre (f.eks. `/skema uge: 42`).
* **Privat Info-oversigt (`/skema-info`)**: Viser en privat liste over alle uger, hvor Zealand har lagt skema ind, samt faste praktiske informationer (f.eks. forklaring af rød fredagskolonne ved Fredagscafé).
* **Hård Kanalspærring (`/skema-all`)**: Bruges til manuelt at nulstille eller oprette den faste live-besked. Kommandoen kan *kun* køres i den korrekte `#skema` kanal for at undgå fejl.

---

## 🛠️ Installation & Opsætning (Linux / Fedora / Ubuntu)

Følg disse trin for at installere og køre botten på din maskine.

### 1. Klon eller download projektet
Placer kildekoden i en mappe på dit skrivebord eller din server:
```bash
cd ~/Desktop/zealand-schedule-discord-bot-main
```

### 2. Installer afhængigheder
Sørg for, at du har Python installeret, og kør derefter følgende kommando for at installere alle nødvendige biblioteker fra `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Konfiguration af `bot.py`
Åbn `bot.py` og indsæt dine specifikke ID'er og links i konfigurationssektionen i toppen af filen:

```python
TOKEN = 'DIN_DISCORD_BOT_TOKEN'
GUILD_ID = discord.Object(id=DIT_SERVER_ID)
SKEMA_CHANNEL_ID = 123456789012345678  # Kanalen hvor det faste skemabillede skal stå
NOTIF_CHANNEL_ID = 123456789012345678  # Kanalen hvor botten skal pinge ved ændringer
ICS_URL = 'DIT_DIREKTE_TIMEEDIT_ICS_LINK'
```
*> **Sikkerhedstip:** Husk altid at fjerne eller skjule dit `TOKEN` og dine private ID'er, før du uploader koden til offentlige GitHub-arkiver!*

### 4. Discord Bot Rettigheder (Permissions)
For at botten kan fungere upåklageligt i din `#skema` kanal, skal dens rolle have følgende tilladelser aktiveret i Discord:
* **Vis kanal** (View Channel)
* **Send beskeder** (Send Messages)
* **Indlejring af links** (Embed Links)
* **Vedhæft filer** (Attach Files)
* **Administrer beskeder** (Manage Messages) — *Vigtigt, da den rydder op i gamle beskeder ved opstart!*
* **Læs beskedhistorik** (Read Message History)

---

## 🏃‍♂️ Sådan køres botten

Du kan starte botten manuelt fra din terminal ved at køre:
```bash
python bot.py
```

Når terminalen skriver `Botten er online som Skema#XXXX`, er botten aktiv og synkroniseret med dine Slash-kommandoer på din Discord-server.

## 📝 Ansvarsfraskrivelse / Disclaimer

Dette projekt henter data automatisk via TimeEdit API/iCal-integrationer og er udelukkende vejledende. Tjek altid Moodle for de seneste officielle udmeldinger, aflysninger og beskeder fra uddannelsesinstitutionen.
