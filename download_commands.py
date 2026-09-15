import os
import logging
import asyncio
import functools
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE_MB = 50

# Chemin du ffmpeg statique installé par build.sh (voir README)
FFMPEG_LOCATION = os.path.expanduser("~/ffmpeg-bin")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logger = logging.getLogger(__name__)


def _download(url: str, audio_only: bool):
    outtmpl = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

    if os.path.isdir(FFMPEG_LOCATION):
        ydl_opts["ffmpeg_location"] = FFMPEG_LOCATION

    if audio_only:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[height<=720][filesize<50M]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if audio_only:
            base, _ = os.path.splitext(filename)
            filename = base + ".mp3"

        return filename, info.get("title", "Sans titre")


async def download_async(url: str, audio_only: bool):
    loop = asyncio.get_event_loop()
    func = functools.partial(_download, url, audio_only)
    return await loop.run_in_executor(None, func)


async def _handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE, audio_only: bool):
    if not context.args:
        cmd = "/play" if audio_only else "/video"
        await update.message.reply_text(f"Utilisation : {cmd} <lien>")
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Téléchargement en cours...")

    try:
        filepath, title = await download_async(url, audio_only)

        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            await status_msg.edit_text(
                f"❌ Fichier trop volumineux ({size_mb:.1f} Mo). "
                f"Limite Telegram : {MAX_FILE_SIZE_MB} Mo."
            )
            os.remove(filepath)
            return

        await status_msg.edit_text("📤 Envoi en cours...")

        with open(filepath, "rb") as f:
            if audio_only:
                await update.message.reply_audio(audio=f, title=title)
            else:
                await update.message.reply_video(video=f, caption=title)

        await status_msg.delete()
        os.remove(filepath)

    except yt_dlp.utils.DownloadError:
        await status_msg.edit_text("❌ Impossible de télécharger ce lien (invalide ou non supporté).")
    except Exception as e:
        logger.error(f"Erreur téléchargement: {e}")
        await status_msg.edit_text(f"❌ Une erreur est survenue : {e}")


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_download(update, context, audio_only=True)


async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_download(update, context, audio_only=False)

