import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

GUILD_ID =1504190915235811360

# DEINE BEWERBUNGS KATEGORIE
BEWERBUNG_CATEGORY_ID = 1504203869130064035

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================
# CHANNEL SUCHEN
# =========================================

def kanal(guild, name):

    return discord.utils.get(
        guild.text_channels,
        name=name
    )


# =========================================
# READY
# =========================================

@bot.event
async def on_ready():

    print(f"{bot.user} online!")

    guild = discord.Object(
        id=GUILD_ID
    )

    bot.tree.copy_global_to(
        guild=guild
    )

    synced = await bot.tree.sync(
        guild=guild
    )

    print(f"{len(synced)} Commands geladen.")

    bot.add_view(
        BewerbungView()
    )


# =========================================
# WELCOME
# =========================================

@bot.event
async def on_member_join(member):

    welcome = kanal(
        member.guild,
        "willkommen"
    )

    if welcome:

        embed = discord.Embed(
            title="🪖 Willkommen",
            description=(
                f"Willkommen {member.mention}\n\n"
                "🚨 Notruf Hamburg Bundeswehr"
            ),
            color=0x2E8B57
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        await welcome.send(
            embed=embed
        )


# =========================================
# SETUP
# =========================================

@bot.tree.command(
    name="setup",
    description="Erstellt Bundeswehr System"
)
async def setup(
    interaction: discord.Interaction
):

    if not interaction.user.guild_permissions.administrator:

        return await interaction.response.send_message(
            "❌ Keine Rechte.",
            ephemeral=True
        )

    await interaction.response.defer(
        ephemeral=True
    )

    channels = [

        "willkommen",
        "bewerbungs-check",
        "ankundigungen",
        "dienstmeldungen",
        "alarmierungen",
        "einsaetze",
        "bw-funk",
        "waffenlogs",
        "personalakten",
        "befoerderungen",
        "logs"

    ]

    for ch in channels:

        if not kanal(
            interaction.guild,
            ch
        ):

            await interaction.guild.create_text_channel(
                ch
            )

    rollen = [

        "Bewerber",
        "Rekrut",
        "Soldat",
        "Militärpolizei",
        "General"

    ]

    for r in rollen:

        if not discord.utils.get(
            interaction.guild.roles,
            name=r
        ):

            await interaction.guild.create_role(
                name=r
            )

    await interaction.followup.send(
        "✅ System erstellt.",
        ephemeral=True
    )


# =========================================
# BEWERBUNGS PANEL
# =========================================

class BewerbungSelect(
    discord.ui.Select
):

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
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        category = guild.get_channel(
            BEWERBUNG_CATEGORY_ID
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

            name=f"📋︱bewerbung-{interaction.user.name}",

            category=category,

            overwrites=overwrites

        )

        embed = discord.Embed(

            title="🪖 Bundeswehr Bewerbung",

            description=(

                f"Willkommen {interaction.user.mention}!\n\n"

                "Bitte beantworte folgende Fragen:\n\n"

                "1. Wie alt sind sie?\n\n"

                "2. Wie heißen sie?\n\n"

                "3. Wie lange spielen sie schon Notruf Hamburg RP?\n\n"

                "4. Wie gut sind sie im schießen?\n\n"

                "5. Warum wollen sie zur Bundeswehr?\n\n"

                "6. Was bringen sie mit?\n\n"

                "7. Warum sollen wir uns für sie entscheiden?\n\n"

                "8. Für welche Kategorie wollen sie?\n\n"

                "9. Sind sie bereit für ein Gespräch?\n"

                "Ja / Nein"

            ),

            color=0x2E8B57

        )

        embed.set_footer(
            text="Notruf Hamburg Bundeswehr"
        )

        await channel.send(
            interaction.user.mention,
            embed=embed
        )

        await interaction.response.send_message(

            f"✅ Bewerbung erstellt: {channel.mention}",

            ephemeral=True

        )


class BewerbungView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            BewerbungSelect()
        )


# =========================================
# PANEL SENDEN
# =========================================

@bot.tree.command(
    name="bewerbung_panel",
    description="Sendet Bewerbungs Panel"
)
async def bewerbung_panel(
    interaction: discord.Interaction
):

    if not interaction.user.guild_permissions.administrator:

        return await interaction.response.send_message(
            "❌ Keine Rechte.",
            ephemeral=True
        )

    embed = discord.Embed(

        title="📋 Appy Bot",

        description=(
            "**Bundeswehr**\n"
            "Bewerbt euch gerne"
        ),

        color=0x2E8B57

    )

    await interaction.channel.send(

        embed=embed,

        view=BewerbungView()

    )

    await interaction.response.send_message(

        "✅ Panel gesendet.",

        ephemeral=True

    )


