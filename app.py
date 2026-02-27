# ===============================
# Sector Rotation Final App
# ===============================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------
# 기본 설정
# -------------------------------
st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")
st.title("📊 Sector Rotation Dashboard (Final)")

START_DATE = "2018-01-01"

# 한국 + 글로벌 섹터 ETF (안정성 위주)
SECTOR_ETF = {
    "반도체": "SOXX",
    "인터넷": "FDN",
    "AI": "BOTZ",
    "바이오": "IBB",
    "에너지": "XLE",
    "2차전지": "LIT"
}

# -------------------------------
# 데이터 로드
# -------------------------------
@st.cache_data
def load_price(ticker):
    df = yf.download(ticker, start=START_DATE, progress=False)
    df = df[["Close"]].dropna()
    return df

# -------------------------------
# 1️⃣ 섹터 모멘텀 점수 계산
# -------------------------------
def momentum_score(df):
    df = df.copy()

    if len(df) < 150:
        return 0

    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma60"] = df["Close"].rolling(60).mean()
    df["ma120"] = df["Close"].rolling(120).mean()

    last = df.iloc[-1]

    score = 0
    if last["Close"] > last["ma20"]:
        score += 1
    if last["Close"] > last["ma60"]:
        score += 1
    if last["Close"] > last["ma120"]:
        score += 1

    ret_3m = df["Close"].pct_change(63).iloc[-1]
    ret_6m = df["Close"].pct_change(126).iloc[-1]

    if ret_3m > 0:
        score += 2
    if ret_6m > 0:
        score += 3

    return int(score)

# -------------------------------
# 섹터별 점수 계산
# -------------------------------
scores = {}
price_data = {}

for sector, ticker in SECTOR_ETF.items():
    df = load_price(ticker)
    price_data[sector] = df
    scores[sector] = momentum_score(df)

score_df = (
    pd.DataFrame.from_dict(scores, orient="index", columns=["Momentum Score"])
    .sort_values("Momentum Score", ascending=False)
)

# -------------------------------
# 1️⃣ 섹터 모멘텀 점수 차트
# -------------------------------
st.header("① 섹터 모멘텀 점수 비교")

fig1, ax1 = plt.subplots()
score_df["Momentum Score"].plot(kind="bar", ax=ax1)
ax1.set_ylabel("Score")
ax1.set_title("Sector Momentum Score")
st.pyplot(fig1)

st.dataframe(score_df)

# -------------------------------
# 2️⃣ 섹터 가격 추이
# -------------------------------
st.header("② 섹터 가격 추이 확인")

selected_sector = st.selectbox("섹터 선택", list(SECTOR_ETF.keys()))
df_price = price_data[selected_sector]

fig2, ax2 = plt.subplots()
ax2.plot(df_price.index, df_price["Close"], label="Close Price")
ax2.set_title(f"{selected_sector} 가격 추이")
ax2.legend()
st.pyplot(fig2)

# -------------------------------
# 3️⃣ 월별 로테이션 백테스트
# -------------------------------
st.header("③ 월별 섹터 로테이션 백테스트")

monthly_returns = {}

for sector, df in price_data.items():
    monthly = df["Close"].resample("M").last().pct_change()
    monthly_returns[sector] = monthly

monthly_df = pd.DataFrame(monthly_returns)

# 매달 가장 강한 섹터 선택
best_sector_each_month = monthly_df.idxmax(axis=1)
strategy_return = monthly_df.lookup(monthly_df.index, best_sector_each_month)

strategy_cum = (1 + strategy_return.fillna(0)).cumprod()

fig3, ax3 = plt.subplots()
ax3.plot(strategy_cum.index, strategy_cum, label="Rotation Strategy", linewidth=2)
ax3.set_title("월별 섹터 로테이션 누적 수익")
ax3.legend()
st.pyplot(fig3)

st.success("✅ 최종 버전 실행 완료 (모멘텀 → 확인 → 검증)")
