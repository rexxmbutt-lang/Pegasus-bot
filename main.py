import discord
from discord.ext import commands, tasks
import os
import json
import urllib.request
import urllib.parse
import asyncio
import io
import datetime

# ======================================================
# === YOUR SETTINGS - EDIT HERE ONLY ===
# ======================================================

# 1. ID LU - Buat DM system, biar cuma lu yang bisa kirim pesan lewat DM
# Cara dapet: Pencet lama profil lu -> Copy User ID
OWNER_ID = 1437432905734291618

# 2. ID CHANNEL VOICE YANG MAU DIJAGA
VOICE_CHANNEL_ID = 1570742871374569562

# 3. ID CHANNEL BUAT INFO UPDATE SCRIPT (default kalo lu pake preset)
UPDATE_CHANNEL_ID = 1570412727019638876

# 4. PESAN PRESET LU - SETTING DI SINI
# Kalo mau nambah, tinggal copy format di bawah
PRESET_MESSAGES = {
    "update_VD": "@everyone\n **VIOLENCE DISTRICT SCRIPT UPDATE**\nNew version is now live!\nGet it with /script violence district",
    "update_universal": "@everyone\n **UNIVERSAL SCRIPT UPDATE**\nNew version is now live!\nGet it with /script universal",
    "maintenance": "@everyone\n```VD SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "update_opah": "@everyone\n **MALAM SAMA OPAH SCRIPT UPDATE**\nNew version is now live!\nGet it now!",
    "maintenance_2": "@everyone\n```UNIVERSAL SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "maintenance_3": "@everyone\n```MALAM SAMA OPAH SCRIPT HAS MAINTENANCE, SCRIPT IN MODE MAINTENANCE OR UPDATING. PLEASE WAIT IN UNTIL TOMORROW```",
    "changelog_VD": "@everyone\n ```CHANGELOG - VIOLENCE DISTRICT\n✅ Added: Auto Farm, ESP\n❌ Removed: Old Aimbot\n🔧 Fixed: Bug teleport```",
    "changelog_universal": "@everyone\n ```CHANGELOG - UNIVERSAL SCRIPT\n✅ Added: New fly\n❌ Removed: Old Fly\n🔧 Fixed: slider```",
    "changelog_opah": "@everyone\n ```CHANGELOG - MALAM SAMA OPAH\n✅ Added: Auto Collect\n❌ Removed: - \n🔧 Fixed: Lag fix```",
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
_voice_lock = asyncio.Lock()

async def join_voice():
    async with _voice_lock:
        print(f"DEBUG JOIN ID={VOICE_CHANNEL_ID}")
        try:
            if VOICE_CHANNEL_ID == 0:
                return
                if bot.voice_clients:
                    vc = bot.voice_clients[0]
                    if vc.is_connected():
                       print("DEBUG UDAH CONNECT, SKIP")
                       return
                   await vc.disconnect(force=True)
                
            channel = bot.get_channel(VOICE_CHANNEL_ID)
            if not channel:
                channel = await bot.fetch_channel(VOICE_CHANNEL_ID)
            await channel.connect(self_deaf=True, self_mute=True)
            print("DEBUG BERHASIL CONNECT!")
        except Exception as e:
            print(f"DEBUG JOIN ERROR: {e}")
        
@tasks.loop(seconds=60)
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

# ======================================================
# === /SCRIPT - INI DOANG YANG DIGANTI, DITAMBAH LOGO ===
# ======================================================

def get_roblox_icon(game_dict):
    if not isinstance(game_dict, dict): return ""
    gid = game_dict.get("gameId") or game_dict.get("placeId") or game_dict.get("universeId") or game_dict.get("id")
    if not gid: return ""
    try:
        url = f"https://thumbnails.roblox.com/v1/games/icons?universeIds={gid}&size=512x512&format=Png&isCircular=false"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode())
            items = d.get("data", [])
            if items and items[0].get("imageUrl"): return items[0]["imageUrl"]
    except: return ""
    return ""

