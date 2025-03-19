# anon.py
import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from anon.config import *
from anon.data.data import *
from anon import app

def strtobool(value):
    value = value.lower()
    if value in ('True', 'true'):
        return True
    elif value in ('False', 'false'):
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")

# Contoh penggunaan
print(strtobool("true"))  # Output: 1
print(strtobool("false")) # Output: 0

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
    
    msg = "Jika Anda ingin, berikan umpan balik tentang pasangan Anda. Ini akan membantu kami menemukan pasangan yang lebih baik untuk Anda di masa depan."
    
    key=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👍", callback_data="like"),
            InlineKeyboardButton("👎", callback_data="dislike")]
         ]
        )


    if user_data:
        partner_id = user_data[0].get('partner_id')
        if partner_id and partner_id != "waiting":
            await message.reply_text(MESSAGES["stop_message"])
            await message.reply(msg, reply_markup=key)
            await app.send_message(partner_id, MESSAGES["partner_stop_message"])
            await app.send_message(partner_id, msg, reply_markup=key)
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

    reply_id = message.reply_to_message.id -1 if message.reply_to_message else None
    partner_data = get_user_data(partner_id)
    if partner_data is not None:
        pt = partner_data.get('protect', 'False')
        status = partner_data.get('hide', '❌')
        print(f"{pt} | {status}")
    else:
        pt = "False"
        status = "❌"

    try:
        if message.photo or message.video:
            if status == "✅":
                await app.send_photo(
                    partner_id,
                    photo="https://akcdn.detik.net.id/community/media/visual/2022/11/18/simbol-bahan-kimia-5.jpeg?w=861",
                    protect_content=strtobool(pt),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Lihat", callback_data=f"lihat {user_id}|{message.id}")]]
                    ),
                    reply_to_message_id=reply_id
                )
            else:
                await message.copy(
                    partner_id,
                    protect_content=strtobool(pt),
                    reply_to_message_id=reply_id
                )
        else:
            await message.copy(
                partner_id,
                protect_content=strtobool(pt),
                reply_to_message_id=reply_id
            )
    except Exception as e:
        print(f"Gagal mengirim pesan/media: {e}")
        await message.reply_text(MESSAGES["block_message"])
        await stop_chat_session(user_id)
        
        
# Handler untuk perintah /start
@app.on_message(filters.private & filters.command("settings"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👨 Jenis Kelamin ️👩", callback_data="gender")],
            [InlineKeyboardButton("📆 Usia", callback_data="age")],
            [InlineKeyboardButton("🎞 Sembunyikan foto/video", callback_data="hide_media")],
            [InlineKeyboardButton("🔐Protect", callback_data="protect")]
        ]
    )
    await message.reply_text("**Pilih pengaturan yang ingin Anda ubah:**.", reply_markup=keyboard)