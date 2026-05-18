import discord
from discord.ext import commands
import os
from datetime import datetime
import random

TOKEN = os.getenv("KI_TOKEN")

BOT_ZENTRALE = "bot-zentrale"
BEWERBUNG_CHANNEL = "bewerbungen"
CHECK_CHANNEL = "bewerbungs-check"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

einsatz_nummer = 1000


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


async def kanal_erstellen(guild, name):
    ch = kanal(guild, name)
    if ch:
        return ch
    return await guild.create_text_channel(name)


def bewerbung_pruefen(text):
    punkte = 100
    gruende = []

    lower = text.lower()

    if len(text) < 200:
        punkte -= 30
        gruende.append("❌ Bewerbung ist sehr kurz.")

    if len(text) > 600:
        punkte += 5
        gruende.append("✅ Ausführliche Bewerbung.")

    schlechte_woerter = [
        "hurensohn",
        "nigger",
        "niga",
        "hs",
        "opfer",
        "spast"
    ]

    if any(wort in lower for wort in schlechte_woerter):
        punkte -= 60
        gruende.append("❌ Unangemessene Wörter gefunden.")

    wichtige_woerter = [
        "motivation",
        "erfahrung",
        "team",
        "respekt",
        "dienst",
        "bundeswehr",
        "notruf hamburg",
        "disziplin",
        "aktiv"
    ]

    gefunden = sum(1 for wort in wichtige_woerter if wort in lower)

    if gefunden >= 4:
        punkte += 10
        gruende.append("✅ Gute Motivation/Erfahrung erkennbar.")
    elif gefunden >= 2:
        gruende.append("🟡 Etwas Motivation erkennbar.")
    else:
        punkte -= 25
        gruende.append("❌ Wenig Motivation/Erfahrung erkennbar.")

    unserioes = [
        "kein plan",
        "weiß nicht",
        "weiss nicht",
        "kp",
        "egal",
        "einfach so"
    ]

    if any(wort in lower for wort in unserioes):
        punkte -= 25
        gruende.append("❌ Antwort wirkt unseriös.")

    if punkte > 100:
        punkte = 100

    if punkte < 0:
        punkte = 0

    if punkte >= 80:
        status = "🟢 Sehr gut"
        empfehlung = "Annehmen oder Gespräch führen."
    elif punkte >= 60:
        status = "🟡 Mittel"
        empfehlung = "Bewerbung prüfen und Gespräch machen."
    else:
        status = "🔴 Schwach"
        empfehlung = "Eher ablehnen oder stark nachfragen."

    if not gruende:
        gruende.append("✅ Keine großen Probleme gefunden.")

    return punkte, status, empfehlung, gruende


@bot.event
async def on_ready():
    print(f"{bot.user} KI-Bot online!")


