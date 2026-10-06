import discord
from discord import app_commands
from discord.ext import tasks
import requests
from icalendar import Calendar
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import io
import hashlib
import textwrap

# Discord Konfiguration
TOKEN = '0'
GUILD_ID = discord.Object(id=0) # Dit Server ID

# INDSÆT DINE TO KANAL-ID'ER HER (rent tal uden '@' eller '#')
SKEMA_CHANNEL_ID = 0        # Kanalen hvor skemabilledet altid står (f.eks. #skema)
NOTIF_CHANNEL_ID = 0        # Kanalen hvor botten pinger ved ændringer (f.eks. #generel / #varsler)

# Dit direkte TimeEdit-link fra Zealand
ICS_URL = '0'

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.last_schedule_hash = None 

    async def setup_hook(self):
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)
        self.check_schedule_changes.start()

    @tasks.loop(minutes=20)
    async def check_schedule_changes(self):
        await self.wait_until_ready()
        skema_channel = self.get_channel(SKEMA_CHANNEL_ID)
        notif_channel = self.get_channel(NOTIF_CHANNEL_ID)
        
        if not skema_channel:
            print(f"[FEJL] Kunne ikke finde skema-kanalen med ID: {SKEMA_CHANNEL_ID}")
            return

        # Henter skemaet for den igangværende uge
        uge_skema, start_date, end_date, fredag_bar, _ = get_live_week_schedule_with_raw(valgt_uge=None)
        if uge_skema is None:
            return 

        # Lav fingeraftryk af den nuværende uge
        skema_streng = str(uge_skema)
        current_hash = hashlib.md5(skema_streng.encode('utf-8')).hexdigest()

        # Første kørsel efter botten er startet: Gem hash og afvent næste tjek
        if self.last_schedule_hash is None:
            self.last_schedule_hash = current_hash
            return

        # Hvis der er en ændring, rydder vi op og opdaterer
        if current_hash != self.last_schedule_hash:
            self.last_schedule_hash = current_hash
            try:
                print("[INFO] Ændring fundet! Genererer nyt skemabillede...")
                billede_data = generate_table_image(uge_skema, start_date, end_date, fredag_bar)
                discord_fil = discord.File(fp=billede_data, filename='ugeskema.png')
                
                skema_tekst = "Ugeskemaet opdateres automatisk, hvis der sker ændringer på TimeEdit."

                # BULLETPROOF LOGIK: Find ALLE bottens egne beskeder i kanalen
                bottens_beskeder = []
                async for message in skema_channel.history(limit=50): # Tjekker de seneste 50 beskeder
                    if message.author == self.user:
                        bottens_beskeder.append(message)

                if bottens_beskeder:
                    # Vi tager den nyeste besked (den første i listen) og redigerer den
                    primær_besked = bottens_beskeder[0]
                    await primær_besked.edit(content=skema_tekst, attachments=[discord_fil])
                    print("[INFO] Opdaterede det nyeste skemabillede.")

                    # Hvis der ligger ANDRE gamle beskeder fra botten (hvis index > 0), sletter vi dem!
                    if len(bottens_beskeder) > 1:
                        for gammel_lortebeskis in bottens_beskeder[1:]:
                            try:
                                await gammel_lortebeskis.delete()
                                print("[INFO] Slettede en overflødig, gammel skemabesked for at holde kanalen ren.")
                            except Exception:
                                pass # Ignorer hvis den ikke kunne slette en enkelt besked
                else:
                    # Hvis kanalen er helt tom, sender vi en ny besked
                    await skema_channel.send(content=skema_tekst, file=discord_fil)
                    print("[INFO] Sendte et helt nyt skemabillede, da kanalen var tom.")

                # SEND NOTIFIKATION I DEN ANDEN KANAL
                if notif_channel:
                    await notif_channel.send(
                        content=f"🚨 **Besked fra Zealand:** Der er sket en ændring i jeres ugeskema! Tjek det opdaterede skema i <#{SKEMA_CHANNEL_ID}>."
                    )
                    print("[INFO] Sendte alarm til notifikations-kanalen.")

            except Exception as e:
                print(f"Fejl under automatisk opdatering: {e}")
    
