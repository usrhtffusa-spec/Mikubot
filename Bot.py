import telebot
import json
import time
import os
import random

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================
# Tumhara Token
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Owner aur Admin IDs
OWNER_ID = 8327837344
ADMIN_IDS = [8279690595, 7738104912]

DATA_FILE = "miku_db.json"
DAY = 86400

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 🛍️ SHOP ITEMS
SHOP_ITEMS = {
    "rose": {"name": "Rose", "icon": "🌹", "price": 500},
    "chocolate": {"name": "Chocolate", "icon": "🍫", "price": 800},
    "ring": {"name": "Ring", "icon": "💍", "price": 2000},
    "teddy": {"name": "Teddy Bear", "icon": "🧸", "price": 1500},
    "pizza": {"name": "Pizza", "icon": "🍕", "price": 600},
    "surprise": {"name": "Surprise Box", "icon": "🎁", "price": 2500},
    "puppy": {"name": "Puppy", "icon": "🐶", "price": 3000},
    "cake": {"name": "Cake", "icon": "🎂", "price": 1000},
    "letter": {"name": "Love Letter", "icon": "💌", "price": 400},
    "cat": {"name": "Cat", "icon": "🐱", "price": 2500}
}

# =========================================================
# 💾 DATABASE
# =========================================================
def load_db():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "eco_lock": False}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "eco_lock": False}

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()
users = db.setdefault("users", {})
db.setdefault("eco_lock", False)

# =========================================================
# 🛠️ UTILS
# =========================================================
def is_admin(uid):
    return uid == OWNER_ID or uid in ADMIN_IDS

def eco_locked():
    return db["eco_lock"]

def mention(uid, name):
    return f'<a href="tg://user?id={uid}">{name}</a>'

def get_user(uid, name):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "name": name,
            "balance": 1000,
            "kills": 0,
            "status": "alive",
            "death_time": 0,
            "protection": 0,
            "last_daily": 0,
            "inventory": {}
        }
    users[uid]["name"] = name
    # Fix missing keys
    if "inventory" not in users[uid]: users[uid]["inventory"] = {}
    return users[uid]

def check_death(uid):
    uid = str(uid)
    if uid not in users: return False
    u = users[uid]
    if u["status"] == "dead":
        # Auto Revive after 6 hours
        if time.time() > u["death_time"] + 21600:
            u["status"] = "alive"
            u["death_time"] = 0
            save_db()
            return False
        return True
    return False

# =========================================================
# 📜 MAIN COMMANDS
# =========================================================

@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    text = (
        "📖 <b>Miku Bot Commands</b>\n\n"
        "👤 <b>User Commands:</b>\n"
        "/daily — Daily reward ($1500)\n"
        "/bal — Check balance & status\n"
        "/rob (reply) — Rob money\n"
        "/kill (reply) — Kill user\n"
        "/protect — Buy protection\n"
        "/give (reply) amount — Transfer\n"
        "/items — View Shop\n"
        "/gift (reply) item — Gift item\n"
        "/toprich — Richest users\n"
        "/topkill — Top killers\n\n"
        "🫡 <b>Owner / Admin Commands:</b>\n"
        "/transfer (reply) amount — Give/Take unlimited money\n"
        "/forcerev (reply) — Revive instantly\n"
        "/forcekill (reply) — Kill instantly\n"
        "/giveprot (reply) — Give 2 days shield\n"
        "/breakprot (reply) — Remove shield\n"
        "/lockeco — Stop economy\n"
        "/unlockeco — Start economy\n"
        "/stats — Bot stats"
    )
    bot.reply_to(m, text)

# =========================================================
# 👤 USER FEATURES
# =========================================================

@bot.message_handler(commands=['daily'])
def daily(m):
    if eco_locked(): return bot.reply_to(m, "🔒 Economy is locked.")
    
    uid = str(m.from_user.id)
    u = get_user(uid, m.from_user.first_name)
    
    if check_death(uid): return bot.reply_to(m, "💀 You are dead.")

    if time.time() - u["last_daily"] < DAY:
        rem = int(DAY - (time.time() - u["last_daily"]))
        hours, mins = rem // 3600, (rem % 3600) // 60
        return bot.reply_to(m, f"⏳ Come back in <b>{hours}h {mins}m</b>")

    u["balance"] += 1500
    u["last_daily"] = time.time()
    save_db()
    bot.reply_to(m, "💰 You claimed your <b>$1500</b> daily reward!")

@bot.message_handler(commands=['bal', 'balance'])
def bal(m):
    if m.reply_to_message:
        uid = m.reply_to_message.from_user.id
        name = m.reply_to_message.from_user.first_name
    else:
        uid = m.from_user.id
        name = m.from_user.first_name

    u = get_user(uid, name)
    
    # Global Rank
    ranking = sorted(users.values(), key=lambda x: x["balance"], reverse=True)
    try: rank = ranking.index(u) + 1
    except: rank = "N/A"

    status = "dead" if check_death(uid) else "alive"

    bot.reply_to(
        m,
        f"👤 Name: {u['name']}\n"
        f"💰 Balance: <b>${u['balance']}</b>\n"
        f"🏆 Rank: {rank}\n"
        f"❤️ Status: {status}\n"
        f"⚔️ Kills: {u['kills']}"
    )

