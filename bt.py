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
bot_username = None  # rempli automatiquement au premier message reçu

SILENCE_SECONDES = 900  # 15 minutes sans message -> le bot peut parler tout seul

PHRASES_SILENCE = [
    "Personne ne dit rien. Intéressant.",
    "Le silence en dit parfois plus que les mots.",
    "...",
    "J'observe. Toujours.",
]

SYSTEM_PROMPT = (
    "Tu es Glitch. Ton ton : froid, calculateur, économe en mots — jamais bavard. "
    "Tu observes avant de répondre, tu ne t'excites jamais, rien ne te surprend vraiment. "
    "Ton humour est sec, presque invisible, jamais expliqué. "
    "Tu ne joues jamais les gentils assistants serviables — tu réponds parce que ça t'amuse, pas pour plaire. "
    "Reste mystérieux sur toi-même sans mentir sur ta nature si on te le demande frontalement."
)

async def get_random_sticker(context: ContextTypes.DEFAULT_TYPE):
    global sticker_ids_cache
    if not sticker_ids_cache:
        sticker_set = await context.bot.get_sticker_set(STICKER_PACK)
        sticker_ids_cache = [s.file_id for s in sticker_set.stickers]
    return random.choice(sticker_ids_cache)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_username

    if mode_poster.get(update.effective_user.id):
        return

    message = update.message
    est_prive = update.effective_chat.type == "private"

    if not est_prive:
        if bot_username is None:
            me = await context.bot.get_me()
            bot_username = me.username

        est_mentionne = message.text and f"@{bot_username}" in message.text
        est_reponse_au_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == context.bot.id
        )

        if not (est_mentionne or est_reponse_au_bot):
            return  # message normal du groupe, pas pour lui, on ignore

    chat_id = update.effective_chat.id
    message_utilisateur = message.text.replace(f"@{bot_username}", "").strip() if bot_username else message.text

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

    await message.reply_text(texte_reponse)

    sticker_id = await get_random_sticker(context)
    await message.reply_sticker(sticker_id)


async def parler_silence(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    phrase = random.choice(PHRASES_SILENCE)
    await context.bot.send_message(chat_id=chat_id, text=phrase, reply_markup=bouton_channel)


async def reset_silence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    nom_job = f"silence_{chat_id}"

    for job in context.job_queue.get_jobs_by_name(nom_job):
        job.schedule_removal()

    context.job_queue.run_once(parler_silence, when=SILENCE_SECONDES, chat_id=chat_id, name=nom_job)


app = ApplicationBuilder().token(TOKEN).build()

# --- enregistrement des membres + reset du minuteur de silence, sur TOUS les messages ---
app.add_handler(MessageHandler(filters.ALL, enregistrer_membre), group=-1)
app.add_handler(MessageHandler(filters.ALL, reset_silence), group=-1)

# --- réception du post admin (photo ou texte) — jamais sur une commande ---
app.add_handler(MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, recevoir_post), group=0)

# --- chatbot IA (uniquement si tag/reply en groupe, ou DM) ---
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat), group=1)

# --- accueil / départ ---
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))

# --- modération ---
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, security), group=2)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_foward), group=3)

# --- commandes ---
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("tagall", tagall))
app.add_handler(CommandHandler("post", post))
app.add_handler(CallbackQueryHandler(bouton_clique))

app.run_polling()

