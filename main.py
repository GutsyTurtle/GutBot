import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.reactions = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store per-guild starboard settings
starboard_settings = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def prompt_for_input(ctx, question):
    """ Helper function to prompt user for input and return their response """
    await ctx.send(question)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        response = await bot.wait_for("message", check=check, timeout=60)
        return response.content
    except asyncio.TimeoutError:
        await ctx.send("Setup timed out. Please start again.")
        return None

@bot.command(name="setupstarboard")
@commands.has_permissions(administrator=True)
async def setup_starboard(ctx):
    """
    Command to guide the user through setting up the starboard channel, emoji, and threshold interactively.
    """
    await ctx.send("Starting starboard setup. Please answer the following questions:")

    # Prompt for channel
    channel_name = await prompt_for_input(ctx, "Enter the name of the channel to use for the starboard:")
    if channel_name is None:
        return

    # Get the channel object by name
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if not channel:
        await ctx.send(f"Channel '{channel_name}' not found. Setup canceled.")
        return

    # Prompt for emoji
    emoji = await prompt_for_input(ctx, "Enter the emoji to use for the starboard reactions (e.g., ⭐ or a custom emoji):")
    if emoji is None:
        return

    # Prompt for threshold
    threshold_str = await prompt_for_input(ctx, "Enter the reaction threshold (number of reactions needed):")
    if threshold_str is None:
        return

    try:
        threshold = int(threshold_str)
    except ValueError:
        await ctx.send("Invalid number entered for threshold. Setup canceled.")
        return

    # Save settings
    starboard_settings[ctx.guild.id] = {
        "channel_id": channel.id,
        "emoji": emoji,
        "threshold": threshold
    }

    await ctx.send(f"Starboard set up successfully for {channel.mention} with emoji '{emoji}' and threshold {threshold}.")

@bot.event
async def on_reaction_add(reaction, user):
    """
    Event that triggers when a reaction is added to a message.
    Checks if the reaction matches the starboard emoji and meets the threshold.
    """
    if user.bot:
        return  # Ignore bot reactions

    guild_id = reaction.message.guild.id
    settings = starboard_settings.get(guild_id)

    if not settings:
        return  # No starboard settings for this guild

    # Retrieve the guild's starboard settings
    channel_id = settings["channel_id"]
    threshold = settings["threshold"]
    target_emoji = settings["emoji"]

    # Check if the reaction emoji matches and if it meets the threshold
    if str(reaction.emoji) == target_emoji and reaction.count >= threshold:
        starboard_channel = reaction.message.guild.get_channel(channel_id)
        if starboard_channel:
            await starboard_channel.send(
                f"⭐ Message from {reaction.message.author.mention} in {reaction.message.channel.mention}:\n{reaction.message.content}"
            )

# Run the bot with your token
bot.run("YOUR_BOT_TOKEN")

