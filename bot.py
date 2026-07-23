import discord
from discord.ext import commands
import asyncio
import os
import random
import subprocess
import shutil
import urllib.request
from flask import Flask
from threading import Thread
import logging

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------- FLASK --------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Kross Radio - Aktif"

def run_flask():
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"Flask başlatılamadı: {e}")

# -------------------- DISCORD BOT --------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# -------------------- FFMPEG KONTROL --------------------
def ffmpeg_kontrol():
    """FFmpeg kurulu mu kontrol et"""
    return shutil.which("ffmpeg") is not None

# -------------------- RADYO LİSTESİ --------------------
RADYOLAR = {
    # 🇹🇷 TÜRK RADYOLARI
    "powerturk": {"isim": "🇹🇷 Power Türk", "url": "https://listen.powerapp.com.tr/powerturk/mpeg/icecast.audio"},
    "powerfm": {"isim": "🎵 Power FM", "url": "https://listen.powerapp.com.tr/powerfm/mpeg/icecast.audio"},
    "powerpop": {"isim": "🎶 Power Pop", "url": "https://listen.powerapp.com.tr/powerpop/mpeg/icecast.audio"},
    "powergold": {"isim": "✨ Power Gold", "url": "https://listen.powerapp.com.tr/powergold/mpeg/icecast.audio"},
    "powerdans": {"isim": "💃 Power Dance", "url": "https://listen.powerapp.com.tr/powerdance/mpeg/icecast.audio"},
    "powerviva": {"isim": "💜 Power Viva", "url": "https://listen.powerapp.com.tr/powerviva/mpeg/icecast.audio"},
    "kralpop": {"isim": "🎤 Kral Pop", "url": "https://dygedge6.radyotvonline.net/kralpop"},
    "kralfm": {"isim": "👑 Kral FM", "url": "https://dygedge6.radyotvonline.net/kralfm"},
    "superfm": {"isim": "📻 Süper FM", "url": "https://dygedge6.radyotvonline.net/superfm"},
    "metrofm": {"isim": "🌆 Metro FM", "url": "https://dygedge6.radyotvonline.net/metrofm"},
    "joyfm": {"isim": "😊 Joy FM", "url": "https://dygedge6.radyotvonline.net/joyfm"},
    "joyturk": {"isim": "🎶 Joy Türk", "url": "https://dygedge6.radyotvonline.net/joyturk"},
    "radyod": {"isim": "🎧 Radyo D", "url": "https://dygedge6.radyotvonline.net/radyod"},
    "fenomen": {"isim": "⭐ Fenomen", "url": "https://dygedge6.radyotvonline.net/fenomen"},
    "slowturk": {"isim": "💙 Slow Türk", "url": "https://dygedge6.radyotvonline.net/slowturk"},
    "bestfm": {"isim": "🏆 Best FM", "url": "https://dygedge6.radyotvonline.net/bestfm"},
    "alembifm": {"isim": "🎻 Alem FM", "url": "https://dygedge6.radyotvonline.net/alembifm"},
    "showradyo": {"isim": "🎭 Show Radyo", "url": "https://dygedge6.radyotvonline.net/showradyo"},
    "radyovoyage": {"isim": "✈️ Radyo Voyage", "url": "https://dygedge6.radyotvonline.net/radyovoyage"},
    "radyomood": {"isim": "🌙 Radyo Mood", "url": "https://dygedge6.radyotvonline.net/radyomood"},
    "radyomydonose": {"isim": "🎼 Radyo Mydonose", "url": "https://dygedge6.radyotvonline.net/radyomydonose"},
    "radyoturkuvaz": {"isim": "🎵 Turkuvaz Radyo", "url": "https://dygedge6.radyotvonline.net/turkuvaz"},
    "radyoseymen": {"isim": "🏹 Radyo Seymen", "url": "https://dygedge6.radyotvonline.net/radyoseymen"},
    "radyomega": {"isim": "📡 Radyo Mega", "url": "https://dygedge6.radyotvonline.net/radyomega"},
    
    # 🌍 DÜNYA RADYOLARI
    "bbc": {"isim": "🇬🇧 BBC World Service", "url": "https://stream.live.vc.bbcmedia.co.uk/bbc_world_service"},
    "bbcradio1": {"isim": "🇬🇧 BBC Radio 1", "url": "https://stream.live.vc.bbcmedia.co.uk/bbc_radio_one"},
    "bbcradio2": {"isim": "🇬🇧 BBC Radio 2", "url": "https://stream.live.vc.bbcmedia.co.uk/bbc_radio_two"},
    "jazz": {"isim": "🎷 Jazz Radio", "url": "https://jazzradio.ice.infomaniak.ch/jazzradio-high.mp3"},
    "classical": {"isim": "🎻 Classical Radio", "url": "https://stream.classicalradio.com/classical"},
    "rock": {"isim": "🎸 Rock Radio", "url": "https://stream.rockradio.com/rock"},
    "lofi": {"isim": "🌧️ Lo-fi Hip Hop", "url": "https://stream.lofi.radio/lofi"},
    "chill": {"isim": "🏖️ Chillhop Radio", "url": "https://stream.chillhop.com/radio"},
    "deephouse": {"isim": "🏠 Deep House Radio", "url": "https://stream.deephouse.com/deephouse"},
    "nrjhit": {"isim": "🇫🇷 NRJ Hits", "url": "https://scdn.nrjaudio.fm/fr/30001/mp3_128.mp3"},
    "nrjdance": {"isim": "🇫🇷 NRJ Dance", "url": "https://scdn.nrjaudio.fm/fr/30015/mp3_128.mp3"},
    "capitalfm": {"isim": "🇬🇧 Capital FM", "url": "https://media-ice.musicradio.com/CapitalUK"},
    "heartfm": {"isim": "❤️ Heart FM", "url": "https://media-ice.musicradio.com/HeartUK"},
    "smoothfm": {"isim": "🎷 Smooth Radio", "url": "https://media-ice.musicradio.com/SmoothUK"},
    
    # 🎮 OYUN & CHILL
    "rainwave": {"isim": "🎮 Rainwave (Game)", "url": "https://rainwave.cc/streams/all.mp3"},
    "ambient": {"isim": "🌌 Ambient Radio", "url": "https://stream.ambientradio.org/ambient"},
}

