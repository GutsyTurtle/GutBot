import discord
from discord.ext import commands
import json
import os

# Define intents and create bot instance
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True  # Ensure this is enabled for privileged intents

bot = commands.Bot(command_prefix="!", intents=intents)

# Global configuration for starboard
starboard_configs = {}

# Load configurations from JSON file
def load_configurations():
    global starboard_configs
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            starboard_configs = json.load(f)
            print("Configurations loaded:", starboard_configs)
    else:
        print("No configuration file found. Starting with empty configurations.")

# Save configurations to JSON file
def save_configurations():
    with open("config.json", "w") as f:
        json.dump(starboard_configs, f)
        print("Configurations saved:", starboard_configs)

# Load configurations on startup
load_configurations()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} and {len(bot.guilds)} guilds.")

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return  # Ignore own reactions
    
    # Check if the reaction is the starboard emoji
    for guild_id, config in starboard_configs.items():
        if str(reaction.emoji) == config['emoji'] and reaction.count >= config['threshold']:
            guild = bot.get_guild(int(guild_id))
            channel = guild.get_channel(config["channel_id"])
            if channel is not None:
                embed = discord.Embed(description=reaction.message.content)
                embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
                embed.set_footer(text=f" {reaction.count} reactions | {reaction.message.jump_url}")
                
                # Check for images, GIFs, and stickers
                if reaction.message.attachments:
                    for attachment in reaction.message.attachments:
                        if attachment.url.endswith(('png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'gif')):
                            embed.set_image(url=attachment.url)
                            break
                
                await channel.send(embed=embed)
                print(f"Message sent to starboard in {channel.mention} for guild {guild_id}.")
            else:
                print(f"Channel '{config['channel_id']}' not found in guild {guild_id}.")
            break

@bot.command(name="setstarboard")
async def setup_starboard(ctx, channel_name: str, emoji: str, threshold: int):
    guild_id = str(ctx.guild.id)
    channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)

    print(f"Attempting to set starboard: Channel Name: {channel_name}, Emoji: {emoji}, Threshold: {threshold}")

    if channel:
        # Update the starboard configurations
        starboard_configs[guild_id] = {
            "channel_id": channel.id,
            "emoji": emoji,
            "threshold": threshold
        }
        save_configurations()
        await ctx.send(f"Starboard set for {channel.mention} with emoji {emoji} and threshold {threshold}")
        print(f"Starboard set for guild {guild_id}: {starboard_configs[guild_id]}")
    else:
        await ctx.send(f"Channel '{channel_name}' not found.")
        print(f"Channel '{channel_name}' not found in guild {guild_id}. Available channels: {[c.name for c in ctx.guild.text_channels]}")

    # Debugging to check saved configurations
    if guild_id in starboard_configs:
        print(f"Configurations for guild {guild_id}: {starboard_configs[guild_id]}")
    else:
        print(f"No configuration found for guild {guild_id}. Please set the starboard again.")

# Start the bot with your token
bot.run("DISCORD_BOT_TOKEN")

