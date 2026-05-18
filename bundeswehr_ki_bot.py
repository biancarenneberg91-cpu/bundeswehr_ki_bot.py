import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
from gtts import gTTS

TOKEN = os.getenv("KI_TOKEN")

GUILD_ID = 123456789012345678  # DEINE SERVER ID
BEWERBUNG_CATEGORY_ID = 1504190916737368328
PANEL_CHANNEL_ID = 1504203869130064035

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

processing_tickets = set()


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


def bewerbung_auswerten(text):
    punkte = 100
    analyse = []
    lower = text.lower()

    fehlend = [p for p in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."] if p not in lower]

    if fehlend:
        punkte -= len(fehlend) * 10
        analyse.append(f"❌ Fehlende Punkte: {', '.join(fehlend)}")

    if len(text) < 350:
        punkte -= 25
        analyse.append("❌ Bewerbung ist zu kurz.")

    gute = [
        "team", "respekt", "disziplin", "aktiv",
        "bundeswehr", "helfen", "einsatz",
        "erfahrung", "lernen"
    ]

    gefunden = sum(1 for wort in gute if wort in lower)

    if gefunden >= 5:
        punkte += 10
        analyse.append("✅ Gute Motivation erkannt.")
    elif gefunden >= 3:
        analyse.append("🟡 Motivation teilweise erkennbar.")
    else:
        punkte -= 20
        analyse.append("❌ Wenig Motivation erkannt.")

    schlechte = [
        "hurensohn", "nigger", "niga", "hs",
        "opfer", "spast", "kacke", "scheiße"
    ]

    if any(wort in lower for wort in schlechte):
        punkte -= 80
        analyse.append("❌ Unangemessene Wörter erkannt.")

    if "ja" in lower:
        analyse.append("✅ Gesprächsbereitschaft erkannt.")
    else:
        punkte -= 10
        analyse.append("🟡 Gesprächsbereitschaft unklar.")

    punkte = max(0, min(100, punkte))

    if fehlend:
        entscheidung = "UNVOLLSTÄNDIG"
    elif punkte >= 70:
        entscheidung = "ANGENOMMEN"
    else:
        entscheidung = "ABGELEHNT"

    return punkte, analyse, entscheidung, fehlend


async def speak(interaction, text, file_name="tts.mp3"):
    if not interaction.user.voice:
        await interaction.followup.send("❌ Du bist in keinem Voicechannel.", ephemeral=True)
        return

    voice_channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        vc = interaction.guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    tts = gTTS(text=text, lang="de")
    tts.save(file_name)

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio(file_name))


class BewerbungSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Bundeswehr",
                description="Bewerbung starten",
                emoji="🪖"
            )
        ]

        super().__init__(
            placeholder="Bundeswehr",
            options=options,
            custom_id="bundeswehr_bewerbung_select"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(BEWERBUNG_CATEGORY_ID)

        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "❌ Bewerbungs-Kategorie wurde nicht gefunden.",
                ephemeral=True
            )

        safe_name = interaction.user.name.lower().replace(" ", "-")
        channel_name = f"bewerbung-{safe_name}"

        existing = discord.utils.get(guild.text_channels, name=channel_name)

        if existing:
            return await interaction.response.send_message(
                f"⚠️ Du hast bereits eine Bewerbung: {existing.mention}",
                ephemeral=True
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🪖 Bundeswehr Bewerbung",
            description=(
                f"Willkommen {interaction.user.mention}!\n\n"
                "Bitte beantworte folgende Fragen **in einer Nachricht**:\n\n"
                "1. Wie alt sind sie?\n"
                "2. Wie heißen sie?\n"
                "3. Wie lange spielen sie schon RP?\n"
                "4. Wie gut sind sie im Schießen?\n"
                "5. Warum wollen sie zur Bundeswehr?\n"
                "6. Was bringen sie mit?\n"
                "7. Warum sollen wir uns für sie entscheiden?\n"
                "8. Für welche Kategorie wollen sie?\n"
                "9. Sind sie bereit für ein Gespräch? Ja/Nein\n\n"
                "⏳ Nach deiner Nachricht wartet der Bot **60 Sekunden** und entscheidet automatisch."
            ),
            color=0x2E8B57
        )

        await channel.send(interaction.user.mention, embed=embed)

        await interaction.response.send_message(
            f"✅ Bewerbung erstellt: {channel.mention}",
            ephemeral=True
        )


class BewerbungView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BewerbungSelect())


@bot.event
async def on_ready():
    print(f"{bot.user} All-In-One System online!")

    bot.add_view(BewerbungView())

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"{len(synced)} Commands geladen.")


@bot.tree.command(name="setup", description="Erstellt alle wichtigen Channels")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    for ch in ["bewerbungs-check", "annahmen", "ablehnungen", "logs", "alarmierungen", "bw-funk"]:
        if not kanal(interaction.guild, ch):
            await interaction.guild.create_text_channel(ch)

    await interaction.followup.send("✅ Setup fertig.", ephemeral=True)


@bot.tree.command(name="bewerbung_panel", description="Sendet das Bewerbungs-Panel")
async def bewerbung_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    panel_channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

    if not panel_channel:
        return await interaction.response.send_message("❌ Panel-Channel wurde nicht gefunden.", ephemeral=True)

    embed = discord.Embed(
        title="📋 Bewerbungssystem",
        description="**Bundeswehr**\nBewerbt euch gerne über das Menü unten.",
        color=0x2E8B57
    )

    await panel_channel.send(embed=embed, view=BewerbungView())
    await interaction.response.send_message("✅ Bewerbungs-Panel wurde gesendet.", ephemeral=True)


