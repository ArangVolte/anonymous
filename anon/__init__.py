import sys
import asyncio
from pyrogram import Client
import logging

from .config import *

LOOP = asyncio.get_event_loop()
logging.basicConfig(level=logging.INFO)


if not API_ID:
    print("API_ID Tidak ada")
    sys.exit()

if not API_HASH:
    print("API_HASH Tidak ada")
    sys.exit()

if not BOT_TOKEN:
    print("BOT_TOKEN Tidak ada")
    sys.exit()



app = Client(
	name="anonim_chatbot", 
	api_id=API_ID, 
	api_hash=API_HASH, 
	bot_token=BOT_TOKEN
	)
