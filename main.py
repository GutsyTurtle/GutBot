import discord
from discord.ext import commands
import os

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True  # For reading message content

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Get the token from an environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Variables for emoji, channel, and star limit selection
STARBOARD_CHANNEL_ID = None
CUSTOM_STAR_EMOJI_ID = None
CUSTOM_STAR_EMOJI_DISPLAY = None
STAR_THRESHOLD = 3  # Default threshold

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command()
async def set_starboard(ctx):
    """Prompts the user to select a custom emoji, starboard channel, and star limit."""
    # Step 1: Prompt for emoji
    await ctx.send("React to this message with the emoji you'd like to use for the starboard!")

    def emoji_check(reaction, user):
        return user == ctx.author and reaction.message.id == ctx.message.id

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=emoji_check)
        global CUSTOM_STAR_EMOJI_ID, CUSTOM_STAR_EMOJI_DISPLAY

        if isinstance(reaction.emoji, discord.Emoji):
            CUSTOM_STAR_EMOJI_ID = reaction.emoji.id
            CUSTOM_STAR_EMOJI_DISPLAY = str(reaction.emoji)
            await ctx.send(f"Custom star emoji set to {CUSTOM_STAR_EMOJI_DISPLAY}!")
        else:
            await ctx.send("Please react with a custom emoji.")
            return
    except asyncio.TimeoutError:
        await ctx.send("You didn't react in time!")
        return

    # Step 2: Prompt for starboard channel
    await ctx.send("Now, please mention the channel you want to use for the starboard.")

    def channel_check(message):
        return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions

    try:
        msg = await bot.wait_for("message", timeout=30.0, check=channel_check)
        global STARBOARD_CHANNEL_ID
        STARBOARD_CHANNEL_ID = msg.channel_mentions[0].id
        await ctx.send(f"Starboard channel set to {msg.channel_mentions[0].mention}!")
    except asyncio.TimeoutError:
        await ctx.send("You didn't mention a channel in time!")
        return

    # Step 3: Prompt for star threshold
    await ctx.send("Please enter the minimum number of reactions needed for a message to reach the starboard.")

    def threshold_check(message):
        return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

    try:
        msg = await bot.wait_for("message", timeout=30.0, check=threshold_check)
        global STAR_THRESHOLD
        STAR_THRESHOLD = int(msg.content)
        await ctx.send(f"Star threshold set to {STAR_THRESHOLD}!")
    except asyncio.TimeoutError:
        await ctx.send("You didn't enter a valid star threshold in time!")
        return

@bot.event
async def on_reaction_add(reaction, user):
    # Ignore bot reactions
    if user.bot:
        return

    # Check if the reaction is the custom star emoji
    if CUSTOM_STAR_EMOJI_ID and isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == CUSTOM_STAR_EMOJI_ID:
        # Ensure the reaction count meets the threshold
        if reaction.count >= STAR_THRESHOLD:
            starboard_channel = bot.get_channel(STARBOARD_CHANNEL_ID)
            if not starboard_channel:
                print("Starboard channel not found!")
                return

            # Check if the message is already in the starboard
            async for message in starboard_channel.history(limit=200):
                if message.embeds and message.embeds[0].footer.text == f"ID: {reaction.message.id}":
                    print("Message already in starboard")
                    return

            # Post about the starboard status
            await starboard_channel.send(
                f"Message in #{reaction.message.channel.name} has reached {reaction.count} {CUSTOM_STAR_EMOJI_DISPLAY}!"
            )

            # Create the embed for the starboard
            embed = discord.Embed(description=f"{reaction.message.content}", color=discord.Color.gold())
            embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.display_avatar.url)
            embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})")
            embed.add_field(name="Reactions", value=f"{reaction.count} {CUSTOM_STAR_EMOJI_DISPLAY}", inline=True)
            embed.add_field(name="Channel", value=f"#{reaction.message.channel.name}", inline=True)
            embed.set_footer(text=f"ID: {reaction.message.id}")

            # Handle attachments and stickers
            if reaction.message.attachments:
                attachment = reaction.message.attachments[0]
                if attachment.content_type.startswith("image/"):
                    embed.set_image(url=attachment.url)
                elif attachment.content_type.startswith("video/"):
                    embed.add_field(name="Attached video", value=attachment.url)

            if reaction.message.stickers:
                sticker = reaction.message.stickers[0]
                embed.add_field(name="Attached sticker", value=f"{sticker.name}", inline=True)

            # Send the embed to the starboard channel
            await starboard_channel.send(embed=embed)
            print(f"Message from {reaction.message.author} posted to starboard with media!")
        else:
            print(f"Reaction count ({reaction.count}) did not meet the threshold ({STAR_THRESHOLD}).")

# Run the bot with your token
bot.run(TOKEN)

