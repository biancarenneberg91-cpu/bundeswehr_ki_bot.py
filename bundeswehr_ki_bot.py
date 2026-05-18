import discord
from discord.ext import commands
import os
from datetime import datetime

TOKEN = os.getenv("KI_TOKEN")

GUILD_ID = 123456789012345678  # DEINE SERVER-ID

BEWERBUNG_CATEGORY_ID = 1504190916737368328
PANEL_CHANNEL_ID = 1504203869130064035

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


@bot.event
async def on_ready():
    print(f"{bot.user} online!")

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
                "Bitte beantworte folgende Fragen in **einer Nachricht**:\n\n"
                "1. Wie alt sind sie?\n"
                "2. Wie heißen sie?\n"
                "3. Wie lange spielen sie schon Notruf Hamburg RP?\n"
                "4. Wie gut sind sie im Schießen?\n"
                "5. Warum wollen sie zur Bundeswehr?\n"
                "6. Was bringen sie mit?\n"
                "7. Warum sollen wir uns für sie entscheiden?\n"
                "8. Für welche Kategorie wollen sie?\n"
                "9. Sind sie bereit für ein Gespräch? Ja/Nein"
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


@bot.tree.command(name="bewerbung_panel", description="Sendet das Bewerbungs-Panel")
async def bewerbung_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "❌ Keine Rechte.",
            ephemeral=True
        )

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

    if message.channel.category and message.channel.category.id == BEWERBUNG_CATEGORY_ID:
        if message.channel.name.startswith("bewerbung-"):
            text = message.content.lower()

            punkte = 100
            analyse = []

            if len(text) < 250:
                punkte -= 25
                analyse.append("❌ Bewerbung ist sehr kurz.")

            gute_woerter = [
                "team",
                "respekt",
                "disziplin",
                "aktiv",
                "bundeswehr",
                "helfen",
                "einsatz",
                "notruf hamburg"
            ]

            gefunden = sum(1 for wort in gute_woerter if wort in text)

            if gefunden >= 4:
                analyse.append("✅ Gute Motivation erkannt.")
                punkte += 10
            elif gefunden >= 2:
                analyse.append("🟡 Etwas Motivation erkannt.")
            else:
                analyse.append("❌ Wenig Motivation erkannt.")
                punkte -= 20

            schlechte_woerter = [
                "hurensohn",
                "nigger",
                "niga",
                "hs",
                "opfer",
                "spast"
            ]

            if any(wort in text for wort in schlechte_woerter):
                punkte -= 70
                analyse.append("❌ Unangemessene Wörter erkannt.")

            if "ja" in text:
                analyse.append("✅ Gesprächsbereit.")
            else:
                punkte -= 10
                analyse.append("🟡 Gesprächsbereitschaft unklar.")

            punkte = max(0, min(100, punkte))

            if punkte >= 80:
                status = "🟢 Sehr gut"
            elif punkte >= 60:
                status = "🟡 Mittel"
            else:
                status = "🔴 Schwach"

            check = kanal(message.guild, "bewerbungs-check")

            if check:
                embed = discord.Embed(
                    title="🤖 KI Bewerbungsprüfung",
                    color=0x3498db
                )

                embed.add_field(name="👤 Bewerber", value=message.author.mention, inline=False)
                embed.add_field(name="📊 Bewertung", value=f"{punkte}/100", inline=True)
                embed.add_field(name="📌 Status", value=status, inline=True)
                embed.add_field(name="📝 Analyse", value="\n".join(analyse), inline=False)
                embed.add_field(name="📥 Bewerbung", value=message.jump_url, inline=False)
                embed.timestamp = datetime.now()

                await check.send(embed=embed)

            try:
                dm = discord.Embed(
                    title="🪖 Bewerbung geprüft",
                    description=(
                        f"📊 Bewertung: {punkte}/100\n"
                        f"📌 Status: {status}"
                    ),
                    color=0x2E8B57
                )

                await message.author.send(embed=dm)
            except:
                print("DM konnte nicht gesendet werden.")

    await bot.process_commands(message)


@bot.tree.command(name="close_bewerbung", description="Schließt einen Bewerbungskanal")
async def close_bewerbung(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message(
            "❌ Keine Rechte.",
            ephemeral=True
        )

    if interaction.channel.name.startswith("bewerbung-"):
        await interaction.response.send_message("✅ Bewerbung wird geschlossen.", ephemeral=True)
        await interaction.channel.delete()
    else:
        await interaction.response.send_message(
            "❌ Das ist kein Bewerbungskanal.",
            ephemeral=True
        )


bot.run(TOKEN)
