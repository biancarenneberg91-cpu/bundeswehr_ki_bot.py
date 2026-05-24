import discord
from discord.ext import commands
from gtts import gTTS
import asyncio
import os

TOKEN = os.getenv("KI_TOKEN")

# =========================================
# IDs
# =========================================

BEWERBUNG_CATEGORY_ID = 1504190916737368328
PANEL_CHANNEL_ID = 1504203869130064035

WARTERAUM_VOICE_CHANNEL_ID = 1506271397591126078
BUERO_VOICE_CHANNEL_ID = 1506271506454544548

# =========================================
# BOT
# =========================================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

processing_tickets = set()

# =========================================
# HELPER
# =========================================

def kanal(guild, name):
    return discord.utils.get(
        guild.text_channels,
        name=name
    )

# =========================================
# TTS
# =========================================

async def bot_speak(guild, text):

    try:

        channel = guild.get_channel(
            BUERO_VOICE_CHANNEL_ID
        )

        if not channel:
            print("❌ Büro Voicechannel nicht gefunden.")
            return

        if guild.voice_client:

            vc = guild.voice_client

            if vc.channel != channel:

                await vc.move_to(channel)
                await asyncio.sleep(1)

        else:

            vc = await asyncio.wait_for(
                channel.connect(),
                timeout=20
            )

            await asyncio.sleep(1)

        tts = gTTS(
            text=text,
            lang="de"
        )

        tts.save("tts.mp3")

        if vc.is_playing():
            vc.stop()

        audio = discord.FFmpegPCMAudio(
            "tts.mp3",
            executable="ffmpeg"
        )

        vc.play(audio)

    except Exception as e:
        print(f"VOICE FEHLER: {e}")

# =========================================
# MOVE
# =========================================

async def move_to_buero(member):

    try:

        if not member.voice:
            return False

        if member.voice.channel.id != WARTERAUM_VOICE_CHANNEL_ID:
            return False

        buero = member.guild.get_channel(
            BUERO_VOICE_CHANNEL_ID
        )

        if not buero:
            return False

        await member.move_to(buero)

        return True

    except Exception as e:
        print(f"MOVE FEHLER: {e}")

    return False

# =========================================
# KI CHECK
# =========================================

def bewerbung_check(text):

    punkte = 100
    analyse = []

    lower = text.lower()

    fehlend = []

    for p in [
        "1.",
        "2.",
        "3.",
        "4.",
        "5.",
        "6.",
        "7.",
        "8.",
        "9."
    ]:

        if p not in lower:
            fehlend.append(p)

    if fehlend:

        punkte -= len(fehlend) * 10

        analyse.append(
            f"❌ Fehlende Fragen: {', '.join(fehlend)}"
        )

    if len(text) < 300:

        punkte -= 20

        analyse.append(
            "❌ Bewerbung zu kurz."
        )

    gute_woerter = [
        "team",
        "respekt",
        "disziplin",
        "aktiv",
        "bundeswehr",
        "einsatz",
        "lernen",
        "erfahrung"
    ]

    gefunden = 0

    for wort in gute_woerter:

        if wort in lower:
            gefunden += 1

    if gefunden >= 5:

        punkte += 10

        analyse.append(
            "✅ Gute Motivation erkannt."
        )

    elif gefunden >= 3:

        analyse.append(
            "🟡 Motivation vorhanden."
        )

    else:

        punkte -= 20

        analyse.append(
            "❌ Zu wenig Motivation."
        )

    schlechte_woerter = [
        "hurensohn",
        "niga",
        "spast",
        "opfer",
        "kacke"
    ]

    for wort in schlechte_woerter:

        if wort in lower:

            punkte -= 80

            analyse.append(
                "❌ Beleidigungen erkannt."
            )

            break

    punkte = max(
        0,
        min(100, punkte)
    )

    if fehlend:
        entscheidung = "UNVOLLSTÄNDIG"

    elif punkte >= 70:
        entscheidung = "ANGENOMMEN"

    else:
        entscheidung = "ABGELEHNT"

    return (
        punkte,
        analyse,
        entscheidung,
        fehlend
    )

