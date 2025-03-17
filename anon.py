import os
from os import getenv
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  # Pastikan untuk mengganti dengan nilai yang aman
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  # Pastikan untuk mengganti dengan nilai yang aman
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAGClqWpLAO_UWyyNR-sXhzKVboi9sY3Gd8")  # Pastikan untuk mengganti dengan nilai yang aman

# Inisialisasi bot
app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Koneksi database
conn = sqlite3.connect('anonim_chatbot.db', check_same_thread=False)
cursor = conn.cursor()

# Buat tabel jika belum ada
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
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

# Pesan dalam bahasa Indonesia
MESSAGES = {
    "start_message": "Halo! Selamat datang di Anonim Chat Bot.\n\nGunakan /next untuk memulai percakapan anonim.",
    "next_message": "Menunggu pasangan chat...",
    "stop_message": "Anda menghentikan percakapan.",
    "partner_connected": "Kalian sudah saling terhubung",
    "partner_stop_message": "Lawan bicara Anda menghentikan percakapan.",
    "no_chat_message": "Anda belum memulai chat. Gunakan /next untuk memulai.",
    "error_message": "Terjadi kesalahan. Anda tidak dapat mengirim pesan ke diri sendiri.",
    "block_message": "Gagal mengirim pesan. Mungkin pasangan chat telah meninggalkan percakapan."
}

# Fungsi untuk menghentikan sesi chat
async def stop_chat_session(user_id):
    cursor.execute('''
    UPDATE chats
    SET active = 0
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    conn.commit()

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

    await message.reply_text(MESSAGES["start_message"])

# Handler perintah /next (mencari pasangan chat)
@app.on_message(filters.private & filters.command("next"))
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

        await app.send_message(first_user_id, MESSAGES["partner_connected"])
        await message.reply_text(MESSAGES["partner_connected"])
        
        print(f"Pengguna {first_user_id} dan {user_id} telah saling bertemu.")
    else:
        cursor.execute('''
        INSERT INTO chats (user_id, active)
        VALUES (?, 0)
        ''', (user_id,))
        conn.commit()

        await message.reply_text(MESSAGES["next_message"])
        
# Handler perintah /stop (menghentikan chat)
@app.on_message(filters.private & filters.command("stop"))
async def stop_chat(client, message):
    user_id = message.from_user.id
    print(f"Perintah /stop diterima dari {user_id}")

    # Cari sesi chat aktif
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if active_chat:
        recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

        # Beri tahu pengguna bahwa sesi dihentikan
        await message.reply_text(MESSAGES["stop_message"])

        # Beri tahu penerima bahwa sesi dihentikan
        try:
            if recipient_id:
                await app.send_message(recipient_id, MESSAGES["partner_stop_message"])
        except Exception as e:
            print(f"Gagal mengirim pesan ke lawan bicara: {e}")

        # Hentikan sesi chat
        await stop_chat_session(user_id)
    else:
        # Jika tidak ada sesi aktif, beri tahu pengguna
        await message.reply_text(MESSAGES["no_chat_message"])

# Handler untuk menerima pesan dan media
@app.on_message(filters.private & ~filters.command(["next", "stop", "start"]))
async def handle_message(client, message):
    user_id = message.from_user.id
    cursor.execute('''
    SELECT * FROM chats
    WHERE (user_id = ? OR user_id_2 = ?) AND active = 1
    ''', (user_id, user_id))
    active_chat = cursor.fetchone()

    if not active_chat:
        await message.reply_text(MESSAGES["no_chat_message"])
        return
        
    recipient_id = active_chat[2] if active_chat[1] == user_id else active_chat[1]

    if recipient_id is None or recipient_id == user_id:
        await message.reply_text(MESSAGES["error_message"])
        return

    reply_id = message.reply_to_message.id -1 if message.reply_to_message else None
    try:
        if message.photo or message.video:
        	await app.send_photo(
            recipient_id, 
            photo="https://akcdn.detik.net.id/community/media/visual/2022/11/18/simbol-bahan-kimia-5.jpeg?w=861",
            reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
            	"Lihat", callback_data=f"lihat {user_id}|{message.id}")]]
            ))
        else:
            await message.copy(recipient_id, reply_to_message_id=reply_id)
        
    except Exception as e:
        print(f"Gagal mengirim pesan/media: {e}")
        await message.reply_text(MESSAGES["block_message"])
        await stop_chat_session(user_id)  # Menghentikan sesi chat jika terjadi kesalahan
        
from pyrogram.types import InputMediaPhoto, InputMediaVideo

@app.on_callback_query(filters.regex("lihat"))
async def handle_callback(client, callback_query):
    test = callback_query.data.strip()
    call = test.split(None, 1)[1]
    ph, ms = call.split("|")
    pp = await app.get_messages(int(ph), int(ms))
    
    # Pastikan caption tidak None
    cp = pp.caption if pp.caption else ""
    
    # Pastikan media yang valid
    if pp.photo:
        xx = pp.photo.file_id
        send = InputMediaPhoto
    elif pp.video:
        xx = pp.video.file_id
        send = InputMediaVideo
    else:
        await callback_query.answer("Media tidak dikenali", show_alert=True)
        return
    
    # Buat media object
    mid = send(xx, cp)
    
    # Edit message media
    await app.edit_message_media(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.id,
        media=mid
    )
        
# Jalankan bot
if __name__ == '__main__':
    print("Bot sudah aktif")
    try:
        app.run()
    except Exception as e:
        print(f"Bot mengalami error: {e}")
        
        


