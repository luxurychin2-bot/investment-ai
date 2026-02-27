import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ======================
# 기본 설정
# ======================
st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")
st.title("📊 Sector Rotation Dashboard")

START = "2018-01-01"

SECTOR_ETF = {
    "AI": "BOTZ",
    "BIO": "IBB",
    "SEMICON": "SOXX",
    "ENERGY": "XLE",
    "DEFENSE": "ITA"
}

# ======================
# 데이터 로딩
# ======================
@st.cache_data
def load_price(ticker):
    try:
        df = yf.download(ticker, start=START, progress=False)
        if df is None or df.empty:
            return None
        df = df[["Close"]].dropna()
        return df
    except Exception:
        return None

# ======================
# 모멘텀 점수
# ======================
def calculate_score(df):
    if df is None or len(df) < 130:
        return 0

    df = df.copy()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma60"] = df["Close"].rolling(60).mean()
    df["ma120"] = df["Close"].rolling(120).mean()

    last = df.iloc[-1]

    try:
        close = float(last["Close"])
        ma20 = float(last["ma20"])
        ma60 = float(last["ma60"])
        ma120 = float(last["ma120"])
    except Exception:
        return 0

    score = 0
    if close > ma20: score += 1
    if ma20 > ma60: score += 1
    if ma60 > ma120: score += 1

    return score

# ======================
# 월별 섹터 로테이션 백테스트
# ======================
def sector_rotation_backtest(price_dict):
    monthly_returns = []

    # 월말 기준
    dates = pd.date_range(start=START, end=pd.Timestamp.today(), freq="M")

    for date in dates:
        scores = {}

        for sector, df in price_dict.items():
            if df is None or df.index[-1] < date:
                continue

            sub = df[df.index <= date]
            scores[sector] = calculate_score(sub)

        if not scores:
            monthly_returns.append(0)
            continue

        best_sector = max(scores, key=scores.get)
        df_best = price_dict[best_sector]

        month_data = df_best[
            (df_best.index > date - pd.DateOffset(months=1)) &
            (df_best.index <= date)
        ]

        if len(month_data) < 2:
            monthly_returns.append(0)
        else:
            ret = month_data["Close"].pct_change().iloc[-1]
            monthly_returns.append(float(ret))

    return pd.Series(monthly_returns, index=dates).fillna(0)

# ======================
# 데이터 준비
# ======================
price_data = {}
scores = {}

for sector, ticker in SECTOR_ETF.items():
    df = load_price(ticker)
    price_data[sector] = df
    scores[sector] = calculate_score(df)

score_df = pd.DataFrame(
    [{"Sector": k, "Score": v} for k, v in scores.items()]
).sort_values("Score", ascending=False)

# ======================
# 상위 섹터
# ======================
st.subheader("🔥 이번 달 상위 섹터")
for _, row in score_df.head(2).iterrows():
    st.write(f"• **{row['Sector']}** | 점수: {row['Score']}")

# ======================
# 섹터 점수 차트
# ======================
st.subheader("📊 섹터 모멘텀 점수")

fig, ax = plt.subplots()
ax.bar(score_df["Sector"], score_df["Score"])
ax.set_ylim(0, 3)
st.pyplot(fig)

# ======================
# 섹터 가격 차트
# ======================
st.subheader("📈 섹터 가격 추이")

selected = st.selectbox("섹터 선택", score_df["Sector"].tolist())
df_sel = price_data[selected]

if df_sel is not None:
    fig2, ax2 = plt.subplots()
    ax2.plot(df_sel.index, df_sel["Close"])
    st.pyplot(fig2)

# ======================
# 백테스트 결과
# ======================
st.subheader("📅 월별 섹터 로테이션 백테스트")

bt = sector_rotation_backtest(price_data)
cum = (1 + bt).cumprod()

# CAGR / MDD
years = len(cum) / 12
cagr = cum.iloc[-1] ** (1 / years) - 1
mdd = (cum / cum.cummax() - 1).min()

st.write(f"📈 CAGR: **{cagr*100:.2f}%**")
st.write(f"📉 MDD: **{mdd*100:.2f}%**")

fig3, ax3 = plt.subplots()
ax3.plot(cum.index, cum.values)
ax3.set_title("Strategy Cumulative Return")
st.pyplot(fig3)
