import os
import threading
import telebot
import yt_dlp
import re 
from flask import Flask

# 1. KONFIGURASI TOKEN BOT TELEGRAM
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8891518666:AAEcdMeyG9WErqueEBtHuY-JKQmUwSB6NzY')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error: File dashboard tidak ditemukan. Pastikan nama file adalah 'dashboard.html'."

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 3. LOGIKA BOT PENGUNDUH DENGAN INJEKSI COOKIES
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Halo! Bot Pengunduh Universal siap.\n"
        "Kirimkan link video apa saja. Saya sudah dilengkapi dengan by-pass keamanan "
        "untuk menangani video YouTube yang dibatasi!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if urls:
        target_url = urls[0] 
        processing_msg = bot.reply_to(message, "⏳ Mesin sedang menganalisis link dan melakukan autentikasi...")
        
        try:
            ydl_opts = {
                'outtmpl': 'video_%(id)s.%(ext)s',
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'max_filesize': 50000000, 
                'quiet': True,
                'nocheckcertificate': True,
                'no_warnings': True,
                'noplaylist': True, 
            }
            
            # FITUR BARU: Memeriksa apakah file cookies.txt ada di dalam folder server
            # Jika ada, beritahu yt-dlp untuk menggunakan file tersebut saat membuka YouTube
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=True)
                filename = ydl.prepare_filename(info)
                video_title = info.get('title', 'Video tanpa judul')
            
            with open(filename, 'rb') as video:
                bot.send_video(
                    message.chat.id, 
                    video, 
                    reply_to_message_id=message.message_id, 
                    caption=f"✅ <b>{video_title}</b>\nBerhasil diunduh melewati keamanan server!",
                    parse_mode='HTML' 
                )
            
            os.remove(filename)
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
        except yt_dlp.utils.DownloadError as e:
            bot.edit_message_text(f"❌ Gagal mengunduh.\nKemungkinan: Video > 50MB, diprivasi, atau cookies kedaluwarsa.\nDetail: {str(e)[:50]}...", message.chat.id, processing_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Terjadi kesalahan sistem: {str(e)[:50]}", message.chat.id, processing_msg.message_id)
            
    else:
        bot.reply_to(message, "⚠️ Silakan kirim pesan yang berisi tautan URL.")

# 4. EKSEKUSI PROGRAM
if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("Sistem berjalan dengan dukungan Cookies...")
    bot.infinity_polling()
