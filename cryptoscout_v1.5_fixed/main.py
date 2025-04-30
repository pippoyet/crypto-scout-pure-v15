import time
import os
from telegram import Bot

# Legge token e chat ID dalle variabili ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inizializza bot e invia messaggio
bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text="🚀 CryptoScout PURE v1.5 è attivo!")

print("CryptoScout PURE v1.5 avviato")

# Simulazione ciclo monitoraggio ogni 5 minuti
while True:
    msg = f"Esecuzione ciclo alle {time.strftime('%H:%M')}"
    print(msg)
    bot.send_message(chat_id=CHAT_ID, text=msg)
    time.sleep(300)