client = MyClient()

def clean_subject_name(summary):
    """Renser og forenkler fagnavnene fra Zealand/TimeEdit"""
    if not summary:
        return "Undervisning"
        
    summary_lower = summary.lower()
    if "fredagsbar" in summary_lower or "fredagskafe" in summary_lower:
        return "Fredagsbar"
    elif "programmering" in summary_lower:
        return "Programmering"
    elif "systemudvikling" in summary_lower:
        return "Systemudvikling"
    elif "forretningsforståelse" in summary_lower or "it og forretning" in summary_lower:
        return "IT & forretningsforståelse"
    elif "teknologi" in summary_lower:
        return "Teknologi"
    
    parts = summary.split(',')
    first_part = parts[0].split('-')[0]
    return first_part.strip()[:20]

def get_live_week_schedule_with_raw(valgt_uge=None):
    headers = {'User-Agent': 'iCalExchange/2.0', 'Accept': 'text/calendar'}
    try:
        response = requests.get(ICS_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, None, None, False, None
        gcal = Calendar.from_ical(response.content)
    except Exception:
        return None, None, None, False, None
    
    local_tz = pytz.timezone('Europe/Copenhagen')
    nu_lokal = datetime.now(local_tz)
    
    if valgt_uge is None and nu_lokal.weekday() >= 5:
        nu_lokal = nu_lokal + timedelta(days=7 - nu_lokal.weekday())

    if valgt_uge is not None:
        nuværende_aar = nu_lokal.year
        jan4 = datetime(nuværende_aar, 1, 4)
        start_af_aaret = jan4 - timedelta(days=jan4.weekday())
        start_af_ugen = start_af_aaret + timedelta(weeks=valgt_uge - 1)
        start_af_ugen = local_tz.localize(start_af_ugen).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_af_ugen = nu_lokal - timedelta(days=nu_lokal.weekday())
        start_af_ugen = start_af_ugen.replace(hour=0, minute=0, second=0, microsecond=0)
        
    slut_af_ugen = start_af_ugen + timedelta(days=7)

    uge_skema = {0: [], 1: [], 2: [], 3: [], 4: []}
    fredag_har_fredagsbar = False
    
    for component in gcal.walk():
        if component.name == "VEVENT":
            start = component.get('dtstart').dt
            slut = component.get('dtend').dt
            summary = str(component.get('summary', 'Undervisning'))
            location = str(component.get('location', 'Ikke angivet'))

            if isinstance(start, datetime):
                start = start.astimezone(local_tz) if start.tzinfo else pytz.utc.localize(start).astimezone(local_tz)
                slut = slut.astimezone(local_tz) if slut.tzinfo else pytz.utc.localize(slut).astimezone(local_tz)
                
                if start_af_ugen <= start < slut_af_ugen:
                    dag_index = start.weekday()
                    if 0 <= dag_index <= 4:
                        clean_name = clean_subject_name(summary)
                        
                        if clean_name == "Fredagsbar":
                            if dag_index == 4:
                                fredag_har_fredagsbar = True
                            continue
                        
                        location_parts = location.split(',')
                        clean_location = location_parts[0].strip() if location_parts else location.strip()
                        
                        uge_skema[dag_index].append({
                            'start': start,
                            'slut': slut,
                            'summary': clean_name,
                            'location': clean_location,
                            'is_pause': False
                        })
    
    # Sorterer kun timerne kronologisk uden at indsætte pauser
    for dag in uge_skema:
        uge_skema[dag].sort(key=lambda x: x['start'])
        
    return uge_skema, start_af_ugen, (slut_af_ugen - timedelta(days=1)), fredag_har_fredagsbar, response.content

def wrap_text(text, width=18):
    if not text:
        return ""
    if "IT & forretningsforståelse" in text:
        width = 30
    lines = textwrap.wrap(text, width=width)
    return "\n".join(lines)

def generate_table_image(uge_skema, start_af_ugen, slut_af_ugen, fredag_har_fredagsbar):
    maaneder = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    kolonne_navne = ["      Tidspunkt      ", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
    
    for i in range(5):
        dag_dato = start_af_ugen + timedelta(days=i)
        dato_streng = f"{dag_dato.strftime('%d')}. {maaneder[dag_dato.month - 1]}"
        kolonne_navne[i+1] = f"{kolonne_navne[i+1]}\n{dato_streng}"
    
    alle_tider = set()
    for dag in uge_skema:
        for lek in uge_skema[dag]:
            alle_tider.add((lek['start'].strftime("%H:%M"), lek['slut'].strftime("%H:%M")))
    
    sorterede_tidsintervaller = sorted(list(alle_tider), key=lambda x: x)
    
    rækker = []
    for række_idx, (t_start, t_slut) in enumerate(sorterede_tidsintervaller):
        række = [f"{t_start} - {t_slut}"]
        
        for dag_index in range(5):
            match_fundet = False
            for lek in uge_skema[dag_index]:
                if lek['start'].strftime("%H:%M") == t_start and lek['slut'].strftime("%H:%M") == t_slut:
                    wrapped_summary = wrap_text(lek['summary'], width=16)
                    række.append(f"{wrapped_summary}\nLokale: {lek['location']}") # Emojien '📍' er fjernet
                    match_fundet = True
                    break
            if not match_fundet:
                række.append("—")
        rækker.append(række)

    beregnet_højde = 1.5 + len(sorterede_tidsintervaller) * 1.5
    fig, ax = plt.subplots(figsize=(14, min(beregnet_højde, 9.5)), dpi=200)
    ax.axis('off')

    tabel = ax.table(cellText=rækker, colLabels=kolonne_navne, cellLoc='center', loc='center')
    tabel.auto_set_font_size(False)
    tabel.set_fontsize(9.5)
    tabel.scale(1.0, 4.2)

    # Kolonneoverskrifter (Række 0)
    for j in range(6):
        celle = tabel[0, j]
        if j == 0:
            celle.set_facecolor('#34495e') 
        elif j == 5 and fredag_har_fredagsbar:
            celle.set_facecolor('#e74c3c') 
        else:
            celle.set_facecolor('#2ecc71') 
        celle.get_text().set_color('white')
        celle.get_text().set_weight('bold')
        celle.set_height(0.15)

    # Tidskolonnen (Kolonne 0)
    for i in range(1, len(sorterede_tidsintervaller) + 1):
        celle = tabel[i, 0]
        celle.set_facecolor('#f8f9fa')
        celle.get_text().set_weight('bold')
        celle.get_text().set_color('#2c3e50')

    # Gør fagnavnene større og med fed skrift
    for i in range(1, len(sorterede_tidsintervaller) + 1):
        for j in range(1, 6):
            celle = tabel[i, j]
            tekst = celle.get_text().get_text()
            
            if tekst and tekst != "—" and tekst != "":
                lines = tekst.split('\n')
                if len(lines) >= 2:
                    fag_tekst = lines[0] # Rettet til indeks 0
                    lokale_tekst = lines[1] # Rettet til indeks 1
                    
                    celle.get_text().set_text(f"{fag_tekst}\n{lokale_tekst}")
                    celle.get_text().set_weight('bold')
                    celle.get_text().set_fontsize(10.5)
                    celle.get_text().set_color('#2c3e50')

    uge_nummer = start_af_ugen.isocalendar()[1] # Tilføjet indeks [1]
    plt.title(f"Zealand Ugeskema — Uge {uge_nummer}", fontsize=14, weight='bold', pad=30, color='#2c3e50') # Emojien '📅' er fjernet

    local_tz = pytz.timezone('Europe/Copenhagen')
    nu_tid = datetime.now(local_tz).strftime("%d.%m.%Y kl. %H:%M:%S")
    fig.text(0.98, 0.96, f"Genereret: {nu_tid}", fontsize=7, color='#7f8c8d', ha='right', style='italic')

    fig.tight_layout()

    billede_buffer = io.BytesIO()
    plt.savefig(billede_buffer, format='png', bbox_inches='tight')
    billede_buffer.seek(0)
    plt.close()
    
    return billede_buffer

def get_weeks_with_lessons():
    """Løber hele TimeEdit-kalenderen igennem og finder uger med planlagt undervisning"""
    headers = {'User-Agent': 'iCalExchange/2.0', 'Accept': 'text/calendar'}
    try:
        response = requests.get(ICS_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        gcal = Calendar.from_ical(response.content)
    except Exception:
        return None

    local_tz = pytz.timezone('Europe/Copenhagen')
    aktive_uger = set()

    for component in gcal.walk():
        if component.name == "VEVENT":
            start = component.get('dtstart').dt
            summary = str(component.get('summary', ''))
            
            if isinstance(start, datetime):
                start = start.astimezone(local_tz) if start.tzinfo else pytz.utc.localize(start).astimezone(local_tz)
                clean_name = clean_subject_name(summary)
                
                if clean_name not in ["Fredagsbar", "Pause", "Undervisning"]:
                    uge_nummer = start.isocalendar()[1] # Tilføjet indeks [1]
                    aktive_uger.add(uge_nummer)
                    
    return sorted(list(aktive_uger))

@client.event
async def on_ready():
    print(f'Botten er online som {client.user}')

@client.tree.command(name="schedule", description="Viser dit ugeskema som et flot, rent tabelfoto med datoer")
@app_commands.describe(uge="Valgfrit ugenummer (f.eks. 38 eller 39) for at se historiske uger")
async def schedule(interaction: discord.Interaction, uge: int = None):
    await interaction.response.defer()
    try:
        uge_skema, start_date, end_date, fredag_bar, _ = get_live_week_schedule_with_raw(valgt_uge=uge)
        
        if uge_skema is None:
            await interaction.followup.send("❌ Kunne ikke hente skemaet live fra Zealand.")
            return
            
        har_data = any(len(uge_skema[i]) > 0 for i in range(5))
        if not har_data and uge is not None:
            await interaction.followup.send(f"🤷‍♂️ Fandt ingen skemadata i TimeEdit for uge {uge}.")
            return

        billede_data = generate_table_image(uge_skema, start_date, end_date, fredag_bar)
        discord_fil = discord.File(fp=billede_data, filename='ugeskema.png')
        await interaction.followup.send(content="Herefter er dit ugeskema:", file=discord_fil)
    except Exception as e:
        print(f"Fejl: {e}")
        await interaction.followup.send("❌ Der skete en fejl under genereringen af skemabilledet.")

@client.tree.command(name="schedule-info", description="Viser hvilke uger der rent faktisk har planlagt undervisning")
async def schedule_info(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        uger = get_weeks_with_lessons()
        
        if uger is None:
            await interaction.followup.send("❌ Kunne ikke læse skemadata fra TimeEdit lige nu.")
            return
            
        if not uger:
            await interaction.followup.send("🤷‍♂️ There is no schedule data entered into TimeEdit yet.")
            return

        uger_tekst = ", ".join([f"Uge {u}" for u in uger])

        embed = discord.Embed(
            title="ℹ️ Planlagte undervisningsuger",
            description="Zealand har lagt skema ind for følgende uger:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📅 Aktive uger med fag", 
            value=f"```text\n{uger_tekst}\n```", 
            inline=False
        )
        
        embed.add_field(
            name="💡 Tip", 
            value="Hvis en uge mangler på listen (f.eks. uge 42), betyder det, at I enten har ferie, eller at Zealand ikke har tastet skemaet ind endnu.", 
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Ansvarsfraskrivelse / Disclaimer", 
            value="Dette skema hentes automatisk og er kun vejledende. **Tjek altid Moodle for de seneste officielle opdateringer og beskeder!** Skaberne af denne bot står ikke til ansvar for eventuelle fejl, aflysninger eller misstoffer.", 
            inline=False
        )
        
        embed.set_footer(text="Opdateret live fra Zealand TimeEdit")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Fejl i schedule-info: {e}")
        await interaction.followup.send("❌ Der skete en fejl under optællingen af ugerne.")

client.run(TOKEN)
