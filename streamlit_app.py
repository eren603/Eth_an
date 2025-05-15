import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
REFRESH_INTERVAL = 30  # Seconds
WINDOW_SIZES = [5, 10, 14, 20, 26, 50, 100, 200]  # Multiple timeframes

def fetch_real_time_data():
    """Fetch comprehensive market data from CoinGecko API"""
    try:
        # Real-time data with multiple metrics
        url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=14&interval=hourly"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return {
            'prices': data.get('prices', []),
            'volumes': data.get('total_volumes', [])
        }
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return None

def calculate_indicators(df):
    """Calculate 26+ technical indicators using pure pandas"""
    # Price transformations
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['Weighted_Close'] = (df['close'] * 2 + df['high'] + df['low']) / 4
    
    # Momentum Indicators
    for period in [14, 20]:
        df[f'RSI_{period}'] = 100 - (100 / (1 + (df['close'].diff().apply(lambda x: x if x > 0 else 0).rolling(period).mean() / 
                                       df['close'].diff().apply(lambda x: -x if x < 0 else 0).rolling(period).mean()))
    
    # Trend Indicators
    for period in WINDOW_SIZES:
        df[f'SMA_{period}'] = df['close'].rolling(period).mean()
        df[f'EMA_{period}'] = df['close'].ewm(span=period).mean()
        df[f'WMA_{period}'] = df['close'].rolling(period).apply(lambda x: np.dot(x, np.arange(1, period+1))/np.sum(np.arange(1, period+1))
    
    # Volatility Indicators
    df['ATR'] = df['high'].combine(df['low'], np.maximum) - df['high'].combine(df['low'], np.minimum)
    for period in [14, 20]:
        df[f'Bollinger_Upper_{period}'] = df[f'SMA_{period}'] + (2 * df['close'].rolling(period).std())
        df[f'Bollinger_Lower_{period}'] = df[f'SMA_{period}'] - (2 * df['close'].rolling(period).std())
    
    # Volume Indicators
    df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['VWAP'] = (df['volume'] * df['Typical_Price']).cumsum() / df['volume'].cumsum()
    
    # Cycle Indicators
    df['HILO'] = (df['high'] + df['low']) / 2
    df['CMF'] = (df['close'] - df['low']) / (df['high'] - df['low']) * df['volume']
    
    # Other Indicators
    df['Momentum'] = df['close'].diff(4)
    df['ROC'] = df['close'].pct_change(12)*100
    df['Williams_%R'] = (df['high'].rolling(14).max() - df['close']) / (df['high'].rolling(14).max() - df['low'].rolling(14).min()) * -100
    
    return df.dropna()

def create_dashboard():
    """Professional trading dashboard layout"""
    st.set_page_config(layout="wide", page_title="Pro Crypto Dashboard", page_icon="₿")
    st.title("💰 Real-Time Cryptocurrency Analysis Dashboard")
    
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            data = fetch_real_time_data()
            
            if data and len(data['prices']) > 200:
                df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Add OHLC data approximation
                df['open'] = df['close'].shift()
                df['high'] = df[['open', 'close']].max(axis=1)
                df['low'] = df[['open', 'close']].min(axis=1)
                df['volume'] = pd.DataFrame(data['volumes'], columns=['timestamp', 'volume'])['volume']
                
                df = calculate_indicators(df)
                latest = df.iloc[-1]
                
                # Real-time metrics
                cols = st.columns(4)
                metrics = [
                    ("Price", f"${latest['close']:,.2f}", "Current market price"),
                    ("24h Change", f"{df['close'].pct_change(24).iloc[-1]*100:.2f}%", "24-hour percentage change"),
                    ("RSI (14)", f"{latest['RSI_14']:.1f}", "Relative Strength Index"),
                    ("VWAP", f"${latest['VWAP']:,.2f}", "Volume Weighted Average Price")
                ]
                
                for col, (title, value, help_text) in zip(cols, metrics):
                    with col:
                        st.metric(title, value, help=help_text)
                
                # Interactive charts
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Price & Moving Averages")
                    st.line_chart(df[['close', 'SMA_50', 'EMA_20']].tail(100))
                
                with col2:
                    st.subheader("Momentum Indicators")
                    st.line_chart(df[['RSI_14', 'Williams_%R']].tail(100))
                
                # Data table
                st.subheader("Technical Indicators")
                st.dataframe(df.tail(10).style.format({
                    'close': "${:,.2f}",
                    'VWAP': "${:,.2f}",
                    'RSI_14': "{:.1f}",
                    'Bollinger_Upper_20': "${:,.2f}"
                }))
                
                st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
            time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    create_dashboard()
