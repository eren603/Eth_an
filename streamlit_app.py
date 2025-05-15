import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import time

# Configurations
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
REFRESH_RATE = 60  # seconds

def fetch_crypto_data():
    """Fetch real-time and historical data with validation"""
    try:
        # Real-time price
        price_url = f"{COINGECKO_API}/simple/price?ids={SYMBOL}&vs_currencies={CURRENCY}&include_market_cap=false&include_24hr_vol=false&include_24hr_change=true"
        price_data = requests.get(price_url, timeout=5).json()
        
        # Historical data (last 7 days for better indicator accuracy)
        history_url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=7"
        history_data = requests.get(history_url, timeout=10).json()
        
        return {
            'current_price': price_data[SYMBOL][CURRENCY],
            'price_change': price_data[SYMBOL][f'{CURRENCY}_24h_change'],
            'history': history_data['prices']
        }
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return None

def calculate_technical_indicators(prices):
    """Enhanced indicator calculations with validation"""
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    
    try:
        # SMA 20
        df['SMA_20'] = df['price'].rolling(window=20, min_periods=1).mean()
        
        # EMA 50
        df['EMA_50'] = df['price'].ewm(span=50, adjust=False).mean()
        
        # RSI 14 with division guard
        delta = df['price'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-10)  # Prevent division by zero
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        return df.dropna()
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return pd.DataFrame()

# Streamlit UI Setup
st.set_page_config(
    page_title="Live Crypto Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    st.title("📈 Real-Time Crypto Analytics Dashboard")
    
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            data = fetch_crypto_data()
            
            if data and len(data['history']) > 50:  # Ensure enough data points
                current_price = data['current_price']
                price_change = data['price_change']
                df = calculate_technical_indicators(data['history'])
                
                if not df.empty:
                    # Real-time Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Price", 
                                f"${current_price:,.2f}", 
                                delta=f"{price_change:.2f}%")
                    with col2:
                        st.metric("RSI (14)", 
                                f"{df['RSI_14'].iloc[-1]:.1f}", 
                                help="Overbought (>70) / Oversold (<30)")
                    with col3:
                        st.metric("EMA (50)", 
                                f"${df['EMA_50'].iloc[-1]:,.2f}", 
                                delta=f"{(current_price - df['EMA_50'].iloc[-1]):.2f}")
                    
                    # Price Chart
                    st.subheader("Price Analysis - Last 7 Days")
                    fig, ax = plt.subplots(figsize=(14, 6))
                    
                    # Plot data
                    ax.plot(df.index, df['price'], label='Price', color='#00FF00', linewidth=2)
                    ax.plot(df.index, df['SMA_20'], label='SMA 20', linestyle='--', color='#FF0000')
                    ax.plot(df.index, df['EMA_50'], label='EMA 50', linestyle='-.', color='#0000FF')
                    
                    # Formatting
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
                    plt.xticks(rotation=45)
                    ax.grid(True, alpha=0.3)
                    ax.legend()
                    
                    st.pyplot(fig)
                    
                    # Data Status
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success(f"✅ Data updated: {current_time}")
                else:
                    st.warning("⚠️ Insufficient data for analysis")
            else:
                st.error("🔴 Failed to fetch market data")
                
        time.sleep(REFRESH_RATE)

if __name__ == "__main__":
    main()
