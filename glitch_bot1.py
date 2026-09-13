from telegram import InlineKeyboardButton,ChatPermissions, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,MessageHandler,ContextTypes,filters
import asyncio
from telegram.ext import ChatMemberHandler
from datetime import datetime, timedelta

CHANEL = "https://t.me/glitch_chanel"
chaine = "@glitch_channel"
id = 8350799876
TOKEN = "8504399293:AAEIlvbiNw0AiGdOkCp5KUH14B02bM997xU"
bouton_channel = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌸 GLITCH CHANNEL", url=CHANEL)]
])
vt = {}
async def welcome(upd: Update, ctn:ContextTypes.DEFAULT_TYPE):
    user = upd.effective_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    nombre_membres = await ctn.bot.get_chat_member_count(chat_id=upd.effective_chat.id)
    for member in upd.message.new_chat_members:
        await upd.message.reply_text(f"""BIENVENUE {mention} DANS {upd.effective_chat.title} avec {nombre_membres} Membres""",reply_markup=bouton_channel)
        
async def goodbye(upd: Update, ctn:ContextTypes.DEFAULT_TYPE):
    gb = upd.message.left_chat_member
    await upd.message.reply_text(f"Nous Sommes Ravie de Faire Ta connaissance By {gb.first_name}",reply_markup=bouton_channel)
async def security(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    user = upd.effective_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    msg = upd.message.text
    link = ["http://","https://","t.me/"]
    for l in link:
        if l in msg:
            try:
                fin_mute = datetime.now() + timedelta(hours=1)
                await ctn.bot.delete_message(chat_id=upd.effective_chat.id,message_id=upd.message.message_id)
                await ctn.bot.restrict_chat_member(chat_id=upd.effective_chat.id,user_id=upd.effective_user.id,permissions=ChatPermissions(can_send_messages=False),until_date=fin_mute)
                await upd.message.reply_text(f"{mention} Les Liens ne sont pas autorises dans ce groupe, Vous pouvez plus envoyez de message jusqu'au {fin_mute}",reply_markup=bouton_channel)
            except:
                pass

async def kick(upd: Update,ctn: ContextTypes.DEFAULT_TYPE):
    if not upd.message.reply_to_message:
        await upd.message.reply_text("Repond au message de la personne avec /kick",reply_markup=bouton_channel)
        return
    cible = upd.message.reply_to_message.from_user
    chat_id=upd.effective_chat.id
    try:
        await ctn.bot.ban_chat_member(chat_id=chat_id,user_id=cible.id)
        await upd.message.reply_text(f"{cible.first_name} à été suprimé",reply_markup=bouton_channel)
    except:
        await upd.message.reply_text("Met Moi admin pour pouvoir kick ce user",reply_markup=bouton_channel)

async def anti_foward(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    if upd.message.forward_origin:
        user = upd.effective_user
        current = vt.get(user.id,0) + 1 
    
        try:
            await ctn.bot.delete_message(chat_id=upd.effective_chat.id,
                             message_id=upd.message.message_id)
        except:
            pass
        current = vt.get(user.id,0) + 1 
        vt[user.id] = current
        nombre_avertisse = vt.get(user.id)
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
        await ctn.bot.send_message(chat_id=upd.effective_chat.id,
                               text=f"⚠️ {mention}, le partage de messages transférés n'est pas autorisé ici avertissements {nombre_avertisse}/3.",
                               reply_markup=bouton_channel)
        if current >= 3:
            fin_mute = datetime.now() + timedelta(hours=1)
            await ctn.bot.restrict_chat_member(chat_id=upd.effective_chat.id,user_id=user.id,permissions=ChatPermissions(can_send_messages=False),until_date=fin_mute)


