import os
import sqlite3
import discord
from discord.ext import commands

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Database connection and setup
db_path = "starboard.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the starboard_configs table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS starboard_configs (
        guild_id TEXT PRIMARY KEY,
        channel_id INTEGER NOT NULL,
        emoji TEXT NOT NULL,
        threshold INTEGER NOT NULL
    )
''')
conn.commit()

# Save starboard configuration to the database
def save_starboard_config(guild_id, channel_id, emoji, threshold):
    cursor.execute('''
        INSERT OR REPLACE INTO starboard_configs (guild_id, channel_id, emoji, threshold)
        VALUES (?, ?, ?, ?)
    ''', (guild_id, channel_id, emoji, threshold))
    conn.commit()
    print(f"Configuration saved for guild {guild_id}: channel_id={channel_id}, emoji='{emoji}', threshold={threshold}")

# Load starboard configuration from the database
def load_starboard_config(guild_id):
    cursor.execute('SELECT channel_id, emoji, threshold FROM starboard_configs WHERE guild_id = ?', (guild_id,))
    result = cursor.fetchone()
    if result:
        print(f"Configuration loaded for guild {guild_id}: {result}")
        return {
            'channel_id': result[0],
            'emoji': result[1],
            'threshold': result[2]
        }
    print(f"No configuration found for guild {guild_id}")
    return None

# Track messages already posted to the starboard
starboard_messages = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print("Bot is ready and configurations loaded from the database.")

@bot.command()
async def setstarboard(ctx, channel: discord.TextChannel, emoji: str, threshold: int):
    guild_id = str(ctx.guild.id)
    save_starboard_config(guild_id, channel.id, emoji, threshold)
    await ctx.send(f'Starboard set in {channel.mention} with emoji {emoji} and threshold {threshold}')
    print(f"Starboard set for guild {guild_id}")

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    guild_id = str(reaction.message.guild.id)
    config = load_starboard_config(guild_id)
    
    if config:
        emoji = config['emoji']
        threshold = config['threshold']
        channel_id = config['channel_id']
        
        if str(reaction.emoji) == emoji:
            current_count = reaction.count
            if current_count >= threshold:
                channel = bot.get_channel(channel_id)
                if channel:
                    # Construct the link to the original message
                    message_url = f"https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}"  
                    # Check if the message is already in starboard
                    if reaction.message.id in starboard_messages:
                        starboard_msg = starboard_messages[reaction.message.id]
                        embed = starboard_msg.embeds[0]
                        embed.set_footer(text=f"{emoji} {current_count} | Sent in #{reaction.message.channel.name}")
                        await starboard_msg.edit(embed=embed)
                        print(f"Updated starboard message for original message ID {reaction.message.id}")
                    else:
                        embed = discord.Embed(
                            description=f"[Jump to message]({message_url})\n\n{reaction.message.content}"
                        )
                        embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
                        embed.set_footer(text=f"{emoji} {current_count} | Sent in #{reaction.message.channel.name}")
                        if reaction.message.attachments:
                            embed.set_image(url=reaction.message.attachments[0].url)
                    
                        # Send the embed to the starboard channel
                        starboard_msg = await channel.send(embed=embed)
                        # Track the starboard message to update it later if needed
                        starboard_messages[reaction.message.id] = starboard_msg
                        print(f"Message sent to starboard: {embed.to_dict()}")

                else:
                    print(f"Channel '{channel_id}' not found in guild '{guild_id}'.")
        else:
            print("Reaction emoji does not match the configured emoji.")

@bot.event
async def on_guild_join(guild):
    print(f"Joined a new guild: {guild.name}")

# Close the database connection on shutdown
@bot.event
async def on_close():
    conn.close()
    print("Database connection closed.")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
