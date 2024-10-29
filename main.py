import os
import discord
from discord.ext import commands
import re

# Set up intents
intents = discord.Intents.default()
intents.messages = True  # Enable message intents
intents.reactions = True  # Enable reaction intents
intents.message_content = True  # Enable message content intent

# Initialize the bot with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Store configurations for each guild
starboard_configs = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.command(name="setstarboard")
@commands.has_permissions(administrator=True)
async def setup_starboard(ctx):
    try:
        print("setup_starboard command triggered!")  # Debug print
        await ctx.send("Let's set up the starboard! Please provide the following information.")

        # Ask for the channel name
        await ctx.send("What is the name of the channel where the starboard should be? (e.g., #starboard)")
        channel_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Ask for the emoji
        await ctx.send("Which emoji should be used for the starboard? (You can use a custom emoji or a default one, e.g., ⭐ or a custom emoji)")
        emoji_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Ask for the threshold
        await ctx.send("What should be the threshold for the starboard? (e.g., 3)")
        threshold_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Extract the channel ID if a mention is provided, otherwise use the name
        channel_name = channel_message.content.strip()
        channel_id = None
        mention_match = re.match(r'<#(\d+)>', channel_name)
        if mention_match:
            channel_id = int(mention_match.group(1))
        else:
            # Retrieve channel by name if it was not a mention
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name.strip('#'))
            if channel:
                channel_id = channel.id

        if not channel_id:
            await ctx.send(f"Channel '{channel_name}' not found.")
            print(f"Channel '{channel_name}' not found.")
            return

        # Store the configuration with the actual channel ID
        emoji = emoji_message.content.strip()
        threshold = int(threshold_message.content.strip())
        starboard_configs[ctx.guild.id] = {
            "channel_id": channel_id,
            "emoji": emoji,
            "threshold": threshold
        }

        # Confirm the config is stored with correct ID
        print(f"Configuration saved for guild {ctx.guild.id}: {starboard_configs[ctx.guild.id]}")

        # Send confirmation to user
        channel = ctx.guild.get_channel(channel_id)
        await ctx.send(f"Starboard set up successfully! Channel: {channel.mention if channel else '#'+channel_name}, Emoji: {emoji}, Threshold: {threshold}")

    except Exception as e:
        print(f"Error occurred: {e}")
        await ctx.send("An error occurred while setting up the starboard. Please check the console for details.")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    guild_id = reaction.message.guild.id
    if guild_id in starboard_configs:
        config = starboard_configs[guild_id]
        
        # Debugging print to check the config for the guild
        print(f"Config for guild {guild_id}: {config}")

        # Check if channel_id is present in config
        if "channel_id" not in config:
            print(f"No channel_id found in config for guild {guild_id}.")
            return

        channel_id = config["channel_id"]
        emoji = config["emoji"]
        threshold = config["threshold"]

        # Check if the emoji matches
        if str(reaction.emoji) == emoji:
            print(f"Emoji matches. Current count: {reaction.count}, Threshold: {threshold}")
            if reaction.count >= threshold:
                channel = reaction.message.guild.get_channel(channel_id)
                if channel:
                    await channel.send(
                        f"Message in #{reaction.message.channel.name} has reached {reaction.count} {emoji}! "
                        f"Message: {reaction.message.jump_url}"
                    )
                    print(f"Message sent to {channel.name}!")  # Debug print
                else:
                    print(f"Channel ID '{channel_id}' not found.")
            else:
                print(f"Current count is {reaction.count}, waiting for {threshold}.")
        else:
            print("Emoji does not match.")
    else:
        print(f"No configuration found for guild {guild_id}.")

# Run the bot with the token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot.run(TOKEN)