@bot.message_handler(commands=['rob'])
def rob(m):
    if eco_locked(): return bot.reply_to(m, "🔒 Economy is locked.")
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    r_id = str(m.from_user.id)
    v_id = str(m.reply_to_message.from_user.id)
    if r_id == v_id: return bot.reply_to(m, "⚠️ Cannot rob yourself.")

    robber = get_user(r_id, m.from_user.first_name)
    victim = get_user(v_id, m.reply_to_message.from_user.first_name)

    if check_death(r_id): return bot.reply_to(m, "💀 You are dead.")
    if check_death(v_id): return bot.reply_to(m, "💀 Victim is already dead.")
    if time.time() < victim["protection"]: return bot.reply_to(m, f"🛡️ <b>{victim['name']}</b> is protected.")

    try: amt = int(m.text.split()[1])
    except: amt = 1000

    if amt <= 0: return bot.reply_to(m, "❌ Invalid amount.")
    if victim["balance"] <= 0: return bot.reply_to(m, "❌ User is empty.")

    taken = min(amt, victim["balance"])
    robber["balance"] += taken
    victim["balance"] -= taken
    save_db()

    bot.reply_to(
        m,
        f"💸 {mention(r_id, robber['name'])} robbed <b>${taken}</b> from {mention(v_id, victim['name'])}"
    )

@bot.message_handler(commands=['kill'])
def kill(m):
    if eco_locked(): return bot.reply_to(m, "🔒 Economy is locked.")
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")

    k_id, v_id = str(m.from_user.id), str(m.reply_to_message.from_user.id)
    killer = get_user(k_id, m.from_user.first_name)
    victim = get_user(v_id, m.reply_to_message.from_user.first_name)

    if check_death(k_id): return bot.reply_to(m, "💀 You are dead.")
    if check_death(v_id): return bot.reply_to(m, "💀 Victim is already dead.")
    if time.time() < victim["protection"]: return bot.reply_to(m, f"🛡️ <b>{victim['name']}</b> is protected.")

    reward = random.randint(200, 600)
    killer["kills"] += 1
    killer["balance"] += reward
    victim["status"] = "dead"
    victim["death_time"] = time.time()
    save_db()

    bot.reply_to(
        m,
        f"🔪 {mention(k_id, killer['name'])} killed {mention(v_id, victim['name'])}\n"
        f"💰 Earned: <b>${reward}</b>"
    )

@bot.message_handler(commands=['give'])
def give(m):
    if eco_locked(): return bot.reply_to(m, "🔒 Economy is locked.")
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")

    try: amt = int(m.text.split()[1])
    except: return bot.reply_to(m, "❌ Usage: /give <amount>")

    if amt <= 0: return bot.reply_to(m, "❌ Invalid amount.")

    s_id, r_id = str(m.from_user.id), str(m.reply_to_message.from_user.id)
    sender = get_user(s_id, m.from_user.first_name)
    receiver = get_user(r_id, m.reply_to_message.from_user.first_name)

    if sender["balance"] < amt: return bot.reply_to(m, "❌ Not enough balance.")

    sender["balance"] -= amt
    receiver["balance"] += amt
    save_db()

    bot.reply_to(m, f"💸 {mention(s_id, sender['name'])} gave <b>${amt}</b> to {mention(r_id, receiver['name'])}")

@bot.message_handler(commands=['protect'])
def protect(m):
    if eco_locked(): return bot.reply_to(m, "🔒 Economy is locked.")
    uid = str(m.from_user.id)
    u = get_user(uid, m.from_user.first_name)

    if check_death(uid): return bot.reply_to(m, "💀 Dead users cannot buy protection.")

    try: plan = m.text.split()[1].lower()
    except: return bot.reply_to(m, "⚠️ Usage: /protect 1d | 2d | 3d")

    costs = {"1d": 500, "2d": 1000, "3d": 1500}
    durs = {"1d": DAY, "2d": DAY*2, "3d": DAY*3}

    if plan not in costs: return bot.reply_to(m, "❌ Invalid plan.")
    if u["balance"] < costs[plan]: return bot.reply_to(m, "❌ Not enough money.")

    u["balance"] -= costs[plan]
    curr = time.time()
    if u["protection"] > curr: u["protection"] += durs[plan]
    else: u["protection"] = curr + durs[plan]
    save_db()

    bot.reply_to(m, f"🛡️ Protected for <b>{plan}</b>.")

@bot.message_handler(commands=['items', 'shop'])
def shop(m):
    text = "🛒 <b>ITEM SHOP</b>\n\n"
    for k, v in SHOP_ITEMS.items():
        text += f"{v['icon']} <b>{v['name']}</b> — ${v['price']}\n"
    text += "\n🎁 Usage: /gift (reply) itemname"
    bot.reply_to(m, text)

