# config.py
from os import getenv

# Konfigurasi API
API_ID = int(getenv("API_ID", "15370078"))  # Pastikan untuk mengganti dengan nilai yang aman
API_HASH = getenv("API_HASH", "e5e8756e459f5da3645d35862808cb30")  # Pastikan untuk mengganti dengan nilai yang aman
BOT_TOKEN = getenv("BOT_TOKEN", "6208650102:AAFvqr9dNwj1Pzbuo29K1XWXI46iQMFBS1Q")  # Pastikan untuk mengganti dengan nilai yang aman
ADMIN = int(getenv("ADMIN", "5401639797"))  # Ganti dengan ID admin Anda

# Pesan dalam bahasa Indonesia
MESSAGES = {
    "start_message": "Halo! Selamat datang di Anonim Chat Bot.\n\nGunakan /next untuk memulai percakapan anonim.",
    "next_message": "Menunggu pasangan chat...",
    "stop_message": "Anda menghentikan percakapan.",
    "partner_connected": "Kalian sudah saling terhubung",
    "partner_stop_message": "Lawan bicara Anda menghentikan percakapan.",
    "no_chat_message": "Anda belum memulai chat. Gunakan /next untuk memulai.",
    "error_message": "Terjadi kesalahan. Anda tidak dapat mengirim pesan ke diri sendiri.",
    "block_message": "Gagal mengirim pesan. Mungkin pasangan chat telah meninggalkan percakapan.",
    "help_message": "Daftar perintah yang tersedia:\n/start - Memulai bot\n/next - Mencari pasangan chat\n/stop - Menghentikan chat\n/help - Menampilkan pesan bantuan",
    "status_message": "📊 **Status Bot**\n\n👥 **Jumlah Pengguna:** {user_count}",
}