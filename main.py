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

# Constants (default values)
STARBOARD_CHANNEL_ID = None  # To be set during setup
CUSTOM_STAR_EMOJI_ID = None  # To be set during setup
STAR_THRESHOLD = 3  # Default threshold

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_guild_join(guild):
    # Find a text channel where the bot can send messages
    general_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None)
    
    if general_channel:
        # Send a setup message
        await general_channel.send(
            "Hello! Thanks for inviting me! :star:\n\n"
            "To set up the starboard, please respond to the following commands:\n"
            "1. **Set the starboard channel** using: `!setchannel <channel_id>`.\n"
            "2. **Set the emoji ID** using: `!setemoji <emoji_id>`.\n"
            "3. **Set the reaction threshold** using: `!setthreshold <number>`."
        )

@bot.command(name="setchannel")
async def set_channel(ctx, channel_id: int):
    global STARBOARD_CHANNEL_ID
    STARBOARD_CHANNEL_ID = channel_id
    await ctx.send(f"Starboard channel set to <#{channel_id}>.")

@bot.command(name="setemoji")
async def set_emoji(ctx, emoji: str):
    global CUSTOM_STAR_EMOJI_ID
    
    # Check if the emoji is a custom emoji
    if emoji.startswith("<:") and emoji.endswith(">"):  # Custom emoji format
        emoji_id = emoji.split(":")[-1][:-1]  # Extract the emoji ID
        try:
            # Convert emoji_id to an integer
            CUSTOM_STAR_EMOJI_ID = int(emoji_id)
            await ctx.send(f"Starboard emoji set to {emoji}.")  # This will display the emoji correctly
        except ValueError:
            await ctx.send("Invalid custom emoji provided.")
    elif emoji in ["⭐", "🌟", "🦐", "🐢"]:  # Check for default star emojis
        CUSTOM_STAR_EMOJI_ID = None  # Indicates we are using a default emoji
        await ctx.send(f"Default star emoji set to {emoji}.")  # This will also display the emoji correctly
    else:
        await ctx.send("Please provide a valid custom or default star emoji.")


@bot.command(name="setthreshold")
async def set_threshold(ctx, threshold: int):
    global STAR_THRESHOLD
    STAR_THRESHOLD = threshold
    await ctx.send(f"Star threshold set to {threshold} reactions.")

@bot.event
@bot.event
async def on_reaction_add(reaction, user):
    # Debugging - See if the reaction event is detected
    print(f"Reaction added by {user} to message {reaction.message.id} in {reaction.message.channel.name}")

    # Ignore bot reactions
    if user.bot:
        print("Ignoring reaction from a bot.")
        return

    # Check if the reaction is the custom star emoji or the default star emoji
    is_custom_star = isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == CUSTOM_STAR_EMOJI_ID
    is_default_star = str(reaction.emoji) == "⭐"  # Change this to the star emoji you want to use
    
    if is_custom_star or is_default_star:
        print("Star emoji matched!")

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

            # Send a message with reaction count and channel name (outside of the embed)
            await starboard_channel.send(
                f"Message in #{reaction.message.channel.name} has reached {reaction.count} {'⭐' if is_default_star else CUSTOM_STAR_EMOJI_DISPLAY}!"
            )

            # Create the embed for the starboard, with message content at the top
            embed = discord.Embed(description=f"{reaction.message.content}", color=discord.Color.gold())
            embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.display_avatar.url)
            embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})")

            # Add the reaction count dynamically within the embed
            embed.add_field(name="Reactions", value=f"{reaction.count} {'⭐' if is_default_star else CUSTOM_STAR_EMOJI_DISPLAY}", inline=True)
            embed.add_field(name="Channel", value=f"#{reaction.message.channel.name}", inline=True)
            embed.set_footer(text=f"ID: {reaction.message.id}")

            # Check if there are any attachments (images or videos)
            if reaction.message.attachments:
                attachment = reaction.message.attachments[0]
                if attachment.content_type.startswith("image/"):
                    embed.set_image(url=attachment.url)
                elif attachment.content_type.startswith("video/"):
                    embed.add_field(name="Attached video", value=attachment.url)

            # Proper indentation for stickers handling
            if reaction.message.stickers:  # Check for stickers
                sticker = reaction.message.stickers[0]
                embed.add_field(name="Attached sticker", value=f"{sticker.name}", inline=True)

            # Send the embed to the starboard channel
            await starboard_channel.send(embed=embed)
            print(f"Message from {reaction.message.author} posted to starboard with media!")
        else:
            print(f"Reaction count ({reaction.count}) did not meet the threshold ({STAR_THRESHOLD}).")

# Run the bot with your token
bot.run(TOKEN)
