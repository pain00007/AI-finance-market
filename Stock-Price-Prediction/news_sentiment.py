import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from textblob import TextBlob
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from collections import Counter

@st.cache_data(ttl=3600)
def fetch_news_with_images(query: str, api_key: str, page_size: int = 10):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": api_key,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("articles", [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.error("🚫 Rate limit exceeded (HTTP 429). Try again later or upgrade your NewsAPI plan.")
        else:
            st.error(f"API Error: {e}")
        return []
    except Exception as e:
        st.error(f"Error fetching news from the API: {e}")
        return []

def get_sentiment_label(polarity):
    if polarity > 0.1:
        return "🟢 Positive"
    elif polarity < -0.1:
        return "🔴 Negative"
    else:
        return "🟡 Neutral"

def news_sentiment():
    # 🕒 Auto-refresh every 5 minutes (300000 ms)
    st_autorefresh(interval=300000, key="news_refresh")

    st.title("🧠 News & Sentiment Analysis")

    ticker = st.text_input("Enter Stock or Crypto Symbol", st.session_state.get("ticker", "AAPL")).upper()
    st.session_state.ticker = ticker

    api_key = "6f15cf7de3414430b24b88e64828f3b"
    st.subheader(f"📰 Latest News for {ticker}")

    news_items = fetch_news_with_images(ticker, api_key, page_size=10)
    sentiments = []
    sentiment_labels = []

    if news_items:
        for article in news_items:
            title = article.get("title") or ""
            if not title.strip():
                continue

            description = article.get("description") or "No description provided."
            url = article.get("url", "#")
            image_url = article.get("urlToImage")
            source = article.get("

