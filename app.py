import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")

START_DATE = "2018-01-01"

SECTORS = {
    "AI": "BOTZ",
    "바이오": "IBB",
    "반도체": "SOXX",
    "에너지": "XLE",
    "2차전지": "LIT",
    "인터넷": "FDN",
}

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_price(ticker):
    df = yf.download(ticker, start=START_DATE, progress=False)
    if df is None or df.empty:
        return None
    return df[["Close"]].dropna()

# =========================
# 안전 수익률
# =========================
def safe_return(series, period):
    try:
        r = series.pct_change(periods=period).iloc[-1]
        if pd.isna(r):
            return 0.0
        return float(r)
    except Exception:
        return 0.0

# =========================
# 모멘텀 점수
# =========================
def momentum_score(df):
    if df is None or len(df) < 130:
        return 0

    returns = [
        safe_return(df["Close"], 21),
        safe_return(df["Close"], 63),
        safe_return(df["Close"], 126),
    ]

    return sum(1 for r in returns if r > 0)

# =========================
# 백테스트 (완전 재작성)
# =========================
def rotation_backtest(price_dict):
    close_df = pd.DataFrame()

    for sector, df in price_dict.items():
        if df is not None and len(df) > 130:
            close_df[sector] = df["Close"]

    if close_df.empty:
        return None

    monthly_price = close_df.resample("M").last()
    monthly_return = monthly_price.pct_change().dropna()

    strategy_returns = []

    for date in monthly_return.index:
        best_sector = monthly_return.loc[date].idxmax()
        strategy_returns.append(monthly_return.loc[date, best_sector])

    strategy_series = pd.Series(strategy_returns, index=monthly_return.index)
    return (1 + strategy_series).cumprod()

# =========================
# UI
# =========================
st.title("📊 Sector Rotation Dashboard (FINAL STABLE VERSION)")

prices = {}
scores = {}

for sector, ticker in SECTORS.items():
    df = load_price(ticker)
    prices[sector] = df
    scores[sector] = momentum_score(df)

# ---------- ① 점수 ----------
st.header("① 섹터 모멘텀 점수")

score_df = (
    pd.DataFrame.from_dict(scores, orient="index", columns=["Momentum Score"])
    .sort_values("Momentum Score", ascending=False)
)

st.dataframe(score_df, use_container_width=True)

fig1, ax1 = plt.subplots()
score_df["Momentum Score"].plot(kind="bar", ax=ax1)
ax1.set_title("Momentum Score by Sector")
st.pyplot(fig1)

# ---------- ② 가격 ----------
st.header("② 섹터 가격 추이")

sector_choice = st.selectbox("섹터 선택", list(SECTORS.keys()))
df_price = prices[sector_choice]

if df_price is not None:
    fig2, ax2 = plt.subplots()
    ax2.plot(df_price.index, df_price["Close"])
    ax2.set_title(f"{sector_choice} 가격 추이")
    st.pyplot(fig2)
else:
    st.warning("데이터 없음")

# ---------- ③ 백테스트 ----------
st.header("③ 월별 섹터 로테이션 백테스트")

bt = rotation_backtest(prices)

if bt is not None:
    fig3, ax3 = plt.subplots()
    ax3.plot(bt.index, bt.values)
    ax3.set_title("Sector Rotation Strategy (Cumulative)")
    st.pyplot(fig3)
else:
    st.warning("백테스트 데이터 부족")

st.caption("※ 매월 가장 수익률이 높은 섹터 1개에 투자하는 전략")
