import os
from os import getenv
import sqlite3
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  # Pastikan untuk mengganti dengan nilai yang aman
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  # Pastikan untuk mengganti dengan nilai yang aman
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAF6CyhFQk8b-duLd44A67chU_cHXlX9SOQ")  # Pastikan untuk mengganti dengan nilai yang aman

# Inisialisasi bot
app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Koneksi database
conn = sqlite3.connect('anonim_chatbot.db', check_same_thread=False)
cursor = conn.cursor()

# Buat tabel jika belum ada
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    language TEXT DEFAULT 'id'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_id_2 INTEGER,
    active INTEGER DEFAULT 0
)
''')

conn.commit()

# Fungsi untuk menghentikan sesi chat
async def stop_chat_session(user_id):
    cursor.execute('''
    UPDATE chats
    SET active = 0
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    conn.commit()

# Fungsi untuk mendapatkan pesan berdasarkan bahasa
def get_message(user_id, key):
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    user_lang = cursor.fetchone()
    lang = user_lang[0] if user_lang else 'id'

    lang_file_path = os.path.join("lang", f"{lang}.json")
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        return messages.get(key, "Pesan tidak ditemukan.")
    else:
        return f"File bahasa {lang}.json tidak ditemukan."

# Handler perintah /start
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Tidak ada username"

    await stop_chat_session(user_id)

    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username)
    VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="setlang_id"),
                InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")
            ]
        ]
    )
    await message.reply_text(
        "Halo! Selamat datang di Anonim Chat Bot.\n\n"
        "Silakan pilih bahasa / Please select your language:",
        reply_markup=keyboard
    )

# Handler callback query (untuk mengubah bahasa)
@app.on_callback_query()
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data.startswith("setlang_"):
        lang = data.split("_")[1]
        cursor.execute('''
        UPDATE users
        SET language = ?
        WHERE user_id = ?
        ''', (lang, user_id))
        conn.commit()

        await callback_query.answer(f"Bahasa telah diubah ke {lang}.")
        await callback_query.message.edit_text(get_message(user_id, "start_message"))

# Handler perintah /next (mencari pasangan chat)
@app.on_message(filters.command("next"))
async def start_chat(client, message):
    user_id = message.from_user.id
    await stop_chat_session(user_id)
    cursor.execute('''
    SELECT * FROM chats
    WHERE active = 0 AND user_id != ?
    ''', (user_id,))
    available_chat = cursor.fetchone()

    if available_chat:
        chat_id = available_chat[0]
        first_user_id = available_chat[1]
        cursor.execute('''
        UPDATE chats
        SET user_id_2 = ?, active = 1
        WHERE chat_id = ?
        ''', (user_id, chat_id))
        conn.commit()

        await app.send_message(first_user_id, get_message(first_user_id, "patner_on"))
        await message.reply_text(get_message(user_id, "patner_on"))
        
        print(f"Pengguna {first_user_id} dan {user_id} telah saling bertemu.")
    else:
        cursor.execute('''
        INSERT INTO chats (user_id, active)
        VALUES (?, 0)
        ''', (user_id,))
        conn.commit()

        await message.reply_text(get_message(user_id, "next_message"))
        
# Handler untuk menerima pesan dan media
@app.on_message(
    filters.text | 
    filters.animation | 
    filters.document | 
    filters.audio |
    filters.voice |
    filters.video | 
    filters.photo | 
    filters.sticker &
    ~filters.command(["start", "next", "stop"])
)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if not active_chat:
        await message.reply_text(get_message(user_id, "no_chat_message"))
        return
        
    recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

    if recipient_id is None or recipient_id == user_id:
        await message.reply_text(get_message(user_id, "error_message"))
        return

    reply_id = message.reply_to_message.id if message.reply_to_message else None

    try:
        if message.text:
            await app.send_message(recipient_id, message.text, reply_to_message_id=reply_id)
        elif message.voice:
            await app.send_voice(recipient_id, message.voice.file_id, caption=message.caption, reply_to_message_id=reply_id)
        elif message.animation:
            await app.send_animation(recipient_id, message.animation.file_id, caption=message.caption, reply_to_message_id=reply_id)
        elif message.audio:
            await app.send_audio(recipient_id, message.audio.file_id, caption=message.caption, reply_to_message_id=reply_id)
        elif message.sticker:
            await app.send_sticker(recipient_id, message.sticker.file_id, reply_to_message_id=reply_id)
        elif message.photo:
            await app.send_photo(recipient_id, message.photo.file_id, caption=message.caption, reply_to_message_id=reply_id)
        elif message.video:
            await app.send_video(recipient_id, message.video.file_id, caption=message.caption, reply_to_message_id=reply_id)
        elif message.document:
            await app.send_document(recipient_id, message.document.file_id, caption=message.caption, reply_to_message_id=reply_id)

    except Exception as e:
        print(f"Gagal mengirim pesan/media: {e}")
        await message.reply_text(get_message(user_id, "block_message"))
        await stop_chat_session(user_id)  # Menghentikan sesi chat jika terjadi kesalahan

# Handler perintah /stop (menghentikan chat)
@app.on_message(filters.command("stop"))
async def stop_chat(client, message):
    user_id = message.from_user.id

    # Cari sesi chat aktif
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if active_chat:
        recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

        # Beri tahu pengguna bahwa sesi dihentikan
        await message.reply_text(get_message(user_id, "stop_message"))

        # Beri tahu penerima bahwa sesi dihentikan
        try:
            if recipient_id:
                await app.send_message(recipient_id, get_message(recipient_id, "partner_stop_message"))
        except Exception as e:
            print(f"Gagal mengirim pesan ke lawan bicara: {e}")

        # Hentikan sesi chat
        await stop_chat_session(user_id)
    else:
        # Jika tidak ada sesi aktif, beri tahu pengguna
        await message.reply_text(get_message(user_id, "no_chat_message"))
# Jalankan bot
if __name__ == '__main__':
    print("Bot sudah aktif")
    try:
        app.run()
    except Exception as e:
        print(f"Bot mengalami error: {e}")