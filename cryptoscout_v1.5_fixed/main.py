# main.py — CryptoScout PURE v1.5

import requests
import time
import os
from datetime import datetime, timezone, timedelta
from telegram import Bot

# Configurazioni personalizzate
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=token)

ALERT_THRESHOLD = 6.0  # percentuale
CHECK_INTERVAL = 300  # ogni 5 minuti
COINBASE_API = "https://api.pro.coinbase.com/products"
MARKET_CAP_API = "https://api.coingecko.com/api/v3/coins/markets"
COINBASE_BASE = "https://www.coinbase.com/price/"

# Cache dei prezzi precedenti
last_prices = {}

# Affidabilità stimata per capitalizzazione

def get_reliability(market_cap):
    if market_cap >= 10_000_000_000:
        return "Alta"
    elif market_cap >= 1_000_000_000:
        return "Media"
    else:
        return "Bassa"


def fetch_coinbase_pairs():
    res = requests.get(COINBASE_API)
    return [p['id'] for p in res.json() if p['quote_currency'] == 'USD']


def fetch_market_data():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False
    }
    res = requests.get(MARKET_CAP_API, params=params)
    return {coin['symbol'].upper(): coin for coin in res.json()}


def format_alert(symbol, name, variation, volume_change, reliability):
    url = f"{COINBASE_BASE}{symbol.lower()}"
    return (f"\n🚨 CryptoScout PURE v1.5 — Opportunità individuata"
            f"\n\n🪙 Criptovaluta: {name} ({symbol})"
            f"\n📈 Variazione 5min: +{variation:.2f}%"
            f"\n📊 Volume spike: +{volume_change:.1f}%"
            f"\n✅ Affidabilità: {reliability}"
            f"\n🕒 Orario: {datetime.now(timezone.utc).astimezone(tz=timezone(timedelta(hours=2))).strftime('%H:%M')} CET"
            f"\n\n📎 Link: {url}")


def monitor():
    coinbase_ids = fetch_coinbase_pairs()
    market_data = fetch_market_data()

    for product_id in coinbase_ids:
        try:
            res = requests.get(f"https://api.pro.coinbase.com/products/{product_id}/ticker")
            ticker = res.json()
            symbol = product_id.split("-")[0]
            price = float(ticker['price'])
            volume = float(ticker['volume'])

            # Calcolo variazione prezzo
            if symbol not in last_prices:
                last_prices[symbol] = (price, volume)
                continue

            old_price, old_volume = last_prices[symbol]
            variation = ((price - old_price) / old_price) * 100
            volume_change = ((volume - old_volume) / old_volume) * 100 if old_volume > 0 else 0
            last_prices[symbol] = (price, volume)

            # Check soglia
            if variation >= ALERT_THRESHOLD and volume_change > 50:
                if symbol in market_data:
                    info = market_data[symbol]
                    name = info['name']
                    market_cap = info['market_cap'] or 0
                    reliability = get_reliability(market_cap)
                    alert = format_alert(symbol, name, variation, volume_change, reliability)
                    bot.send_message(chat_id=chat_id, text=alert)
        except Exception as e:
            print(f"Errore su {product_id}: {e}")


if __name__ == "__main__":
    bot.send_message(chat_id=chat_id, text="🚀 CryptoScout PURE v1.5 attivo e in ascolto su Coinbase.")
    while True:
        monitor()
        time.sleep(CHECK_INTERVAL)
