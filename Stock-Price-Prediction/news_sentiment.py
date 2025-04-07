import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from textblob import TextBlob
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from collections import Counter

@st.cache_data(ttl=3600)
def fetch_finnhub_news(symbol: str, api_key: str):
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e}")
        return []
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def get_sentiment_label(polarity):
    if polarity > 0.1:
        return "🟢 Positive"
    elif polarity < -0.1:
        return "🔴 Negative"
    else:
        return "🟡 Neutral"

def news_sentiment():
    # 🕒 Auto-refresh every 5 minutes
    st_autorefresh(interval=300000, key="news_refresh")

    st.title("🧠 News & Sentiment Analysis (via Finnhub)")

    ticker = st.text_input("Enter Stock Symbol", st.session_state.get("ticker", "AAPL")).upper()
    st.session_state.ticker = ticker

    api_key = "cvpota9r01qve7iqb6qgcvpota9r01qve7iqb6r0"
    st.subheader(f"📰 Latest News for {ticker}")

    news_items = fetch_finnhub_news(ticker, api_key)
    sentiments = []
    sentiment_labels = []

    if news_items:
        for article in news_items[:10]:
            title = article.get("headline", "")
            if not title.strip():
                continue

            description = article.get("summary") or "No description provided."
            url = article.get("url", "#")
            image_url = article.get("image")
            source = article.get("source", "Unknown Source")
            date = datetime.fromtimestamp(article.get("datetime")).strftime("%Y-%m-%d")

            polarity = TextBlob(title).sentiment.polarity
            label = get_sentiment_label(polarity)

            sentiments.append(polarity)
            sentiment_labels.append(label)

            st.markdown(f"### {title}")
            st.caption(f"{source} | Published: {date}")
            if image_url:
                st.image(image_url, width=300)
            st.write(description)
            st.markdown(f"[🔗 Read more]({url})")
            st.markdown(f"**Sentiment:** {label} _(Polarity: {polarity:.2f})_")
            st.markdown("---")
    else:
        st.warning("No news articles available.")

    # 📊 Overall Sentiment Summary
    st.subheader("📊 Overall Sentiment of Headlines")

    if sentiments:
        avg_polarity = sum(sentiments) / len(sentiments)
        overall_label = get_sentiment_label(avg_polarity)

        st.metric("Average Polarity", f"{avg_polarity:.2f}", help="Mean sentiment polarity across top articles")
        st.markdown(f"**Overall Sentiment:** {overall_label}")

        label_counts = Counter(sentiment_labels)
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Positive", label_counts.get("🟢 Positive", 0))
        col2.metric("🟡 Neutral", label_counts.get("🟡 Neutral", 0))
        col3.metric("🔴 Negative", label_counts.get("🔴 Negative", 0))

        st.bar_chart(pd.Series(sentiments, name="Headline Sentiment"))
        st.caption("Note: Polarity ranges from -1 (very negative) to +1 (very positive).")

    else:
        st.info("No valid headlines to compute sentiment.")

if __name__ == "__main__":
    news_sentiment()


