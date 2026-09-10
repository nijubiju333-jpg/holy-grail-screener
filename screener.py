import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime
import time

# Use a fixed path for the cloud database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'screener_results.db')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  stock_symbol TEXT, stock_price REAL, scan_date TEXT,
                  daily_rsi REAL, scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_nse_stocks():
    # Top 50 highly liquid NSE stocks for fast cloud scanning
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 
        'HINDUNILVR.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
        'HCLTECH.NS', 'WIPRO.NS', 'ULTRACEMCO.NS', 'TITAN.NS', 'NESTLEIND.NS',
        'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS',
        'TECHM.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'BAJFINANCE.NS', 'BRITANNIA.NS',
        'CIPLA.NS', 'COALINDIA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS',
        'HEROMOTOCO.NS', 'HINDALCO.NS', 'INDUSINDBK.NS', 'JSWSTEEL.NS', 'LTIM.NS',
        'M&M.NS', 'SHRIRAMFIN.NS', 'TATACONSUM.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS',
        'GODREJCP.NS', 'HAVELLS.NS', 'ICICIPRULI.NS', 'JINDALSTEL.NS', 'ZOMATO.NS'
    ]

def check_rules(df):
    try:
        if len(df) < 50: return False
        today = df.iloc[-1]
        
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        
        if today['Close'] <= ema20 or today['Close'] <= ema50: return False
        if abs((ema20 - ema50) / ema50 * 100) >= 3: return False
        
        sma_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
        if today['Volume'] <= sma_vol * 2: return False
        if (today['Close'] - ema20) / ema20 * 100 >= 3: return False
        
        max_high = df['High'].tail(13).max()
        if today['Close'] <= max_high: return False
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + gain / loss)).iloc[-1]
        
        if rsi <= 55 or rsi >= 60: return False
        
        return True, round(today['Close'], 2), round(rsi, 2)
    except:
        return False

def run_screener():
    print("Starting cloud scan...")
    init_db()
    stocks = get_nse_stocks()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for symbol in stocks:
        try:
            df = yf.download(symbol, period='6mo', progress=False)
            if len(df) == 0: continue
            
            result = check_rules(df)
            if result:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO results (stock_symbol, stock_price, scan_date, daily_rsi) VALUES (?, ?, ?, ?)",
                          (symbol.replace('.NS', ''), result[1], today, result[2]))
                conn.commit()
                conn.close()
                print(f"Found: {symbol}")
        except:
            continue
    print("Scan complete!")
