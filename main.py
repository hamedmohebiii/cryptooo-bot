import os
import time
import requests
import ccxt
import pandas as pd
import pandas_ta as ta

# دریافت اطلاعات حساس از تنظیمات سرور
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# اتصال به صرافی بایننس
exchange = ccxt.binance({
    'enableRateLimit': True,
})

# لیست ارزها
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 
    'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 
    'LINK/USDT', 'DOT/USDT', 'NEAR/USDT', 'SUI/USDT'
]

TIMEFRAME = '15m'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_signals():
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            df['ema9'] = ta.ema(df['close'], length=9)
            df['ema25'] = ta.ema(df['close'], length=25)
            
            prev_candle = df.iloc[-2]
            before_prev_candle = df.iloc[-3]
            
            # تقاطع رو به بالا (BUY / LONG)
            if (before_prev_candle['ema9'] <= before_prev_candle['ema25']) and (prev_candle['ema9'] > prev_candle['ema25']):
                entry_price = prev_candle['close']
                stop_loss = prev_candle['ema9']
                
                if stop_loss >= entry_price:
                    stop_loss = entry_price * 0.995
                
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * 2)
                
                msg = (
                    f"🟢 **سیگنال خرید (LONG)**\n\n"
                    f"🪙 **جفت‌ارز:** {symbol}\n"
                    f"⏱ **تایم‌فریم:** {TIMEFRAME}\n"
                    f"📍 **قیمت ورود:** `{entry_price:.4f}`\n"
                    f"🛑 **حد ضرر (SL):** `{stop_loss:.4f}`\n"
                    f"🎯 **حد سود (TP R:R 2):** `{take_profit:.4f}`\n\n"
                    f"⚠️ *مدیریت سرمایه را رعایت کنید.*"
                )
                send_telegram_message(msg)
                
            # تقاطع رو به پایین (SELL / SHORT)
            elif (before_prev_candle['ema9'] >= before_prev_candle['ema25']) and (prev_candle['ema9'] < prev_candle['ema25']):
                entry_price = prev_candle['close']
                stop_loss = prev_candle['ema9']
                
                if stop_loss <= entry_price:
                    stop_loss = entry_price * 1.005
                
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * 2)
                
                msg = (
                    f"🔴 **سیگنال فروش (SHORT)**\n\n"
                    f"🪙 **جفت‌ارز:** {symbol}\n"
                    f"⏱ **تایم‌فریم:** {TIMEFRAME}\n"
                    f"📍 **قیمت ورود:** `{entry_price:.4f}`\n"
                    f"🛑 **حد ضرر (SL):** `{stop_loss:.4f}`\n"
                    f"🎯 **حد سود (TP R:R 2):** `{take_profit:.4f}`\n\n"
                    f"⚠️ *مدیریت سرمایه را رعایت کنید.*"
                )
                send_telegram_message(msg)

        except Exception as e:
            print(f"Error checking {symbol}: {e}")

if __name__ == "__main__":
    send_telegram_message("🤖 **ربات معامله‌گر با موفقیت فعال شد و بازار را رصد می‌کند.**")
    while True:
        check_signals()
        time.sleep(60)
