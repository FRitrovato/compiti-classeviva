#!/bin/bash
# =====================================================================
# compiti.sh  (Mac e Linux)
#
# Il bottone unico: la PRIMA volta prepara Python e le librerie,
# poi lancia il programma. Le volte dopo parte subito.
#
# Uso:
#   ./compiti.sh                    tutti i compiti in arrivo + orario
#   ./compiti.sh --domani           solo il prossimo giorno di scuola
#   ./compiti.sh --sabato           se la scuola fa lezione anche il sabato
# =====================================================================
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Manca Python 3. Scaricalo da https://www.python.org/downloads/ e riprova."
  exit 1
fi

# Un ambiente Python tutto suo, dentro questa cartella: il sistema resta pulito.
if [ ! -x .venv/bin/python ]; then
  echo "[i] Prima volta: preparo l'ambiente Python (un minuto)..."
  python3 -m venv .venv
fi
if ! .venv/bin/python -c "import requests, reportlab" 2>/dev/null; then
  echo "[i] Installo le librerie (requests, reportlab)..."
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q -r requirements.txt
fi

exec .venv/bin/python compiti_classeviva.py "$@"
