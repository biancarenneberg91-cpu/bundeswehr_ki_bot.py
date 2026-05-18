import discord
from discord.ext import commands
from gtts import gTTS
import asyncio
import os
from datetime import datetime

TOKEN = os.getenv("KI_TOKEN")

GUILD_ID = 1504190915235811360  # DEINE SERVER ID

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

    gute_woerter = [
        "team", "respekt", "disziplin", "aktiv",
        "bundeswehr", "helfen", "einsatz",
        "lernen", "erfahrung"
    ]

    gefunden = sum(1 for wort in gute_woerter if wort in lower)

    if gefunden >= 5:
        punkte += 10
        analyse.append("✅ Gute Motivation erkannt.")
    elif gefunden >= 3:
        analyse.append("🟡 Motivation teilweise erkannt.")
    else:
        punkte -= 20
        analyse.append("❌ Wenig Motivation erkannt.")

    schlechte_woerter = [
        "hurensohn", "niga", "nigger",
        "hs", "opfer", "spast", "kacke"
    ]

    if any(wort in lower for wort in schlechte_woerter):
        punkte -= 80
        analyse.append("❌ Schlechte Wörter erkannt.")

    if "ja" in lower:
        analyse.append("✅ Gesprächsbereit.")
    else:
        punkte -= 10
        analyse.append("🟡 Gespräch unklar.")

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

    ffmpeg_paths = [
        "/usr/bin/ffmpeg",
        "/bin/ffmpeg",
        "ffmpeg"
    ]

    last_error = None

    for path in ffmpeg_paths:
        try:
            audio = discord.FFmpegPCMAudio(
                file_name,
                executable=path
            )
            vc.play(audio)
            await interaction.followup.send("🔊 Bot spricht jetzt.", ephemeral=True)
            return
        except Exception as e:
            last_error = e

    await interaction.followup.send(
        f"❌ FFmpeg Fehler: {last_error}",
        ephemeral=True
    )
    print(f"FFmpeg Fehler: {last_error}")


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
                "❌ Bewerbungs-Kategorie nicht gefunden.",
                ephemeral=True
            )

        safe_name = interaction.user.name.lower().replace(" ", "-")
        channel_name = f"bewerbung-{safe_name}"

        existing = discord.utils.get(guild.text_channels, name=channel_name)

        if existing:
            return await interaction.response.send_message(
                f"⚠️ Du hast bereits ein Bewerbungsticket: {existing.mention}",
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
                "Bitte beantworte alles in **EINER Nachricht**:\n\n"
                "1. Wie alt sind sie?\n"
                "2. Wie heißen sie?\n"
                "3. Wie lange spielen sie schon Notruf Hamburg RP?\n"
                "4. Wie gut sind sie im Schießen?\n"
                "5. Warum wollen sie zur Bundeswehr?\n"
                "6. Was bringen sie mit?\n"
                "7. Warum sollen wir uns für sie entscheiden?\n"
                "8. Für welche Kategorie wollen sie?\n"
                "9. Sind sie bereit für ein Gespräch? Ja/Nein\n\n"
                "⏳ Nach deiner Nachricht wartet der Bot **60 Sekunden** und prüft automatisch."
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

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"{len(synced)} Commands geladen.")
    except Exception as e:
        print(f"Command Sync Fehler: {e}")


@bot.tree.command(name="bewerbung_panel", description="Sendet Bewerbungs Panel")
async def bewerbung_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    panel_channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

    if not panel_channel:
        return await interaction.response.send_message("❌ Panel-Channel nicht gefunden.", ephemeral=True)

    embed = discord.Embed(
        title="📋 Bewerbung",
        description="**Bundeswehr**\nBewerbt euch gerne",
        color=0x2E8B57
    )

    await panel_channel.send(embed=embed, view=BewerbungView())
    await interaction.response.send_message("✅ Panel gesendet.", ephemeral=True)


@bot.tree.command(name="voice_join", description="Bot joint Voice")
async def voice_join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Du bist in keinem Voicechannel.", ephemeral=True)

    voice_channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()

    await interaction.response.send_message(
        f"✅ Bot ist {voice_channel.name} beigetreten.",
        ephemeral=True
    )


@bot.tree.command(name="sagen", description="Bot spricht")
async def sagen(interaction: discord.Interaction, text: str):
    await interaction.response.defer(ephemeral=True)
    await speak(interaction, text, "tts.mp3")


@bot.tree.command(name="alarm_voice", description="Alarmansage")
async def alarm_voice(interaction: discord.Interaction, stufe: str, ort: str):
    await interaction.response.defer(ephemeral=True)

    text = (
        f"Achtung Achtung. "
        f"Alarmstufe {stufe}. "
        f"Einsatzort {ort}. "
        f"Alle verfügbaren Einheiten sofort antreten."
    )

    await speak(interaction, text, "alarm.mp3")


@bot.tree.command(name="voice_leave", description="Bot verlässt Voice")
async def voice_leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ Voice verlassen.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot ist in keinem Voicechannel.", ephemeral=True)


@bot.tree.command(name="close_bewerbung", description="Schließt Bewerbungsticket")
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

    if not message.channel.category:
        return

    if message.channel.category.id != BEWERBUNG_CATEGORY_ID:
        return

    if message.channel.id in processing_tickets:
        return

    processing_tickets.add(message.channel.id)

    await message.channel.send(
        "🤖 Bewerbung erkannt.\n"
        "Ich warte jetzt **60 Sekunden** und prüfe danach automatisch."
    )

    await asyncio.sleep(60)

    messages = []

    async for msg in message.channel.history(limit=50, oldest_first=True):
        if not msg.author.bot:
            messages.append(f"{msg.author}: {msg.content}")

    kompletter_text = "\n".join(messages)

    punkte, analyse, entscheidung, fehlend = bewerbung_auswerten(kompletter_text)

    check = kanal(message.guild, "bewerbungs-check")

    check_embed = discord.Embed(
        title="🤖 Bewerbungsprüfung",
        color=0x3498DB
    )

    check_embed.add_field(name="👤 Bewerber", value=message.author.mention, inline=False)
    check_embed.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
    check_embed.add_field(name="📌 Entscheidung", value=entscheidung, inline=True)
    check_embed.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)
    check_embed.timestamp = datetime.now()

    if check:
        await check.send(embed=check_embed)

    if entscheidung == "UNVOLLSTÄNDIG":
        await message.channel.send(
            "⚠️ Bewerbung unvollständig.\n"
            f"Fehlende Punkte: {', '.join(fehlend)}\n\n"
            "Bitte ergänze alles. Danach prüfe ich erneut."
        )

        processing_tickets.discard(message.channel.id)
        return

    if entscheidung == "ANGENOMMEN":
        ziel = kanal(message.guild, "annahmen")
        farbe = 0x00FF00
        titel = "✅ Bewerbung angenommen"
    else:
        ziel = kanal(message.guild, "ablehnungen")
        farbe = 0xFF0000
        titel = "❌ Bewerbung abgelehnt"

    result = discord.Embed(title=titel, color=farbe)
    result.add_field(name="👤 Bewerber", value=message.author.mention, inline=False)
    result.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
    result.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)

    if ziel:
        await ziel.send(embed=result)

    await message.channel.send(embed=result)

    try:
        await message.author.send(embed=result)
    except:
        print("DM Fehler")

    await message.channel.send("🔒 Ticket wird in 30 Sekunden geschlossen.")

    await asyncio.sleep(30)

    try:
        await message.channel.delete()
    except:
        print("Ticket konnte nicht gelöscht werden.")

    processing_tickets.discard(message.channel.id)


bot.run(TOKEN)
