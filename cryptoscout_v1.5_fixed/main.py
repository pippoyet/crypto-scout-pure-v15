import requests
import time
from datetime import datetime
import pytz
import telegram
from collections import deque
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COINBASE_ONLY, ALERT_THRESHOLD_PERCENT, TIMEZONE

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Salviamo gli ultimi 2 prezzi (cioè 10 minuti fa e ora)
previous_prices = {}  # base: deque(maxlen=2)

def get_coinbase_prices():
    url = "https://api.coinbase.com/v2/prices/USD/spot"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            prices = data.get("data", [])
            if isinstance(prices, dict):
                return [prices]
            return prices
        else:
            print(f"Errore Coinbase: codice {response.status_code}")
            return []
    except Exception as e:
        print(f"Eccezione nel recupero prezzi Coinbase: {e}")
        return []

def send_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Errore nell'invio dell'alert Telegram: {e}")

def monitor():
    global previous_prices
    while True:
        prices = get_coinbase_prices()
        now = datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M')

        if not prices:
            print(f"[{now}] Nessun dato ricevuto.")
            send_alert(f"⚠️ {now} - Nessun dato ricevuto da Coinbase.")
        else:
            for entry in prices:
                base = entry.get("base")
                amount = float(entry.get("amount"))

                # Inizializza la coda se non esiste
                if base not in previous_prices:
                    previous_prices[base] = deque(maxlen=2)

                price_history = previous_prices[base]
                price_history.append(amount)

                if len(price_history) == 2:
                    old_price = price_history[0]
                    change_pct = ((amount - old_price) / old_price) * 100
                    if abs(change_pct) >= ALERT_THRESHOLD_PERCENT:
                        direction = "📈" if change_pct > 0 else "📉"
                        msg = f"{direction} {now} - {base} ha avuto una variazione del {change_pct:.2f}% negli ultimi 10 minuti. Ora a {amount} USD."
                        send_alert(msg)

        time.sleep(5 * 60)  # Monitoraggio ogni 5 minuti

if __name__ == "__main__":
    send_alert("🚀 CryptoScout attivo. Monitoraggio ogni 5 minuti. Alert su variazioni ≥6% in 10 minuti.")
    monitor()