# =========================================
# KI CHECK
# =========================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if "1." in message.content and "2." in message.content:

        check = kanal(
            message.guild,
            "bewerbungs-check"
        )

        if not check:
            return

        text = message.content.lower()

        punkte = 100
        analyse = []

        if len(text) < 300:

            punkte -= 20

            analyse.append(
                "❌ Bewerbung zu kurz"
            )

        gute = [

            "team",
            "respekt",
            "disziplin",
            "bundeswehr",
            "helfen",
            "aktiv"

        ]

        gefunden = sum(
            1 for wort in gute
            if wort in text
        )

        if gefunden >= 4:

            punkte += 10

            analyse.append(
                "✅ Gute Motivation"
            )

        else:

            punkte -= 10

            analyse.append(
                "🟡 Wenig Motivation"
            )

        schlechte = [

            "hurensohn",
            "niga",
            "nigger",
            "hs",
            "opfer"

        ]

        if any(
            wort in text
            for wort in schlechte
        ):

            punkte -= 50

            analyse.append(
                "❌ Beleidigungen erkannt"
            )

        if punkte >= 80:
            status = "🟢 Sehr gut"

        elif punkte >= 60:
            status = "🟡 Mittel"

        else:
            status = "🔴 Schwach"

        embed = discord.Embed(

            title="🤖 KI Bewerbungsprüfung",

            color=0x3498db

        )

        embed.add_field(
            name="👤 Bewerber",
            value=message.author.mention,
            inline=False
        )

        embed.add_field(
            name="📊 Bewertung",
            value=f"{punkte}/100"
        )

        embed.add_field(
            name="📌 Status",
            value=status
        )

        embed.add_field(
            name="📝 Analyse",
            value="\n".join(analyse),
            inline=False
        )

        embed.timestamp = datetime.now()

        await check.send(
            embed=embed
        )

        try:

            dm = discord.Embed(

                title="🪖 Bewerbung geprüft",

                description=(
                    f"📊 Bewertung: {punkte}/100\n"
                    f"📌 Status: {status}"
                ),

                color=0x2E8B57

            )

            await message.author.send(
                embed=dm
            )

        except:
            print("DM Fehler")

    await bot.process_commands(
        message
    )


# =========================================
# DIENST
# =========================================

@bot.tree.command(
    name="dienst",
    description="In Dienst gehen"
)
async def dienst(
    interaction: discord.Interaction
):

    ch = kanal(
        interaction.guild,
        "dienstmeldungen"
    )

    if ch:

        await ch.send(
            f"🟢 {interaction.user.mention} ist im Dienst."
        )

    await interaction.response.send_message(
        "✅ Dienst aktiviert.",
        ephemeral=True
    )


# =========================================
# ALARM
# =========================================

@bot.tree.command(
    name="alarm",
    description="Löst Alarm aus"
)
async def alarm(
    interaction: discord.Interaction,
    stufe: str,
    ort: str,
    bedrohung: str
):

    alarm = kanal(
        interaction.guild,
        "alarmierungen"
    )

    embed = discord.Embed(

        title=f"🚨 ALARMSTUFE {stufe}",

        color=0xFF0000

    )

    embed.add_field(
        name="📍 Ort",
        value=ort
    )

    embed.add_field(
        name="⚠️ Bedrohung",
        value=bedrohung,
        inline=False
    )

    embed.add_field(
        name="👮 Gemeldet von",
        value=interaction.user.mention
    )

    if alarm:

        await alarm.send(
            "@everyone 🚨",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=True
            )
        )

    await interaction.response.send_message(
        "🚨 Alarm gesendet.",
        ephemeral=True
    )


# =========================================
# FUNK
# =========================================

@bot.tree.command(
    name="funk",
    description="Sendet Funk"
)
async def funk(
    interaction: discord.Interaction,
    text: str
):

    funk = kanal(
        interaction.guild,
        "bw-funk"
    )

    if funk:

        await funk.send(
            f"📻 {interaction.user.mention}: {text}"
        )

    await interaction.response.send_message(
        "📻 Funk gesendet.",
        ephemeral=True
    )


# =========================================
# STATS
# =========================================

@bot.tree.command(
    name="stats",
    description="Zeigt Stats"
)
async def stats(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📊 Bundeswehr Stats",
        color=0x2E8B57
    )

    embed.add_field(
        name="🤖 System",
        value="Online"
    )

    embed.add_field(
        name="🪖 Bewerbungen",
        value="Aktiv"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


bot.run(TOKEN)
