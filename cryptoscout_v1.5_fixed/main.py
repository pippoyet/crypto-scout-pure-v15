import requests
import time
from datetime import datetime, timedelta
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ALERT_THRESHOLD_PERCENT, MONITOR_INTERVAL_MINUTES, TIMEZONE

API_URL = "https://api.coinbase.com/v2/prices/{}/spot"
PRODUCTS_URL = "https://api.exchange.coinbase.com/products"

previous_prices = {}
price_history = {}
volume_history = {}

HEADERS = {
    "User-Agent": "CryptoScout PURE v1.5"
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Errore nell'invio del messaggio Telegram:", e)

def get_usdt_pairs():
    response = requests.get(PRODUCTS_URL, headers=HEADERS)
    pairs = response.json()
    return [p['id'] for p in pairs if p['quote_currency'] == 'USDT' and p['base_currency'] not in ['USDT', 'EUR', 'USD']]

def fetch_price(product_id):
    try:
        url = API_URL.format(product_id.replace("-", ""))
        response = requests.get(url, headers=HEADERS)
        price = float(response.json()['data']['amount'])
        return price
    except:
        return None

def fetch_volume(product_id):
    try:
        url = f"https://api.exchange.coinbase.com/products/{product_id}/stats"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        volume = float(data['volume'])
        return volume
    except:
        return 0.0

def monitor():
    pairs = get_usdt_pairs()
    now = datetime.now()

    for pair in pairs:
        price = fetch_price(pair)
        if not price:
            continue

        volume = fetch_volume(pair)
        if pair not in price_history:
            price_history[pair] = []
            volume_history[pair] = []

        price_history[pair].append((now, price))
        volume_history[pair].append((now, volume))

        # Pulisce le entry troppo vecchie (oltre 10 minuti)
        price_history[pair] = [(t, p) for t, p in price_history[pair] if t >= now - timedelta(minutes=10)]
        volume_history[pair] = [(t, v) for t, v in volume_history[pair] if t >= now - timedelta(minutes=10)]

        # Verifica se abbiamo dati di almeno 10 minuti fa
        if len(price_history[pair]) > 1 and price_history[pair][0][0] <= now - timedelta(minutes=10):
            old_price = price_history[pair][0][1]
            change_percent = ((price - old_price) / old_price) * 100

            if abs(change_percent) >= ALERT_THRESHOLD_PERCENT:
                # Volume spike detection
                volumes = [v for _, v in volume_history[pair]]
                if len(volumes) >= 2:
                    avg_volume = sum(volumes[:-1]) / (len(volumes) - 1)
                    if volume > avg_volume * 2:
                        direction = "📈" if change_percent > 0 else "📉"
                        msg = f"{direction} {now.strftime('%H:%M')} - {pair.replace('-USDT', '')} ha avuto una variazione del {change_percent:.2f}% negli ultimi 10 minuti con spike di volume. Ora a {price} USD."
                        send_telegram_message(msg)

if __name__ == "__main__":
    send_telegram_message("📡 CryptoScout PURE v1.5 attivo. Monitoraggio ogni 5 minuti, alert su variazioni >=6% in 10 minuti con volume spike.")
    while True:
        try:
            monitor()
        except Exception as e:
            print("Errore durante il monitoraggio:", e)
        time.sleep(MONITOR_INTERVAL_MINUTES * 60)
