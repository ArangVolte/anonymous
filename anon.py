# anon.py
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from config import ADMIN, MESSAGES, API_ID, API_HASH, BOT_TOKEN
from data import db, User, user_data, present_user, add_user, full_userbase, del_user, stop_chat_session, info_table


app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Handler perintah /start
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Tidak ada username"

    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    user_data = db.search(User.user_id == user_id)
    if user_data and user_data[0].get('partner_id') not in [None, "waiting"]:
        await message.reply_text("Kamu masih dalam obrolan. Gunakan /stop untuk menghentikan percakapan.")
        return  # Hentikan eksekusi lebih lanjut jika masih dalam obrolan

    # Jika tidak dalam obrolan, lanjutkan seperti biasa
    db.insert({'user_id': user_id, 'username': username, 'partner_id': None})
    await message.reply_text(MESSAGES["start_message"])

# Handler perintah /next (mencari pasangan chat)
@app.on_message(filters.private & filters.command("next"))
async def start_chat(client, message):
    user_id = str(message.from_user.id)
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    # Cek apakah pengguna masih dalam obrolan
    user_data = db.search(User.user_id == user_id)
    if user_data and user_data[0].get('partner_id') not in [None, "waiting"]:
        await message.reply_text("Kamu masih dalam obrolan. Gunakan /stop untuk menghentikan percakapan.")
        return  # Hentikan eksekusi lebih lanjut jika masih dalam obrolan

    # Jika tidak dalam obrolan, lanjutkan seperti biasa
    waiting_partner = db.search(User.partner_id == "waiting")
    if waiting_partner:
        waiting_partner_id = waiting_partner[0]['user_id']

        # Cek apakah user_id sama dengan waiting_partner_id
        if user_id == waiting_partner_id:
            # Hapus data pengguna yang sedang menunggu
            db.remove(User.user_id == user_id)
            db.insert({'user_id': user_id, 'partner_id': "waiting"})
            await message.reply_text(MESSAGES["next_message"])
            return

        # Jika tidak sama, lanjutkan dengan menghubungkan kedua pengguna
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
    _count = await full_userbase()
    xx = len(_count)
    await message.reply_text(MESSAGES["status_message"].format(user_count=xx))

# Handler untuk broadcast (hanya admin)
@app.on_message(filters.private & filters.command("cast") & filters.user(ADMIN))
async def send_text(client, message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Silahkan balas ke pesan")
        await asyncio.sleep(8)
        await msg.delete()
        
        
# Handler untuk menerima pesan dan media
@app.on_message(filters.private & ~filters.command(["next", "stop", "start", "help", "cast", "status", "settings"]))
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


# Handler untuk perintah /settings
@app.on_message(filters.private & filters.command("settings"))
async def settings(client, message):
    user_id = message.from_user.id
    user_data = info_table.get(User.id == user_id)

    if not user_data:
        info_table.insert({'id': user_id, 'kelamin': None, 'usia': None, 'notif': False, 'bahasa': None})

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👨 Jenis Kelamin ️👩", callback_data="gender")],
            [InlineKeyboardButton("📆 Usia", callback_data="age")],
            [InlineKeyboardButton("🎞 Sembunyikan foto/video", callback_data="hide_media")],
            [InlineKeyboardButton("🌍 Bahasa", callback_data="language")]
        ]
    )
    await message.reply_text("Pilih pengaturan yang ingin Anda ubah:\n\n**Catatan:** Anda hanya akan dicocokkan dengan pengguna yang menggunakan bahasa yang sama.", reply_markup=keyboard)

# Handler untuk jenis kelamin
@app.on_callback_query(filters.regex("^gender$"))
async def gender_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user_data = info_table.get(User.id == user_id)
    
    # Ambil data jenis kelamin dari database
    jenis_kelamin = user_data.get('kelamin', 'Belum diatur')  # Default jika tidak ada data

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Saya laki-laki 👨", callback_data="male"),
            InlineKeyboardButton("Saya perempuan 👩", callback_data="female")],
            [InlineKeyboardButton("Hapus jenis kelamin saya", callback_data="remove_gender")],
            [InlineKeyboardButton("← Kembali", callback_data="back_to_main")]
        ]
    )
    
    # Tampilkan pesan dengan data jenis kelamin dari database
    await callback_query.edit_message_text(
        f"Jenis kelamin Anda: **{jenis_kelamin}**\nUntuk mengubah atau menghapus jenis kelamin, klik tombol di bawah ini", 
        reply_markup=keyboard
    )

