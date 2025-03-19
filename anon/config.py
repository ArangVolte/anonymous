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
    "stop_message": "Anda telah menghentikan obrolan. Mencari pasangan baru",
    "partner_connected": "Pasangan ditemukan\n\n/next - cari pasangan baru\n/stop - hentikan obrolan",
    "partner_stop_message": "Pasangan Anda telah menghentikan obrolan tekan /next untuk menemukan pasangan baru",
    "no_chat_message": "Anda belum memulai chat. Gunakan /next untuk memulai.",
    "error_message": "Terjadi kesalahan. Anda tidak dapat mengirim pesan ke diri sendiri.",
    "block_message": "Gagal mengirim pesan. Mungkin pasangan chat telah meninggalkan percakapan.",
    "help_message": "Daftar perintah yang tersedia:\n/start - Memulai bot\n/next - Mencari pasangan chat\n/stop - Menghentikan chat\n/help - Menampilkan pesan bantuan\n/settings - Ubah jenis kelamin dan pengaturan lainnya",
    "status_message": "📊 **Status Bot**\n\n👥 **Jumlah Pengguna:** {user_count}",
}