# cbb.py
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from anon.config import MESSAGES
from anon.data.data import *
from anon import app

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

# Handler untuk jenis kelamin
@app.on_callback_query(filters.regex("^gender$"))
async def gender_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data and user_data.get('gender'):
        gender_text = user_data['gender']
    else:
        gender_text = "Belum diatur"
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Saya laki-laki 👨", callback_data="male"),
            InlineKeyboardButton("Saya perempuan 👩", callback_data="female")],
            [InlineKeyboardButton("Hapus jenis kelamin saya", callback_data="remove_gender")],
            [InlineKeyboardButton("← Kembali", callback_data="back_to_main")]
        ]
    )
    await callback_query.edit_message_text(f"Jenis kelamin Anda: **{gender_text}**\nUntuk mengubah atau menghapus jenis kelamin, klik tombol di bawah ini", reply_markup=keyboard)

@app.on_callback_query(filters.regex("^male$|^female$"))
async def set_gender(client, callback_query):
    user_id = callback_query.from_user.id
    xx = callback_query.data
    if xx == "male":
    	gender = "Laki-laki"
    	await callback_query.answer("Anda memilih Laki-laki")
    elif xx == "female":
    	gender = "Perempuan"
    	await callback_query.answer("Anda memilih Perempuan")
    update_user_data(user_id, gender=gender)
    await callback_query.answer(f"Jenis kelamin Anda telah diatur menjadi {gender}", show_alert=True)
    await gender_settings(client, callback_query)

@app.on_callback_query(filters.regex("^remove_gender$"))
async def remove_gender(client, callback_query):
    user_id = callback_query.from_user.id
    
    update_user_data(user_id, gender=None)
    await callback_query.answer("Jenis kelamin Anda telah dihapus", show_alert=True)
    await gender_settings(client, callback_query)

    return {"age": 25}  # Contoh data pengguna

# age
@app.on_callback_query(filters.regex("^age$"))
async def age_settings(client, callback_query):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    if user_data and user_data.get('age'):
        age_text = str(user_data['age'])
    else:
        age_text = "Belum diatur"
    
    # Tampilkan halaman pertama
    await show_age_page(client, callback_query, page=1)

async def show_age_page(client, callback_query, page):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    if user_data and user_data.get('age'):
        age_text = str(user_data['age'])
    else:
        age_text = "Belum diatur"
    
    # Hitung range angka untuk halaman ini
    start = 9 + (page - 1) * 100
    end = min(start + 100, 100)  # Maksimal sampai 99

    # Buat grid 10x10
    keyboard = []
    for row in range(0, 100, 10):
        row_buttons = [
            InlineKeyboardButton(str(start + i), callback_data=f"update_age_{start + i}")
            for i in range(row, min(row + 10, 100 - start))
        ]
        keyboard.append(row_buttons)
    
    # Tambahkan tombol navigasi
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("← Prev", callback_data=f"prev_page_{page-1}"))
    if end < 100:
        navigation_buttons.append(InlineKeyboardButton("Next →", callback_data=f"next_page_{page+1}"))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    # Tambahkan tombol "Hapus Usia" dan "Kembali"
    keyboard.append([InlineKeyboardButton("❌ Hapus Usia", callback_data="remove_age")])
    keyboard.append([InlineKeyboardButton("← Kembali", callback_data="back_to_main")])

    await callback_query.edit_message_text(
        f"Masukkan usia Anda, Usia anda saat ini: **{age_text}**\n"
        "dan itu akan membantu kami menemukan pasangan yang lebih cocok.\n\n"
        "Masukkan angka antara 9 dan 99. Misalnya, kirimkan kami 18 jika Anda berusia 18 tahun.\n\n"
        "Anda selalu dapat mengubah usia Anda di /settings.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("^next_page_(\d+)$"))
async def next_page(client, callback_query):
    page = int(callback_query.matches[0].group(1))
    await show_age_page(client, callback_query, page)

@app.on_callback_query(filters.regex("^prev_page_(\d+)$"))
async def prev_page(client, callback_query):
    page = int(callback_query.matches[0].group(1))
    await show_age_page(client, callback_query, page)

@app.on_callback_query(filters.regex("^update_age_(\d+)$"))
async def update_age(client, callback_query):
    user_id = callback_query.from_user.id
    age = int(callback_query.matches[0].group(1))
    
    if 9 <= age <= 99:
        update_user_data(user_id, age=age)  # Langsung update usia
        await callback_query.answer(f"Usia Anda telah diatur menjadi {age}", show_alert=True)
        await age_settings(client, callback_query)  # Refresh tampilan
    else:
        await callback_query.answer("Usia harus antara 9 dan 99.", show_alert=True)

@app.on_callback_query(filters.regex("^remove_age$"))
async def remove_age(client, callback_query):
    user_id = callback_query.from_user.id
    
    update_user_data(user_id, age=None)  # Hapus usia
    await callback_query.answer("Usia Anda telah dihapus", show_alert=True)
    await age_settings(client, callback_query)  
  
  
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
            InlineKeyboardButton("🇮🇩Indonesian", callback_data="lang_id"),
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