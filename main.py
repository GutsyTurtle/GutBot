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
async def set_starboard(ctx, channel: discord.TextChannel, emoji: str, threshold: int):
    guild_id = ctx.guild.id
    server_configs[guild_id] = {
        "starboard_channel_id": channel.id,
        "emoji": emoji,
        "threshold": threshold
    }
    await ctx.send(f"Starboard set to {channel.mention} with emoji {emoji} and threshold {threshold}.")

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

