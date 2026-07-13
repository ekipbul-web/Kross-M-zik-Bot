import discord
from discord.ext import commands
import asyncio
import os
import random
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "Kross Radio - Aktif"
def run_flask(): app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

volume_level = 0.5
current_radio = None
RADYO_KANALLARI = ["Radyo Odası #1", "Radyo Odası #2"]

# -------------------- RADYO LİSTESİ --------------------
RADYOLAR = {
    "powerturk": {"isim": "🇹🇷 Power Türk", "url": "https://listen.powerapp.com.tr/powerturk/mpeg/icecast.audio"},
    "powerfm": {"isim": "🎵 Power FM", "url": "https://listen.powerapp.com.tr/powerfm/mpeg/icecast.audio"},
    "kralpop": {"isim": "🎤 Kral Pop", "url": "https://dygedge6.radyotvonline.net/kralpop"},
    "superfm": {"isim": "📻 Süper FM", "url": "https://dygedge6.radyotvonline.net/superfm"},
    "joyfm": {"isim": "😊 Joy FM", "url": "https://dygedge6.radyotvonline.net/joyfm"},
    "joyturk": {"isim": "🎶 Joy Türk", "url": "https://dygedge6.radyotvonline.net/joyturk"},
    "metrofm": {"isim": "🌆 Metro FM", "url": "https://dygedge6.radyotvonline.net/metrofm"},
    "radyod": {"isim": "🎧 Radyo D", "url": "https://dygedge6.radyotvonline.net/radyod"},
    "fenomen": {"isim": "⭐ Fenomen", "url": "https://dygedge6.radyotvonline.net/fenomen"},
    "slowturk": {"isim": "💙 Slow Türk", "url": "https://dygedge6.radyotvonline.net/slowturk"},
    "bestfm": {"isim": "🏆 Best FM", "url": "https://dygedge6.radyotvonline.net/bestfm"},
    "alembifm": {"isim": "🎻 Alem FM", "url": "https://dygedge6.radyotvonline.net/alembifm"},
    "showradyo": {"isim": "🎭 Show Radyo", "url": "https://dygedge6.radyotvonline.net/showradyo"},
    "radyovoyage": {"isim": "✈️ Radyo Voyage", "url": "https://dygedge6.radyotvonline.net/radyovoyage"},
    "bbc": {"isim": "🇬🇧 BBC World", "url": "https://stream.live.vc.bbcmedia.co.uk/bbc_world_service"},
    "jazz": {"isim": "🎷 Jazz Radio", "url": "https://jazzradio.ice.infomaniak.ch/jazzradio-high.mp3"},
    "classical": {"isim": "🎻 Classical", "url": "https://stream.classicalradio.com/classical"},
    "rock": {"isim": "🎸 Rock Radio", "url": "https://stream.rockradio.com/rock"},
    "lofi": {"isim": "🌧️ Lo-fi Hip Hop", "url": "https://stream.lofi.radio/lofi"},
    "chill": {"isim": "🏖️ Chill Radio", "url": "https://stream.chillradio.com/chill"},
    "deephouse": {"isim": "🏠 Deep House", "url": "https://stream.deephouse.com/deephouse"},
}

async def play_radio(ctx, radio_key):
    global current_radio
    
    if not ctx.voice_client:
        return await ctx.send("❌ Önce `!gir` ile ses kanalına katıl!")
    
    if radio_key not in RADYOLAR:
        return await ctx.send("❌ Radyo bulunamadı! `!radyolar` yaz.")
    
    radio = RADYOLAR[radio_key]
    
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    
    try:
        source = discord.FFmpegPCMAudio(radio['url'], before_options='-reconnect 1 -reconnect_streamed 1')
        source = discord.PCMVolumeTransformer(source, volume_level)
        ctx.voice_client.play(source)
        current_radio = radio_key
        
        embed = discord.Embed(title="📻 RADYO BAŞLADI!", description=f"**{radio['isim']}** yayında!", color=0xFF0000)
        embed.set_footer(text="Kross Radio • !durdur ile durdurabilirsin")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Yayın başlatılamadı: {str(e)[:80]}")

