import requests
import time
from datetime import datetime
import pytz
import telegram
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COINBASE_ONLY, ALERT_THRESHOLD_PERCENT, MONITOR_INTERVAL_MINUTES, TIMEZONE

bot = telegram.Bot(token=TELEGRAM_TOKEN)

previous_prices = {}

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

                if base in previous_prices:
                    prev = previous_prices[base]
                    change_pct = ((amount - prev) / prev) * 100
                    if abs(change_pct) >= ALERT_THRESHOLD_PERCENT:
                        direction = "📈" if change_pct > 0 else "📉"
                        msg = f"{direction} {now} - {base} ha avuto una variazione del {change_pct:.2f}% ed è ora a {amount} USD."
                        send_alert(msg)

                previous_prices[base] = amount

        time.sleep(MONITOR_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    send_alert("🚀 CryptoScout avviato. Monitoraggio in corso ogni 10 minuti...")
    monitor()
