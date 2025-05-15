import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import plotly.graph_objects as go

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"
CURRENCY = "usd"
REFRESH_INTERVAL = 45  # Optimal refresh rate in seconds
CACHE_TIMEOUT = 1800    # 30-minute caching

# Streamlit configuration
st.set_page_config(
    page_title="Professional Crypto Dashboard",
    layout="wide",
    page_icon="₿",
    initial_sidebar_state="collapsed"
)

@st.cache_resource(ttl=CACHE_TIMEOUT, show_spinner=False)
def fetch_market_data():
    """Fetch optimized market data with enhanced caching"""
    try:
        url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=14"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return None

def create_interactive_chart(df):
    """Create stable Plotly visualization"""
    fig = go.Figure()
    
    # Price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['prices'],
        name='Price',
        line=dict(color='#4CAF50', width=2)
    ))
    
    # Technical indicators
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA_20'],
        name='20 SMA',
        line=dict(color='#FF5722', dash='dot')
    ))
    
    fig.update_layout(
        title='Real-Time Price Analysis',
        xaxis_title='Time',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def main_dashboard():
    """Main dashboard application logic"""
    st.title("🚀 Professional Crypto Analytics Dashboard")
    
    placeholder = st.empty()
    error_counter = 0
    
    while error_counter < 3:
        try:
            with placeholder.container():
                market_data = fetch_market_data()
                
                if market_data and 'prices' in market_data:
                    df = pd.DataFrame(market_data['prices'], columns=['timestamp', 'prices'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Technical calculations
                    df['SMA_20'] = df['prices'].rolling(20).mean()
                    df['RSI_14'] = 100 - (100 / (1 + (
                        df['prices'].diff().clip(lower=0).rolling(14).mean() / 
                        df['prices'].diff().clip(upper=0).abs().rolling(14).mean()
                    ))
                    
                    # Real-time metrics
                    current_price = df['prices'].iloc[-1]
                    rsi_value = df['RSI_14'].iloc[-1]
                    
                    # Metric columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Price", f"${current_price:,.2f}")
                    with col2:
                        st.metric("RSI (14)", f"{rsi_value:.1f}", 
                                "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral")
                    with col3:
                        st.metric("Last Update", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    # Interactive visualization
                    st.plotly_chart(create_interactive_chart(df), use_container_width=True)
                    
                    error_counter = 0  # Reset error counter
                else:
                    st.warning("Data unavailable. Please wait...")
                    error_counter += 1
                
        except Exception as e:
            error_counter += 1
            st.error(f"System error: {str(e)}")
            time.sleep(10)  # Error cooldown
        
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main_dashboard()
