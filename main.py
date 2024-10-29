import discord
from discord.ext import commands
import os

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Default configurations per server
server_configs = {}

# Add your token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command(name="setstarboard")
@commands.has_permissions(administrator=True)
async def set_starboard(ctx, channel_name: str, emoji: str, threshold: int):
    # Check if channel_name is a mention and extract ID
    if channel_name.startswith("<#") and channel_name.endswith(">"):
        channel_id = int(channel_name[2:-1])
        channel = ctx.guild.get_channel(channel_id)
    else:
        # Otherwise, try finding by name
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    
    if channel is None:
        await ctx.send(f"Channel '{channel_name}' not found.")
        return

    # Rest of your code for setting emoji and threshold
    guild_id = ctx.guild.id

    # Check if the emoji is a custom emoji or a default one
    if emoji.startswith("<:") and emoji.endswith(">"):  # Custom emoji format
        custom_emoji = await commands.EmojiConverter().convert(ctx, emoji)
        emoji_id = custom_emoji.id
        emoji_name = str(custom_emoji)
    else:  # Default emoji (unicode)
        emoji_id = emoji  # Keep it as a string for default emojis
        emoji_name = emoji

    # Store configuration for the guild
    server_configs[guild_id] = {
        "starboard_channel_id": channel.id,
        "emoji": emoji_id,
        "emoji_name": emoji_name,
        "threshold": threshold
    }
    await ctx.send(f"Starboard set to {channel.mention} with emoji {emoji_name} and threshold {threshold}.")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    guild_id = reaction.message.guild.id
    if guild_id not in server_configs:
        return

    config = server_configs[guild_id]
    starboard_channel_id = config["starboard_channel_id"]
    threshold = config["threshold"]
    emoji = config["emoji"]

    # Check if the reaction is the correct emoji
    if str(reaction.emoji) == emoji and reaction.count >= threshold:
        starboard_channel = bot.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        # Check if the message is already in the starboard
        async for message in starboard_channel.history(limit=200):
            if message.embeds and message.embeds[0].footer.text == f"ID: {reaction.message.id}":
                return

        # Create the embed
        embed = discord.Embed(description=reaction.message.content, color=discord.Color.gold())
        embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.display_avatar.url)
        embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})")
        embed.add_field(name="Reactions", value=f"{reaction.count} {emoji}", inline=True)
        embed.add_field(name="Channel", value=f"#{reaction.message.channel.name}", inline=True)
        embed.set_footer(text=f"ID: {reaction.message.id}")

        # Attach images if present
        if reaction.message.attachments:
            attachment = reaction.message.attachments[0]
            if attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)

        await starboard_channel.send(embed=embed)

bot.run(TOKEN)

