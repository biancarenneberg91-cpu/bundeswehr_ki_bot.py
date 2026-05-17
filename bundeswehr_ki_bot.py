import discord
from discord.ext import commands
import os
from datetime import datetime

TOKEN = os.getenv("KI_TOKEN") or "Token"
BOT_ZENTRALE = "bot-zentrale"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)

@bot.event
async def on_ready():
    print(f"{bot.user} KI-Körperbot online!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != BOT_ZENTRALE:
        await bot.process_commands(message)
        return

    content = message.content

    if content.startswith("AUFGABE:create_channel:"):
        channel_name = content.split(":")[2]

        existing = kanal(message.guild, channel_name)

        if existing:
            await message.channel.send(f"ℹ️ `{channel_name}` existiert schon.")
        else:
            await message.guild.create_text_channel(channel_name)
            await message.channel.send(f"✅ Channel `{channel_name}` erstellt.")

    elif content.startswith("ALARM:"):
        daten = content.replace("ALARM:", "").split("|")

        if len(daten) >= 5:
            stufe, ort, bedrohung, ausruestung, melder = daten

            einsatz_ch = kanal(message.guild, "einsaetze")
            funk_ch = kanal(message.guild, "bundeswehr-funk")

            embed = discord.Embed(
                title=f"🚨 ALARMSTUFE {stufe.upper()}",
                color=0xFF0000
            )
            embed.add_field(name="📍 Ort", value=ort, inline=True)
            embed.add_field(name="⚠️ Bedrohung", value=bedrohung, inline=False)
            embed.add_field(name="🪖 Ausrüstung", value=ausruestung, inline=False)
            embed.add_field(name="📡 Melder", value=melder, inline=True)
            embed.add_field(name="🕒 Zeit", value=datetime.now().strftime("%d.%m.%Y %H:%M"), inline=True)

            if einsatz_ch:
                await einsatz_ch.send(
                    content="@everyone 🚨 **BUNDESWEHR ALARM**",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(everyone=True)
                )

            if funk_ch:
                await funk_ch.send(
                    f"📻 KI-Funkzentrale bestätigt Alarmstufe **{stufe.upper()}**."
                )

            await message.channel.send("✅ Alarm weitergeleitet.")

    elif content == "AUFGABE:status":
        await message.channel.send("🤖 KI-Körperbot online und bereit.")

    await bot.process_commands(message)

bot.run(TOKEN)
