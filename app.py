import streamlit as st
import numpy as np

st.set_page_config(page_title="김동진 투자 AI", layout="wide")

st.title("📊 김동진 전용 투자 AI 대시보드")

menu = st.sidebar.selectbox("메뉴 선택", ["DCF 계산기", "기업 점수 계산기"])

if menu == "DCF 계산기":

    st.header("📈 DCF 목표가 계산")

    eps = st.number_input("현재 EPS", value=3000)
    growth = st.number_input("연 성장률 (%)", value=10)
    discount = st.number_input("할인율 (%)", value=8)
    current_price = st.number_input("현재 주가", value=60000)

    years = 10

    future_eps = eps * ((1 + growth/100) ** years)
    fair_price = future_eps / ((1 + discount/100) ** years)

    gap = ((fair_price - current_price) / current_price) * 100

    st.subheader("📊 결과")

    st.write(f"10년 후 예상 EPS: {round(future_eps,2)}")
    st.write(f"내재 가치: {round(fair_price,2)} 원")
    st.write(f"저평가/고평가: {round(gap,2)} %")

    if gap > 20:
        st.success("💎 저평가 가능성 높음")
    elif gap < -20:
        st.error("⚠ 고평가 가능성 있음")
    else:
        st.info("중립 구간")

elif menu == "기업 점수 계산기":

    st.header("📊 재무 점수 계산")

    roe = st.slider("ROE (%)", 0, 50, 15)
    debt = st.slider("부채비율 (%)", 0, 300, 100)
    growth = st.slider("매출 성장률 (%)", -20, 50, 10)

    score = (roe * 0.4) + ((200 - debt) * 0.3) + (growth * 0.3)

    st.subheader("📈 종합 점수")
    st.write(f"기업 점수: {round(score,1)}")

    if score > 80:
        st.success("🔥 매우 우수")
    elif score > 60:
        st.info("👍 양호")
    else:
        st.warning("⚠ 개선 필요")
