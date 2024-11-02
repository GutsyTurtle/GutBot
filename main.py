import os
import json
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load starboard configurations
def load_starboard_configs():
    if os.path.exists("starboard_configs.json"):
        with open("starboard_configs.json", "r") as f:
            return json.load(f)
    return {}

# Save starboard configurations
def save_starboard_configs(configs):
    with open("starboard_configs.json", "w") as f:
        json.dump(configs, f)

starboard_configs = load_starboard_configs()

# Track messages already posted to the starboard
starboard_messages = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} and {bot.user.id}')
    print(f'Configurations loaded: {starboard_configs}')

@bot.command()
async def setstarboard(ctx, channel: discord.TextChannel, emoji: str, threshold: int):
    guild_id = str(ctx.guild.id)
    starboard_configs[guild_id] = {
        'channel_id': channel.id,
        'emoji': emoji,
        'threshold': threshold
    }
    save_starboard_configs(starboard_configs)
    await ctx.send(f'Starboard set in {channel.mention} with emoji {emoji} and threshold {threshold}')
    print(f"Starboard set for guild {guild_id}: {starboard_configs[guild_id]}")

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    guild_id = str(reaction.message.guild.id)
    if guild_id in starboard_configs:
        config = starboard_configs[guild_id]
        emoji = config['emoji']
        threshold = config['threshold']
        channel_id = config['channel_id']
        
        print(f"Reaction received: {reaction.emoji}, Expected emoji: {emoji}, Threshold: {threshold}")

        if str(reaction.emoji) == emoji:
            current_count = reaction.count
            print(f"Emoji matches. Current count: {current_count}, Threshold: {threshold}")

            if current_count >= threshold:
                channel = bot.get_channel(channel_id)
                if channel:
                    # Construct a link to the original message
                    message_url = f"https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}"
                    
                    # Check if the message is already in starboard
                    if reaction.message.id in starboard_messages:
                        starboard_msg = starboard_messages[reaction.message.id]
                        # Update the embed with the new reaction count
                        embed = starboard_msg.embeds[0]
                        embed.set_footer(text=f"⭐ {current_count} | Sent in #{reaction.message.channel.name}")
                        await starboard_msg.edit(embed=embed)
                        print(f"Updated starboard message for original message ID {reaction.message.id}")
                    else:
                        # Create a new embed and send to starboard
                        embed = discord.Embed(
                            description=f"[Jump to message]({message_url})\n\n{reaction.message.content}"
                        )
                        embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
                        embed.set_footer(text=f"⭐ {current_count} | Sent in #{reaction.message.channel.name}")
                        if reaction.message.attachments:
                            attachment = reaction.message.attachments[0]
                            embed.set_image(url=attachment.url)

                        starboard_msg = await channel.send(embed=embed)
                        # Track the starboard message to update later
                        starboard_messages[reaction.message.id] = starboard_msg
                        print(f"Message sent to starboard: {embed.to_dict()}")
                else:
                    print(f"Channel '{channel_id}' not found in guild {guild_id}.")
        else:
            print("Reaction emoji does not match the configured emoji.")

@bot.event
async def on_guild_join(guild):
    print(f"Joined a new guild: {guild.name}")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
