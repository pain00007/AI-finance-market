import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from transformers import pipeline 


# === Technical Indicators ===
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data):
    ema12 = data.ewm(span=12).mean()
    ema26 = data.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

def calculate_bollinger_bands(data, window=20):
    sma = data.rolling(window).mean()
    std = data.rolling(window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return upper, lower

def calculate_stochastic(data, k_period=14, d_period=3):
    low_min = data.rolling(k_period).min()
    high_max = data.rolling(k_period).max()
    stoch_k = 100 * ((data - low_min) / (high_max - low_min))
    stoch_d = stoch_k.rolling(d_period).mean()
    return stoch_k, stoch_d

def calculate_atr(df, window=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    atr = tr.rolling(window).mean()
    return atr

# === News Sentiment (FinBERT + NewsAPI) ===



@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", framework="pt")



def fetch_news_headlines(ticker, limit=10):
    api_key = "cvpota9r01qve7iqb6qgcvpota9r01qve7iqb6r0"
    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&pageSize={limit}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return [article["title"] for article in articles]
    else:
        return []

def fetch_sentiment(ticker):
    headlines = fetch_news_headlines(ticker)

    if not headlines:
        return {"sentiment": "🟡 No News", "score": 0.0, "headlines": [], "distribution": {}}

    classifier = load_sentiment_model()
    results = classifier(headlines)

    sentiment_scores = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for res in results:
        label = res["label"].upper()
        sentiment_scores[label] += 1

    total = sum(sentiment_scores.values())
    score = (sentiment_scores["POSITIVE"] - sentiment_scores["NEGATIVE"]) / total
    label = "🟢 Positive" if score > 0.2 else "🔴 Negative" if score < -0.2 else "🟡 Neutral"

    return {
        "sentiment": label,
        "score": score,
        "headlines": headlines,
        "distribution": sentiment_scores
    }

# === Main Dashboard ===
def overview_dashboard():
    st.title("📊 Stock & Crypto Overview")

    ticker_input = st.text_input("🔍 Enter Symbol (e.g., AAPL, TSLA, BTC-USD)", "AAPL")
    ticker = ticker_input.strip().upper()
    st.session_state.ticker = ticker

    try:
        asset = yf.Ticker(ticker)
        info = asset.info
        hist = asset.history(period="6mo")

        if hist.empty:
            st.error(f"No data found for '{ticker}'. Try another symbol.")
            return

        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        daily_change_pct = ((current_price - prev_close) / prev_close) * 100

        volume = info.get("volume", "N/A")
        market_cap = info.get("marketCap", "N/A")

        # === Snapshot ===
        st.subheader(f"📌 Snapshot: {ticker}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Price", f"${current_price:.2f}")
        col2.metric("Change", f"{daily_change_pct:.2f}%")
        col3.metric("Volume", f"{volume:,}" if isinstance(volume, int) else "N/A")
        col4.metric("Market Cap", f"${market_cap/1e9:.2f}B" if isinstance(market_cap, (int, float)) else "N/A")

        # === Price Chart ===
        st.markdown("### 📈 Price Chart (6 Months)")
        st.line_chart(hist['Close'])

        # === Indicators ===
        with st.expander("📊 Technical Indicators"):
            close = hist['Close']

            rsi = calculate_rsi(close)
            macd, signal = calculate_macd(close)
            upper, lower = calculate_bollinger_bands(close)
            stoch_k, stoch_d = calculate_stochastic(close)
            atr = calculate_atr(hist)

            st.markdown("**RSI**")
            st.line_chart(rsi.dropna())

            st.markdown("**MACD & Signal**")
            st.line_chart(pd.DataFrame({'MACD': macd, 'Signal': signal}).dropna())

            st.markdown("**Bollinger Bands**")
            st.line_chart(pd.DataFrame({'Close': close, 'Upper': upper, 'Lower': lower}).dropna())

            st.markdown("**Stochastic Oscillator**")
            st.line_chart(pd.DataFrame({'%K': stoch_k, '%D': stoch_d}).dropna())

            st.markdown("**ATR (Volatility)**")
            st.line_chart(atr.dropna())

        # === Sentiment ===
        st.subheader("🧠 News Sentiment (FinBERT)")
        result = fetch_sentiment(ticker)

        st.markdown(f"**Sentiment:** {result['sentiment']} ({result['score']:.2f})")

        col_pos, col_neu, col_neg = st.columns(3)
        col_pos.metric("Positive", result["distribution"].get("POSITIVE", 0))
        col_neu.metric("Neutral", result["distribution"].get("NEUTRAL", 0))
        col_neg.metric("Negative", result["distribution"].get("NEGATIVE", 0))

        with st.expander("📰 Latest Headlines"):
            for headline in result["headlines"]:
                st.markdown(f"- {headline}")

        # === Info ===
        st.subheader("🏢 Asset Info")
        st.markdown(f"**Name:** {info.get('shortName', 'N/A')}")
        st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
        st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
        st.markdown(f"**Website:** [{info.get('website', 'N/A')}]({info.get('website', '#')})")

    except Exception as e:
        st.error(f"⚠️ Error loading data for '{ticker}': {e}")
