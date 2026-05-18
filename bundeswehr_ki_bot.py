import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

GUILD_ID = 123456789012345678

DB = "bundeswehr.db"

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================
# DATABASE
# =========================================

def db():
    return sqlite3.connect(DB)


def setup_db():

    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dienst (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        start TEXT,
        ende TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item TEXT,
        typ TEXT,
        von TEXT,
        zeit TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS personal (
        user_id INTEGER PRIMARY KEY,
        rang TEXT,
        status TEXT,
        notiz TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS einsaetze (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titel TEXT,
        ort TEXT,
        leitung TEXT,
        status TEXT,
        zeit TEXT
    )
    """)

    con.commit()
    con.close()


# =========================================
# HILFE
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

    setup_db()

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

    rolle = discord.utils.get(
        member.guild.roles,
        name="Bewerber"
    )

    if rolle:
        await member.add_roles(rolle)


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
        "ankundigungen",
        "bewerbungen",
        "bewerbungs-check",
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

        if not kanal(interaction.guild, ch):

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
# BEWERBUNG
# =========================================

class BewerbungModal(
    discord.ui.Modal,
    title="🪖 Bundeswehr Bewerbung"
):

    alter = discord.ui.TextInput(
        label="Wie alt sind sie?"
    )

    name = discord.ui.TextInput(
        label="Wie heißen sie?"
    )

    spielzeit = discord.ui.TextInput(
        label="Wie lange spielen sie Notruf Hamburg?"
    )

    motivation = discord.ui.TextInput(
        label="Warum wollen sie zur Bundeswehr?",
        style=discord.TextStyle.paragraph
    )

    staerken = discord.ui.TextInput(
        label="Was bringen sie mit?",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        bewerbung = kanal(
            interaction.guild,
            "bewerbungen"
        )

        check = kanal(
            interaction.guild,
            "bewerbungs-check"
        )

        text = (
            self.motivation.value.lower()
            + " " +
            self.staerken.value.lower()
        )

        punkte = 100
        analyse = []

        if len(text) < 100:
            punkte -= 20
            analyse.append(
                "❌ Wenig Motivation"
            )

        gute = [

            "team",
            "respekt",
            "disziplin",
            "bundeswehr",
            "helfen"

        ]

        gefunden = sum(
            1 for wort in gute
            if wort in text
        )

        if gefunden >= 3:

            punkte += 10

            analyse.append(
                "✅ Gute Motivation"
            )

        else:

            punkte -= 10

            analyse.append(
                "🟡 Wenig Motivation"
            )

        if punkte >= 80:
            status = "🟢 Sehr gut"

        elif punkte >= 60:
            status = "🟡 Mittel"

        else:
            status = "🔴 Schwach"

        embed = discord.Embed(
            title="🪖 Neue Bewerbung",
            color=0x2E8B57
        )

        embed.add_field(
            name="👤 Bewerber",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Alter",
            value=self.alter.value,
            inline=False
        )

        embed.add_field(
            name="Name",
            value=self.name.value,
            inline=False
        )

        embed.add_field(
            name="Spielzeit",
            value=self.spielzeit.value,
            inline=False
        )

        embed.add_field(
            name="Motivation",
            value=self.motivation.value,
            inline=False
        )

        embed.add_field(
            name="Stärken",
            value=self.staerken.value,
            inline=False
        )

        embed.timestamp = datetime.now()

        if bewerbung:
            await bewerbung.send(
                embed=embed
            )

        if check:

            check_embed = discord.Embed(
                title="🤖 KI Bewerbungsprüfung",
                color=0x3498db
            )

            check_embed.add_field(
                name="📊 Bewertung",
                value=f"{punkte}/100"
            )

            check_embed.add_field(
                name="📌 Status",
                value=status
            )

            check_embed.add_field(
                name="📝 Analyse",
                value="\n".join(analyse),
                inline=False
            )

            await check.send(
                embed=check_embed
            )

        try:

            dm = discord.Embed(
                title="🪖 Bewerbung abgeschickt",
                description=(
                    f"📊 Bewertung: {punkte}/100\n"
                    f"📌 Status: {status}"
                ),
                color=0x2E8B57
            )

            await interaction.user.send(
                embed=dm
            )

        except:
            print("DM Fehler")

        await interaction.response.send_message(
            "✅ Bewerbung abgeschickt.",
            ephemeral=True
        )


@bot.tree.command(
    name="bewerbung",
    description="Öffnet Bewerbung"
)
async def bewerbung(
    interaction: discord.Interaction
):

    await interaction.response.send_modal(
        BewerbungModal()
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

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO dienst
        (user_id, name, start, ende)
        VALUES (?, ?, ?, NULL)
        """,
        (
            interaction.user.id,
            str(interaction.user),
            datetime.now().strftime(
                "%d.%m.%Y %H:%M"
            )
        )
    )

    con.commit()
    con.close()

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
# WAFFEN
# =========================================

@bot.tree.command(
    name="waffe_geben",
    description="Gibt Waffe"
)
async def waffe_geben(
    interaction: discord.Interaction,
    person: discord.Member,
    waffe: str
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO inventar
        (user_id, item, typ, von, zeit)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            person.id,
            waffe,
            "Waffe",
            str(interaction.user),
            datetime.now().strftime(
                "%d.%m.%Y %H:%M"
            )
        )
    )

    con.commit()
    con.close()

    logs = kanal(
        interaction.guild,
        "waffenlogs"
    )

    if logs:

        await logs.send(
            f"🔫 {waffe} an {person.mention} ausgegeben."
        )

    await interaction.response.send_message(
        "✅ Waffe ausgegeben.",
        ephemeral=True
    )


# =========================================
# PERSONALAKTE
# =========================================

@bot.tree.command(
    name="personalakte",
    description="Erstellt Akte"
)
async def personalakte(
    interaction: discord.Interaction,
    person: discord.Member,
    rang: str,
    status: str,
    notiz: str
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO personal
        (user_id, rang, status, notiz)
        VALUES (?, ?, ?, ?)
        """,
        (
            person.id,
            rang,
            status,
            notiz
        )
    )

    con.commit()
    con.close()

    akte = kanal(
        interaction.guild,
        "personalakten"
    )

    if akte:

        embed = discord.Embed(
            title="📁 Personalakte",
            color=0x2E8B57
        )

        embed.add_field(
            name="👮 Soldat",
            value=person.mention
        )

        embed.add_field(
            name="🎖️ Rang",
            value=rang
        )

        embed.add_field(
            name="📋 Status",
            value=status
        )

        embed.add_field(
            name="📝 Notiz",
            value=notiz,
            inline=False
        )

        await akte.send(
            embed=embed
        )

    await interaction.response.send_message(
        "✅ Akte gespeichert.",
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

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM dienst WHERE ende IS NULL"
    )

    dienst = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM inventar"
    )

    inventar = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM personal"
    )

    personal = cur.fetchone()[0]

    con.close()

    embed = discord.Embed(
        title="📊 Bundeswehr Stats",
        color=0x2E8B57
    )

    embed.add_field(
        name="🟢 Im Dienst",
        value=str(dienst)
    )

    embed.add_field(
        name="🔫 Waffen",
        value=str(inventar)
    )

    embed.add_field(
        name="📁 Personalakten",
        value=str(personal)
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


bot.run(TOKEN)
