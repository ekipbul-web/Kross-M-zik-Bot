import discord
from discord.ext import commands
import asyncio
import os
import random
import requests
import json
import re
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "Kross SC - Aktif"
def run_flask(): app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

CLIENT_ID = "a3e059563d7fd3372b49b37f00a00bcf"

queue = []
now_playing = None
volume_level = 0.5
loop_mode = False

def sc_search(query, limit=5):
    """SoundCloud'da şarkı arar"""
    url = f"https://api-v2.soundcloud.com/search?q={requests.utils.quote(query)}&limit={limit}&client_id={CLIENT_ID}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        tracks = []
        for item in data.get('collection', []):
            if item.get('kind') == 'track':
                tracks.append({
                    'title': item.get('title', 'Bilinmeyen'),
                    'artist': item.get('user', {}).get('username', 'Bilinmeyen'),
                    'url': item.get('permalink_url', ''),
                    'stream_url': item.get('media', {}).get('transcodings', [{}])[0].get('url', ''),
                    'duration': item.get('duration', 0),
                    'artwork': item.get('artwork_url', ''),
                    'id': item.get('id')
                })
        return tracks
    return []

def get_stream_url(track):
    """Geçerli stream URL'si al"""
    if not track.get('stream_url'):
        return None
    
    stream_api = track['stream_url']
    if '?' in stream_api:
        stream_api += f"&client_id={CLIENT_ID}"
    else:
        stream_api += f"?client_id={CLIENT_ID}"
    
    r = requests.get(stream_api)
    if r.status_code == 200:
        return r.json().get('url')
    return None

async def play_next(ctx):
    global now_playing, loop_mode
    
    if not ctx.voice_client:
        return
    
    if loop_mode and now_playing:
        queue.insert(0, now_playing)
    
    if queue:
        now_playing = queue.pop(0)
        stream_url = get_stream_url(now_playing)
        
        if not stream_url:
            await ctx.send(f"❌ **{now_playing['title']}** çalınamadı, atlanıyor...")
            return await play_next(ctx)
        
        def after_play(error):
            if error: print(f"Hata: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        source = discord.FFmpegPCMAudio(stream_url, before_options='-reconnect 1 -reconnect_streamed 1')
        source = discord.PCMVolumeTransformer(source, volume_level)
        ctx.voice_client.play(source, after=after_play)
        
        embed = discord.Embed(title="🎶 Şimdi Çalıyor", description=f"**[{now_playing['title']}]({now_playing['url']})**", color=0xFF5500)
        embed.add_field(name="👤 Sanatçı", value=now_playing['artist'], inline=True)
        if now_playing['duration']:
            m, s = divmod(now_playing['duration'] // 1000, 60)
            embed.add_field(name="⏱️", value=f"{int(m)}:{int(s):02d}", inline=True)
        if now_playing['artwork']: embed.set_thumbnail(url=now_playing['artwork'])
        await ctx.send(embed=embed)
    else:
        now_playing = None

@bot.command(name='gir')
async def join(ctx):
    if not ctx.author.voice: return await ctx.send("❌ Ses kanalında değilsin!")
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
    if not ctx.author.voice: return await ctx.send("❌ Ses kanalında değilsin!")
    
    ch = ctx.author.voice.channel
    if not ctx.voice_client: await ch.connect()
    elif ctx.voice_client.channel != ch: await ctx.voice_client.move_to(ch)
    
    msg = await ctx.send("🔍 **SoundCloud'da aranıyor...**")
    
    tracks = sc_search(query)
    if not tracks: return await msg.edit(content="❌ **Bulunamadı!**")
    
    track = tracks[0]
    queue.append(track)
    
    embed = discord.Embed(title="🎵 Sıraya Eklendi", description=f"**[{track['title']}]({track['url']})**", color=0xFF5500)
    embed.add_field(name="👤", value=track['artist'], inline=True)
    embed.add_field(name="📋 Sıra", value=f"#{len(queue)}", inline=True)
    if track['artwork']: embed.set_thumbnail(url=track['artwork'])
    await msg.edit(content=None, embed=embed)
    
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command(name='atla', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ **Atlandı!**")

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
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume_level
        await ctx.send(f"🔊 %{vol}")

@bot.command(name='sira', aliases=['q'])
async def queue_list(ctx):
    if not now_playing and not queue: return await ctx.send("📋 Boş!")
    text = "📋 **Sıra:**\n"
    if now_playing: text += f"🎶 **{now_playing['title']}** (çalıyor)\n"
    for i, t in enumerate(queue[:10], 1): text += f"#{i} **{t['title']}** - {t['artist']}\n"
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
    await ctx.send("""
🎵 **KROSS SOUNDCLOUD BOT**
`!oynat <şarkı>` - SoundCloud'da ara/çal
`!atla` `!durdur` `!devam` `!stop`
`!sira` `!dongu` `!ses <0-200>`
`!gir` `!cik` `!yardim`
""")

@bot.event
async def on_ready():
    print(f"🎵 {bot.user} hazır!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!yardim | SoundCloud"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    await ctx.send(f"❌ {str(error)[:80]}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    TOKEN = os.environ.get('DISCORD_TOKEN')
    if TOKEN: bot.run(TOKEN)
    else: print("Token yok!")
