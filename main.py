from anon import app
from pyrogram.types import BotCommand
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

async def main():
    print("Bot sudah aktif")
    try:
        # Mulai bot
        await app.start()
        
        # Set perintah bot
        await app.set_bot_commands([
            BotCommand("start", "Memulai bot"),
            BotCommand("next", "Mencari pasangan chat"),
            BotCommand("stop", "Menghentikan chat"),
            BotCommand("help", "Menampilkan pesan bantuan"),
            BotCommand("settings", "Ubah jenis kelamin dan pengaturan lainnya")
        ])
        print("Perintah bot berhasil dipasang.")
        
        # Biarkan bot tetap berjalan
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"Bot mengalami error: {e}")
    finally:
        # Hentikan bot saat program selesai
        await app.stop()

if __name__ == '__main__':
    # Jalankan fungsi main secara asinkron
    asyncio.run(main())