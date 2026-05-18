import discord
from discord.ext import commands
import os
from datetime import datetime
import random

TOKEN = os.getenv("KI_TOKEN")
BOT_ZENTRALE = "bot-zentrale"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

einsatz_nummer = 1000


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


@bot.event
async def on_ready():
    print(f"{bot.user} Ultra KI-Leitstelle online!")


@bot.event
async def on_message(message):
    global einsatz_nummer

    if message.author == bot.user:
        return

    if message.channel.name != BOT_ZENTRALE:
        await bot.process_commands(message)
        return

    content = message.content

    if content.startswith("ALARM:"):
        daten = content.replace("ALARM:", "").split("|")

        if len(daten) >= 5:
            stufe, ort, bedrohung, ausruestung, melder = daten

            einsatz_nummer += 1

            analyse = []

            b = bedrohung.lower()

            if "terror" in b or "geisel" in b:
                analyse.append("🪖 MP-Einheit")
                analyse.append("🚑 Sanitäter")
                analyse.append("🔫 Schwere Ausrüstung")
                empfohlene_stufe = "ROT"
            elif "explosion" in b or "brand" in b:
                analyse.append("🚒 Feuerwehr")
                analyse.append("🚑 Rettungsdienst")
                analyse.append("🪖 Absicherung")
                empfohlene_stufe = "ROT"
            elif "bewaffnet" in b or "schuss" in b:
                analyse.append("🪖 2x Bundeswehr-Streifen")
                analyse.append("👮 Militärpolizei")
                empfohlene_stufe = "ORANGE"
            else:
                analyse.append("🪖 Standard Einheit")
                analyse.append("📻 Lage prüfen")
                empfohlene_stufe = stufe.upper()

            einsatz_channel = f"einsatz-{einsatz_nummer}"
            funk_channel = f"funk-{einsatz_nummer}"

            if not kanal(message.guild, einsatz_channel):
                await message.guild.create_text_channel(einsatz_channel)

            if not kanal(message.guild, funk_channel):
                await message.guild.create_text_channel(funk_channel)

            alarm_ch = kanal(message.guild, "alarmierungen")
            funk_ch = kanal(message.guild, "bw-funk")
            logs = kanal(message.guild, "logs")

            embed = discord.Embed(
                title=f"🚨 EINSATZ #{einsatz_nummer} | ALARM {empfohlene_stufe}",
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
                    "📻 Einsatzleitung bitte Rückmeldung geben."
                ]
                await funk_ch.send(random.choice(meldungen))

            if logs:
                await logs.send(f"🤖 KI hat Einsatz #{einsatz_nummer} verarbeitet.")

            await message.channel.send(
                f"✅ Einsatz #{einsatz_nummer} verarbeitet.\n"
                f"📻 Funk: #{funk_channel}\n"
                f"🪖 Einsatz: #{einsatz_channel}"
            )

    elif content.startswith("AUFGABE:create_channel:"):
        channel_name = content.split(":")[2]

        if kanal(message.guild, channel_name):
            await message.channel.send(f"ℹ️ `{channel_name}` existiert bereits.")
        else:
            await message.guild.create_text_channel(channel_name)
            await message.channel.send(f"✅ Channel `{channel_name}` erstellt.")

    elif content == "AUFGABE:status":
        await message.channel.send(
            "🤖 KI-Leitstelle online.\n"
            "✅ Alarmanalyse aktiv\n"
            "✅ Channel-Erstellung aktiv\n"
            "✅ Funkweiterleitung aktiv\n"
            "✅ Einsatzsystem bereit"
        )

    await bot.process_commands(message)


@bot.command()
async def ki(ctx):
    embed = discord.Embed(
        title="🤖 Ultra KI-Leitstelle",
        description="Alarmsystem, Funksystem, Einsatzanalyse und Channel-Verwaltung aktiv.",
        color=0x2E8B57
    )
    await ctx.send(embed=embed)


bot.run(TOKEN)
