import os
import threading
import telebot
import yt_dlp
import re 
from flask import Flask

# 1. KONFIGURASI TOKEN BOT TELEGRAM
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8891518666:AAEcdMeyG9WErqueEBtHuY-JKQmUwSB6NzY')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. WEB SERVER BERSYARAT
app = Flask(__name__)

@app.route('/')
def home():
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return "[007]"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 3. LOGIKA BOT PENGUNDUH DENGAN FORMAT TOLERAN
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "[001]")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if urls:
        target_url = urls[0] 
        processing_msg = bot.reply_to(message, "[002]")
        
        try:
            ydl_opts = {
                'outtmpl': 'video_%(id)s.%(ext)s',
                # SOLUSI DEFINITIF ERROR FORMAT: 
                # Menggunakan rantai prioritas (fallback chain). 
                # Jika tidak ada best tunggal, ambil resolusi lebih rendah (<=720p, <=480p, dll) 
                # yang sudah berisi audio dan video dalam satu paket tanpa perlu FFmpeg.
                'format': 'best[ext=mp4]/best[height<=720]/best[height<=480]/worst', 
                'max_filesize': 50000000, 
                'quiet': True,
                'nocheckcertificate': True,
                'no_warnings': True,
                'noplaylist': True, 
            }
            
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=True)
                filename = ydl.prepare_filename(info)
                video_title = info.get('title', 'Unknown Title')
            
            with open(filename, 'rb') as video:
                bot.send_video(
                    message.chat.id, 
                    video, 
                    reply_to_message_id=message.message_id, 
                    caption=f"[003]\n<b>{video_title}</b>",
                    parse_mode='HTML' 
                )
            
            os.remove(filename)
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
        except yt_dlp.utils.DownloadError as e:
            bot.edit_message_text(f"[004]\nDetail: {str(e)}", message.chat.id, processing_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"[005]\nDetail: {str(e)}", message.chat.id, processing_msg.message_id)
            
    else:
        bot.reply_to(message, "[006]")

# 4. EKSEKUSI PROGRAM
if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("Sistem berjalan dengan Rantai Prioritas Format...")
    bot.infinity_polling()
