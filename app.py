import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")

# -----------------------------
# 섹터 ETF (한국 컨셉, 미국 ETF 대용)
# -----------------------------
SECTORS = {
    "AI": "BOTZ",
    "반도체": "SOXX",
    "2차전지": "LIT",
    "바이오": "IBB",
    "에너지": "XLE",
    "인터넷": "FDN"
}

START_DATE = "2018-01-01"

# -----------------------------
# 데이터 로드 (안전)
# -----------------------------
@st.cache_data
def load_price(ticker):
    df = yf.download(ticker, start=START_DATE, progress=False)
    df = df[["Close"]].dropna()
    return df

# -----------------------------
# 모멘텀 점수 (절대값만 비교, Series 비교 금지)
# -----------------------------
def momentum_score(df):
    score = 0
    if len(df) < 130:
        return 0

    ret_1m = df["Close"].pct_change(21).iloc[-1]
    ret_3m = df["Close"].pct_change(63).iloc[-1]
    ret_6m = df["Close"].pct_change(126).iloc[-1]

    for r in [ret_1m, ret_3m, ret_6m]:
        if r > 0:
            score += 1

    return score

# =============================
# ① 섹터 모멘텀 점수
# =============================
st.title("📊 Sector Rotation Dashboard")

scores = {}
prices = {}

for sector, ticker in SECTORS.items():
    df = load_price(ticker)
    prices[sector] = df
    scores[sector] = momentum_score(df)

score_df = pd.DataFrame.from_dict(scores, orient="index", columns=["Momentum Score"])
score_df = score_df.sort_values("Momentum Score", ascending=False)

st.header("① 섹터 모멘텀 점수")
st.dataframe(score_df, use_container_width=True)

fig1, ax1 = plt.subplots()
score_df["Momentum Score"].plot(kind="bar", ax=ax1)
ax1.set_ylabel("Score")
st.pyplot(fig1)

# =============================
# ② 섹터 가격 추이
# =============================
st.header("② 섹터 가격 추이")
selected_sector = st.selectbox("섹터 선택", list(SECTORS.keys()))

price_df = prices[selected_sector].copy()
price_df["MA20"] = price_df["Close"].rolling(20).mean()
price_df["MA60"] = price_df["Close"].rolling(60).mean()

fig2, ax2 = plt.subplots()
ax2.plot(price_df.index, price_df["Close"], label="Close")
ax2.plot(price_df.index, price_df["MA20"], label="MA20")
ax2.plot(price_df.index, price_df["MA60"], label="MA60")
ax2.legend()
ax2.set_title(f"{selected_sector} 가격 추이")

st.pyplot(fig2)

# =============================
# ③ 월별 섹터 로테이션 백테스트
# =============================
st.header("③ 월별 섹터 로테이션 백테스트")

monthly_returns = pd.DataFrame()

for sector, df in prices.items():
    monthly = df["Close"].resample("M").last().pct_change()
    monthly_returns[sector] = monthly

monthly_returns = monthly_returns.dropna()

strategy_returns = []

for date in monthly_returns.index:
    row = monthly_returns.loc[date]
    best_sector = row.idxmax()
    strategy_returns.append(row[best_sector])

strategy_returns = pd.Series(strategy_returns, index=monthly_returns.index)
strategy_cum = (1 + strategy_returns).cumprod()

# 벤치마크 (KOSPI 대용 SPY)
benchmark = load_price("SPY")["Close"].resample("M").last().pct_change()
benchmark = benchmark.loc[strategy_cum.index]
benchmark_cum = (1 + benchmark).cumprod()

fig3, ax3 = plt.subplots()
ax3.plot(strategy_cum.index, strategy_cum, label="Sector Rotation")
ax3.plot(benchmark_cum.index, benchmark_cum, label="Benchmark")
ax3.legend()
ax3.set_title("누적 수익률 비교")

st.pyplot(fig3)

st.success("✅ 최종 버전 실행 완료")
