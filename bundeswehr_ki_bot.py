import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

TOKEN = os.getenv("KI_TOKEN")

GUILD_ID = 123456789012345678  # DEINE SERVER-ID

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

    pflicht = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]
    fehlend = []

    for p in pflicht:
        if p not in lower:
            fehlend.append(p)

    if fehlend:
        punkte -= len(fehlend) * 10
        analyse.append(f"❌ Fehlende Punkte: {', '.join(fehlend)}")

    if len(text) < 350:
        punkte -= 25
        analyse.append("❌ Bewerbung ist zu kurz.")

    gute_woerter = [
        "team", "respekt", "disziplin", "aktiv",
        "bundeswehr", "helfen", "einsatz",
        "notruf hamburg", "erfahrung", "lernen"
    ]

    gefunden = sum(1 for wort in gute_woerter if wort in lower)

    if gefunden >= 5:
        punkte += 10
        analyse.append("✅ Gute Motivation erkannt.")
    elif gefunden >= 3:
        analyse.append("🟡 Motivation teilweise erkennbar.")
    else:
        punkte -= 20
        analyse.append("❌ Wenig Motivation erkannt.")

    schlechte_woerter = [
        "hurensohn", "nigger", "niga", "hs",
        "opfer", "spast", "kacke", "scheiße"
    ]

    if any(wort in lower for wort in schlechte_woerter):
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


@bot.event
async def on_ready():
    print(f"{bot.user} Bewerbungssystem online!")

    bot.add_view(BewerbungView())

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"{len(synced)} Commands geladen.")


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

        channel_name = f"bewerbung-{interaction.user.name}".lower()

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
                "3. Wie lange spielen sie schon Notruf Hamburg RP?\n"
                "4. Wie gut sind sie im Schießen?\n"
                "5. Warum wollen sie zur Bundeswehr?\n"
                "6. Was bringen sie mit?\n"
                "7. Warum sollen wir uns für sie entscheiden?\n"
                "8. Für welche Kategorie wollen sie?\n"
                "9. Sind sie bereit für ein Gespräch? Ja/Nein\n\n"
                "⏳ Sobald du deine Bewerbung sendest, prüft der Bot sie nach 60 Sekunden automatisch."
            ),
            color=0x2E8B57
        )

        embed.set_footer(text="Notruf Hamburg Bundeswehr Bewerbungssystem")

        await channel.send(interaction.user.mention, embed=embed)

        await interaction.response.send_message(
            f"✅ Bewerbung erstellt: {channel.mention}",
            ephemeral=True
        )


class BewerbungView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BewerbungSelect())


@bot.tree.command(name="setup", description="Erstellt Bewerbungs-Channels")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    channels = [
        "bewerbungs-check",
        "annahmen",
        "ablehnungen",
        "logs"
    ]

    for ch in channels:
        if not kanal(interaction.guild, ch):
            await interaction.guild.create_text_channel(ch)

    await interaction.followup.send("✅ Setup fertig.", ephemeral=True)


@bot.tree.command(name="bewerbung_panel", description="Sendet das Bewerbungs-Panel")
async def bewerbung_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    panel_channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

    if not panel_channel:
        return await interaction.response.send_message(
            "❌ Panel-Channel wurde nicht gefunden.",
            ephemeral=True
        )

    embed = discord.Embed(
        title="📋 Appy Bot",
        description="**Bundeswehr**\nBewerbt euch gerne",
        color=0x2E8B57
    )

    await panel_channel.send(embed=embed, view=BewerbungView())

    await interaction.response.send_message(
        "✅ Bewerbungs-Panel wurde gesendet.",
        ephemeral=True
    )


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
        "Ich warte jetzt **60 Sekunden**, damit du alles vollständig schreiben kannst.\n"
        "Danach prüfe ich automatisch deine Bewerbung."
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
        title="🤖 KI Bewerbungsprüfung",
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
            "⚠️ Deine Bewerbung ist noch nicht vollständig.\n"
            f"Es fehlen wahrscheinlich diese Punkte: **{', '.join(fehlend)}**\n\n"
            "Bitte ergänze die fehlenden Antworten. Danach prüfe ich erneut."
        )

        processing_tickets.discard(message.channel.id)
        return

    if entscheidung == "ANGENOMMEN":
        ziel_channel = kanal(message.guild, "annahmen")
        farbe = 0x00FF00
        titel = "✅ Bewerbung angenommen"
        dm_text = "Glückwunsch! Deine Bewerbung wurde angenommen. Bitte warte auf weitere Informationen vom Team."
    else:
        ziel_channel = kanal(message.guild, "ablehnungen")
        farbe = 0xFF0000
        titel = "❌ Bewerbung abgelehnt"
        dm_text = "Deine Bewerbung wurde leider abgelehnt. Du kannst es später erneut versuchen."

    embed = discord.Embed(
        title=titel,
        color=farbe
    )

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
        dm = discord.Embed(
            title=titel,
            description=dm_text,
            color=farbe
        )

        dm.add_field(name="📊 Bewertung", value=f"{punkte}/100")
        dm.add_field(name="📝 Analyse", value="\n".join(analyse)[:1000], inline=False)

        await message.author.send(embed=dm)

    except:
        print("DM konnte nicht gesendet werden.")

    await message.channel.send(
        "🔒 Dieses Bewerbungsticket wird in **30 Sekunden** automatisch geschlossen."
    )

    await asyncio.sleep(30)

    try:
        await message.channel.delete()
    except:
        print("Ticket konnte nicht gelöscht werden.")

    processing_tickets.discard(message.channel.id)


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


bot.run(TOKEN)
