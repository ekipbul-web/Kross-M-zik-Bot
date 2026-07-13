import discord
from discord.ext import commands
import asyncio
import os
import random
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "Kross Music - Aktif"
def run_flask(): app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

INVIDIOUS = "https://inv.nadeko.net"
queue = []
now_playing = None
volume_level = 0.5
loop_mode = False

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

def search_yt(query):
    try:
        url = f"{INVIDIOUS}/api/v1/search?q={requests.utils.quote(query)}&type=video"
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json() if r.status_code == 200 else []
    except: return []

def get_audio(video_id):
    try:
        url = f"{INVIDIOUS}/api/v1/videos/{video_id}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for fmt in r.json().get('adaptiveFormats', []):
                if 'audio' in fmt.get('type', ''): return fmt['url']
        return None
    except: return None

async def play_next(ctx):
    global now_playing, loop_mode
    if not ctx.voice_client: return
    if loop_mode and now_playing: queue.insert(0, now_playing)
    if queue:
        now_playing = queue.pop(0)
        audio = get_audio(now_playing['videoId'])
        if not audio: return await play_next(ctx)
        
        def after(e):
            if e: print(f"Hata: {e}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        source = discord.FFmpegPCMAudio(audio, before_options='-reconnect 1 -reconnect_streamed 1')
        source = discord.PCMVolumeTransformer(source, volume_level)
        ctx.voice_client.play(source, after=after)
        await ctx.send(f"🎶 **{now_playing['title']}**")
    else: now_playing = None

@bot.command(name='gir')
async def join(ctx):
    if not ctx.author.voice: return await ctx.send("❌ Ses kanalına katıl!")
    ch = ctx.author.voice.channel
    if ctx.voice_client: await ctx.voice_client.move_to(ch)
    else: await ch.connect()
    await ctx.send(f"🔊 **{ch.name}**")

@bot.command(name='cik')
async def leave(ctx):
    if ctx.voice_client:
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋")

@bot.command(name='oynat', aliases=['p'])
async def play(ctx, *, query):
    if not ctx.author.voice: return await ctx.send("❌ Ses kanalına katıl!")
    ch = ctx.author.voice.channel
    if not ctx.voice_client: await ch.connect()
    elif ctx.voice_client.channel != ch: await ctx.voice_client.move_to(ch)
    
    msg = await ctx.send("🔍 Aranıyor...")
    results = search_yt(query)
    if not results: return await msg.edit(content="❌ Bulunamadı!")
    
    v = results[0]
    track = {'title': v.get('title','?'), 'videoId': v.get('videoId',''), 'author': v.get('author','?')}
    queue.append(track)
    
    await msg.edit(content=f"✅ **{track['title']}** (#{len(queue)})")
    if not ctx.voice_client.is_playing(): await play_next(ctx)

@bot.command(name='atla', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️")

@bot.command(name='durdur')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️")

@bot.command(name='devam')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️")

@bot.command(name='ses', aliases=['v'])
async def volume(ctx, vol: int = None):
    global volume_level
    if vol is None: return await ctx.send(f"🔊 %{int(volume_level*100)}")
    if 0 <= vol <= 200:
        volume_level = vol/100
        if ctx.voice_client and ctx.voice_client.source: ctx.voice_client.source.volume = volume_level
        await ctx.send(f"🔊 %{vol}")

@bot.command(name='sira', aliases=['q'])
async def queue_list(ctx):
    if not now_playing and not queue: return await ctx.send("📋 Boş!")
    text = "📋 **Sıra:**\n"
    if now_playing: text += f"🎶 **{now_playing['title']}**\n"
    for i, t in enumerate(queue[:10], 1): text += f"#{i} **{t['title']}**\n"
    await ctx.send(text)

@bot.command(name='dongu')
async def loop(ctx):
    global loop_mode
    loop_mode = not loop_mode
    await ctx.send(f"🔁 {'AÇIK' if loop_mode else 'KAPALI'}")

@bot.command(name='stop')
async def stop(ctx):
    queue.clear()
    if ctx.voice_client: ctx.voice_client.stop()
    await ctx.send("⏹️")

@bot.command(name='yardim', aliases=['h'])
async def help_cmd(ctx):
    await ctx.send("🎵 **KROSS MUSİC**\n`!oynat` `!atla` `!durdur` `!devam` `!stop`\n`!sira` `!dongu` `!ses` `!gir` `!cik`")

@bot.event
async def on_ready():
    print(f"🎵 {bot.user} hazır!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!yardim"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return

if __name__ == "__main__":
    Thread(target=run_flask).start()
    TOKEN = os.environ.get('DISCORD_TOKEN')
    if TOKEN: bot.run(TOKEN)
