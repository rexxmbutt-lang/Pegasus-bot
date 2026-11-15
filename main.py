import discord
from discord.ext import commands, tasks
import os
import json
import urllib.request
import urllib.parse
import asyncio

# ======================================================
# === YOUR SETTINGS - EDIT HERE ONLY ===
# ======================================================

# 1. ID LU - Buat DM system, biar cuma lu yang bisa kirim pesan lewat DM
# Cara dapet: Pencet lama profil lu -> Copy User ID
OWNER_ID = 1437432905734291618

# 2. ID CHANNEL VOICE YANG MAU DIJAGA
VOICE_CHANNEL_ID = 1568316222792278218

# 3. ID CHANNEL BUAT INFO UPDATE SCRIPT (default kalo lu pake preset)
UPDATE_CHANNEL_ID = 1570412727019638876

# 4. PESAN PRESET LU - SETTING DI SINI
# Kalo mau nambah, tinggal copy format di bawah
PRESET_MESSAGES = {
    "update_VD": "@everyone\n🔥 **VIOLENCE DISTRICT SCRIPT UPDATE**\nNew version is now live!\nGet it with /script violence district",
    "update_universal": "@everyone\n🔥 **UNIVERSAL SCRIPT UPDATE**\nNew version is now live!\nGet it with /script universal",
    "maintenance": "@everyone\n```VD SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "update_opah": "@everyone\n🔥 **MALAM SAMA OPAH SCRIPT UPDATE**\nNew version is now live!\nGet it now!",
    "maintenance_2": "@everyone\n```UNIVERSAL SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "maintenance_3": "@everyone\n```MALAM SAMA OPAH SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "changelog_VD": "@everyone\n📝 **CHANGELOG - VIOLENCE DISTRICT**\n✅ Added: Auto Farm, ESP\n❌ Removed: Old Aimbot\n🔧 Fixed: Bug teleport",
    "changelog_universal": "@everyone\n📝 **CHANGELOG - UNIVERSAL SCRIPT**\n✅ Added: New UI\n❌ Removed: Old Fly\n🔧 Fixed: Crash on load",
    "changelog_opah": "@everyone\n📝 **CHANGELOG - MALAM SAMA OPAH**\n✅ Added: Auto Collect\n❌ Removed: - \n🔧 Fixed: Lag fix",
}

HELP_MESSAGE = """**PEGASUS - HOW TO USE**

**/help** - Show this message
**/script [game name]** - Search scripts on ScriptBlox
Example: `/script blox fruit`
Example: `/script blade ball`
"""

# ======================================================
# === DO NOT EDIT BELOW ===
# ======================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- VOICE: NYANGKUT SELAMANYA ---
async def join_voice():
    print(f"DEBUG JOIN ID={VOICE_CHANNEL_ID}")
    try:
        if VOICE_CHANNEL_ID == 0:
            print("DEBUG ID MASIH 0!")
            return
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if not channel:
            print("DEBUG CHANNEL KETEMU NONE, COBA FETCH...")
            channel = await bot.fetch_channel(VOICE_CHANNEL_ID)
        print(f"DEBUG CHANNEL={channel} TYPE={type(channel)}")
        if bot.voice_clients:
            print("DEBUG UDAH CONNECT, SKIP")
            return
        await channel.connect(self_deaf=True, self_mute=True)
        print("DEBUG BERHASIL CONNECT!")
    except Exception as e:
        print(f"DEBUG JOIN ERROR: {e}")
        
tasks.loop(seconds=60)
async def keep_voice_alive():
    if VOICE_CHANNEL_ID != 0 and not bot.voice_clients:
        await join_voice()

@bot.event
async def on_ready():
    print(f"LOGGED IN AS {bot.user}")
    try: await bot.tree.sync()
    except Exception as e: print(e)
    await join_voice()
    if not keep_voice_alive.is_running(): keep_voice_alive.start()

@bot.event
async def on_voice_state_update(member, before, after):
    # Kalo Pegasus ke-kick dari voice, masuk lagi
    if member.id == bot.user.id and before.channel and not after.channel:
        await asyncio.sleep(2); await join_voice()
        
#------ /HELP ---
@bot.tree.command(name="help", description="How to use Pegasus")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(HELP_MESSAGE)

# --- /SCRIPT - CARI DI SCRIPTBLOX ---
@bot.tree.command(name="script", description="Search scripts on ScriptBlox")
async def script_cmd(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    try:
        query = urllib.parse.quote(name)
        url = f"https://scriptblox.com/api/script/search?q={query}&mode=free"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        results = data.get("result", {}).get("scripts", [])[:5]
        if not results:
            await interaction.followup.send(f"No scripts found for **{name}**.")
            return
        msg = f"**🔎 Top results for `{name}` from ScriptBlox:**\n\n"
        for s in results:
            msg += f"**• {s.get('title','No Title')}** - {s.get('game',{}).get('name','Unknown')}\nhttps://scriptblox.com/script/{s.get('slug','')}\n\n"
        await interaction.followup.send(msg)
    except Exception as e:
        print(e); await interaction.followup.send("ScriptBlox is busy, try again!")

# --- KIRIM PESAN SENDIRI LEWAT DM - TANPA TAG, TANPA / ---
@bot.event
async def on_message(message):
    # Biar slash command tetep jalan
    await bot.process_commands(message)
    # Cuma jalan kalo di DM, dan cuma dari lu
    if message.guild is not None: return
    if message.author.id != OWNER_ID: return
    if message.author.bot: return

    content = message.content.strip()

    # Cara 1: Kirim preset -> DM: preset update_blox
    if content.startswith("preset "):
        key = content.split(" ", 1)[1].strip()
        if key in PRESET_MESSAGES and UPDATE_CHANNEL_ID != 0:
            ch = bot.get_channel(UPDATE_CHANNEL_ID)
            if ch:
                await ch.send(PRESET_MESSAGES[key])
                await message.reply(f"Sent preset `{key}` ✅")
            else:
                await message.reply("Update channel not found. Check UPDATE_CHANNEL_ID")
        else:
            await message.reply(f"Preset `{key}` not found. Available: {', '.join(PRESET_MESSAGES.keys())}")
        return

    # Cara 2: Kirim bebas -> DM: send #announcements Halo update baru
    if content.startswith("send "):
        try:
            rest = content[5:].strip()
            channel_part, msg_text = rest.split(" ", 1)
            channel_id = int(channel_part.replace("<#", "").replace(">", "").replace("#", ""))
            ch = bot.get_channel(channel_id)
            if ch:
                await ch.send(msg_text)
                await message.reply(f"Sent to {ch.mention} ✅")
            else:
                await message.reply("Channel not found.")
        except:
            await message.reply("Format: send #channel your message")
        return

    await message.reply("DM Commands:\n`preset update_blox` - Send preset update\n`send #channel your message` - Send custom message")

bot.run(os.getenv("DISCORD_TOKEN"))
