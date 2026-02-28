import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")

# =========================
# 1. 설정
# =========================
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
# 2. 데이터 로딩
# =========================
@st.cache_data
def load_price(ticker):
    df = yf.download(ticker, start=START_DATE, progress=False)
    if df.empty:
        return None
    df = df[["Close"]].dropna()
    return df

# =========================
# 3. 모멘텀 점수 (안 터지는 버전)
# =========================
def momentum_score(df):
    if df is None or len(df) < 130:
        return 0

    def safe_return(series, period):
        r = series.pct_change(period).iloc[-1]
        if pd.isna(r):
            return 0.0
        return float(r)

    r1 = safe_return(df["Close"], 21)
    r3 = safe_return(df["Close"], 63)
    r6 = safe_return(df["Close"], 126)

    score = 0
    for r in [r1, r3, r6]:
        if r > 0:
            score += 1

    return score

# =========================
# 4. 월별 백테스트
# =========================
def sector_rotation_backtest(price_dict):
    monthly_prices = {}

    for sector, df in price_dict.items():
        if df is None:
            continue
        m = df["Close"].resample("M").last()
        monthly_prices[sector] = m

    monthly_df = pd.DataFrame(monthly_prices).dropna()
    monthly_ret = monthly_df.pct_change().dropna()

    strategy_returns = []

    for date in monthly_ret.index:
        row = monthly_ret.loc[date]
        best_sector = row.idxmax()
        strategy_returns.append(row[best_sector])

    result = pd.Series(strategy_returns, index=monthly_ret.index)
    return (1 + result).cumprod()

# =========================
# 5. UI 시작
# =========================
st.title("📊 Sector Rotation Dashboard (최종판)")

# =========================
# ① 섹터 모멘텀 점수
# =========================
st.header("① 섹터 모멘텀 점수")

prices = {}
scores = {}

for sector, ticker in SECTORS.items():
    df = load_price(ticker)
    prices[sector] = df
    scores[sector] = momentum_score(df)

score_df = (
    pd.DataFrame.from_dict(scores, orient="index", columns=["Momentum Score"])
    .sort_values("Momentum Score", ascending=False)
)

st.dataframe(score_df, use_container_width=True)

fig1, ax1 = plt.subplots()
score_df["Momentum Score"].plot(kind="bar", ax=ax1)
ax1.set_title("Sector Momentum Score")
st.pyplot(fig1)

# =========================
# ② 섹터 가격 추이
# =========================
st.header("② 섹터 가격 추이")

selected_sector = st.selectbox("섹터 선택", list(SECTORS.keys()))
price_df = prices[selected_sector]

if price_df is not None:
    fig2, ax2 = plt.subplots()
    ax2.plot(price_df.index, price_df["Close"])
    ax2.set_title(f"{selected_sector} 가격 추이")
    st.pyplot(fig2)
else:
    st.warning("가격 데이터를 불러올 수 없습니다.")

# =========================
# ③ 월별 섹터 로테이션 백테스트
# =========================
st.header("③ 월별 섹터 로테이션 백테스트")

bt = sector_rotation_backtest(prices)

fig3, ax3 = plt.subplots()
ax3.plot(bt.index, bt.values)
ax3.set_title("Sector Rotation Strategy (Cumulative Return)")
st.pyplot(fig3)

st.caption("※ 매월 가장 수익률이 높은 섹터에 투자하는 단순 로테이션 전략")
