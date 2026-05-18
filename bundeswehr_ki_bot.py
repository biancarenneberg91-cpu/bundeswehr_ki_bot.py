import discord
from discord.ext import commands
import os
from datetime import datetime

TOKEN = os.getenv("KI_TOKEN")

BOT_ZENTRALE = "bot-zentrale"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


@bot.event
async def on_ready():
    print(f"{bot.user} KI-Bot online!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != BOT_ZENTRALE:
        await bot.process_commands(message)
        return

    content = message.content

    if content.startswith("ALARM:"):
        daten = content.replace("ALARM:", "").split("|")

        if len(daten) >= 4:
            stufe, ort, bedrohung, melder = daten

            alarm_ch = kanal(message.guild, "alarmierungen")
            funk_ch = kanal(message.guild, "bw-funk")

            embed = discord.Embed(
                title=f"🤖 KI-Leitstelle bestätigt Alarmstufe {stufe.upper()}",
                color=0xFF0000
            )

            embed.add_field(name="📍 Ort", value=ort, inline=True)
            embed.add_field(name="⚠️ Bedrohung", value=bedrohung, inline=False)
            embed.add_field(name="📡 Gemeldet von", value=melder, inline=True)
            embed.add_field(name="🕒 Zeit", value=datetime.now().strftime("%d.%m.%Y %H:%M"), inline=True)

            if alarm_ch:
                await alarm_ch.send(embed=embed)

            if funk_ch:
                await funk_ch.send(
                    f"📻 **KI-Leitstelle:** Alarm **{stufe.upper()}** bei **{ort}** bestätigt. Kräfte vorbereiten."
                )

            await message.channel.send("✅ KI-Bot hat Alarm verarbeitet.")

    elif content.startswith("AUFGABE:create_channel:"):
        channel_name = content.split(":")[2]

        if kanal(message.guild, channel_name):
            await message.channel.send(f"ℹ️ `{channel_name}` existiert schon.")
        else:
            await message.guild.create_text_channel(channel_name)
            await message.channel.send(f"✅ `{channel_name}` wurde erstellt.")

    elif content == "AUFGABE:status":
        await message.channel.send("🤖 KI-Bot online. Systeme bereit.")

    await bot.process_commands(message)


@bot.command()
async def status(ctx):
    await ctx.send("🤖 KI-Bot ist online und bereit.")


bot.run(TOKEN)