def format_num(n):
    try:
        n = int(n)
        if n >= 1000000: return f"{n/1000000:.1f}M".replace(".0M", "M")
        if n >= 1000: return f"{n/1000:.1f}K".replace(".0K", "K")
        return str(n)
    except: return "0"

def time_ago(date_str):
    if not date_str: return "?"
    try:
        dt = datetime.datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - dt
        if delta.days >= 365: return f"{delta.days//365} year ago" if delta.days//365 == 1 else f"{delta.days//365} years ago"
        if delta.days >= 30: return f"{delta.days//30} month ago" if delta.days//30 == 1 else f"{delta.days//30} months ago"
        if delta.days >= 1: return f"{delta.days} day ago" if delta.days == 1 else f"{delta.days} days ago"
        if delta.seconds >= 3600:
            h = delta.seconds//3600
            return f"{h} hour ago" if h == 1 else f"{h} hours ago"
        return "just now"
    except: return "?"

def get_script_code(s): return s.get("script") or s.get("code") or ""
def get_game_name(s):
    g = s.get("game") or {}
    if isinstance(g, dict): return g.get("name") or "Universal"
    return str(g) if g else "Universal"

def get_game_image(s):
    g = s.get("game") or {}
    # 1. Coba gambar dari ScriptBlox dulu
    if isinstance(g, dict):
        for k in ["imageUrl", "image", "icon", "thumbnail"]:
            v = g.get(k)
            if v and isinstance(v, str) and v.startswith("http"): return v
            if v and isinstance(v, str) and v.startswith("/"): return "https://scriptblox.com" + v
    # 2. Coba gambar dari script-nya
    for k in ["image", "imageUrl", "thumbnail"]:
        v = s.get(k)
        if v and isinstance(v, str) and v.startswith("http"): return v
        if v and isinstance(v, str) and v.startswith("/"): return "https://scriptblox.com" + v
    # 3. Kalo ga ada, ambil logo dari Roblox pake gameId
    return get_roblox_icon(g)

def extract_scripts(data):
    if isinstance(data, str):
        try: data = json.loads(data)
        except: return []
    if not isinstance(data, dict): return []
    r = data.get("result")
    if isinstance(r, dict) and isinstance(r.get("scripts"), list): return r["scripts"]
    if isinstance(r, list): return r
    if isinstance(data.get("scripts"), list): return data["scripts"]
    return []

def fetch_json(url):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://scriptblox.com/"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode(errors="ignore"))

def search_scriptblox(query_text):
    q = query_text.strip()
    queries = [q]
    low = q.lower()
    if "block fruit" in low: queries.append(low.replace("block fruit", "blox fruit"))
    if "blox fruit" in low: queries.append("blox")
    words = q.split()
    if len(words) > 1: queries.append(words[0])
    for qq in queries:
        enc = urllib.parse.quote(qq)
        target = f"https://scriptblox.com/api/script/search?q={enc}&mode=free&page=1"
        for url in [target, f"https://api.allorigins.win/raw?url={urllib.parse.quote(target)}"]:
            try:
                data = fetch_json(url)
                scripts = extract_scripts(data)
                if scripts: return scripts
            except: continue
    return []

