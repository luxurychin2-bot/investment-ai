# ===============================
# Sector Rotation Dashboard FINAL (Stable)
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
st.title("📊 Sector Rotation Dashboard (Final Stable Version)")

START_DATE = "2018-01-01"

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
    df["Close"] = df["Close"].astype(float)  # 🔒 핵심
    return df

# -------------------------------
# 1️⃣ 모멘텀 점수
# -------------------------------
def momentum_score(df):
    if len(df) < 150:
        return 0

    df = df.copy()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma60"] = df["Close"].rolling(60).mean()
    df["ma120"] = df["Close"].rolling(120).mean()

    close = float(df["Close"].iloc[-1])
    ma20 = float(df["ma20"].iloc[-1])
    ma60 = float(df["ma60"].iloc[-1])
    ma120 = float(df["ma120"].iloc[-1])

    score = 0
    if close > ma20:
        score += 1
    if close > ma60:
        score += 1
    if close > ma120:
        score += 1

    ret_3m = float(df["Close"].pct_change(63).iloc[-1])
    ret_6m = float(df["Close"].pct_change(126).iloc[-1])

    if ret_3m > 0:
        score += 2
    if ret_6m > 0:
        score += 3

    return score

# -------------------------------
# 섹터 점수 계산
# -------------------------------
price_data = {}
scores = {}

for sector, ticker in SECTOR_ETF.items():
    df = load_price(ticker)
    price_data[sector] = df
    scores[sector] = momentum_score(df)

score_df = (
    pd.DataFrame.from_dict(scores, orient="index", columns=["Momentum Score"])
    .sort_values("Momentum Score", ascending=False)
)

# -------------------------------
# ① 섹터 모멘텀 점수
# -------------------------------
st.header("① 섹터 모멘텀 점수")

fig1, ax1 = plt.subplots()
score_df["Momentum Score"].plot(kind="bar", ax=ax1)
ax1.set_ylabel("Score")
ax1.set_title("Sector Momentum Score")
st.pyplot(fig1)

st.dataframe(score_df)

# -------------------------------
# ② 섹터 가격 추이
# -------------------------------
st.header("② 섹터 가격 추이")

selected_sector = st.selectbox("섹터 선택", list(SECTOR_ETF.keys()))
df_price = price_data[selected_sector]

fig2, ax2 = plt.subplots()
ax2.plot(df_price.index, df_price["Close"])
ax2.set_title(f"{selected_sector} 가격 추이")
st.pyplot(fig2)

# -------------------------------
# ③ 월별 로테이션 백테스트
# -------------------------------
st.header("③ 월별 섹터 로테이션 백테스트")

monthly_returns = pd.DataFrame()

for sector, df in price_data.items():
    monthly_returns[sector] = (
        df["Close"]
        .resample("M")
        .last()
        .pct_change()
    )

best_sector = monthly_returns.idxmax(axis=1)

strategy_return = []
for date in monthly_returns.index:
    sector = best_sector.loc[date]
    strategy_return.append(monthly_returns.loc[date, sector])

strategy_return = pd.Series(strategy_return, index=monthly_returns.index)
strategy_cum = (1 + strategy_return.fillna(0)).cumprod()

fig3, ax3 = plt.subplots()
ax3.plot(strategy_cum.index, strategy_cum, linewidth=2)
ax3.set_title("월별 섹터 로테이션 누적 수익")
st.pyplot(fig3)

st.success("✅ 최종 안정판 실행 완료 (분석 → 확인 → 검증)")