# =========================================
# VIEW
# =========================================

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
            placeholder="Bundeswehr Bewerbung",
            options=options,
            custom_id="bundeswehr_bewerbung"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        category = guild.get_channel(
            BEWERBUNG_CATEGORY_ID
        )

        if not category:

            return await interaction.response.send_message(
                "❌ Kategorie nicht gefunden.",
                ephemeral=True
            )

        name = interaction.user.name.lower().replace(
            " ",
            "-"
        )

        channel_name = f"bewerbung-{name}"

        existing = discord.utils.get(
            guild.text_channels,
            name=channel_name
        )

        if existing:

            return await interaction.response.send_message(
                f"⚠️ Ticket existiert bereits: {existing.mention}",
                ephemeral=True
            )

        overwrites = {

            guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),

            guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
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

                "Bitte beantworte alles in EINER Nachricht.\n\n"

                "1. Wie alt sind sie?\n"
                "2. Wie heißen sie?\n"
                "3. Wie lange spielen sie schon Notruf Hamburg RP?\n"
                "4. Wie gut sind sie im Schießen?\n"
                "5. Warum wollen sie zur Bundeswehr?\n"
                "6. Was bringen sie mit?\n"
                "7. Warum sollen wir sie nehmen?\n"
                "8. Welche Kategorie wollen sie?\n"
                "9. Sind sie bereit für ein Gespräch?\n\n"

                "⏳ Automatische Prüfung nach 60 Sekunden.\n"
                "🔊 Wenn sie im Warteraum sind, werden sie verschoben."

            ),

            color=0x2E8B57

        )

        await channel.send(
            interaction.user.mention,
            embed=embed
        )

        moved = await move_to_buero(
            interaction.user
        )

        if moved:

            await bot_speak(

                guild,

                f"Willkommen {interaction.user.display_name}. "
                f"Sie wurden in das Bewerbungsbüro verschoben."

            )

        else:

            await bot_speak(

                guild,

                f"Neue Bewerbung von "
                f"{interaction.user.display_name} "
                f"wurde erstellt."

            )

        await interaction.response.send_message(
            f"✅ Bewerbung erstellt: {channel.mention}",
            ephemeral=True
        )

class BewerbungView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            BewerbungSelect()
        )

# =========================================
# READY
# =========================================

@bot.event
async def on_ready():

    print(f"{bot.user} online!")

    bot.add_view(
        BewerbungView()
    )

    try:

        synced = await bot.tree.sync()

        print(f"{len(synced)} Commands geladen.")

    except Exception as e:
        print(f"SYNC FEHLER: {e}")

# =========================================
# PANEL
# =========================================

@bot.tree.command(
    name="bewerbung_panel",
    description="Sendet Bewerbungspanel"
)
async def bewerbung_panel(
    interaction: discord.Interaction
):

    embed = discord.Embed(

        title="📋 Bundeswehr Bewerbung",

        description=(
            "Klicke unten zum Bewerben."
        ),

        color=0x2E8B57

    )

    panel = interaction.guild.get_channel(
        PANEL_CHANNEL_ID
    )

    if not panel:

        return await interaction.response.send_message(
            "❌ Panelchannel nicht gefunden.",
            ephemeral=True
        )

    await panel.send(
        embed=embed,
        view=BewerbungView()
    )

    await interaction.response.send_message(
        "✅ Panel gesendet.",
        ephemeral=True
    )

# =========================================
# SAY
# =========================================