# Sunucu bazlı veri depolama
sunucu_verileri = {}

def sunucu_verisi_al(guild_id):
    if guild_id not in sunucu_verileri:
        sunucu_verileri[guild_id] = {"volume": 0.5, "current_radio": None}
    return sunucu_verileri[guild_id]

# -------------------- SES KONTROL BUTONLARI --------------------
class SesKontrolView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    
    @discord.ui.button(label="🔊 +10", style=discord.ButtonStyle.green, row=0)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            veri = sunucu_verisi_al(interaction.guild.id)
            yeni = min(200, int(veri["volume"] * 100) + 10)
            veri["volume"] = yeni / 100
            vc.source.volume = veri["volume"]
            await interaction.response.edit_message(content=f"🔊 **%{yeni}**", view=self)
        else:
            await interaction.response.edit_message(content="❌ Radyo çalmıyor!", view=self)
    
    @discord.ui.button(label="🔉 -10", style=discord.ButtonStyle.red, row=0)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            veri = sunucu_verisi_al(interaction.guild.id)
            yeni = max(0, int(veri["volume"] * 100) - 10)
            veri["volume"] = yeni / 100
            vc.source.volume = veri["volume"]
            await interaction.response.edit_message(content=f"🔉 **%{yeni}**", view=self)
        else:
            await interaction.response.edit_message(content="❌ Radyo çalmıyor!", view=self)
    
    @discord.ui.button(label="🔇 Sustur", style=discord.ButtonStyle.gray, row=1)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vc.source.volume = 0
            await interaction.response.edit_message(content="🔇 **Susturuldu**", view=self)
    
    @discord.ui.button(label="🔈 Aç", style=discord.ButtonStyle.blurple, row=1)
    async def unmute(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source:
            veri = sunucu_verisi_al(interaction.guild.id)
            vc.source.volume = veri["volume"]
            await interaction.response.edit_message(content=f"🔈 Ses açıldı: **%{int(veri['volume']*100)}**", view=self)

# -------------------- ANA FONKSİYONLAR --------------------
async def play_radio(ctx, radio_key):
    if not ffmpeg_kontrol():
        embed = discord.Embed(title="❌ FFmpeg Bulunamadı!", description="Sunucuda FFmpeg kurulu değil.\nLütfen sunucu sahibiyle iletişime geçin.", color=0xFF0000)
        return await ctx.send(embed=embed)
    
    if not ctx.voice_client:
        return await ctx.send("❌ Önce `!gir` ile ses kanalına katıl!")
    
    if radio_key not in RADYOLAR:
        en_yakin = []
        for key in RADYOLAR:
            if key.startswith(radio_key[:3]):
                en_yakin.append(key)
        if en_yakin:
            oneriler = "\n".join([f"`!radyo {k}` - {RADYOLAR[k]['isim']}" for k in en_yakin[:5]])
            return await ctx.send(f"❌ Radyo bulunamadı!\n\n**Bunlardan birini mi demek istediniz?**\n{oneriler}\n\nTüm liste: `!radyolar`")
        return await ctx.send(f"❌ Radyo bulunamadı! `!radyolar` yazın.")
    
    radio = RADYOLAR[radio_key]
    veri = sunucu_verisi_al(ctx.guild.id)
    
    # Eski yayını güvenli durdur
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await asyncio.sleep(0.5)
    
    # Yükleniyor mesajı
    yukleniyor = await ctx.send(embed=discord.Embed(title="🔄 Bağlanıyor...", description=f"**{radio['isim']}** yükleniyor...", color=0xFFA500))
    
    try:
        source = discord.FFmpegPCMAudio(
            radio['url'],
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        )
        source = discord.PCMVolumeTransformer(source, veri["volume"])
        ctx.voice_client.play(source)
        veri["current_radio"] = radio_key
        
        embed = discord.Embed(
            title="📻 RADYO BAŞLADI!",
            description=f"**{radio['isim']}** yayında!\n🔊 Ses: **%{int(veri['volume']*100)}**",
            color=0xFF0000
        )
        embed.set_footer(text="Kross Radio • !durdur ile durdurun • Butonlarla ses kontrolü")
        await yukleniyor.edit(embed=embed, view=SesKontrolView())
        
    except Exception as e:
        await yukleniyor.edit(embed=discord.Embed(title="❌ Bağlantı Hatası!", description=f"**{radio['isim']}** şu anda çalınmıyor.\n\nHata: `{str(e)[:80]}`\n\nBaşka bir radyo deneyin: `!radyolar`", color=0xFF0000))

async def radyo_kanalina_gir(ctx):
    """Akıllı kanal seçimi"""
    radyo_kanallari = ["Radyo Odası #1", "Radyo Odası #2", "Radyo", "Müzik", "🎵 Müzik Odası"]
    
    # Önce boş kanal ara
    for kanal_adi in radyo_kanallari:
        kanal = discord.utils.get(ctx.guild.voice_channels, name=kanal_adi)
        if kanal:
            non_bot = [m for m in kanal.members if not m.bot]
            if len(non_bot) == 0:
                if ctx.voice_client:
                    await ctx.voice_client.move_to(kanal)
                else:
                    await kanal.connect()
                await ctx.send(f"🔊 **{kanal.name}** kanalına katıldım!")
                return True
    
    # Dolu kanala katıl
    for kanal_adi in radyo_kanallari:
        kanal = discord.utils.get(ctx.guild.voice_channels, name=kanal_adi)
        if kanal:
            if ctx.voice_client:
                await ctx.voice_client.move_to(kanal)
            else:
                await kanal.connect()
            await ctx.send(f"🔊 **{kanal.name}** kanalına katıldım!")
            return True
    
    # Kullanıcının kanalına katıl
    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()
        await ctx.send(f"🔊 **{ctx.author.voice.channel.name}** kanalına katıldım!")
        return True
    
    await ctx.send("❌ Katılacak kanal bulunamadı!")
    return False

# -------------------- KOMUTLAR --------------------
@bot.command(name='gir', aliases=['join', 'katil'])
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Önce bir ses kanalına katıl!")
    await radyo_kanalina_gir(ctx)

@bot.command(name='cik', aliases=['leave', 'ayril'])
async def leave(ctx):
    if ctx.voice_client:
        veri = sunucu_verisi_al(ctx.guild.id)
        veri["current_radio"] = None
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Radyodan ayrıldım!")
    else:
        await ctx.send("❌ Zaten bir kanalda değilim!")

@bot.command(name='radyolar', aliases=['list', 'liste'])
async def radyo_list(ctx):
    embed = discord.Embed(
        title="📻 KROSS RADYO LİSTESİ",
        description=f"Toplam **{len(RADYOLAR)}** radyo kanalı",
        color=0xFF0000
    )
    
    turk_keys = ["powerturk", "powerfm", "powerpop", "powergold", "powerdans", "powerviva",
                 "kralpop", "kralfm", "superfm", "metrofm", "joyfm", "joyturk", "radyod",
                 "fenomen", "slowturk", "bestfm", "alembifm", "showradyo", "radyovoyage",
                 "radyomood", "radyomydonose", "radyoturkuvaz", "radyoseymen", "radyomega"]
    
    dunya_keys = ["bbc", "bbcradio1", "bbcradio2", "jazz", "classical", "rock", "lofi",
                  "chill", "deephouse", "nrjhit", "nrjdance", "capitalfm", "heartfm", "smoothfm"]
    
    oyun_keys = ["rainwave", "ambient"]
    
    turk = ""
    for key in turk_keys:
        if key in RADYOLAR:
            turk += f"`!radyo {key}` - {RADYOLAR[key]['isim']}\n"
    
    dunya = ""
    for key in dunya_keys:
        if key in RADYOLAR:
            dunya += f"`!radyo {key}` - {RADYOLAR[key]['isim']}\n"
    
    oyun = ""
    for key in oyun_keys:
        if key in RADYOLAR:
            oyun += f"`!radyo {key}` - {RADYOLAR[key]['isim']}\n"
    
    if turk: embed.add_field(name="🇹🇷 Türk Radyolar", value=turk, inline=False)
    if dunya: embed.add_field(name="🌍 Dünya Radyoları", value=dunya, inline=False)
    if oyun: embed.add_field(name="🎮 Oyun & Chill", value=oyun, inline=False)
    
    embed.set_footer(text="Kross Radio • !radyo <isim> ile dinle")
    await ctx.send(embed=embed)

@bot.command(name='radyo', aliases=['radyodinle', 'play'])
async def radyo_dinle(ctx, *, radyo_adi: str = None):
    if not radyo_adi:
        return await ctx.send("❌ Kullanım: `!radyo <isim>`\nÖrnek: `!radyo powerturk`\nTüm liste: `!radyolar`")
    radyo_adi = radyo_adi.lower().replace(" ", "")
    await play_radio(ctx, radyo_adi)

@bot.command(name='durdur', aliases=['stop', 'pause'])
async def stop_radio(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏸️ Radyo durduruldu!")
    else:
        await ctx.send("❌ Şu anda radyo çalmıyor!")

@bot.command(name='devam', aliases=['resume'])
async def resume_radio(ctx):
    veri = sunucu_verisi_al(ctx.guild.id)
    if veri["current_radio"]:
        await play_radio(ctx, veri["current_radio"])
    else:
        await ctx.send("❌ Önce bir radyo başlatın! `!radyo powerturk`")

@bot.command(name='ses', aliases=['v', 'volume'])
async def volume(ctx, vol: int = None):
    veri = sunucu_verisi_al(ctx.guild.id)
    
    if vol is None:
        embed = discord.Embed(
            title="🔊 Ses Kontrolü",
            description=f"Şu anki ses: **%{int(veri['volume']*100)}**\n\nAyarlamak için: `!ses <0-200>`",
            color=0xFF0000
        )
        return await ctx.send(embed=embed, view=SesKontrolView())
    
    if 0 <= vol <= 200:
        veri["volume"] = vol / 100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = veri["volume"]
        await ctx.send(f"🔊 Ses **%{vol}** olarak ayarlandı!")
    else:
        await ctx.send("❌ 0-200 arası bir değer girin!")

@bot.command(name='yardim', aliases=['h', 'help'])
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📻 KROSS RADIO BOT",
        description="24/7 Radyo Keyfi!",
        color=0xFF0000
    )
    embed.add_field(
        name="🎵 Dinleme Komutları",
        value="`!radyolar` - Tüm radyo listesi\n`!radyo <isim>` - Radyo dinle\n`!gir` - Ses kanalına katıl\n`!cik` - Kanaldan ayrıl",
        inline=False
    )
    embed.add_field(
        name="🎛️ Kontrol Komutları",
        value="`!durdur` - Radyoyu durdur\n`!devam` - Kaldığın yerden devam\n`!ses <0-200>` - Ses ayarla\n`!ses` - Ses panelini aç",
        inline=False
    )
    embed.add_field(
        name="🇹🇷 Hızlı Başlat",
        value="`!radyo powerturk` - Power Türk\n`!radyo kralpop` - Kral Pop\n`!radyo slowturk` - Slow Türk\n`!radyo joyturk` - Joy Türk\n`!radyo superfm` - Süper FM",
        inline=False
    )
    embed.add_field(
        name="🌍 Dünya Radyoları",
        value="`!radyo bbc` - BBC World\n`!radyo jazz` - Jazz Radio\n`!radyo lofi` - Lo-fi Hip Hop\n`!radyo classical` - Classical",
        inline=False
    )
    embed.set_footer(text="Kross Radio • 2026 • Ses butonlarıyla kolay kontrol!")
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f"🏓 **{round(bot.latency * 1000)}ms**")

