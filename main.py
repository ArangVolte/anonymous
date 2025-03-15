from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import asyncio

app = Client("anonim_chatbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


if __name__ == '__main__':
    print("Bot sedang berjalan...")
    asyncio.run(app.run())