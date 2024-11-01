import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load starboard configurations
CONFIG_FILE = 'starboard_configs.json'
starboard_configs = {}

def load_configurations():
    global starboard_configs
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            starboard_configs = json.load(f)
            print(f"Configurations loaded: {starboard_configs}")
    else:
        print("Configuration file not found. Starting with empty configurations.")

def save_configurations():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(starboard_configs, f)
        print(f"Configurations saved: {starboard_configs}")

load_configurations()

@bot.command(name="setstarboard")
async def setup_starboard(ctx, channel_name: str, emoji: str, threshold: int):
    guild_id = ctx.guild.id
    channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)

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
        print(f"Channel '{channel_name}' not found in guild {guild_id}.")

    # Debugging to check saved configurations
    if guild_id in starboard_configs:
        print(f"Configurations for guild {guild_id}: {starboard_configs[guild_id]}")
        try:
            # Attempt to access the channel ID
            test_channel = ctx.guild.get_channel(starboard_configs[guild_id]['channel_id'])
            if test_channel:
                print(f"Channel found: {test_channel.name}")
            else:
                print("Channel not found in guild context!")
        except KeyError as e:
            print(f"KeyError accessing channel ID: {e}")
        except Exception as e:
            print(f"Error accessing channel: {str(e)}")
    else:
        print(f"No configuration found for guild {guild_id}. Please set the starboard again.")

        
@bot.event
async def on_reaction_add(reaction, user):
    print(f"Reaction added by {user} on message ID {reaction.message.id} in channel {reaction.message.channel.name}")

    if user.bot:
        return

    guild_id = reaction.message.guild.id
    if guild_id in starboard_configs:
        config = starboard_configs[guild_id]
        print(f"Config for guild {guild_id}: {config}")

        if str(reaction.emoji) == config["emoji"]:
            if reaction.count >= config["threshold"]:
                channel = reaction.message.guild.get_channel(config["channel_id"])
                if channel:
                    embed = discord.Embed(description=reaction.message.content, color=discord.Color.gold())
                    embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)

                    if reaction.message.attachments:
                        attachment = reaction.message.attachments[0]
                        if any(attachment.url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4"]):
                            embed.set_image(url=attachment.url)

                    await channel.send(embed=embed)
                    print(f"Message sent to starboard channel {channel.name} in guild {guild_id}")
                else:
                    print(f"Channel ID {config['channel_id']} not found in guild {guild_id}")
            else:
                print(f"Emoji matches. Current count: {reaction.count}, Threshold: {config['threshold']}")
    else:
        print(f"No config found for guild {guild_id}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    load_configurations()  # Reload configurations on bot ready to handle reconnects without losing configs

# Load token from environment
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot.run(TOKEN)