@bot.tree.command(name="voice_join", description="Bot joint deinen Voicechannel")
async def voice_join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Du bist in keinem Voicechannel.", ephemeral=True)

    voice_channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()

    await interaction.response.send_message(f"✅ Bot ist {voice_channel.name} beigetreten.", ephemeral=True)


@bot.tree.command(name="sagen", description="Bot spricht im Voice")
async def sagen(interaction: discord.Interaction, text: str):
    await interaction.response.defer(ephemeral=True)
    await speak(interaction, text, "tts.mp3")
    await interaction.followup.send("🔊 Bot spricht jetzt.", ephemeral=True)


@bot.tree.command(name="alarm_voice", description="Alarmansage im Voice")
async def alarm_voice(interaction: discord.Interaction, stufe: str, ort: str):
    await interaction.response.defer(ephemeral=True)

    text = (
        f"Achtung Achtung. Alarmstufe {stufe}. "
        f"Einsatzort {ort}. Alle verfügbaren Einheiten sofort antreten."
    )

    await speak(interaction, text, "alarm.mp3")
    await interaction.followup.send("🚨 Alarmansage abgespielt.", ephemeral=True)


@bot.tree.command(name="voice_leave", description="Bot verlässt Voice")
async def voice_leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ Bot hat Voice verlassen.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot ist in keinem Voicechannel.", ephemeral=True)


@bot.tree.command(name="close_bewerbung", description="Schließt ein Bewerbungsticket")
async def close_bewerbung(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    if interaction.channel.name.startswith("bewerbung-"):
        await interaction.response.send_message("✅ Ticket wird geschlossen.", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()
    else:
        await interaction.response.send_message("❌ Das ist kein Bewerbungsticket.", ephemeral=True)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if not message.channel.name.startswith("bewerbung-"):
        return

    if not message.channel.category or message.channel.category.id != BEWERBUNG_CATEGORY_ID:
        return

    if message.channel.id in processing_tickets:
        return

    processing_tickets.add(message.channel.id)

    await message.channel.send(
        "🤖 Bewerbung erkannt.\n"
        "Ich warte jetzt **60 Sekunden**, damit alles vollständig geschrieben werden kann."
    )

    await asyncio.sleep(60)

    messages = []

    async for msg in message.channel.history(limit=50, oldest_first=True):
        if not msg.author.bot:
            messages.append(f"{msg.author}: {msg.content}")

    kompletter_text = "\n".join(messages)

    punkte, analyse, entscheidung, fehlend = bewerbung_auswerten(kompletter_text)

    check_channel = kanal(message.guild, "bewerbungs-check")

    check_embed = discord.Embed(
        title="🤖 Bewerbungsprüfung",
        color=0x3498db
    )
    check_embed.add_field(name="👤 Bewerber", value=message.author.mention, inline=False)
    check_embed.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
    check_embed.add_field(name="📌 Entscheidung", value=entscheidung, inline=True)
    check_embed.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)
    check_embed.add_field(name="📥 Ticket", value=message.channel.mention, inline=False)
    check_embed.timestamp = datetime.now()

    if check_channel:
        await check_channel.send(embed=check_embed)

    if entscheidung == "UNVOLLSTÄNDIG":
        await message.channel.send(
            "⚠️ Bewerbung unvollständig.\n"
            f"Fehlende Punkte: **{', '.join(fehlend)}**\n\n"
            "Bitte ergänze die fehlenden Antworten. Danach prüfe ich erneut."
        )
        processing_tickets.discard(message.channel.id)
        return

    if entscheidung == "ANGENOMMEN":
        ziel_channel = kanal(message.guild, "annahmen")
        farbe = 0x00FF00
        titel = "✅ Bewerbung angenommen"
        dm_text = "Glückwunsch! Deine Bewerbung wurde angenommen."
    else:
        ziel_channel = kanal(message.guild, "ablehnungen")
        farbe = 0xFF0000
        titel = "❌ Bewerbung abgelehnt"
        dm_text = "Deine Bewerbung wurde leider abgelehnt."

    embed = discord.Embed(title=titel, color=farbe)
    embed.add_field(name="👤 Bewerber", value=message.author.mention, inline=False)
    embed.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
    embed.add_field(name="📌 Entscheidung", value=entscheidung, inline=True)
    embed.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)
    embed.add_field(name="📥 Ticket", value=message.channel.mention, inline=False)
    embed.timestamp = datetime.now()

    if ziel_channel:
        await ziel_channel.send(embed=embed)

    await message.channel.send(embed=embed)

    try:
        dm = discord.Embed(title=titel, description=dm_text, color=farbe)
        dm.add_field(name="📊 Bewertung", value=f"{punkte}/100")
        dm.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)
        await message.author.send(embed=dm)
    except:
        print("DM konnte nicht gesendet werden.")

    await message.channel.send("🔒 Dieses Bewerbungsticket wird in **30 Sekunden** automatisch geschlossen.")

    await asyncio.sleep(30)

    try:
        await message.channel.delete()
    except:
        print("Ticket konnte nicht gelöscht werden.")

    processing_tickets.discard(message.channel.id)


bot.run(TOKEN)
