import os
import discord
from discord.ext import commands

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
        print("setstarboard command triggered!")  # Debug print
        await ctx.send("Let's set up the starboard! Please provide the following information.")

        # Ask for the channel name
        await ctx.send("What is the name of the channel where the starboard should be? (e.g., #starboard)")
        channel_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Extract the channel ID from the mention if provided
        channel_id = int(channel_message.content.strip('<#>'))
        channel = ctx.guild.get_channel(channel_id)

        # Check if the channel exists
        if channel is None:
            await ctx.send("Could not find the channel. Please ensure it exists and try again.")
            return

        print(f"Channel name provided: {channel_message.content.strip()}")  # Debug print

        # Ask for the emoji
        await ctx.send("Which emoji should be used for the starboard? (You can use a custom emoji or a default one, e.g., ⭐ or a custom emoji)")
        emoji_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        print(f"Emoji provided: {emoji_message.content.strip()}")  # Debug print

        # Ask for the threshold
        await ctx.send("What should be the threshold for the starboard? (e.g., 3)")
        threshold_message = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        print(f"Threshold provided: {threshold_message.content.strip()}")  # Debug print

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

        print(f"Starboard configuration saved for guild {ctx.guild.id}: {starboard_configs[ctx.guild.id]}")  # Debug print

        await ctx.send(f"Starboard set up successfully! Channel: {channel_name}, Emoji: {emoji}, Threshold: {threshold}")

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error
        await ctx.send("An error occurred while setting up the starboard. Please check the console for details.")

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
        print(f"Reaction received: {reaction.emoji} by {user.name} on message {reaction.message.id}")  # Debug print
        if str(reaction.emoji) == emoji:
            print(f"Emoji matches. Current count: {reaction.count}, Threshold: {threshold}")  # Debug print
            if reaction.count == threshold:
                channel = discord.utils.get(reaction.message.guild.text_channels, name=channel_name.strip('#'))
                if channel:
                    await channel.send(f"Message in #{reaction.message.channel.name} has reached {reaction.count} {emoji}! Message: {reaction.message.jump_url}")
                    print(f"Message sent to {channel_name}!")  # Debug print
                else:
                    print(f"Channel '{channel_name}' not found.")
            else:
                print(f"Current count is {reaction.count}, waiting for {threshold}.")
        else:
            print("Emoji does not match.")

# Run the bot with the token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot.run(TOKEN)
