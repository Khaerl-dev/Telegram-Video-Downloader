import os
import threading
import telebot
import yt_dlp
from flask import Flask

# 1. KONFIGURASI TOKEN
# Bot akan mengambil token dari environment variable, atau langsung dari string di bawah ini
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'GANTI_TEKS_INI_DENGAN_TOKEN_ANDA')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. DUMMY WEB SERVER (Wajib untuk Cloud Hosting seperti Render agar tidak crash)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram Sedang Berjalan 24/7!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 3. LOGIKA BOT TELEGRAM
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "Halo! Kirimkan link video TikTok, Instagram, atau Facebook. Saya akan mengunduhnya tanpa watermark untuk Anda!"
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    supported_platforms = ['tiktok.com', 'instagram.com', 'facebook.com', 'fb.watch']
    
    if any(domain in url.lower() for domain in supported_platforms):
        processing_msg = bot.reply_to(message, "⏳ Sedang memproses... Mohon tunggu sebentar.")
        try:
            ydl_opts = {
                'outtmpl': 'video_%(id)s.%(ext)s',
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'quiet': True,
                'nocheckcertificate': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, reply_to_message_id=message.message_id, caption="✅ Berhasil diunduh!")
            os.remove(filename)
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except Exception as e:
            bot.edit_message_text("❌ Gagal mengunduh video. Pastikan akun tidak diprivasi.", message.chat.id, processing_msg.message_id)
    else:
        bot.reply_to(message, "⚠️ Kirimkan link yang valid (TikTok, Instagram, Facebook).")

# 4. MENJALANKAN BOT DAN SERVER BERSAMAAN
if __name__ == '__main__':
    # Memulai server Flask di thread latar belakang agar bot dan server berjalan beriringan
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    # Memulai Bot Telegram
    print("Bot berhasil dijalankan!")
    bot.infinity_polling()
