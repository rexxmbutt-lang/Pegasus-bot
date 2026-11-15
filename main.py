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

OWNER_ID = 1437432905734291618
VOICE_CHANNEL_ID = 1570742871374569562
UPDATE_CHANNEL_ID = 1570412727019638876

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
    if member.id == bot.user.id and before.channel and not after.channel:
        await asyncio.sleep(2); await join_voice()

#------ /HELP ---
@bot.tree.command(name="help", description="How to use Pegasus")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(HELP_MESSAGE)

# ======================================================
# === /SCRIPT - MODEL C PURE (KAYAK VIDEO) ===
# ======================================================

def format_num(n):
    try:
        n = int(n)
        if n >= 1000000:
            return f"{n/1000000:.1f}M".replace(".0M", "M")
        if n >= 1000:
            return f"{n/1000:.1f}K".replace(".0K", "K")
        return str(n)
    except:
        return "0"

def time_ago(date_str):
    if not date_str:
        return "?"
    try:
        dt = datetime.datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - dt
        if delta.days >= 365:
            return f"{delta.days//365} year ago" if delta.days//365 == 1 else f"{delta.days//365} years ago"
        if delta.days >= 30:
            return f"{delta.days//30} month ago" if delta.days//30 == 1 else f"{delta.days//30} months ago"
        if delta.days >= 1:
            return f"{delta.days} day ago" if delta.days == 1 else f"{delta.days} days ago"
        if delta.seconds >= 3600:
            h = delta.seconds//3600
            return f"{h} hour ago" if h == 1 else f"{h} hours ago"
        return "just now"
    except:
        return "?"

def get_script_code(s):
    return s.get("script") or s.get("code") or ""

def get_game_name(s):
    g = s.get("game") or {}
    if isinstance(g, dict):
        return g.get("name") or "Universal"
    return str(g) if g else "Universal"

def get_game_image(s):
    g = s.get("game") or {}
    if isinstance(g, dict):
        return g.get("imageUrl") or g.get("image") or ""
    return ""

def build_embed(scripts, idx, query):
    s = scripts[idx]
    title = s.get("title") or "No Title"
    game = get_game_name(s)
    views = format_num(s.get("views") or s.get("viewCount") or 0)
    likes = format_num(s.get("likeCount") or s.get("likes") or 0)
    verified = "Verified" if s.get("verified") else "Not Verified"
    key = "Key" if s.get("key") else "Keyless"
    universal = "Universal" if s.get("isUniversal") or game.lower() == "universal" else game
    created = time_ago(s.get("createdAt") or s.get("created_at"))
    updated = time_ago(s.get("updatedAt") or s.get("updated_at"))
    code = get_script_code(s).strip()
    if not code:
        code = "-- No script code in API, open Game List for link"
    # Potong code biar muat di embed, full-nya ada di Copy / Download
    display_code = code if len(code) <= 900 else code[:900] + "\n-- ... (pencet Copy Script buat full)"

    embed = discord.Embed(title=title, color=0x2b2d31)
    # Header kayak di video: views | likes | verified | key | universal | umur
    embed.description = f"👁 {views}  |  👍 {likes}  |  ✅ {verified}  |  🔑 {key}  |  🌐 {universal}  |  📅 {created}  |  🔄 {updated}\n\n```lua\n{display_code}\n```"
    embed.set_footer(text=f"Page 1/1 | Script {idx+1}/{len(scripts)}  •  Search: {query}")
    # Gambar: utamain image script, kalo ga ada pake image game
    img = s.get("image") or s.get("imageUrl") or get_game_image(s)
    if img:
        if img.startswith("http"):
            embed.set_image(url=img)
    return embed

class ScriptView(discord.ui.View):
    def __init__(self, scripts, query, owner_id):
        super().__init__(timeout=300)
        self.scripts = scripts
        self.query = query
        self.idx = 0
        self.owner_id = owner_id

    def current(self):
        return self.scripts[self.idx]

    async def update_msg(self, interaction):
        embed = build_embed(self.scripts, self.idx, self.query)
        await interaction.response.edit_message(embed=embed, view=self)

    # --- ROW 0: Copy / Download / Options ---
    @discord.ui.button(label="Copy Script", style=discord.ButtonStyle.secondary, emoji="📋", row=0)
    async def copy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current()
        code = get_script_code(s).strip()
        if not code:
            await interaction.response.send_message("Script code-nya kosong di API. Coba script lain.", ephemeral=True)
            return
        # Kalo kepanjangan buat 1 pesan, kirim jadi file + potongan pertama
        if len(code) > 1900:
            f = discord.File(io.BytesIO(code.encode()), filename=f"{s.get('slug','script')}.lua")
            await interaction.response.send_message(content=f"**{s.get('title','Script')}** - full code di file bawah, tinggal download & copy:", file=f, ephemeral=True)
        else:
            await interaction.response.send_message(content=f"```lua\n{code}\n```", ephemeral=True)

    @discord.ui.button(label="Download Script", style=discord.ButtonStyle.secondary, emoji="⬇️", row=0)
    async def download_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current()
        code = get_script_code(s).strip() or "-- no code"
        f = discord.File(io.BytesIO(code.encode()), filename=f"{s.get('slug','script')}.lua")
        await interaction.response.send_message(content=f"Download: **{s.get('title','Script')}**", file=f, ephemeral=True)

    @discord.ui.button(label="Options", style=discord.ButtonStyle.secondary, emoji="≡", row=0)
    async def options_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current()
        desc = s.get("description") or s.get("features") or "No description."
        if len(desc) > 1500:
            desc = desc[:1500] + "..."
        await interaction.response.send_message(
            f"**{s.get('title','Script')}**\n"
            f"Game: **{get_game_name(s)}**\n"
            f"Verified: {s.get('verified')} | Key: {s.get('key')} | Universal: {s.get('isUniversal')}\n"
            f"Views: {format_num(s.get('views') or 0)} | Likes: {format_num(s.get('likeCount') or 0)}\n\n{desc}",
            ephemeral=True
        )

    # --- ROW 1: Pagination ---
    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.idx = (self.idx - 1) % len(self.scripts)
        await self.update_msg(interaction)

    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.idx = (self.idx + 1) % len(self.scripts)
        await self.update_msg(interaction)

    # --- ROW 2: Game List doang, PURE ---
    @discord.ui.button(label="Game List", style=discord.ButtonStyle.success, emoji="✅", row=2)
    async def gamelist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self.current()
        game = get_game_name(s)
        slug = s.get("slug") or ""
        link = f"https://scriptblox.com/script/{slug}" if slug else "https://scriptblox.com"
        await interaction.response.send_message(f"**Game:** {game}\n**Script:** {s.get('title','')}\n**Link:** {link}", ephemeral=True)

@bot.tree.command(name="script", description="Search scripts on ScriptBlox")
async def script_cmd(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    try:
        query = urllib.parse.quote(name)
        url = f"https://scriptblox.com/api/script/search?q={query}&mode=free"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        results = data.get("result", {}).get("scripts", [])[:10]
        if not results:
            await interaction.followup.send(f"No scripts found for **{name}**.")
            return
        view = ScriptView(results, name, interaction.user.id)
        embed = build_embed(results, 0, name)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        print(e); await interaction.followup.send("ScriptBlox is busy, try again!")

# --- KIRIM PESAN SENDIRI LEWAT DM - TANPA TAG, TANPA / ---
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.guild is not None: return
    if message.author.id != OWNER_ID: return
    if message.author.bot: return
    content = message.content.strip()
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
