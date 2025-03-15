import os
import asyncio
import sqlite3
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 15370078
API_HASH = "e5e8756e459f5da3645d35862808cb30"
BOT_TOKEN = "6208650102:AAF6CyhFQk8b-duLd44A67chU_cHXlX9SOQ"

# Inisialisasi Pyrogram Client
app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Inisialisasi SQLite database
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

# Fungsi untuk mengakhiri percakapan
async def stop_chat_session(user_id):
    # Nonaktifkan chat yang sedang berlangsung
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
    lang = user_lang[0] if user_lang else 'id'  # Default ke 'id' jika tidak ditemukan

    # Baca file JSON dari folder lang
    lang_file_path = os.path.join("lang", f"{lang}.json")
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        return messages.get(key, "Pesan tidak ditemukan.")
    else:
        return f"File bahasa {lang}.json tidak ditemukan."

# Handler untuk /start
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Tidak ada username"

    # Akhiri percakapan yang sedang berlangsung (jika ada)
    await stop_chat_session(user_id)

    # Update atau tambahkan pengguna ke database
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username)
    VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()

    # Buat tombol untuk memilih bahasa
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="setlang_id"),
                InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")
            ]
        ]
    )

    # Kirim pesan dengan tombol
    await message.reply_text(
        "Halo! Selamat datang di Anonim Chat Bot.\n\n"
        "Silakan pilih bahasa / Please select your language:",
        reply_markup=keyboard
    )

# Handler untuk callback dari tombol
@app.on_callback_query()
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data.startswith("setlang_"):
        lang = data.split("_")[1]  # Ambil kode bahasa (id atau en)

        # Update bahasa pengguna di database
        cursor.execute('''
        UPDATE users
        SET language = ?
        WHERE user_id = ?
        ''', (lang, user_id))
        conn.commit()

        # Kirim pesan konfirmasi
        await callback_query.answer(f"Bahasa telah diubah ke {lang}.")
        await callback_query.message.edit_text(get_message(user_id, "start_message"))

# Handler untuk /next
@app.on_message(filters.command("next"))
async def start_chat(client, message):
    user_id = message.from_user.id

    # Akhiri percakapan yang sedang berlangsung (jika ada)
    await stop_chat_session(user_id)

    # Cari pasangan chat yang tersedia (pastikan user_id tidak sama dengan user_id_2)
    cursor.execute('''
    SELECT * FROM chats
    WHERE active = 0 AND user_id != ?
    ''', (user_id,))
    available_chat = cursor.fetchone()

    if available_chat:
        # Gabungkan ke chat yang tersedia
        cursor.execute('''
        UPDATE chats
        SET user_id_2 = ?, active = 1
        WHERE chat_id = ?
        ''', (user_id, available_chat[0]))
        conn.commit()

        await message.reply_text(get_message(user_id, "next_message"))
    else:
        # Buat chat baru
        cursor.execute('''
        INSERT INTO chats (user_id, active)
        VALUES (?, 0)
        ''', (user_id,))
        conn.commit()

        await message.reply_text(get_message(user_id, "next_message"))

# Handler untuk mengirim pesan atau media
@app.on_message(filters.document & filters.text & filters.audio & filters.voice & filters.video & filters.photo & filters.sticker & ~filters.command(["start", "next", "stop"]))
async def handle_message(client, message: Message):
    user_id = message.from_user.id

    # Cari chat aktif pengguna
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if not active_chat:
        await message.reply_text(get_message(user_id, "no_chat_message"))
        return

    # Tentukan penerima pesan
    recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

    # Pastikan recipient_id tidak sama dengan user_id
    if recipient_id == user_id:
        await message.reply_text(get_message(user_id, "error_message"))
        return

    # Kirim pesan atau media ke penerima
    try:
        if message.text:
            await app.send_message(recipient_id, message.text)
        elif message.voice:
            await app.send_voice(recipient_id, message.voice.file_id, caption=message.caption)
        elif message.audio:
            await app.send_audio(recipient_id, message.audio.file_id, caption=message.caption)
        elif message.sticker:
            await app.send_sticker(recipient_id, message.sticker.file_id)
        elif message.photo:
            await app.send_photo(recipient_id, message.photo.file_id, caption=message.caption)
        elif message.video:
            await app.send_video(recipient_id, message.video.file_id, caption=message.caption)
        elif message.document:
            await app.send_document(recipient_id, message.document.file_id, caption=message.caption)

    except Exception as e:
        print(f"Gagal mengirim pesan/media: {e}")
        await message.reply_text("Gagal mengirim pesan/media. Mungkin pasangan chat telah meninggalkan percakapan.")

# Handler untuk /stop
@app.on_message(filters.command("stop"))
async def stop_chat(client, message):
    user_id = message.from_user.id

    # Cari chat aktif pengguna
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if active_chat:
        # Tentukan ID lawan bicara
        recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

        # Kirim pesan ke pengguna yang menekan /stop
        await message.reply_text(get_message(user_id, "stop_message"))

        # Kirim pesan ke lawan bicara
        try:
            await app.send_message(recipient_id, get_message(recipient_id, "partner_stop_message"))
        except Exception as e:
            print(f"Gagal mengirim pesan ke lawan bicara: {e}")

        # Nonaktifkan chat
        await stop_chat_session(user_id)
    else:
        await message.reply_text(get_message(user_id, "no_chat_message"))

# Jalankan bot
if __name__ == '__main__':
    print("Bot sedang berjalan...")
    asyncio.run(app.run())