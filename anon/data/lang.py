import os
import json
from anon.data.data import *

def get_message(user_id, key):
    # Cari user berdasarkan user_id
    user_data = get_user_data(user_id)
        
    
    lang = user_data['lang'] if user_data else 'id'

    # Baca file bahasa
    lang_file_path = os.path.join("lang", f"{lang}.json")
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        return messages.get(key, "Pesan tidak ditemukan.")
    else:
        return f"File bahasa {lang}.json tidak ditemukan."

