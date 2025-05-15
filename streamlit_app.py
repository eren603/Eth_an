import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import time
import logging

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
REFRESH_INTERVAL = 60  # seconds
MIN_DATA_POINTS = 50   # Minimum data points for accurate calculations

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_crypto_data():
    """Fetch real-time and historical cryptocurrency data with enhanced validation"""
    try:
        # Fetch current price
        price_url = f"{COINGECKO_API}/simple/price?ids={SYMBOL}&vs_currencies={CURRENCY}"
        price_response = requests.get(price_url, timeout=10)
        
        if price_response.status_code != 200:
            logging.error(f"Price API Error: {price_response.text}")
            return None
            
        price_data = price_response.json()
        
        if SYMBOL not in price_data:
            logging.error(f"Invalid symbol response: {price_data}")
            return None
        
        # Fetch historical data
        history_url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=7"
        history_response = requests.get(history_url, timeout=15)
        
        if history_response.status_code != 200:
            logging.error(f"History API Error: {history_response.text}")
            return None
            
        return {
            'current_price': price_data[SYMBOL][CURRENCY],
            'history': history_response.json()['prices']
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Network Error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected Error: {str(e)}")
    return None

def calculate_technical_indicators(prices):
    """Calculate technical indicators with pandas and proper validation"""
    if not prices or len(prices) < MIN_DATA_POINTS:
        logging.warning("Insufficient data for indicator calculations")
        return None
        
    try:
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True)
        
        # Calculate moving averages
        df['SMA_20'] = df['price'].rolling(window=20, min_periods=1).mean()
        df['EMA_50'] = df['price'].ewm(span=50, adjust=False).mean()
        
        # Calculate RSI
        delta = df['price'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        return df.dropna()
        
    except Exception as e:
        logging.error(f"Indicator calculation error: {str(e)}")
        return None

def main():
    """Main application function with proper function ordering"""
    st.set_page_config(
        page_title="Crypto Analytics Pro",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("🚀 Real-Time Cryptocurrency Analysis")
    status_placeholder = st.empty()
    chart_placeholder = st.empty()
    
    while True:
        try:
            with status_placeholder.container():
                data = fetch_crypto_data()
                
                if data and len(data['history']) >= MIN_DATA_POINTS:
                    current_price = data['current_price']
                    df = calculate_technical_indicators(data['history'])
                    
                    if df is not None and not df.empty:
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Current Price", 
                                    f"${current_price:,.2f}", 
                                    help="Real-time market price")
                        with col2:
                            rsi_value = df['RSI_14'].iloc[-1]
                            rsi_status = "⬇️ Oversold" if rsi_value < 30 else "⬆️ Overbought" if rsi_value > 70 else "➡️ Neutral"
                            st.metric("RSI (14)", 
                                    f"{rsi_value:.1f} {rsi_status}")
                        with col3:
                            ema_value = df['EMA_50'].iloc[-1]
                            price_diff = current_price - ema_value
                            st.metric("EMA (50)", 
                                    f"${ema_value:,.2f}", 
                                    delta=f"{price_diff:+.2f}")

                        # Display chart
                        with chart_placeholder.container():
                            fig, ax = plt.subplots(figsize=(14, 6))
                            
                            # Plot price data
                            ax.plot(df.index, df['price'], 
                                   label='Price', 
                                   color='#1f77b4',
                                   linewidth=2)
                            
                            # Plot indicators
                            ax.plot(df.index, df['SMA_20'], 
                                   label='SMA 20', 
                                   linestyle='--', 
                                   color='#ff7f0e')
                            ax.plot(df.index, df['EMA_50'], 
                                   label='EMA 50', 
                                   linestyle='-.', 
                                   color='#2ca02c')
                            
                            # Formatting
                            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                            ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
                            plt.xticks(rotation=45)
                            ax.grid(True, alpha=0.3)
                            ax.legend()
                            plt.tight_layout()
                            
                            st.pyplot(fig)
                            
                        # Update timestamp
                        st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                    else:
                        st.warning("⚠️ Insufficient data for analysis")
                else:
                    st.error("🔴 Failed to fetch market data")
                    
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            st.error("⚠️ Application error - trying to recover...")
            
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
