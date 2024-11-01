import os
import discord
import json
from discord.ext import commands

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True

# Initialize the bot with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# File path for storing configuration
CONFIG_FILE_PATH = "starboard_config.json"

# Load existing configurations from file if it exists
def load_configurations():
    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Configuration file not found. Starting with empty configurations.")
        return {}
    except json.JSONDecodeError:
        print("Error decoding the configuration file. Starting with empty configurations.")
        return {}

# Save configurations to file
def save_configurations():
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(starboard_configs, file)
        print("Configurations saved.")

# Store configurations for each guild
starboard_configs = load_configurations()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.command(name="setstarboard")
@commands.has_permissions(administrator=True)
async def setup_starboard(ctx):
    try:
        print("setup_starboard command triggered!")
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

        # Save the updated configurations
        save_configurations()

        await ctx.send(f"Starboard set up successfully! Channel: {channel_name}, Emoji: {emoji}, Threshold: {threshold}")

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
        channel_name = config.get("channel_name")
        emoji = config.get("emoji")
        threshold = config.get("threshold")

        # Check if the emoji matches
        if str(reaction.emoji) == emoji:
            print(f"Emoji matches. Current count: {reaction.count}, Threshold: {threshold}")
            if reaction.count >= threshold:
                # Get the channel by name
                channel = discord.utils.get(reaction.message.guild.text_channels, name=channel_name.strip('#'))
                if channel:
                    # Create and send an embed with image or video if present
                    embed = discord.Embed(description=f"[Jump to Message]({reaction.message.jump_url})")
                    embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)

                    # Add image, gif, or video if exists
                    if reaction.message.attachments:
                        for attachment in reaction.message.attachments:
                            if attachment.url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm')):
                                embed.set_image(url=attachment.url)
                                break  # Only display the first attachment

                    await channel.send(f"{emoji} **Message by {reaction.message.author.mention} has reached {reaction.count} reactions!**", embed=embed)
                else:
                    print(f"Channel '{channel_name}' not found.")
            else:
                print(f"Current count is {reaction.count}, waiting for {threshold}.")
        else:
            print("Emoji does not match.")

# Run the bot with the token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot.run(TOKEN)
