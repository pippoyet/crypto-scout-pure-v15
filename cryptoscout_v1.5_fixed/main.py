import requests
import time
from datetime import datetime
import pytz
import telegram
from collections import deque
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, COINBASE_ONLY, ALERT_THRESHOLD_PERCENT, TIMEZONE

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Salviamo gli ultimi 2 prezzi e volumi per ogni coin
previous_data = {}  # base: deque(maxlen=2)

COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"

# Mappa simboli per nomi e market cap
market_info = {}

def update_market_info():
    try:
        response = requests.get(COINGECKO_API, params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': 'false'
        })
        data = response.json()
        for coin in data:
            market_info[coin['symbol'].upper()] = {
                'name': coin['name'],
                'market_cap': coin.get('market_cap', 0)
            }
    except Exception as e:
        print(f"Errore aggiornamento info CoinGecko: {e}")

def get_reliability(market_cap):
    if market_cap >= 10_000_000_000:
        return "Alta"
    elif market_cap >= 1_000_000_000:
        return "Media"
    else:
        return "Bassa"

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

def send_alert(symbol, name, amount, change_pct, volume_change, reliability, now):
    direction = "📈" if change_pct > 0 else "📉"
    msg = (
        f"🚨 CryptoScout PURE v1.5 — Opportunità individuata\n\n"
        f"🪙 Criptovaluta: {name} ({symbol})\n"
        f"📈 Variazione 10min: {change_pct:.2f}%\n"
        f"📊 Volume spike: {volume_change:.1f}%\n"
        f"✅ Affidabilità: {reliability}\n"
        f"🕒 Orario: {now} CET\n\n"
        f"📎 https://www.coinbase.com/price/{symbol.lower()}"
    )
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Errore nell'invio dell'alert Telegram: {e}")

def monitor():
    global previous_data
    update_market_info()

    while True:
        prices = get_coinbase_prices()
        now = datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M')

        if not prices:
            print(f"[{now}] Nessun dato ricevuto.")
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⚠️ {now} - Nessun dato ricevuto da Coinbase.")
        else:
            for entry in prices:
                base = entry.get("base")
                amount = float(entry.get("amount"))
                volume = float(entry.get("volume", 0))

                if base not in previous_data:
                    previous_data[base] = deque(maxlen=2)

                data_history = previous_data[base]
                data_history.append((amount, volume))

                if len(data_history) == 2:
                    old_price, old_volume = data_history[0]
                    change_pct = ((amount - old_price) / old_price) * 100
                    volume_change = ((volume - old_volume) / old_volume) * 100 if old_volume > 0 else 0

                    if change_pct >= ALERT_THRESHOLD_PERCENT and volume_change > 50:
                        symbol = base
                        info = market_info.get(symbol, {})
                        name = info.get('name', symbol)
                        market_cap = info.get('market_cap', 0)
                        reliability = get_reliability(market_cap)
                        send_alert(symbol, name, amount, change_pct, volume_change, reliability, now)

        time.sleep(5 * 60)

if __name__ == "__main__":
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🚀 CryptoScout PURE v1.5 avviato. Monitoraggio ogni 5 minuti, alert su variazioni >=6% in 10 minuti con volume spike.")
    monitor()
