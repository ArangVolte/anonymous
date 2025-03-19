import importlib
from sys import version as pyver

from pyrogram import __version__ as pyrover
from pyrogram import idle
from pyrogram.types import BotCommand
from pyrogram.errors import RPCError

from anon import app, LOOP
from anon.hand import ALL_MODULES

from anon.config import *

msg = """
🔥 **AnonBot Berhasil Di Aktifkan**
━━
➠ **Python Version** > `{}`
➠ **Pyrogram Version** > `{}`
━━
"""


async def main():
    await app.start()
    try:
        await app.set_bot_commands([
            BotCommand("start", "Memulai bot"),
            BotCommand("next", "Mencari pasangan chat"),
            BotCommand("stop", "Menghentikan chat"),
            BotCommand("help", "Menampilkan pesan bantuan"),
            BotCommand("settings", "Ubah jenis kelamin dan pengaturan lainnya")
        ])
    except RPCError as e:
        print(f"Bot mengalami error: {e}")
   
    for all_module in ALL_MODULES:
        importlib.import_module(f"anon.hand.{all_module}")
    print (msg.format(pyver.split()[0], pyrover))
    await idle()


if __name__ == "__main__":
    LOOP.run_until_complete(main())
