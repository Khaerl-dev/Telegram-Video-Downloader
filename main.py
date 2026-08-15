import os
import threading
import telebot
import yt_dlp
import re # Library regex untuk mendeteksi keberadaan URL dalam teks
from flask import Flask

# 1. KONFIGURASI TOKEN BOT TELEGRAM
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8891518666:AAEcdMeyG9WErqueEBtHuY-JKQmUwSB6NzY')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. WEB SERVER BERSYARAT (MEMBACA FILE EXTERNAL)
app = Flask(__name__)

@app.route('/')
def home():
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
        return html_content
    except Exception as e:
        return f"Error: File dashboard tidak ditemukan. Pastikan nama file adalah 'dashboard.html'."

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 3. LOGIKA BOT PENGUNDUH UNIVERSAL
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Halo! Saya adalah Bot Pengunduh Universal yang menggunakan mesin yt-dlp.\n"
        "Kirimkan link video apa saja (YouTube, TikTok, Twitter/X, Instagram, Facebook, Reddit, dsb.), "
        "dan saya akan mencoba mengekstrak serta mengunduh videonya untuk Anda!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    
    # MENDETEKSI URL: Menggunakan regex untuk mencari apakah ada link di dalam pesan
    # Ini memastikan bahwa "halo bang, tolong download ini dong https://youtu.be/..." tetap terbaca linknya
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if urls:
        # Mengambil link pertama yang ditemukan dalam pesan
        target_url = urls[0] 
        processing_msg = bot.reply_to(message, "⏳ Mesin sedang menganalisis link Anda...")
        
        try:
            # KONFIGURASI KHUSUS UNTUK MENANGANI BERBAGAI PLATFORM (Termasuk batas ukuran file Telegram)
            ydl_opts = {
                'outtmpl': 'video_%(id)s.%(ext)s',
                # Prioritas: mp4 terbaik, atau fallback ke format apapun yang kualitasnya cukup namun tidak terlalu besar
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                # Telegram memiliki batas unggah maksimal 50MB per file untuk bot gratis
                # Batasan ini mencegah bot mendownload video YouTube berdurasi 3 jam yang akan gagal dikirim
                'max_filesize': 50000000, 
                'quiet': True,
                'nocheckcertificate': True,
                'no_warnings': True,
                # Mengabaikan error pada playlist dan hanya mendownload satu video saja jika linknya berupa playlist
                'noplaylist': True, 
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=True)
                filename = ydl.prepare_filename(info)
                # Menyimpan judul asli video untuk dijadikan caption di Telegram
                video_title = info.get('title', 'Video tanpa judul')
            
            with open(filename, 'rb') as video:
                bot.send_video(
                    message.chat.id, 
                    video, 
                    reply_to_message_id=message.message_id, 
                    caption=f"✅ <b>{video_title}</b>\nBerhasil diekstrak dari berbagai platform!",
                    parse_mode='HTML' # Mengaktifkan format teks tebal (bold) untuk judul
                )
            
            # Membersihkan sampah file dari server cloud
            os.remove(filename)
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
        except yt_dlp.utils.DownloadError as e:
            # Menangani error yang berasal dari yt-dlp secara spesifik (misal: video dibatasi usia, atau file lebih dari 50MB)
            bot.edit_message_text(f"❌ Gagal mengunduh.\nKemungkinan: Video lebih dari 50MB (Batas Telegram), diprivasi, atau platform tidak didukung.\nDetail: {str(e)[:50]}...", message.chat.id, processing_msg.message_id)
        except Exception as e:
            # Error sistem lainnya
            bot.edit_message_text(f"❌ Terjadi kesalahan sistem: {str(e)[:50]}", message.chat.id, processing_msg.message_id)
            
    else:
        # Jika pesan murni teks tanpa mengandung "http://" atau "https://"
        bot.reply_to(message, "⚠️ Silakan kirim pesan yang berisi tautan (link) URL yang valid.")

# 4. EKSEKUSI PROGRAM
if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("Sistem bot Universal berjalan...")
    bot.infinity_polling()
