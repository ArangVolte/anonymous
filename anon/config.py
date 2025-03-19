# config.py
from os import getenv

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  # Pastikan untuk mengganti dengan nilai yang aman
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  # Pastikan untuk mengganti dengan nilai yang aman
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAFvqr9dNwj1Pzbuo29K1XWXI46iQMFBS1Q")  # Pastikan untuk mengganti dengan nilai yang aman
ADMIN = int(getenv("ADMIN", "5401639797"))  # Ganti dengan ID admin Anda