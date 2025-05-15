import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import talib
from datetime import datetime

# API Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
DAYS = 365  # 1 year of historical data

def fetch_coingecko_data():
    """Fetch cryptocurrency data from CoinGecko API"""
    try:
        url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days={DAYS}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def calculate_technical_indicators(df):
    """Calculate technical indicators using TA-Lib"""
    closes = df['price'].values
    
    # Moving Averages
    df['SMA_20'] = talib.SMA(closes, timeperiod=20)
    df['EMA_50'] = talib.EMA(closes, timeperiod=50)
    
    # Oscillators
    df['RSI_14'] = talib.RSI(closes, timeperiod=14)
    
    # MACD
    macd, signal, _ = talib.MACD(closes, 
                                fastperiod=12, 
                                slowperiod=26, 
                                signalperiod=9)
    df['MACD'] = macd
    df['Signal'] = signal
    
    # Bollinger Bands
    upper, middle, lower = talib.BBANDS(closes, 
                                       timeperiod=20, 
                                       nbdevup=2, 
                                       nbdevdn=2)
    df['BB_Upper'] = upper
    df['BB_Middle'] = middle
    df['BB_Lower'] = lower
    
    return df.dropna()

# Streamlit Interface Configuration
st.set_page_config(page_title="Crypto Technical Analysis Dashboard", layout="wide")
st.title("📈 Advanced Cryptocurrency Analysis")
st.markdown("""
**Data Source:** CoinGecko API | **Technical Indicators:** SMA, EMA, RSI, MACD, Bollinger Bands
""")

# Data Processing
raw_data = fetch_coingecko_data()

if raw_data:
    prices = raw_data.get('prices', [])
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df = calculate_technical_indicators(df)
    
    # Latest Values
    latest = df.iloc[-1]
    
    # Key Metrics Display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${latest['price']:,.2f}")
    with col2:
        st.metric("RSI (14)", f"{latest['RSI_14']:.1f}")
    with col3:
        st.metric("MACD", f"{latest['MACD']:.2f}")
    with col4:
        st.metric("EMA 50", f"${latest['EMA_50']:,.2f}")
    
    # Price and Bollinger Bands Chart
    st.subheader("Price Action with Bollinger Bands")
    fig1, ax1 = plt.subplots(figsize=(14, 5))
    ax1.plot(df.index, df['price'], label='Price', color='#1f77b4')
    ax1.plot(df.index, df['BB_Upper'], linestyle='--', color='#ff7f0e', label='Upper Band')
    ax1.plot(df.index, df['BB_Lower'], linestyle='--', color='#ff7f0e', label='Lower Band')
    ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='orange')
    ax1.set_title("Price with Bollinger Bands")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Price (USD)")
    ax1.legend()
    st.pyplot(fig1)
    
    # MACD and RSI Chart
    st.subheader("Momentum Indicators")
    fig2, (ax2, ax3) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    ax2.plot(df.index, df['MACD'], label='MACD', color='green')
    ax2.plot(df.index, df['Signal'], label='Signal Line', color='red')
    ax2.set_title("MACD (12,26,9)")
    ax2.legend()
    
    ax3.plot(df.index, df['RSI_14'], label='RSI 14', color='purple')
    ax3.axhline(30, linestyle='--', color='gray', alpha=0.5)
    ax3.axhline(70, linestyle='--', color='gray', alpha=0.5)
    ax3.set_title("Relative Strength Index (RSI)")
    ax3.legend()
    
    plt.tight_layout()
    st.pyplot(fig2)
    
else:
    st.warning("Failed to retrieve data. Please check your internet connection or try again later.")

# Footer
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Made with Streamlit")