@bot.message_handler(commands=['gift'])
def gift(m):
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to gift.")
    try: item = m.text.split(maxsplit=1)[1].lower()
    except: return bot.reply_to(m, "⚠️ Usage: /gift rose")
    
    key = next((k for k, v in SHOP_ITEMS.items() if k in item or v['name'].lower() in item), None)
    if not key: return bot.reply_to(m, "❌ Item not found.")
    
    s_id, r_id = str(m.from_user.id), str(m.reply_to_message.from_user.id)
    sender = get_user(s_id, m.from_user.first_name)
    rec = get_user(r_id, m.reply_to_message.from_user.first_name)
    
    price = SHOP_ITEMS[key]['price']
    if sender["balance"] < price: return bot.reply_to(m, "❌ Not enough money.")
    
    sender["balance"] -= price
    rec["inventory"][key] = rec["inventory"].get(key, 0) + 1
    save_db()
    bot.reply_to(m, f"🎁 {sender['name']} sent {SHOP_ITEMS[key]['icon']} to {rec['name']}!")

@bot.message_handler(commands=['toprich'])
def toprich(m):
    top = sorted(users.values(), key=lambda x: x["balance"], reverse=True)[:10]
    msg = "🏆 <b>Top Richest:</b>\n"
    for i, u in enumerate(top, 1): msg += f"{i}. {u['name']} — ${u['balance']}\n"
    bot.reply_to(m, msg)

@bot.message_handler(commands=['topkill'])
def topkill(m):
    top = sorted(users.values(), key=lambda x: x["kills"], reverse=True)[:10]
    msg = "💀 <b>Top Killers:</b>\n"
    for i, u in enumerate(top, 1): msg += f"{i}. {u['name']} — {u['kills']} Kills\n"
    bot.reply_to(m, msg)

# =========================================================
# 👑 ADMIN COMMANDS (FIXED)
# =========================================================

@bot.message_handler(commands=['transfer'])
def transfer(m):
    if not is_admin(m.from_user.id): return bot.reply_to(m, "❌ Admin only.")
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    try: amt = int(m.text.split()[1])
    except: return bot.reply_to(m, "❌ Usage: /transfer <amount>")
    
    # Negative amount se paise le sakte hain, positive se de sakte hain
    target = get_user(m.reply_to_message.from_user.id, m.reply_to_message.from_user.first_name)
    target["balance"] += amt
    save_db()
    
    action = "Added" if amt > 0 else "Removed"
    bot.reply_to(m, f"💰 <b>{action} ${abs(amt)}</b> to {target['name']}'s balance.")

@bot.message_handler(commands=['forcerev'])
def forcerev(m):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    target = get_user(m.reply_to_message.from_user.id, m.reply_to_message.from_user.first_name)
    target["status"] = "alive"
    target["death_time"] = 0
    save_db()
    bot.reply_to(m, f"🚑 {target['name']} has been Force Revived!")

@bot.message_handler(commands=['forcekill'])
def forcekill(m):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    target = get_user(m.reply_to_message.from_user.id, m.reply_to_message.from_user.first_name)
    target["status"] = "dead"
    target["death_time"] = time.time()
    save_db()
    bot.reply_to(m, f"☠️ {target['name']} has been Force Killed!")

@bot.message_handler(commands=['giveprot'])
def giveprot(m):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    target = get_user(m.reply_to_message.from_user.id, m.reply_to_message.from_user.first_name)
    target["protection"] = time.time() + (DAY * 2)
    save_db()
    bot.reply_to(m, f"🛡️ Given 2 Days Protection to {target['name']}.")

@bot.message_handler(commands=['breakprot'])
def breakprot(m):
    if not is_admin(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    target = get_user(m.reply_to_message.from_user.id, m.reply_to_message.from_user.first_name)
    target["protection"] = 0
    save_db()
    bot.reply_to(m, f"🛡️ Protection removed from {target['name']}.")

@bot.message_handler(commands=['lockeco'])
def lockeco(m):
    if not is_admin(m.from_user.id): return
    db["eco_lock"] = True
    save_db()
    bot.reply_to(m, "🔒 Economy has been <b>LOCKED</b>.")

@bot.message_handler(commands=['unlockeco'])
def unlockeco(m):
    if not is_admin(m.from_user.id): return
    db["eco_lock"] = False
    save_db()
    bot.reply_to(m, "🔓 Economy has been <b>UNLOCKED</b>.")

@bot.message_handler(commands=['stats'])
def stats(m):
    if not is_admin(m.from_user.id): return
    
    total_users = len(users)
    total_money = sum(u["balance"] for u in users.values())
    
    bot.reply_to(m, f"📊 <b>Bot Stats</b>\n👥 Users: {total_users}\n💰 Economy: ${total_money}")

print("🚀 Miku Bot (Final Fixed) is Running...")
bot.infinity_polling()
