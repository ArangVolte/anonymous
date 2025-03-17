from os import getenv
import asyncio
from tinydb import TinyDB, Query  # Ganti LevelDB dengan TinyDB
from pyrogram import idle
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  # Pastikan untuk mengganti dengan nilai yang aman
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  # Pastikan untuk mengganti dengan nilai yang aman
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAGClqWpLAO_UWyyNR-sXhzKVboi9sY3Gd8")  # Pastikan untuk mengganti dengan nilai yang aman
ADMIN = int(getenv("ADMIN", "5401639797"))  # Ganti dengan ID admin Anda

# Inisialisasi TinyDB
db = TinyDB('./tinydb_data.json')  # Database disimpan di file JSON
User = Query()

# Inisialisasi bot
app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Pesan dalam bahasa Indonesia
MESSAGES = {
    "start_message": "Halo! Selamat datang di Anonim Chat Bot.\n\nGunakan /next untuk memulai percakapan anonim.",
    "next_message": "Menunggu pasangan chat...",
    "stop_message": "Anda menghentikan percakapan.",
    "partner_connected": "Kalian sudah saling terhubung",
    "partner_stop_message": "Lawan bicara Anda menghentikan percakapan.",
    "no_chat_message": "Anda belum memulai chat. Gunakan /next untuk memulai.",
    "error_message": "Terjadi kesalahan. Anda tidak dapat mengirim pesan ke diri sendiri.",
    "block_message": "Gagal mengirim pesan. Mungkin pasangan chat telah meninggalkan percakapan.",
    "help_message": "Daftar perintah yang tersedia:\n/start - Memulai bot\n/next - Mencari pasangan chat\n/stop - Menghentikan chat\n/help - Menampilkan pesan bantuan",
    "status_message": "📊 **Status Bot**\n\n👥 **Jumlah Pengguna:** {user_count}",
    "broadcast_success": "✅ Pesan broadcast telah dikirim ke {success_count} pengguna.",
    "broadcast_failed": "❌ Gagal mengirim pesan ke {failed_count} pengguna."
}

# Fungsi untuk menghentikan sesi chat
async def stop_chat_session(user_id):
    user_data = db.search(User.user_id == user_id)
    if user_data:
        partner_id = user_data[0].get('partner_id')
        db.remove(User.user_id == user_id)
        if partner_id and partner_id != "waiting":
            db.remove(User.user_id == partner_id)

# Handler perintah /start
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Tidak ada username"

    db.insert({'user_id': user_id, 'username': username, 'partner_id': None})

    await message.reply_text(MESSAGES["start_message"])

# Handler perintah /next (mencari pasangan chat)
@app.on_message(filters.private & filters.command("next"))
async def start_chat(client, message):
    user_id = str(message.from_user.id)

    # Cari pasangan yang sedang menunggu
    waiting_partner = db.search(User.partner_id == "waiting")
    if waiting_partner:
        waiting_partner_id = waiting_partner[0]['user_id']
        db.update({'partner_id': user_id}, User.user_id == waiting_partner_id)
        db.insert({'user_id': user_id, 'partner_id': waiting_partner_id})

        await app.send_message(waiting_partner_id, MESSAGES["partner_connected"])
        await message.reply_text(MESSAGES["partner_connected"])
    else:
        db.insert({'user_id': user_id, 'partner_id': "waiting"})
        await message.reply_text(MESSAGES["next_message"])

# Handler perintah /stop (menghentikan chat)
@app.on_message(filters.private & filters.command("stop"))
async def stop_chat(client, message):
    user_id = str(message.from_user.id)
    user_data = db.search(User.user_id == user_id)

    if user_data:
        partner_id = user_data[0].get('partner_id')
        if partner_id and partner_id != "waiting":
            await message.reply_text(MESSAGES["stop_message"])
            await app.send_message(partner_id, MESSAGES["partner_stop_message"])
            await stop_chat_session(user_id)
        else:
            await message.reply_text(MESSAGES["no_chat_message"])
    else:
        await message.reply_text(MESSAGES["no_chat_message"])

