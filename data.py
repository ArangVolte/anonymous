# data.py
from tinydb import TinyDB, Query

# Inisialisasi TinyDB
db = TinyDB('./tinydb_data.json')  # Database disimpan di file JSON
User = Query()
user_data = db.table('cast')
userdb = db.table('info')

async def present_user(user_id: int):
    found = user_data.contains(User._id == user_id)
    return found

async def add_user(user_id: int):
    user_data.insert({'_id': user_id})
    return

async def full_userbase():
    user_ids = [doc['_id'] for doc in user_data.all()]
    return user_ids

async def del_user(user_id: int):
    user_data.remove(User._id == user_id)
    return

# Fungsi untuk menghentikan sesi chat
async def stop_chat_session(user_id):
    user_data = db.search(User.user_id == user_id)
    if user_data:
        partner_id = user_data[0].get('partner_id')
        db.remove(User.user_id == user_id)
        if partner_id and partner_id != "waiting":
            db.remove(User.user_id == partner_id)
            

async def add_data(user_id, kelamin, usia, notif, bahasa):
    cek = userdb.get((User.user_id == user_id) & (User.kelamin == kelamin) & (User.usia == usia) & (User.notif == notif) & (User.bahasa == bahasa))
    if cek:
        userdb.update(
            {
                "kelamin": kelamin,
                "usia": usia,
                "notif": notif,
                "bahasa": bahasa,
            },
            User.user_id == user_id
        )
    else:
        userdb.insert({"user_id": user_id, "kelamin": kelamin, "usia": usia, "notif": notif, "bahasa": bahasa})

async def kelamin_info(user_id, kelamin):
    r = userdb.get((User.user_id == user_id) & (User.kelamin == kelamin))
    if r:
        return r
    else:
        return "Tidak diketahui"

async def usia_info(user_id, usia):
    r = userdb.get((User.user_id == user_id) & (User.usia == usia))
    if r:
        return r
    else:
        return "Tidak diketahui"
        
async def noti_info(user_id, notif):
    r = userdb.get((User.user_id == user_id) & (User.notif == notif))
    if r:
        return r
    else:
        return "on"

async def bahasa_info(user_id, bahasa):
    r = userdb.get((User.user_id == user_id) & (User.bahasa == bahasa))
    if r:
        return r
    else:
        return "Indonesia"