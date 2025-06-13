import os
import requests
import telebot
from flask import Flask, request

# قراءة التوكنات من متغيرات البيئة
BS_API_TOKEN = os.environ['BS_API_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {BS_API_TOKEN}"
}

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def get_full_brawl_data(player_tag):
    tag = player_tag.replace("#", "").upper()
    resp = requests.get(f"https://api.brawlstars.com/v1/players/%23{tag}", headers=HEADERS)
    if resp.status_code != 200:
        return f"❌ Player not found. Code: {resp.status_code}", None
    data = resp.json()
    name = data.get("name", "Unknown")
    trophies = data.get("trophies", "?")
    highest = data.get("highestTrophies", "?")
    exp = data.get("expLevel", "?")
    tag = data.get("tag", "?")
    club = data.get("club", {}).get("name", "No Club")
    xp = data.get("expPoints", 0)
    solo = data.get("soloVictories", 0)
    duo = data.get("duoVictories", 0)
    team = data.get("3vs3Victories", 0)
    brawlers = data.get("brawlers", [])
    msg = (
        f"👤 Name: {name}\n"
        f"🏷️ Tag: {tag}\n"
        f"📈 Level: {exp} - XP: {xp}\n"
        f"🎖️ Trophies: {trophies} / Highest: {highest}\n"
        f"🏡 Club: {club}\n"
        f"🏆 Wins:\n• Solo: {solo}\n• Duo: {duo}\n• 3v3: {team}\n"
        f"🔫 Total Brawlers: {len(brawlers)}"
    )
    brawler_info = "\n".join(
        f"• {b.get('name','?')} - 🔋 Power {b.get('power','?')} | 🏅 Rank {b.get('rank','?')} | 🏆 {b.get('trophies','?')}"
        for b in brawlers
    )
    return msg, brawler_info

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.reply_to(
        m, f"👋 Hello {m.from_user.first_name}!\nSend me a player ID (e.g. #8PCLLYJU) and I'll show their stats!"
    )

@bot.message_handler(func=lambda m: True)
def handle_tag(m):
    tag = m.text.strip()
    if not tag.startswith("#"):
        tag = "#" + tag
    bot.reply_to(m, "⏳ Fetching data...")
    main, brawlers = get_full_brawl_data(tag)
    if not brawlers:
        bot.reply_to(m, main)
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔫 Show Brawlers", callback_data="show"))
    bot.send_message(m.chat.id, main, reply_markup=markup)
    bot.b_cache = brawlers

@bot.callback_query_handler(lambda c: c.data=="show")
def show_callback(c):
    info = getattr(bot, "b_cache", "❌ No data.")
    bot.send_message(c.message.chat.id, f"🧱 Brawlers:\n{info}")

@app.route(f"/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def home():
    return "Bot is live!"

if __name__ == "__main__":
    url = os.environ['REPLIT_URL']
    bot.remove_webhook()
    bot.set_webhook(url=f"{url}/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=3000)
