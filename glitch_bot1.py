from telegram import InlineKeyboardButton, ChatPermissions, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
from telegram.constants import ParseMode

HTML = ParseMode.HTML
CHANEL = "https://t.me/glitch_chanel"       # lien cliquable, pour les boutons
chaine = "@glitch_channel"                   # identifiant, pour les appels API (poster, vérifier admin)

bouton_channel = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌸 GLITCH CHANNEL", url=CHANEL)]
])

vt = {}                  # avertissements anti-forward {user_id: nombre}
membres_connus = {}      # {chat_id: {user_id: prenom}} pour /tagall
mode_poster = {}         # {user_id: True/False} pour le post admin dans la chaîne


async def welcome(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    nombre_membres = await ctn.bot.get_chat_member_count(chat_id=upd.effective_chat.id)
    for member in upd.message.new_chat_members:
        mention = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        await upd.message.reply_text(
            f"BIENVENUE {mention} DANS <b>{upd.effective_chat.title}</b> avec <b>{nombre_membres}</b> Membres\n\nMerci, n'oublie pas de t'abonner",
            parse_mode=HTML,
            reply_markup=bouton_channel
        )


async def goodbye(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    gb = upd.message.left_chat_member
    mention = f'<a href="tg://user?id={gb.id}">{gb.first_name}</a>'
    await upd.message.reply_text(
        f"Nous sommes ravis d'avoir fait ta connaissance, au revoir {mention}\nAbonne toi à la chaîne",
        parse_mode=HTML,
        reply_markup=bouton_channel
    )


async def security(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    if mode_poster.get(upd.effective_user.id):
        return

    user = upd.effective_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    msg = upd.message.text
    liens = ["http://", "https://", "t.me/"]
    for l in liens:
        if l in msg:
            try:
                fin_mute = datetime.now() + timedelta(hours=1)
                await ctn.bot.delete_message(chat_id=upd.effective_chat.id, message_id=upd.message.message_id)
                await ctn.bot.restrict_chat_member(
                    chat_id=upd.effective_chat.id,
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=fin_mute
                )
                await upd.message.reply_text(
                    f"{mention} Les Liens ne sont pas autorises dans ce groupe, Vous pouvez plus envoyez de message jusqu'au {fin_mute}",
                    parse_mode=HTML,
                    reply_markup=bouton_channel
                )
            except Exception:
                pass
            return


async def kick(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    if not upd.message.reply_to_message:
        await upd.message.reply_text("Repond au message de la personne avec /kick", reply_markup=bouton_channel)
        return
    cible = upd.message.reply_to_message.from_user
    chat_id = upd.effective_chat.id
    try:
        await ctn.bot.ban_chat_member(chat_id=chat_id, user_id=cible.id)
        await upd.message.reply_text(f"{cible.first_name} à été suprimé", reply_markup=bouton_channel)
    except Exception:
        await upd.message.reply_text("Met Moi admin pour pouvoir kick ce user", reply_markup=bouton_channel)


async def anti_foward(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    if upd.effective_user.id == 777000:
        return  # message auto de la chaîne liée, pas un vrai forward

    if mode_poster.get(upd.effective_user.id):
        return

    if upd.message.forward_origin:
        user = upd.effective_user
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

        try:
            await ctn.bot.delete_message(chat_id=upd.effective_chat.id, message_id=upd.message.message_id)
        except Exception:
            pass

        current = vt.get(user.id, 0) + 1
        vt[user.id] = current

        await ctn.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=f"⚠️ {mention}, le partage de messages transférés n'est pas autorisé ici. Avertissement {current}/3.",
            parse_mode=HTML,
            reply_markup=bouton_channel
        )

        if current >= 3:
            fin_mute = datetime.now() + timedelta(hours=1)
            await ctn.bot.restrict_chat_member(
                chat_id=upd.effective_chat.id,
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=fin_mute
            )
            await ctn.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f"{mention} Vous Avez enfreins les regles de ce groupe vous pouvez plus Envoyé de messsage jusqu'à {fin_mute}",
                parse_mode=HTML,
                reply_markup=bouton_channel
            )


# ---------- TAG ALL ----------

async def enregistrer_membre(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    if not upd.effective_user or not upd.effective_chat:
        return
    chat_id = upd.effective_chat.id
    user = upd.effective_user

    if chat_id not in membres_connus:
        membres_connus[chat_id] = {}
    membres_connus[chat_id][user.id] = user.first_name


async def tagall(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    chat_id = upd.effective_chat.id

    if chat_id not in membres_connus or not membres_connus[chat_id]:
        await upd.message.reply_text("Aucun membre enregistré pour l'instant.", reply_markup=bouton_channel)
        return

    mentions = [
        f'<a href="tg://user?id={uid}">{prenom}</a>'
        for uid, prenom in membres_connus[chat_id].items()
    ]
    texte = "📢 " + " ".join(mentions)

    await upd.message.reply_text(texte, parse_mode=HTML, reply_markup=bouton_channel)


# ---------- POST ADMIN DANS LA CHAÎNE ----------

async def post(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    user_id = upd.effective_user.id
    try:
        membre = await ctn.bot.get_chat_member(chat_id=chaine, user_id=user_id)
    except Exception:
        await upd.message.reply_text(
            "Impossible de vérifier ton statut admin (vérifie que le bot est bien admin de la chaîne).",
            reply_markup=bouton_channel
        )
        return

    if membre.status not in ("administrator", "creator"):
        await upd.message.reply_text("Tu dois être admin de la chaîne pour poster.", reply_markup=bouton_channel)
        return

    mode_poster[user_id] = True
    await upd.message.reply_text("Envoie-moi la photo (avec légende) ou le texte à poster dans la chaîne.")


async def recevoir_post(upd: Update, ctn: ContextTypes.DEFAULT_TYPE):
    user_id = upd.effective_user.id
    if not mode_poster.get(user_id):
        return

    message = upd.message

    if message.photo:
        await ctn.bot.send_photo(
            chat_id=chaine,
            photo=message.photo[-1].file_id,
            caption=message.caption or "",
            reply_markup=bouton_channel
        )
    elif message.text:
        await ctn.bot.send_message(chat_id=chaine, text=message.text, reply_markup=bouton_channel)

    mode_poster[user_id] = False
    await message.reply_text("✅ Posté dans la chaîne.")

