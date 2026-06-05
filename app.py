import os
import ccxt
import pandas as pd
import urllib.parse
import urllib.request
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8770808986:AAGCkY93I_cEg11CuSmzTa2-sF4aVTrhcQA")
CHAT_ID = "8770808986"
WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
TIMEFRAME = "5m"
# ---------------------

exchange = ccxt.kraken({'rateLimit': 1200, 'enableRateLimit': True})

# Web Server Handler to keep the project alive on cloud platforms
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>SMC 5m Sniper Engine: ONLINE 24/7</h1>")

def start_web_server():
    server = HTTPServer(('0.0.0.0', 8080), WebServer)
    server.serve_forever()

def send_telegram_message(message):
    try:
        encoded_msg = urllib.parse.quote(message)
        url = f"https://telegram.org{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_msg}&parse_mode=Markdown"
        urllib.request.urlopen(url)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scan_market():
    print(f"Scanning market at {pd.Timestamp.now()}...")
    for symbol in WATCHLIST:
        try:
            bars = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 1. Liquidity Sweep Rule (20 candle lookback)
            df['lookback_low'] = df['low'].shift(1).rolling(window=20).min()
            df['sweep'] = (df['low'] < df['lookback_low']) & (df['close'] > df['lookback_low'])
            
            # 2. Fair Value Gap Rule (Imbalance)
            df['fvg'] = df['low'] > df['high'].shift(2)
            
            latest = df.iloc[-1]
            
            if latest['sweep'] and latest['fvg']:
                fvg_min = df['high'].shift(2).iloc[-1]
                fvg_max = latest['low']
                alert_text = (
                    f"🚨 *SMC 5m SNIPER BUY* 🚨\n\n"
                    f"📈 *Pair*: {symbol}\n"
                    f"🎯 *Entry Zone*: {fvg_min:.2f} - {fvg_max:.2f}\n"
                    f"🛑 *Stop Loss*: Below {latest['low']:.2f}"
                )
                send_telegram_message(alert_text)
                print(f"Alert sent for {symbol}!")
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

def background_scanner():
    while True:
        scan_market()
        time.sleep(300) # Loop every 5 minutes

# Start both the web server and market scanner at the same time
if __name__ == "__main__":
    threading.Thread(target=background_scanner, daemon=True).start()
    print("Starting Web Server on port 8080...")
    start_web_server()
