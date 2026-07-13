import discord
from discord.ext import commands
import asyncio
import os
import random
import re
import urllib.request
import urllib.parse
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

queue = []
now_playing = None
volume_level = 0.5
loop_mode = False

def search_youtube(query):
    """YouTube'da ara - embed API"""
    try:
        query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode()
        
        # Video ID'lerini bul
        video_ids = re.findall(r'\/watch\?v=([a-zA-Z0-9_-]{11})', html)
        video_ids = list(dict.fromkeys(video_ids))  # Tekrar edenleri kaldır
        
        results = []
        for vid in video_ids[:5]:
            results.append({
                'videoId': vid,
                'title': f'YouTube Video ({vid})',
                'url': f'https://www.youtube.com/watch?v={vid}'
            })
        return results
    except Exception as e:
        print(f"Arama hatası: {e}")
        return []

def get_direct_audio(video_id):
    """YouTube embed üzerinden direkt ses akışı al"""
    try:
        # Önce embed sayfasını al
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(embed_url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode()
        
        # Stream URL'sini bul
        match = re.search(r'"(https[^"]*googlevideo\.com[^"]*)"', html)
        if match:
            return match.group(1)
        
        # Alternatif: player response
        match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
        if match:
            import json
            data = json.loads(match.group(1))
            formats = data.get('streamingData', {}).get('adaptiveFormats', [])
            for fmt in formats:
                if 'audio' in fmt.get('mimeType', ''):
                    return fmt.get('url')
        
        return None
    except Exception as e:
        print(f"Ses alma hatası: {e}")
        return None

async def play_next(ctx):
    global now_playing, loop_mode
    if not ctx.voice_client: return
    if loop_mode and now_playing: queue.insert(0, now_playing)
    
    if queue:
        now_playing = queue.pop(0)
        
        await ctx.send(f"🔍 **{now_playing['title']}** ses alınıyor...")
        audio_url = get_direct_audio(now_playing['videoId'])
        
        if not audio_url:
            await ctx.send(f"❌ Ses alınamadı, atlanıyor...")
            return await play_next(ctx)
        
        def after_play(error):
            if error: print(f"Hata: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        try:
            source = discord.FFmpegPCMAudio(audio_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
            source = discord.PCMVolumeTransformer(source, volume_level)
            ctx.voice_client.play(source, after=after_play)
            await ctx.send(f"🎶 **{now_playing['title']}**")
        except Exception as e:
            await ctx.send(f"❌ Oynatma hatası: {e}")
            await play_next(ctx)
    else:
        now_playing = None

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
    
    msg = await ctx.send(f"🔍 **{query}** aranıyor...")
    
    results = search_youtube(query)
    if not results:
        return await msg.edit(content="❌ Bulunamadı! Farklı bir şarkı dene.")
    
    track = results[0]
    queue.append(track)
    
    await msg.edit(content=f"✅ **{track['title']}** sıraya eklendi! (#{len(queue)})")
    
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command(name='atla', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Atlandı!")
    else:
        await ctx.send("❌ Müzik çalmıyor!")

@bot.command(name='durdur')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Durduruldu!")

@bot.command(name='devam')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Devam ediyor!")

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
    if not now_playing and not queue: return await ctx.send("📋 Sıra boş!")
    text = "📋 **Şarkı Sırası:**\n"
    if now_playing: text += f"🎶 Çalıyor: **{now_playing['title']}**\n"
    for i, t in enumerate(queue[:10], 1): text += f"#{i} **{t['title']}**\n"
    await ctx.send(text)

@bot.command(name='dongu')
async def loop(ctx):
    global loop_mode
    loop_mode = not loop_mode
    await ctx.send(f"🔁 Döngü: {'**AÇIK**' if loop_mode else '**KAPALI**'}")

@bot.command(name='stop')
async def stop(ctx):
    queue.clear()
    if ctx.voice_client: ctx.voice_client.stop()
    await ctx.send("⏹️ Durduruldu!")

@bot.command(name='yardim', aliases=['h'])
async def help_cmd(ctx):
    embed = discord.Embed(title="🎵 KROSS MUSİC BOT", color=0xFF0000)
    embed.add_field(name="🎵 Müzik", value="`!oynat <şarkı>` - YouTube'da ara\n`!atla` `!durdur` `!devam` `!stop`", inline=False)
    embed.add_field(name="📋 Sıra", value="`!sira` `!dongu`", inline=False)
    embed.add_field(name="⚙️ Diğer", value="`!ses <0-200>` `!gir` `!cik` `!yardim`", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"🎵 {bot.user} hazır!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!yardim | !oynat"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    print(f"Hata: {error}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    TOKEN = os.environ.get('DISCORD_TOKEN')
    if TOKEN: bot.run(TOKEN)
