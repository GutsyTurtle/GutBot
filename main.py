import os
import discord
from discord.ext import commands

# Set up intents
intents = discord.Intents.default()
intents.messages = True  # Enable message intents
intents.reactions = True  # Enable reaction intents

# Initialize the bot with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Store configurations for each guild
starboard_configs = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.command(name="setupstarboard")
@commands.has_permissions(administrator=True)
async def setup_starboard(ctx):
    await ctx.send("Let's set up the starboard! Please provide the following information.")

    # Ask for the channel name
    await ctx.send("What is the name of the channel where the starboard should be? (e.g., #starboard)")
    channel_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

    # Ask for the emoji
    await ctx.send("Which emoji should be used for the starboard? (You can use a custom emoji or a default one, e.g., ⭐ or :raywheeze:)")
    emoji_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

    # Ask for the threshold
    await ctx.send("What should be the threshold for the starboard? (e.g., 3)")
    threshold_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

    # Store the values
    channel_name = channel_message.content.strip()
    emoji = emoji_message.content.strip()
    threshold = int(threshold_message.content.strip())

    # Store the configuration for the guild
    starboard_configs[ctx.guild.id] = {
        "channel_name": channel_name,
        "emoji": emoji,
        "threshold": threshold
    }

    await ctx.send(f"Starboard set up successfully! Channel: {channel_name}, Emoji: {emoji}, Threshold: {threshold}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    guild_id = reaction.message.guild.id
    if guild_id in starboard_configs:
        config = starboard_configs[guild_id]
        channel_name = config['channel_name']
        emoji = config['emoji']
        threshold = config['threshold']

        # Check if the emoji matches
        if str(reaction.emoji) == emoji:
            if reaction.count == threshold:
                channel = discord.utils.get(reaction.message.guild.text_channels, name=channel_name.strip('#'))
                if channel:
                    await channel.send(f"Message in #{reaction.message.channel.name} has reached {reaction.count} {emoji}! Message: {reaction.message.jump_url}")
                else:
                    print(f"Channel '{channel_name}' not found.")
            else:
                print(f"Current count is {reaction.count}, waiting for {threshold}.")
        else:
            print("Emoji does not match.")

# Run the bot with the token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot.run(TOKEN)


