import discord
from discord.ext import commands
import os

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True  # For reading message content

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

#Get the token from an environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Constants
STARBOARD_CHANNEL_ID = 1290745202813960203  # Starboard channel ID where the messages will be posted
CUSTOM_STAR_EMOJI_ID = 1143285896725135370  # Custom emoji ID (without name, just the ID)
CUSTOM_STAR_EMOJI_DISPLAY = "<:raywheeze:1143285896725135370>"  # Custom emoji display (as it appears in the message)
STAR_THRESHOLD = 3  # Number of reactions needed to post to the starboard

# STARBOARD_CHANNEL_ID = os.environ.get('STARBOARD_CHANNEL_ID')
# CUSTOM_STAR_EMOJI_ID = os.environ.get('CUSTOM_STAR_EMOJI_ID')
# CUSTOM_STAR_EMOJI_DISPLAY = os.environ.get('CUSTOM_STAR_EMOJI_DISPLAY')
# STAR_THRESHOLD = int(os.environ.get('STAR_THRESHOLD'))  # Convert to int if needed


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_reaction_add(reaction, user):
    # Debugging - See if the reaction event is detected
    print(f"Reaction added by {user} to message {reaction.message.id} in {reaction.message.channel.name}")

    # Ignore bot reactions
    if user.bot:
        print("Ignoring reaction from a bot.")
        return

    # Check if the reaction is the custom star emoji
    if isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == CUSTOM_STAR_EMOJI_ID:
        print(f"Custom emoji {reaction.emoji.name} matched!")
        
        # Ensure the reaction count meets the threshold
        if reaction.count >= STAR_THRESHOLD:
            starboard_channel = bot.get_channel(STARBOARD_CHANNEL_ID)
            if not starboard_channel:
                print("Starboard channel not found!")
                return

            # Check if the message is already in the starboard
            async for message in starboard_channel.history(limit=200):
                if message.embeds and message.embeds[0].footer.text == f"ID: {reaction.message.id}":
                    print("Message already in starboard")
                    return

            # Create the embed for the starboard, with message content at the top
            embed = discord.Embed(description=f"**{reaction.message.content}**", color=discord.Color.gold())  # Message at top
            embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.display_avatar.url)
            embed.add_field(name="Jump to message", value=f"[Click here]({reaction.message.jump_url})")
            
            # Add the reaction count and channel name to the embed, using the custom emoji
            embed.add_field(name="Reactions", value=f"{reaction.count} {CUSTOM_STAR_EMOJI_DISPLAY}", inline=True)
            embed.add_field(name="Channel", value=f"#{reaction.message.channel.name}", inline=True)
            
            embed.set_footer(text=f"ID: {reaction.message.id}")

            # Check if there are any attachments (images or videos)
            if reaction.message.attachments:
                attachment = reaction.message.attachments[0]
                if attachment.content_type.startswith("image/"):
                    # If it's an image, embed the image
                    embed.set_image(url=attachment.url)
                elif attachment.content_type.startswith("video/"):
                    # If it's a video, just add the video URL (Discord will embed it automatically)
                    embed.add_field(name="Attached video", value=attachment.url)

            # Send the embed to the starboard channel
            await starboard_channel.send(embed=embed)
            print(f"Message from {reaction.message.author} posted to starboard with media!")
        else:
            print(f"Reaction count ({reaction.count}) did not meet the threshold ({STAR_THRESHOLD}).")

# Run the bot with your token
bot.run(TOKEN)