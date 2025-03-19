import os
import json
from anon.data.data import *

# Cache untuk pesan bahasa
LANG_CACHE = {}

def load_language(lang_code="id"):
    """
    Memuat file bahasa berdasarkan kode bahasa (default: id).
    """
    if lang_code in LANG_CACHE:
        return LANG_CACHE[lang_code]

    lang_file = os.path.join("lang", f"{lang}.json")
    if os.path.exists(lang_file):
        with open(lang_file, "r", encoding="utf-8") as f:
            LANG_CACHE[lang_code] = json.load(f)
            return LANG_CACHE[lang_code]
    else:
        raise FileNotFoundError(f"File bahasa '{lang_code}.json' tidak ditemukan.")

def get_message(user_id, key, lang_code="id"):
    """
    Mengambil pesan berdasarkan user_id dan key.
    Jika user_id memiliki preferensi bahasa, gunakan bahasa tersebut.
    """
    # Dapatkan preferensi bahasa pengguna dari database
    user_data = get_user_data(user_id)  # Fungsi ini harus diimplementasikan
    lang_code = user_data.get("lang", lang_code)  # Default ke bahasa Indonesia

    # Muat pesan bahasa
    messages = load_language(lang_code)
    return messages.get(key, f"Pesan '{key}' tidak ditemukan.")