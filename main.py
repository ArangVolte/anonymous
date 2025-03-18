from anon import app
from pyrogram.types import BotCommand


if __name__ == '__main__':
    print("Bot sudah aktif")
    try:
        app.start()
        app.set_bot_commands([
            BotCommand("start", "Memulai bot"),
            BotCommand("next", "Mencari pasangan chat"),
            BotCommand("stop", "Menghentikan chat"),
            BotCommand("help", "Menampilkan pesan bantuan"),
            BotCommand("settings", "Ubah jenis kelamin dan pengaturan lainnya")
        ])
        print("Perintah bot berhasil dipasang.")
        
    except Exception as e:
        print(f"Bot mengalami error: {e}")