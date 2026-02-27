import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="KR Sector Rotation FINAL", layout="wide")
st.title("🇰🇷 한국시장 섹터 로테이션 – 최종판 v1.0")

START_DATE = "2018-01-01"

# =========================================================
# 한국 섹터 ETF (안정적인 KODEX 위주)
# =========================================================
SECTORS = {
    "반도체": "091160",
    "2차전지": "305720",
    "바이오": "244580",
    "자동차": "091180",
    "인터넷": "266360",
}

# =========================================================
# 데이터 로드 (완전 방어)
# =========================================================
@st.cache_data
def load_price(code):
    try:
        ticker = f"{code}.KS"
        df = yf.download(ticker, start=START_DATE, progress=False)
        if df is None or df.empty:
            return None
        df = df[["Close"]].dropna()
        return df
    except Exception:
        return None

# =========================================================
# 섹터 모멘텀 점수 (최종 확정 로직)
# =========================================================
def sector_score(df):
    if df is None or len(df) < 130:
        return 0

    close = df["Close"]

    try:
        ret_3m = float(close.pct_change(63).iloc[-1])
        ret_6m = float(close.pct_change(126).iloc[-1])
        ma120 = float(close.rolling(120).mean().iloc[-1])
        last = float(close.iloc[-1])
        vol_now = float(close.pct_change().rolling(60).std().iloc[-1])
        vol_avg = float(close.pct_change().rolling(60).std().mean())
    except Exception:
        return 0

    score = 0
    if ret_3m > 0: score += 3
    if ret_6m > 0: score += 3
    if last > ma120: score += 2
    if vol_now < vol_avg: score += 2

    return int(score)

def signal(score):
    if score >= 8:
        return "🔥 강세"
    elif score >= 5:
        return "👀 관찰"
    else:
        return "❌ 약세"

# =========================================================
# 데이터 준비
# =========================================================
price_data = {}
result = []

for sector, code in SECTORS.items():
    df = load_price(code)
    price_data[sector] = df
    sc = sector_score(df)
    result.append({
        "섹터": sector,
        "모멘텀 점수": sc,
        "시그널": signal(sc)
    })

score_df = (
    pd.DataFrame(result)
    .sort_values("모멘텀 점수", ascending=False)
    .reset_index(drop=True)
)

# =========================================================
# 1️⃣ 섹터 점수 테이블
# =========================================================
st.subheader("① 섹터 모멘텀 점수")
st.dataframe(score_df, use_container_width=True)

# =========================================================
# 2️⃣ 섹터 점수 차트
# =========================================================
st.subheader("② 섹터 모멘텀 비교")

fig1, ax1 = plt.subplots()
ax1.bar(score_df["섹터"], score_df["모멘텀 점수"])
ax1.set_ylim(0, 10)
ax1.set_ylabel("Score")
st.pyplot(fig1)

# =========================================================
# 3️⃣ 섹터 가격 추이
# =========================================================
st.subheader("③ 섹터 가격 추이")

selected = st.selectbox("섹터 선택", score_df["섹터"].tolist())
df_sel = price_data[selected]

if df_sel is not None:
    fig2, ax2 = plt.subplots()
    ax2.plot(df_sel.index, df_sel["Close"])
    ax2.set_title(f"{selected} 가격")
    st.pyplot(fig2)
else:
    st.warning("가격 데이터 없음")

# =========================================================
# 4️⃣ 월별 섹터 로테이션 백테스트
# =========================================================
st.subheader("④ 월별 섹터 로테이션 백테스트 (Top 1)")

dates = pd.date_range("2019-01-01", pd.Timestamp.today(), freq="M")
monthly_returns = []

for d in dates:
    scores = {}
    for sector, df in price_data.items():
        if df is None or df.index[-1] < d:
            continue
        scores[sector] = sector_score(df[df.index <= d])

    if not scores:
        monthly_returns.append(0)
        continue

    best = max(scores, key=scores.get)
    df_best = price_data[best]
    m = df_best[(df_best.index > d - pd.DateOffset(months=1)) & (df_best.index <= d)]

    if len(m) < 2:
        monthly_returns.append(0)
    else:
        monthly_returns.append(float(m["Close"].pct_change().iloc[-1]))

bt = pd.Series(monthly_returns, index=dates).fillna(0)
equity = (1 + bt).cumprod()

years = len(equity) / 12
cagr = equity.iloc[-1] ** (1 / years) - 1 if years > 0 else 0
mdd = (equity / equity.cummax() - 1).min()

st.write(f"📈 CAGR: **{cagr*100:.2f}%**")
st.write(f"📉 MDD: **{mdd*100:.2f}%**")

fig3, ax3 = plt.subplots()
ax3.plot(equity.index, equity.values)
ax3.set_title("전략 누적 수익률")
st.pyplot(fig3)
