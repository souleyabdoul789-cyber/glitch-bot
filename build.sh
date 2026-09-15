#!/usr/bin/env bash
set -e

echo "=== Installation de ffmpeg (binaire statique) ==="

FFMPEG_DIR="$HOME/ffmpeg-bin"
mkdir -p "$FFMPEG_DIR"

# Télécharge un build statique ffmpeg (amd64, pas de dépendances système)
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz

tar -xf /tmp/ffmpeg.tar.xz -C /tmp

# Le dossier extrait a un nom versionné (ex: ffmpeg-7.0.2-amd64-static), on le retrouve dynamiquement
FFMPEG_EXTRACTED=$(find /tmp -maxdepth 1 -type d -name "ffmpeg-*-amd64-static")

cp "$FFMPEG_EXTRACTED/ffmpeg" "$FFMPEG_DIR/ffmpeg"
cp "$FFMPEG_EXTRACTED/ffprobe" "$FFMPEG_DIR/ffprobe"
chmod +x "$FFMPEG_DIR/ffmpeg" "$FFMPEG_DIR/ffprobe"

echo "ffmpeg installé dans $FFMPEG_DIR"
"$FFMPEG_DIR/ffmpeg" -version | head -n 1

echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt

