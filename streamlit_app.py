import streamlit as st
import requests
import pandas as pd
import time

# Configuration Settings
BASE_URL = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"
INTERVALS = {
    "5min": "5m",
    "15min": "15m",
    "1hour": "1h"
}

# Streamlit Interface
st.set_page_config(page_title="Crypto Indicator Panel", layout="wide")
st.title("📊 Real-Time Crypto Analysis")
st.markdown("Market data powered by Binance Futures API")

def fetch_data(symbol, interval, limit=200):
    """Fetch data from Binance API"""
    try:
        url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        df = pd.DataFrame(response.json(), columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.set_index('timestamp')
    except Exception as e:
        st.error(f"🔴 Data fetch error: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(df):
    """Calculate technical indicators"""
    # EMAs
    df['EMA_9'] = df['close'].ewm(span=9).mean()
    df['EMA_21'] = df['close'].ewm(span=21).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def main_panel():
    """Main application interface"""
    selected_interval = st.sidebar.selectbox("Time Interval", list(INTERVALS.keys()))
    
    try:
        df = fetch_data(SYMBOL, INTERVALS[selected_interval])
        if not df.empty:
            df = calculate_indicators(df)
            
            # Price Chart
            st.subheader(f"{SYMBOL} Price Action ({selected_interval})")
            st.line_chart(df[['close', 'EMA_9', 'EMA_21']].tail(100))
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Last Price", f"{df['close'].iloc[-1]:,.2f} $")
                st.progress((df['RSI'].iloc[-1]/100))
                st.caption(f"RSI: {df['RSI'].iloc[-1]:.1f}")
                
            with col2:
                st.metric("24h Change", f"{(df['close'].iloc[-1]/df['close'].iloc[-24]-1)*100:.2f}%")
                st.metric("Volume", f"{df['volume'].mean():,.0f} $")
            
            # Auto-refresh
            time.sleep(60)
            st.experimental_rerun()
            
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")

if __name__ == "__main__":
    main_panel()
