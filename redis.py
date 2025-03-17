from os import getenv
from tinydb import TinyDB, Query  
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAGClqWpLAO_UWyyNR-sXhzKVboi9sY3Gd8")  
ADMIN = int(getenv("ADMIN", "5401639797"))  

# Inisialisasi TinyDB
db = TinyDB('./tinydb_data.json')  
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
    "help_message": "Daftar perintah yang tersedia:\n/start - Memulai bot\n/next - Mencari pasangan chat\n/stop - Menghentikan chat\n/help - Menampilkan pesan bantuan"
}

# Fungsi untuk menghentikan sesi chat
async def stop_chat_session(user_id):
    user_data = db.search(User.user_id == user_id)
    if user_data:
        partner_id = user_data[0].get('partner_id')
        db.remove(User.user_id == user_id)
        if partner_id and partner_id != 'waiting':
            db.remove(User.user_id == partner_id)

# Handler perintah /start
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Tidak ada username"

    await stop_chat_session(user_id)

    db.insert({'user_id': user_id, 'username': username})

    await message.reply_text(MESSAGES["start_message"])

# Handler perintah /next (mencari pasangan chat)
@app.on_message(filters.private & filters.command("next"))
async def start_chat(client, message):
    user_id = str(message.from_user.id)
    await stop_chat_session(user_id)

    waiting_partner = db.search(User.partner_id == 'waiting')
    if waiting_partner:
        waiting_partner_id = waiting_partner[0]['user_id']
        db.update({'partner_id': user_id}, User.user_id == waiting_partner_id)
        db.insert({'user_id': user_id, 'partner_id': waiting_partner_id})

        await app.send_message(waiting_partner_id, MESSAGES["partner_connected"])
        await message.reply_text(MESSAGES["partner_connected"])
    else:
        db.insert({'user_id': user_id, 'partner_id': 'waiting'})
        await message.reply_text(MESSAGES["next_message"])

# Handler perintah /stop (menghentikan chat)
@app.on_message(filters.private & filters.command("stop"))
async def stop_chat(client, message):
    user_id = str(message.from_user.id)
    user_data = db.search(User.user_id == user_id)

    if user_data:
        partner_id = user_data[0].get('partner_id')
        if partner_id != 'waiting':
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

# Handler untuk broadcast (hanya admin)
@app.on_message(filters.private & filters.command("cast") & filters.user(ADMIN))
async def broadcast(client, message):
    broadcast_message = message.reply_to_message
    if not broadcast_message:
        await message.reply_text("Balas pesan yang ingin Anda broadcast.")
        return

    # Ambil semua pengguna dari TinyDB
    all_users = db.all()
    
    for user in all_users:
        user_id = user['user_id']
        try:
            await broadcast_message.copy(user_id)
        except Exception as e:
            print(f"Gagal mengirim pesan ke {user_id}: {e}")

    await message.reply_text("Pesan broadcast telah dikirim.")

# Handler untuk menerima pesan dan media
@app.on_message(filters.private & ~filters.command(["next", "stop", "start", "help", "cast"]))
async def handle_message(client, message):
    user_id = str(message.from_user.id)
    
    user_data = db.search(User.user_id == user_id)
    
    if not user_data or user_data[0].get('partner_id') == 'waiting':
        await message.reply_text(MESSAGES["no_chat_message"])
        return

    partner_id = user_data[0].get('partner_id')
    
    # Prevent self-messaging.
    if partner_id == user_id:
        await message.reply_text(MESSAGES["error_message"])
        return
    
    reply_to_msg = message.reply_to_message.id if message.reply_to_message else None
    
    try:
        if message.photo or message.video:
            # Kirim media dengan tombol "Lihat"
            media_content = {
                'photo': ('https://akcdn.detik.net.id/community/media/visual/2022/11/18/simbol-bahan-kimia-5.jpeg', None),
                'video': ('<video_url>', None)  # Ganti dengan URL video jika alternatif diperlukan.
            }
            
            media_type = 'photo' if message.photo else 'video'
            
            await app.send_photo(
                partner_id,
                photo="https://akcdn.detik.net.id/community/media/visual/2022/11/18/simbol-bahan-kimia-5.jpeg?w=861",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Lihat", callback_data=f"lihat {user_id}|{message.id}")]]
                ),
                reply_to_message=reply_to_msg
            )
            
        else:
            # Salin pesan ke pasangan.
            await message.copy(partner_id, reply_to_msg=reply_to_msg)

   except Exception as e:
       print(f"Gagal mengirim pesan/media: {e}")
       await message.reply_text(MESSAGES["block_message"])
       await stop_chat_session(user_id)

# Handler untuk callback query (tombol "Lihat")
@app.on_callback_query(filters.regex("lihat"))
async def handle_callback(client, callback_query):
   data_split = callback_query.data.strip().split(None, 1)
   
   if len(data_split) < 2:
       return
   
   call_info = data_split[1]
   
   ph_userid, msgid_str = call_info.split("|")
   
   try:
       pp = await app.get_messages(int(ph_userid), int(msgid_str))

       if pp.photo:
           file_type_identifier = pp.photo.file_unique_id
           send_media_function = InputMediaPhoto
           caption_content = pp.caption or ""
       elif pp.video:
           file_type_identifier = pp.video.file_unique_id
           send_media_function = InputMediaVideo
           caption_content = pp.caption or ""
       else:
           await callback_query.answer("Media tidak dikenali.", show_alert=True)
           return

       mid_media_object_instance = send_media_function(file_type_identifier,
                                                          caption=caption_content.html) 

       # Edit media pada callback query.
       await app.edit_message_media(
           chat_kadal=callback_query.from_user.id,
           id_pesan=callback_query.message.id,
           media=mid_media_object_instance
       )
   except Exception as e:
       print(f"Gagal memproses callback: {e}")
       
# Jalankan bot
if __name__ == '__main__':
   print("Bot sudah aktif")
   try: 
       app.set_bot_commands([
           BotCommand("start", "Memulai bot"),
           BotCommand("next", "Mencari pasangan chat"),
           BotCommand("stop", "Menghentikan chat"),
           BotCommand("help", "Menampilkan pesan bantuan")
       ])      
       app.run()
   except Exception as e: 
       print(f"Bot mengalami error: {e}")