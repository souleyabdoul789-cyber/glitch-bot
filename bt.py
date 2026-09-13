from flask import Flask, send_file
import threading
import os

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    if os.path.exists("index.html"):
        return send_file('index.html')
    return "Bot ON - index.html manquant"

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask, daemon=True).start()

import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq
from glitch_bot1 import *
from subcribe import *
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
STICKER_PACK = "classroom_by_pinterest_to_stickerbot"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
sticker_ids_cache = []
historique = {}

SYSTEM_PROMPT = (
    "Tu t'appelles glitch, un  mec sympa et Cool, répond pas comme une IA répond comme un humain  "
    "Tu réponds court, avec aura, en français. "
    "Tu reste froid et courte, pas de gros discours des mot claire sans vague, reste froid comme kyotaka ayanokoji"
    "Aprend des humain, Aprend de leurs reponses, cherche a comprendre si t'a pas compris un mot, t'a aissi le droit de comprendre, nourit toi de savoir, reste froid"
    "utulise pas des emoji de humeur, des fleurs,humain,Maison,tasse de the.. "
)

async def get_random_sticker(context: ContextTypes.DEFAULT_TYPE):
    global sticker_ids_cache
    if not sticker_ids_cache:
        sticker_set = await context.bot.get_sticker_set(STICKER_PACK)
        sticker_ids_cache = [s.file_id for s in sticker_set.stickers]
    return random.choice(sticker_ids_cache)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if mode_poster.get(update.effective_user.id):
        return  # en train de poster dans la chaîne, le chatbot se tait

    chat_id = update.effective_chat.id
    message_utilisateur = update.message.text

    if chat_id not in historique:
        historique[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    historique[chat_id].append({"role": "user", "content": message_utilisateur})

    reponse = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=historique[chat_id]
    )
    texte_reponse = reponse.choices[0].message.content

    historique[chat_id].append({"role": "assistant", "content": texte_reponse})

    if len(historique[chat_id]) > 21:
        historique[chat_id] = [historique[chat_id][0]] + historique[chat_id][-20:]

    await update.message.reply_text(texte_reponse)

    sticker_id = await get_random_sticker(context)
    await update.message.reply_sticker(sticker_id)

app = ApplicationBuilder().token(TOKEN).build()

# --- enregistrement des membres, pour /tagall (doit tourner sur TOUS les messages) ---
app.add_handler(MessageHandler(filters.ALL, enregistrer_membre), group=-1)

# --- réception du post admin (photo ou texte), avant le chatbot ---
app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, recevoir_post), group=0)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat), group=1)
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, security), group=2)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_foward), group=3)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("tagall", tagall))
app.add_handler(CommandHandler("post", post))
app.add_handler(CallbackQueryHandler(bouton_clique))

app.run_polling()

