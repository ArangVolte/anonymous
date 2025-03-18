from pyrogram import Client
from pyrogram.types import BotCommand
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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