# -------------------- EVENTS --------------------
@bot.event
async def on_ready():
    logger.info(f"📻 {bot.user} yayında!")
    logger.info(f"🔧 FFmpeg: {'✅ Var' if ffmpeg_kontrol() else '❌ YOK!'}")
    
    # URL'leri kontrol et
    calismayan = []
    for key, radio in RADYOLAR.items():
        try:
            req = urllib.request.Request(radio['url'], method='HEAD')
            urllib.request.urlopen(req, timeout=3)
        except:
            calismayan.append(radio['isim'])
    
    aktif = len(RADYOLAR) - len(calismayan)
    logger.info(f"📡 {aktif}/{len(RADYOLAR)} radyo aktif")
    
    if calismayan:
        logger.warning(f"⚠️ Kapalı radyolar: {', '.join(calismayan)}")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"!yardim | {len(RADYOLAR)} radyo"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Eksik kullanım! `!yardim` yazın.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Geçersiz değer!")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Biraz bekleyin! {error.retry_after:.1f}s")
    else:
        logger.error(f"Komut hatası: {error}")
        await ctx.send(f"❌ Bir hata oluştu: `{str(error)[:60]}`")

@bot.event
async def on_voice_state_update(member, before, after):
    """Bot'un bulunduğu kanal boşalırsa 5 dakika sonra otomatik çık"""
    if not before.channel:
        return
    
    guild = before.channel.guild
    
    # Bot'un bağlı olduğu kanal kontrolü
    if guild.voice_client and guild.voice_client.channel == before.channel:
        non_bot = [m for m in before.channel.members if not m.bot]
        if len(non_bot) == 0:
            await asyncio.sleep(300)  # 5 dakika bekle
            # Tekrar kontrol et
            if guild.voice_client and guild.voice_client.channel:
                current_non_bot = [m for m in guild.voice_client.channel.members if not m.bot]
                if len(current_non_bot) == 0:
                    if guild.voice_client.is_playing():
                        guild.voice_client.stop()
                    veri = sunucu_verisi_al(guild.id)
                    veri["current_radio"] = None
                    await guild.voice_client.disconnect()
                    logger.info(f"👋 Boş kanaldan otomatik ayrıldım: {guild.name}")

# -------------------- BAŞLAT --------------------
if __name__ == "__main__":
    # Flask'ı daemon olarak başlat
    Thread(target=run_flask, daemon=True).start()
    
    TOKEN = os.environ.get('DISCORD_TOKEN')
    
    if not TOKEN:
        logger.error("❌ DISCORD_TOKEN bulunamadı!")
        logger.error("Environment Variables'a DISCORD_TOKEN ekleyin.")
        exit(1)
    
    logger.info("📻 Kross Radio başlatılıyor...")
    logger.info("=" * 40)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Geçersiz token!")
    except Exception as e:
        logger.error(f"❌ Bot başlatılamadı: {e}")
