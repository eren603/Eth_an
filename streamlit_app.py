import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
DAYS = 90  # 3 months historical data

@st.cache_resource(show_spinner=False)
def fetch_data():
    """Fetch cryptocurrency data from CoinGecko API"""
    try:
        url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days={DAYS}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('prices', [])
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def calculate_indicators(prices):
    """Calculate technical indicators using pure Python"""
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    
    # Simple Moving Average (20 period)
    df['SMA_20'] = df['price'].rolling(window=20).mean()
    
    # Exponential Moving Average (50 period)
    df['EMA_50'] = df['price'].ewm(span=50, adjust=False).mean()
    
    # Relative Strength Index (14 period)
    delta = df['price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    return df.dropna()

# Streamlit UI Configuration
st.set_page_config(
    page_title="Crypto Analytics Pro",
    page_icon="📈",
    layout="centered"
)

def main():
    st.title("💰 Crypto Analysis Dashboard")
    st.markdown("Real-time cryptocurrency market analysis")
    
    with st.spinner("Loading market data..."):
        prices = fetch_data()
    
    if prices:
        df = calculate_indicators(prices)
        
        if not df.empty:
            # Display Key Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${df['price'].iloc[-1]:,.2f}")
            with col2:
                st.metric("RSI (14)", f"{df['RSI_14'].iloc[-1]:.1f}")
            with col3:
                st.metric("EMA (50)", f"${df['EMA_50'].iloc[-1]:,.2f}")
            
            # Price Chart
            st.subheader("Price Analysis")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df.index, df['price'], label='Price', color='#4CAF50')
            ax.plot(df.index, df['SMA_20'], label='SMA 20', linestyle='--', color='#FF5722')
            ax.set_title("Price Movement with Technical Indicators")
            ax.legend()
            st.pyplot(fig)
        else:
            st.warning("Insufficient data for analysis")
    else:
        st.error("Failed to retrieve market data")
        
    st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