# Handler untuk usia
@app.on_callback_query(filters.regex("^age$"))
async def age_settings(client, callback_query):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❌ Hapus Usia", callback_data="remove_age")],
            [InlineKeyboardButton("← Kembali", callback_data="back_to_main")]
        ]
    )
    await callback_query.edit_message_text("Masukkan usia Anda dan itu akan membantu kami menemukan pasangan yang lebih cocok.\n\nMasukkan angka antara 9 dan 99. Misalnya, kirimkan kami 18 jika Anda berusia 18 tahun.\n\nAnda selalu dapat mengubah usia Anda di /settings.", reply_markup=keyboard)

# Handler untuk menyembunyikan media
@app.on_callback_query(filters.regex("^hide_media$"))
async def hide_media_settings(client, callback_query):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Aktifkan sembunyikan foto/video", callback_data="enable_hide_media")],
            [InlineKeyboardButton("← Kembali", callback_data="back_to_main")]
        ]
    )
    await callback_query.edit_message_text("Dengan mengaktifkan mode disembunyikan, semua foto, video, dokumen dan GIF yang masuk akan diburamkan. Anda bisa melihatnya jika Anda membuka media tersebut", reply_markup=keyboard)

# Handler untuk bahasa
@app.on_callback_query(filters.regex("^language$"))
async def language_settings(client, callback_query):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇮🇩 Indonesian", callback_data="lang_id"),
            InlineKeyboardButton("🇮🇹 Italian", callback_data="lang_it")],
            [InlineKeyboardButton("🇪🇸 Spanish", callback_data="lang_es"),
            InlineKeyboardButton("🇹🇷 Turkish", callback_data="lang_tr"),
            InlineKeyboardButton("🇰🇷 Korean", callback_data="lang_ko")],
            [InlineKeyboardButton("← Kembali", callback_data="back_to_main")]
        ]
    )
    await callback_query.edit_message_text("Atur bahasa Anda.\n\n**Catatan:** Anda hanya akan dicocokkan dengan pengguna yang menggunakan bahasa yang sama.", reply_markup=keyboard)

# Handler untuk kembali ke menu utama
@app.on_callback_query(filters.regex("^back_to_main$"))
async def back_to_main(client, callback_query):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👨 Jenis Kelamin ️👩", callback_data="gender")],
            [InlineKeyboardButton("📆 Usia", callback_data="age")],
            [InlineKeyboardButton("🎞 Sembunyikan foto/video", callback_data="hide_media")],
            [InlineKeyboardButton("🌍 Bahasa", callback_data="language")]
        ]
    )
    await callback_query.edit_message_text("Pilih pengaturan yang ingin Anda ubah:\n\n**Catatan:** Anda hanya akan dicocokkan dengan pengguna yang menggunakan bahasa yang sama.", reply_markup=keyboard)

# Handler untuk callback query
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data.startswith("age_"):
        usia = int(data.split("_")[1])
        info_table.update({'usia': usia}, User.id == user_id)
        await callback_query.answer(f"Usia Anda telah diatur menjadi {usia} tahun.")
    elif data in ["male", "female"]:
        info_table.update({'kelamin': data}, User.id == user_id)
        await callback_query.answer(f"Jenis kelamin Anda telah diatur menjadi {data}.")
    elif data == "remove_gender":
        info_table.update({'kelamin': None}, User.id == user_id)
        await callback_query.answer("Jenis kelamin Anda telah dihapus.")
    elif data == "toggle_notif":
        user_data = info_table.get(User.id == user_id)
        new_status = not user_data['notif']
        info_table.update({'notif': new_status}, User.id == user_id)
        await callback_query.answer(f"Notifikasi telah diubah menjadi {'✅ Aktif' if new_status else '❌ Nonaktif'}.")
    elif data.startswith("lang_"):
        bahasa = data.split("_")[1]
        info_table.update({'bahasa': bahasa}, User.id == user_id)
        await callback_query.answer(f"Bahasa Anda telah diatur menjadi {bahasa}.")
    elif data == "back_to_main":
        await start(client, callback_query.message)