@bot.event
async def on_message(message):
    global einsatz_nummer

    if message.author == bot.user:
        return

    # =========================
    # APPY BEWERBUNGS CHECK
    # =========================

    if message.channel.name == BEWERBUNG_CHANNEL and message.author.bot:
        text = message.content or ""

        if message.embeds:
            for embed in message.embeds:
                if embed.title:
                    text += "\n" + embed.title
                if embed.description:
                    text += "\n" + embed.description
                for field in embed.fields:
                    text += f"\n{field.name}: {field.value}"

        punkte, status, empfehlung, gruende = bewerbung_pruefen(text)

        check_ch = await kanal_erstellen(message.guild, CHECK_CHANNEL)

        embed = discord.Embed(
            title="🤖 KI Bewerbungsprüfung",
            description="Automatische Prüfung einer neuen Appy-Bewerbung.",
            color=0x2E8B57
        )

        embed.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
        embed.add_field(name="📌 Status", value=status, inline=True)
        embed.add_field(name="💡 Empfehlung", value=empfehlung, inline=False)
        embed.add_field(name="📝 Analyse", value="\n".join(gruende)[:1000], inline=False)
        embed.add_field(name="📥 Quelle", value=message.jump_url, inline=False)

        embed.timestamp = datetime.now()

        await check_ch.send(embed=embed)

    # =========================
    # BOT-ZENTRALE
    # =========================

    if message.channel.name != BOT_ZENTRALE:
        await bot.process_commands(message)
        return

    content = message.content

    # =========================
    # CHANNEL ERSTELLEN
    # =========================

    if content.startswith("AUFGABE:create_channel:"):
        channel_name = content.split(":")[2]

        if kanal(message.guild, channel_name):
            await message.channel.send(f"ℹ️ `{channel_name}` existiert bereits.")
        else:
            await message.guild.create_text_channel(channel_name)
            await message.channel.send(f"✅ Channel `{channel_name}` erstellt.")

    # =========================
    # STATUS
    # =========================

    elif content == "AUFGABE:status":
        await message.channel.send(
            "🤖 KI-Bot online.\n"
            "✅ Alarmanalyse aktiv\n"
            "✅ Appy-Bewerbungsprüfung aktiv\n"
            "✅ Channel-System aktiv\n"
            "✅ Funkweiterleitung aktiv"
        )

    # =========================
    # ALARM ANALYSE
    # =========================

    elif content.startswith("ALARM:"):
        daten = content.replace("ALARM:", "").split("|")

        if len(daten) >= 5:
            stufe, ort, bedrohung, ausruestung, melder = daten

            einsatz_nummer += 1

            analyse = []
            b = bedrohung.lower()

            if "terror" in b or "geisel" in b:
                analyse.append("🪖 Militärpolizei anfordern")
                analyse.append("🚑 Sanitäter bereithalten")
                analyse.append("🔫 Schwere Ausrüstung empfohlen")
                alarmstufe = "ROT"
            elif "explosion" in b or "brand" in b:
                analyse.append("🚒 Feuerwehr benötigt")
                analyse.append("🚑 Rettungsdienst benötigt")
                analyse.append("🪖 Bereich absichern")
                alarmstufe = "ROT"
            elif "bewaffnet" in b or "schuss" in b:
                analyse.append("🪖 Zwei Bundeswehr-Streifen")
                analyse.append("👮 Militärpolizei")
                analyse.append("🦺 Schutzwesten empfohlen")
                alarmstufe = "ORANGE"
            else:
                analyse.append("🪖 Standard-Einheit entsenden")
                analyse.append("📻 Lage weiter beobachten")
                alarmstufe = stufe.upper()

            einsatz_channel = f"einsatz-{einsatz_nummer}"
            funk_channel = f"funk-{einsatz_nummer}"

            await kanal_erstellen(message.guild, einsatz_channel)
            await kanal_erstellen(message.guild, funk_channel)

            alarm_ch = kanal(message.guild, "alarmierungen")
            funk_ch = kanal(message.guild, "bw-funk")
            logs_ch = kanal(message.guild, "logs")

            embed = discord.Embed(
                title=f"🚨 EINSATZ #{einsatz_nummer} | ALARM {alarmstufe}",
                color=0xFF0000
            )

            embed.add_field(name="📍 Ort", value=ort, inline=True)
            embed.add_field(name="⚠️ Bedrohung", value=bedrohung, inline=False)
            embed.add_field(name="🪖 Ausrüstung", value=ausruestung, inline=False)
            embed.add_field(name="📡 Melder", value=melder, inline=True)
            embed.add_field(name="🤖 KI Analyse", value="\n".join(analyse), inline=False)
            embed.add_field(name="📻 Funkraum", value=f"#{funk_channel}", inline=True)
            embed.add_field(name="🪖 Einsatzraum", value=f"#{einsatz_channel}", inline=True)

            embed.timestamp = datetime.now()

            if alarm_ch:
                await alarm_ch.send(
                    content="@everyone 🚨 **BUNDESWEHR EINSATZ**",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(everyone=True)
                )

            if funk_ch:
                meldungen = [
                    f"📻 KI-Leitstelle bestätigt Einsatz #{einsatz_nummer}.",
                    f"📻 Alle verfügbaren Einheiten Richtung {ort}.",
                    "📻 Lage wird fortlaufend bewertet.",
                    "📻 Einsatzleitung bitte Rückmeldung geben.",
                    "📻 Bundeswehr-Kräfte bereitmachen."
                ]

                await funk_ch.send(random.choice(meldungen))

            if logs_ch:
                await logs_ch.send(f"🤖 KI hat Einsatz #{einsatz_nummer} verarbeitet.")

            await message.channel.send(
                f"✅ Einsatz #{einsatz_nummer} verarbeitet.\n"
                f"📻 Funk: #{funk_channel}\n"
                f"🪖 Einsatz: #{einsatz_channel}"
            )

    await bot.process_commands(message)


@bot.command()
async def ki(ctx):
    embed = discord.Embed(
        title="🤖 Ultra KI-Bot",
        description=(
            "✅ Appy Bewerbungsprüfung\n"
            "✅ Alarmanalyse\n"
            "✅ Channel-Erstellung\n"
            "✅ Funkweiterleitung\n"
            "✅ Einsatzanalyse"
        ),
        color=0x2E8B57
    )

    await ctx.send(embed=embed)


bot.run(TOKEN)
