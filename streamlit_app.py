import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
REFRESH_INTERVAL = 60  # seconds

def fetch_real_time_data():
    """Get real-time price and historical data"""
    try:
        # Real-time price
        price_url = f"{COINGECKO_API}/simple/price?ids={SYMBOL}&vs_currencies={CURRENCY}"
        price_data = requests.get(price_url, timeout=5).json()
        
        # Historical data (last 24 hours)
        history_url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=1"
        history_data = requests.get(history_url, timeout=10).json()
        
        return {
            'current_price': price_data[SYMBOL][CURRENCY],
            'history': history_data['prices']
        }
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return None

def calculate_indicators(prices):
    """Calculate technical indicators in real-time"""
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    
    # Moving Averages
    df['SMA_20'] = df['price'].rolling(window=20).mean()
    df['EMA_50'] = df['price'].ewm(span=50, adjust=False).mean()
    
    # RSI Calculation
    delta = df['price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    return df.dropna()

# Streamlit UI
st.set_page_config(
    page_title="Real-Time Crypto Dashboard",
    page_icon="🚀",
    layout="wide"
)

def main():
    st.title("📊 Live Crypto Analysis Dashboard")
    
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            data = fetch_real_time_data()
            
            if data:
                current_price = data['current_price']
                history_df = calculate_indicators(data['history'])
                
                # Real-time Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${current_price:,.2f}", delta=f"{((current_price/history_df['price'].iloc[0])-1)*100:.2f}%")
                with col2:
                    st.metric("RSI (14)", f"{history_df['RSI_14'].iloc[-1]:.1f}")
                with col3:
                    st.metric("EMA (50)", f"${history_df['EMA_50'].iloc[-1]:,.2f}")

                # Live Price Chart
                st.subheader("Live Price Movement")
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.plot(history_df.index, history_df['price'], label='Price', color='#00FF00')
                ax.plot(history_df.index, history_df['SMA_20'], label='SMA 20', linestyle='--', color='#FF0000')
                ax.plot(history_df.index, history_df['EMA_50'], label='EMA 50', linestyle='-.', color='#0000FF')
                ax.set_xlabel("Time", fontsize=12)
                ax.set_ylabel("Price (USD)", fontsize=12)
                ax.legend()
                st.pyplot(fig)
                
                # Data Freshness Indicator
                st.write(f"🔄 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
