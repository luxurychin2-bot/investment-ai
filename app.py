import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =================================================
# 기본 설정
# =================================================
st.set_page_config(page_title="KR Sector Rotation", layout="wide")
st.title("📊 한국시장 섹터 로테이션 대시보드")

START = "2018-01-01"

# =================================================
# 한국 섹터 ETF 정의
# =================================================
KR_SECTOR_ETF = {
    "반도체": "091160",     # KODEX 반도체
    "2차전지": "305720",   # KODEX 2차전지
    "바이오": "244580",     # KODEX 바이오
    "자동차": "091180",    # KODEX 자동차
    "인터넷": "266360",    # KODEX IT
}

# =================================================
# 데이터 로드 (완전 방어)
# =================================================
@st.cache_data
def load_kr_price(code):
    try:
        ticker = f"{code}.KS"
        df = yf.download(ticker, start=START, progress=False)
        if df is None or df.empty:
            return None
        return df[["Close"]].dropna()
    except Exception:
        return None

# =================================================
# STEP 2: 고급 점수 함수 (0~10)
# =================================================
def advanced_score(df):
    if df is None or len(df) < 130:
        return 0

    close = df["Close"]

    ret_3m = close.pct_change(63).iloc[-1]
    ret_6m = close.pct_change(126).iloc[-1]
    ma120 = close.rolling(120).mean().iloc[-1]
    vol_60 = close.pct_change().rolling(60).std().iloc[-1]
    vol_mean = close.pct_change().rolling(60).std().mean()

    score = 0
    if ret_3m > 0: score += 3
    if ret_6m > 0: score += 3
    if close.iloc[-1] > ma120: score += 2
    if vol_60 < vol_mean: score += 2

    return int(score)

# =================================================
# STEP 3: 투자 시그널
# =================================================
def investment_signal(score):
    if score >= 8:
        return "✔ 보유"
    elif score >= 5:
        return "⚠ 관찰"
    else:
        return "❌ 회피"

# =================================================
# 데이터 준비
# =================================================
price_data = {}
scores = {}

for sector, code in KR_SECTOR_ETF.items():
    df = load_kr_price(code)
    price_data[sector] = df
    scores[sector] = advanced_score(df)

score_df = pd.DataFrame(
    [{"섹터": k, "점수": v, "시그널": investment_signal(v)} for k, v in scores.items()]
).sort_values("점수", ascending=False).reset_index(drop=True)

# =================================================
# STEP 1 결과: 섹터 점수 & 시그널
# =================================================
st.subheader("🔥 이번 달 섹터 강도 & 투자 시그널")
st.dataframe(score_df, use_container_width=True)

# =================================================
# 섹터 점수 시각화
# =================================================
st.subheader("📊 섹터 점수 비교")

fig, ax = plt.subplots()
ax.bar(score_df["섹터"], score_df["점수"])
ax.set_ylim(0, 10)
ax.set_ylabel("Score (0~10)")
st.pyplot(fig)

# =================================================
# 섹터 가격 차트
# =================================================
st.subheader("📈 섹터 가격 추이")

selected = st.selectbox("섹터 선택", score_df["섹터"].tolist())
df_sel = price_data[selected]

if df_sel is not None:
    fig2, ax2 = plt.subplots()
    ax2.plot(df_sel.index, df_sel["Close"])
    ax2.set_title(f"{selected} 가격")
    st.pyplot(fig2)
else:
    st.warning("가격 데이터가 없습니다.")

# =================================================
# 월별 섹터 로테이션 백테스트 (Top 1)
# =================================================
st.subheader("📅 월별 섹터 로테이션 백테스트 (Top 1)")

monthly_returns = []
dates = pd.date_range("2019-01-01", pd.Timestamp.today(), freq="M")

for date in dates:
    month_scores = {}

    for sector, df in price_data.items():
        if df is None or df.index[-1] < date:
            continue
        sub = df[df.index <= date]
        month_scores[sector] = advanced_score(sub)

    if not month_scores:
        monthly_returns.append(0)
        continue

    best_sector = max(month_scores, key=month_scores.get)
    df_best = price_data[best_sector]

    month_df = df_best[
        (df_best.index > date - pd.DateOffset(months=1)) &
        (df_best.index <= date)
    ]

    if len(month_df) < 2:
        monthly_returns.append(0)
    else:
        monthly_returns.append(float(month_df["Close"].pct_change().iloc[-1]))

bt = pd.Series(monthly_returns, index=dates).fillna(0)
equity = (1 + bt).cumprod()

# 성과 지표
years = len(equity) / 12
cagr = equity.iloc[-1] ** (1 / years) - 1
mdd = (equity / equity.cummax() - 1).min()

st.write(f"📈 CAGR: **{cagr*100:.2f}%**")
st.write(f"📉 MDD : **{mdd*100:.2f}%**")

fig3, ax3 = plt.subplots()
ax3.plot(equity.index, equity.values)
ax3.set_title("전략 누적 수익률")
st.pyplot(fig3)