# Handler perintah /help
@app.on_message(filters.private & filters.command("help"))
async def help(client, message):
    await message.reply_text(MESSAGES["help_message"])

# Handler perintah /status (khusus admin)
@app.on_message(filters.private & filters.command("status") & filters.user(ADMIN))
async def status(client, message):
    # Hitung jumlah pengguna
    user_count = len(db.search(User.user_id.exists()))
    await message.reply_text(MESSAGES["status_message"].format(user_count=user_count))

# Handler untuk broadcast (hanya admin)
@app.on_message(filters.private & filters.command("cast") & filters.user(ADMIN))
async def broadcast(client, message):
    broadcast_message = message.reply_to_message
    if not broadcast_message:
        await message.reply_text("Balas pesan yang ingin Anda broadcast.")
        return

    # Ambil semua pengguna dari TinyDB
    all_users = db.search(User.user_id.exists())
    success_count = 0
    failed_count = 0

    # Kirim pesan ke semua pengguna
    for user in all_users:
        user_id = user['user_id']
        try:
            await broadcast_message.copy(user_id)
            success_count += 1
        except Exception as e:
            print(f"Gagal mengirim pesan ke {user_id}: {e}")
            failed_count += 1

    # Kirim laporan broadcast
    report_message = (
        f"{MESSAGES['broadcast_success'].format(success_count=success_count)}\n"
        f"{MESSAGES['broadcast_failed'].format(failed_count=failed_count)}"
    )
    await message.reply_text(report_message)

# Handler untuk menerima pesan dan media
@app.on_message(filters.private & ~filters.command(["next", "stop", "start", "help", "cast", "status"]))
async def handle_message(client, message):
    user_id = str(message.from_user.id)
    user_data = db.search(User.user_id == user_id)

    if not user_data or user_data[0].get('partner_id') == "waiting":
        await message.reply_text(MESSAGES["no_chat_message"])
        return

    partner_id = user_data[0].get('partner_id')
    if partner_id == user_id:
        await message.reply_text(MESSAGES["error_message"])
        return
    reply_id = message.reply_to_message.id - 1 if message.reply_to_message else None
    try:
        if message.photo or message.video:
            # Kirim media dengan tombol "Lihat"
            await app.send_photo(
                partner_id,
                photo="https://akcdn.detik.net.id/community/media/visual/2022/11/18/simbol-bahan-kimia-5.jpeg?w=861",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Lihat", callback_data=f"lihat {user_id}|{message.id}")]]
                ),
                reply_to_message_id=reply_id
            )
        else:
            await message.copy(partner_id, reply_to_message_id=reply_id)
    except Exception as e:
        print(f"Gagal mengirim pesan/media: {e}")
        await message.reply_text(MESSAGES["block_message"])
        await stop_chat_session(user_id)

# Handler untuk callback query (tombol "Lihat")
@app.on_callback_query(filters.regex("lihat"))
async def handle_callback(client, callback_query):
    test = callback_query.data.strip()
    call = test.split(None, 1)[1]
    ph, ms = call.split("|")
    pp = await app.get_messages(int(ph), int(ms))
    
    # Pastikan caption tidak None
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
    mid = send(xx, caption=pp.caption and pp.caption.html or "")
    
    # Edit message media
    await app.edit_message_media(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.id,
        media=mid
    )


if __name__ == '__main__':
    print("Bot sudah aktif")
    try:
        app.run()
        app.set_bot_commands([
        BotCommand("start", "Memulai bot"),
        BotCommand("next", "Mencari pasangan chat"),
        BotCommand("stop", "Menghentikan chat"),
        BotCommand("help", "Menampilkan pesan bantuan")
    ])
    except Exception as e:
        print(f"Bot mengalami error: {e}")