@bot.tree.command(
    name="sagen",
    description="Bot spricht"
)
async def sagen(
    interaction: discord.Interaction,
    text: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    await bot_speak(
        interaction.guild,
        text
    )

    await interaction.followup.send(
        "🔊 Bot hat gesprochen.",
        ephemeral=True
    )

# =========================================
# ZELLO
# =========================================

@bot.tree.command(name="zello", description="Zeigt die Zello Funk Anleitung")
async def zello(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📻 Bundeswehr Zello Funk",
        description=(
            "📲 **Zello herunterladen**\n"
            "Android / iPhone / PC\n"
            "https://zello.com\n\n"
            "📷 **QR-Code**\n"
            "Der QR-Code wird später separat gesendet.\n\n"
            "🎤 **Funkname einstellen**\n"
            "Beispiele:\n"
            "• BW_Phil\n"
            "• BW_Max\n"
            "• BW_Leitung\n\n"
            "📡 **Funk Regeln**\n"
            "✅ Kurz sprechen\n"
            "✅ Kein Reinreden\n"
            "✅ Funkdisziplin\n"
            "✅ Keine Musik / Trolls"
        ),
        color=0x8B0000
    )

    await interaction.response.send_message(embed=embed)

    await interaction.response.send_message(
        embed=embed,
        file=file
    )

# =========================================
# DEBUG
# =========================================

@bot.tree.command(
    name="debug_voice",
    description="Voice Test"
)
async def debug_voice(
    interaction: discord.Interaction
):

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        channel = interaction.guild.get_channel(
            BUERO_VOICE_CHANNEL_ID
        )

        if not channel:

            return await interaction.followup.send(
                "❌ Büro nicht gefunden.",
                ephemeral=True
            )

        if interaction.guild.voice_client:

            await interaction.guild.voice_client.move_to(
                channel
            )

        else:

            await channel.connect()

        await interaction.followup.send(
            f"✅ Bot ist {channel.name} gejoint.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ FEHLER: {e}",
            ephemeral=True
        )

# =========================================
# CLOSE
# =========================================

@bot.tree.command(
    name="close",
    description="Schließt Ticket"
)
async def close(
    interaction: discord.Interaction
):

    if not interaction.channel.name.startswith(
        "bewerbung-"
    ):

        return await interaction.response.send_message(
            "❌ Kein Bewerbungsticket.",
            ephemeral=True
        )

    await interaction.response.send_message(
        "🔒 Ticket wird geschlossen.",
        ephemeral=True
    )

    await asyncio.sleep(3)

    await interaction.channel.delete()

# =========================================
# MESSAGE
# =========================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    await bot.process_commands(message)

    if not message.channel.name.startswith(
        "bewerbung-"
    ):
        return

    if message.channel.id in processing_tickets:
        return

    processing_tickets.add(
        message.channel.id
    )

    await message.channel.send(

        "🤖 Bewerbung erkannt.\n"
        "Prüfung startet in 60 Sekunden."

    )

    await bot_speak(

        message.guild,

        f"Bewerbung von "
        f"{message.author.display_name} "
        f"wird überprüft."

    )

    await asyncio.sleep(60)

    messages = []

    async for msg in message.channel.history(
        limit=50,
        oldest_first=True
    ):

        if not msg.author.bot:
            messages.append(msg.content)

    text = "\n".join(messages)

    punkte, analyse, entscheidung, fehlend = bewerbung_check(
        text
    )

    if entscheidung == "UNVOLLSTÄNDIG":

        await message.channel.send(

            "⚠️ Bewerbung unvollständig.\n"
            f"Fehlend: {', '.join(fehlend)}"

        )

        await bot_speak(

            message.guild,

            f"Die Bewerbung von "
            f"{message.author.display_name} "
            f"ist unvollständig."

        )

        processing_tickets.discard(
            message.channel.id
        )

        return

    if entscheidung == "ANGENOMMEN":

        farbe = 0x00FF00
        titel = "✅ Bewerbung angenommen"

        voice_text = (
            f"Bewerbung von "
            f"{message.author.display_name} "
            f"wurde angenommen."
        )

    else:

        farbe = 0xFF0000
        titel = "❌ Bewerbung abgelehnt"

        voice_text = (
            f"Bewerbung von "
            f"{message.author.display_name} "
            f"wurde abgelehnt."
        )

    embed = discord.Embed(
        title=titel,
        color=farbe
    )

    embed.add_field(
        name="👤 Bewerber",
        value=message.author.mention,
        inline=False
    )

    embed.add_field(
        name="📊 Bewertung",
        value=f"{punkte}/100",
        inline=True
    )

    embed.add_field(
        name="📝 Analyse",
        value="\n".join(analyse),
        inline=False
    )

    await message.channel.send(
        embed=embed
    )

    await bot_speak(
        message.guild,
        voice_text
    )

    await message.channel.send(
        "🔒 Ticket wird in 15 Sekunden geschlossen."
    )

    await asyncio.sleep(30)

    try:
        await message.channel.delete()

    except Exception as e:
        print(f"LÖSCH FEHLER: {e}")

    processing_tickets.discard(
        message.channel.id
    )
# =========================================
# UPRANK COMMAND
# =========================================

@bot.tree.command(
    name="uprank",
    description="Sendet eine Beförderungs Nachricht"
)
async def uprank(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    user: discord.Member,
    von: str,
    auf: str,
    grund: str
):

    embed = discord.Embed(
        title="🚨 | Upranks",
        color=0x2E8B57
    )

    embed.add_field(
        name="Wer:",
        value=user.mention,
        inline=False
    )

    embed.add_field(
        name="Von:",
        value=von,
        inline=True
    )

    embed.add_field(
        name="Auf:",
        value=auf,
        inline=True
    )

    embed.add_field(
        name="🪖 Grund:",
        value=grund,
        inline=False
    )

    embed.set_footer(
        text="Bundeswehr Beförderungssystem"
    )

    await channel.send(
        embed=embed
    )

    await interaction.response.send_message(
        f"✅ Uprank wurde in {channel.mention} gesendet.",
        ephemeral=True
    )
bot.run(TOKEN)
