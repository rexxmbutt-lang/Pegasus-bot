import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"LOGIN SEBAGAI {bot.user} - ONLINE CUK!")
    try:
        synced = await bot.tree.sync()
        print(f"Sync {len(synced)} slash command")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Cek bot hidup apa engga")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency*1000)}ms - Pegasus Online Cuk!")

@bot.tree.command(name="halo", description="Sapa Pegasus")
async def halo(interaction: discord.Interaction):
    await interaction.response.send_message(f"Halo {interaction.user.mention}! Gw Pegasus, siap jaga server lu 🔥")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"Selamat datang {member.mention}! 🔥")

bot.run(os.getenv("DISCORD_TOKEN"))