def build_embed(scripts, idx, query):
    s = scripts[idx]
    title = s.get("title") or "No Title"
    prefix = "[KEYLESS]" if not s.get("key") else "[KEY]"
    if not title.startswith("["): title = f"{prefix} {title}"
    game = get_game_name(s)
    views = format_num(s.get("views") or s.get("viewCount") or 0)
    likes = format_num(s.get("likeCount") or s.get("likes") or 0)
    verified = "Verified" if s.get("verified") else "Not Verified"
    key = "Keyless" if not s.get("key") else "Key"
    created = time_ago(s.get("createdAt") or s.get("created_at"))
    code = get_script_code(s).strip()
    if not code: code = "-- No script code in API, open Game List for link"
    display_code = code if len(code) <= 900 else code[:900] + "\n-- ... (pencet Copy Script buat full)"
    embed = discord.Embed(title=title, color=0x2b2d31)
    embed.description = f"{views} Views  |  {likes} Likes  |  {verified}  |  {key}  |  {game}  |  {created}\n\n```lua\n{display_code}\n```"
    embed.set_footer(text=f"Page 1/1 | Script {idx+1}/{len(scripts)}  •  Search: {query}")
    img = get_game_image(s)
    if img: embed.set_image(url=img)
    return embed

class ScriptView(discord.ui.View):
    def __init__(self, scripts, query, owner_id):
        super().__init__(timeout=300)
        self.scripts = scripts; self.query = query; self.idx = 0; self.owner_id = owner_id
    def current(self): return self.scripts[self.idx]
    async def update_msg(self, interaction):
        embed = build_embed(self.scripts, self.idx, self.query)
        await interaction.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label="Copy Script", style=discord.ButtonStyle.secondary, row=0)
    async def copy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current(); code = get_script_code(s).strip()
        if not code:
            await interaction.response.send_message("Script code-nya kosong di API. Coba script lain.", ephemeral=True); return
        if len(code) > 1900:
            f = discord.File(io.BytesIO(code.encode()), filename=f"{s.get('slug','script')}.lua")
            await interaction.response.send_message(content=f"**{s.get('title','Script')}** - full code di file bawah:", file=f, ephemeral=True)
        else: await interaction.response.send_message(content=f"```lua\n{code}\n```", ephemeral=True)
    @discord.ui.button(label="Download Script", style=discord.ButtonStyle.secondary, row=0)
    async def download_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current(); code = get_script_code(s).strip() or "-- no code"
        f = discord.File(io.BytesIO(code.encode()), filename=f"{s.get('slug','script')}.lua")
        await interaction.response.send_message(content=f"Download: **{s.get('title','Script')}**", file=f, ephemeral=True)
    @discord.ui.button(label="Options", style=discord.ButtonStyle.secondary, row=0)
    async def options_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current()
        desc = s.get("description") or s.get("features") or "No description."
        if len(desc) > 1500: desc = desc[:1500] + "..."
        await interaction.response.send_message(f"**{s.get('title','Script')}**\nGame: **{get_game_name(s)}**\nVerified: {s.get('verified')} | Key: {s.get('key')} | Universal: {s.get('isUniversal')}\nViews: {format_num(s.get('views') or 0)} | Likes: {format_num(s.get('likeCount') or 0)}\n\n{desc}", ephemeral=True)
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.idx = (self.idx - 1) % len(self.scripts); await self.update_msg(interaction)
    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button): pass
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.idx = (self.idx + 1) % len(self.scripts); await self.update_msg(interaction)
    @discord.ui.button(label="Game List", style=discord.ButtonStyle.success, row=2)
    async def gamelist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current(); game = get_game_name(s); slug = s.get("slug") or ""
        link = f"https://scriptblox.com/script/{slug}" if slug else "https://scriptblox.com"
        await interaction.response.send_message(f"**Game:** {game}\n**Script:** {s.get('title','')}\n**Link:** {link}", ephemeral=True)

@bot.tree.command(name="script", description="Search scripts on ScriptBlox")
async def script_cmd(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    try:
        results = await asyncio.to_thread(search_scriptblox, name)
        results = results[:10]
        if not results:
            await interaction.followup.send(f"No scripts found for **{name}**.")
            return
        view = ScriptView(results, name, interaction.user.id)
        embed = build_embed(results, 0, name)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        print(f"SCRIPT CMD ERR: {e}")
        await interaction.followup.send("ScriptBlox lagi down / kena limit, tunggu 30 detik terus coba lagi!")

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
