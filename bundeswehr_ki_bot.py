# =========================
# BEWERBUNGS CHANNEL
# =========================

BEWERBUNG_CHANNEL = "𝐁𝐄𝐖𝐄𝐑𝐁𝐔𝐍𝐆𝐄𝐍"
CHECK_CHANNEL = "bewerbungs-check"


# =========================
# APPY CHECK
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

    # WICHTIG:
    # KEINE CHANNELS MEHR ERSTELLEN

    check_ch = kanal(
        message.guild,
        CHECK_CHANNEL
    )

    if not check_ch:
        return

    embed = discord.Embed(
        title="🤖 KI Bewerbungsprüfung",
        description="Automatische Appy Analyse",
        color=0x2E8B57
    )

    embed.add_field(
        name="📊 Bewertung",
        value=f"{punkte}/100",
        inline=True
    )

    embed.add_field(
        name="📌 Status",
        value=status,
        inline=True
    )

    embed.add_field(
        name="💡 Empfehlung",
        value=empfehlung,
        inline=False
    )

    embed.add_field(
        name="📝 Analyse",
        value="\n".join(gruende)[:1000],
        inline=False
    )

    embed.timestamp = datetime.now()

    await check_ch.send(
        embed=embed
    )
