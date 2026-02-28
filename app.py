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
# 안전한 수익률 계산 (핵심 수정)
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

    r1 = safe_return(df["Close"], 21)
    r3 = safe_return(df["Close"], 63)
    r6 = safe_return(df["Close"], 126)

    score = 0
    for r in [r1, r3, r6]:
        if r > 0:
            score += 1
    return score

# =========================
# 백테스트
# =========================
def rotation_backtest(price_dict):
    monthly = {}
    for sector, df in price_dict.items():
        if df is not None:
            monthly[sector] = df["Close"].resample("M").last()

    monthly_df = pd.DataFrame(monthly).dropna()
    returns = monthly_df.pct_change().dropna()

    strategy = []
    for date in returns.index:
        best = returns.loc[date].idxmax()
        strategy.append(returns.loc[date, best])

    return (1 + pd.Series(strategy, index=returns.index)).cumprod()

# =========================
# UI
# =========================
st.title("📊 Sector Rotation Dashboard (FINAL STABLE)")

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

fig3, ax3 = plt.subplots()
ax3.plot(bt.index, bt.values)
ax3.set_title("Sector Rotation Strategy (Cumulative)")
st.pyplot(fig3)

st.caption("※ 매월 가장 강한 섹터 1개에 투자하는 단순 전략")