async def radyo_kanalina_gir(ctx):
    """Radyo Odası #1 veya #2'ye katıl"""
    
    # Müsait kanalı bul
    for kanal_adi in RADYO_KANALLARI:
        kanal = discord.utils.get(ctx.guild.voice_channels, name=kanal_adi)
        if kanal:
            # Kanalda bot dışında kimse yoksa veya kanal boşsa
            if len([m for m in kanal.members if not m.bot]) == 0:
                if ctx.voice_client:
                    await ctx.voice_client.move_to(kanal)
                else:
                    await kanal.connect()
                await ctx.send(f"🔊 **{kanal.name}** kanalına katıldım!")
                return True
    
    # Hepsi doluysa rastgele birine katıl
    for kanal_adi in RADYO_KANALLARI:
        kanal = discord.utils.get(ctx.guild.voice_channels, name=kanal_adi)
        if kanal:
            if ctx.voice_client:
                await ctx.voice_client.move_to(kanal)
            else:
                await kanal.connect()
            await ctx.send(f"🔊 **{kanal.name}** kanalına katıldım!")
            return True
    
    await ctx.send("❌ Radyo Odası bulunamadı! `Radyo Odası #1` veya `Radyo Odası #2` oluşturun.")
    return False

@bot.command(name='gir')
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Önce bir ses kanalına katıl!")
    await radyo_kanalina_gir(ctx)

@bot.command(name='cik')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Radyodan ayrıldım!")

@bot.command(name='radyolar')
async def radyo_list(ctx):
    embed = discord.Embed(title="📻 KROSS RADYO LİSTESİ", color=0xFF0000)
    
    turk = ""
    dunya = ""
    
    turk_keys = ["powerturk", "powerfm", "kralpop", "superfm", "joyfm", "joyturk", "metrofm", "radyod", "fenomen", "slowturk", "bestfm", "alembifm", "showradyo", "radyovoyage"]
    
    for key in turk_keys:
        if key in RADYOLAR:
            turk += f"`!radyo {key}` - {RADYOLAR[key]['isim']}\n"
    
    for key in RADYOLAR:
        if key not in turk_keys:
            dunya += f"`!radyo {key}` - {RADYOLAR[key]['isim']}\n"
    
    if turk: embed.add_field(name="🇹🇷 Türk Radyolar", value=turk, inline=False)
    if dunya: embed.add_field(name="🌍 Dünya Radyoları", value=dunya, inline=False)
    embed.set_footer(text="Kross Radio • !radyo <isim> ile dinle")
    await ctx.send(embed=embed)

@bot.command(name='radyo', aliases=['radyodinle'])
async def radyo_dinle(ctx, *, radyo_adi: str):
    radyo_adi = radyo_adi.lower().replace(" ", "")
    await play_radio(ctx, radyo_adi)

@bot.command(name='durdur')
async def stop_radio(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏸️ Radyo durduruldu!")

@bot.command(name='devam')
async def resume_radio(ctx):
    if current_radio:
        await play_radio(ctx, current_radio)

@bot.command(name='ses', aliases=['v'])
async def volume(ctx, vol: int = None):
    global volume_level
    if vol is None: return await ctx.send(f"🔊 %{int(volume_level*100)}")
    if 0 <= vol <= 200:
        volume_level = vol/100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume_level
        await ctx.send(f"🔊 %{vol}")

@bot.command(name='yardim', aliases=['h'])
async def help_cmd(ctx):
    embed = discord.Embed(title="📻 KROSS RADIO BOT", color=0xFF0000)
    embed.add_field(name="📋 Komutlar", value="`!radyolar` - Liste\n`!radyo <isim>` - Dinle\n`!gir` - Radyo Odasına katıl\n`!cik` - Çık\n`!durdur` `!devam` `!ses`", inline=False)
    embed.add_field(name="🇹🇷 Popüler", value="`!radyo powerturk` `!radyo kralpop` `!radyo slowturk` `!radyo superfm`", inline=False)
    embed.set_footer(text="Kross Radio • 2026")
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"📻 {bot.user} yayında!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!yardim | Radyo"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    await ctx.send(f"❌ {str(error)[:80]}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    TOKEN = os.environ.get('DISCORD_TOKEN')
    if TOKEN: bot.run(TOKEN)
