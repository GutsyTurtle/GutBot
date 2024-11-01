import discord
from discord.ext import commands
import json
import os

# Set up intents and bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load configurations on startup
starboard_configs = {}

def load_configurations():
    global starboard_configs
    try:
        if os.path.exists("starboard_config.json"):
            with open("starboard_config.json", "r") as f:
                starboard_configs = json.load(f)
                print("Configurations loaded on startup:", starboard_configs)
        else:
            print("Configuration file not found. Starting with empty configurations.")
    except Exception as e:
        print("Error loading configurations:", e)
        starboard_configs = {}

# Save configurations to file
def save_configurations():
    try:
        with open("starboard_config.json", "w") as f:
            json.dump(starboard_configs, f, indent=4)
            print("Configurations saved:", starboard_configs)
    except Exception as e:
        print("Error saving configurations:", e)

# Load configurations on bot startup
load_configurations()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.command(name="setstarboard")
async def set_starboard(ctx, channel: discord.TextChannel, emoji: str, threshold: int):
    guild_id = str(ctx.guild.id)
    starboard_configs[guild_id] = {
        "channel_id": channel.id,
        "emoji": emoji,
        "threshold": threshold
    }
    save_configurations()  # Save changes after setting configuration
    await ctx.send(f"Starboard set to {channel.mention} with emoji {emoji} and threshold {threshold}")
    print(f"Starboard set for guild {guild_id}: {starboard_configs[guild_id]}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    guild_id = str(reaction.message.guild.id)
    config = starboard_configs.get(guild_id)
    
    if not config:
        print(f"No configuration found for guild {guild_id}")
        return
    
    # Check if the emoji matches and count exceeds threshold
    if str(reaction.emoji) == config["emoji"] and reaction.count >= config["threshold"]:
        print("Emoji matches and threshold reached.")
        
        # Retrieve starboard channel
        channel = bot.get_channel(config["channel_id"])
        if channel is None:
            print(f"Starboard channel with ID {config['channel_id']} not found.")
            return
        
        # Embed the message with images/videos
        embed = discord.Embed(description=reaction.message.content, color=discord.Color.gold())
        if reaction.message.attachments:
            for attachment in reaction.message.attachments:
                if any(attachment.url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    embed.set_image(url=attachment.url)
                elif any(attachment.url.lower().endswith(ext) for ext in ['.mp4', '.webm']):
                    embed.add_field(name="Video", value=attachment.url, inline=False)
        
        embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
        embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})")
        
        await channel.send(embed=embed)
        print("Message sent to starboard.")

# Run the bot with your token
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
