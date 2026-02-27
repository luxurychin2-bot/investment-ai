import streamlit as st
import yfinance as yf
import pandas as pd
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
# 데이터 로딩 (완전 방어)
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
# 점수 계산 (Series 비교 에러 완전 차단)
# ======================
def calculate_score(df):
    if df is None or len(df) < 130:
        return 0

    df = df.copy()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma60"] = df["Close"].rolling(60).mean()
    df["ma120"] = df["Close"].rolling(120).mean()

    last = df.iloc[-1]

    # ❗ 무조건 float로 변환 (핵심)
    try:
        close = float(last["Close"])
        ma20 = float(last["ma20"])
        ma60 = float(last["ma60"])
        ma120 = float(last["ma120"])
    except Exception:
        return 0

    score = 0
    if close > ma20:
        score += 1
    if ma20 > ma60:
        score += 1
    if ma60 > ma120:
        score += 1

    return score

# ======================
# 섹터 점수 계산
# ======================
scores = {}
price_data = {}

for sector, ticker in SECTOR_ETF.items():
    df = load_price(ticker)
    price_data[sector] = df
    scores[sector] = calculate_score(df)

score_df = pd.DataFrame(
    [{"Sector": k, "Score": int(v)} for k, v in scores.items()]
)

# ❗ 숫자 없을 경우 차트 에러 방지
if score_df.empty or score_df["Score"].sum() == 0:
    st.warning("⚠️ 현재 계산 가능한 데이터가 없습니다.")
    st.stop()

score_df = score_df.sort_values("Score", ascending=False).reset_index(drop=True)

# ======================
# 상위 섹터
# ======================
st.subheader("🔥 이번 달 상위 섹터")
for i in range(min(2, len(score_df))):
    st.write(f"• **{score_df.loc[i,'Sector']}** | 점수: {score_df.loc[i,'Score']}")

# ======================
# 섹터 점수 차트 (numeric 보장)
# ======================
st.subheader("📊 섹터별 모멘텀 점수")

fig, ax = plt.subplots()
ax.bar(score_df["Sector"], score_df["Score"])
ax.set_ylim(0, 3)
ax.set_ylabel("Score")

st.pyplot(fig)

# ======================
# 개별 섹터 가격 차트
# ======================
st.subheader("📈 섹터 가격 추이")

selected = st.selectbox("섹터 선택", score_df["Sector"].tolist())
df_sel = price_data.get(selected)

if df_sel is not None and not df_sel.empty:
    fig2, ax2 = plt.subplots()
    ax2.plot(df_sel.index, df_sel["Close"])
    ax2.set_title(f"{selected} Price")
    st.pyplot(fig2)
else:
    st.warning("가격 데이터를 불러올 수 없습니다.")
     
