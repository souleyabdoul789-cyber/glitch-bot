from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

CHANNEL_USERNAME = "@glitch_chanel"  # celle qu'il faut rejoindre

async def est_membre(user_id, context):
    try:
        membre = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return membre.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await est_membre(user_id, context):
        await update.message.reply_text("✅ Bienvenue, tu peux utiliser le bot !")
        return

    keyboard = [
        [InlineKeyboardButton("📢 Rejoindre la chaîne", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
        [InlineKeyboardButton("✅ J'ai rejoint", callback_data="verifier")],
    ]
    await update.message.reply_text(
        "Pour utiliser ce bot, rejoins d'abord notre chaîne 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def bouton_clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verifier":
        if await est_membre(query.from_user.id, context):
            await query.edit_message_text("✅ Vérifié ! Tu peux utiliser le bot.")
        else:
            await query.answer("❌ Tu n'as pas encore rejoint la chaîne !", show_alert=True)

