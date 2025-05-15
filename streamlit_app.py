import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Config
COINGECKO_API = "https://api.coingecko.com/api/v3"
SYMBOL = "bitcoin"  # Resmi ID: "btc-bitcoin" de deneyebilirsiniz
CURRENCY = "usd"
REFRESH_RATE = 65  # Rate limit koruması

def fetch_crypto_data():
    """Enhanced data fetcher with error handling"""
    try:
        # Real-time price
        price_url = f"{COINGECKO_API}/simple/price?ids={SYMBOL}&vs_currencies={CURRENCY}"
        price_response = requests.get(price_url, timeout=15)
        
        if price_response.status_code != 200:
            st.error(f"Price API Error: {price_response.text}")
            return None
            
        price_data = price_response.json()
        
        if SYMBOL not in price_data:
            st.error(f"Invalid symbol response: {price_data}")
            return None
        
        # Historical data
        history_url = f"{COINGECKO_API}/coins/{SYMBOL}/market_chart?vs_currency={CURRENCY}&days=7"
        history_response = requests.get(history_url, timeout=20)
        
        if history_response.status_code != 200:
            st.error(f"History API Error: {history_response.text}")
            return None
            
        return {
            'current_price': price_data[SYMBOL][CURRENCY],
            'history': history_response.json()['prices']
        }
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected Error: {str(e)}")
    return None

# ... (Önceki calculate_technical_indicators fonksiyonu aynı kalacak) ...

def main():
    st.title("📈 Real-Time Crypto Dashboard")
    
    while True:
        data = fetch_crypto_data()
        
        if data:
            # Veri işleme ve gösterim
            current_price = data['current_price']
            df = calculate_technical_indicators(data['history'])
            
            st.metric("Current Price", f"${current_price:,.2f}")
            st.line_chart(df[['price', 'SMA_20', 'EMA_50']])
            
        time.sleep(REFRESH_RATE)

if __name__ == "__main__":
    main()
