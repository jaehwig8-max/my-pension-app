import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="S&P 500 실시간 분할매수 가이드", layout="centered")

# 디자인 CSS
st.markdown("""
    <style>
    .buy-box { 
        font-size: 2.2rem; font-weight: bold; color: #EAFF00; 
        background-color: #1E1E1E; padding: 25px; border-radius: 15px; 
        text-align: center; border: 2px solid #EAFF00;
    }
    .metric-card { background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 S&P 500 실시간 분할매수 계산기")
st.caption("실시간 시장 지표를 반영한 Retirement Traveler 전용 전략")

# 2. 사이드바: 자산 설정
st.sidebar.header("💰 나의 투자 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)
invest_period = st.sidebar.number_input("매수 기간 (일)", value=180, min_value=1)
base_amount = total_budget / invest_period

st.sidebar.divider()
st.sidebar.write(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원")

# 3. 데이터 로드 함수 (캐싱 적용으로 속도 향상)
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_live_data():
    # S&P 500 (^GSPC) 및 VIX (^VIX) 데이터 가져오기
    spy = yf.Ticker("^GSPC")
    vix_data = yf.Ticker("^VIX")
    
    # RSI 계산을 위해 1년치 데이터 수집
    df = spy.history(period="1y")
    
    # 1. RSI (14일)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    current_rsi = df['RSI'].iloc[-1]
    
    # 2. MDD (전고점 대비 하락폭)
    rolling_max = df['Close'].cummax()
    df['Drawdown'] = (df['Close'] - rolling_max) / rolling_max * 100
    current_mdd = df['Drawdown'].iloc[-1]
    
    # 3. VIX
    current_vix = vix_data.history(period="1d")['Close'].iloc[-1]
    
    return current_vix, current_mdd, current_rsi

# 데이터 호출
try:
    with st.spinner('실시간 시장 데이터를 가져오는 중...'):
        vix_val, mdd_val, rsi_val = get_live_data()
except:
    st.error("데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# 4. 가중치 로직
def calculate_weights(v, m, r):
    # VIX
    if v >= 35: v_w = 3.0
    elif v >= 28: v_w = 2.2
    elif v >= 22: v_w = 1.5
    elif v >= 18: v_w = 1.0
    else: v_w = 0.6

    # MDD
    if m <= -20: m_w = 5.0
    elif m <= -15: m_w = 3.5
    elif m <= -10: m_w = 2.5
    elif m <= -5: m_w = 1.5
    elif m <= -2: m_w = 0.8
    else: m_w = 0.3

    # RSI
    if r <= 25: r_w = 4.0
    elif r <= 35: r_w = 3.0
    elif r <= 45: r_w = 1.8
    elif r <= 55: r_w = 1.0
    elif r <= 65: r_w = 0.6
    else: r_w = 0.3
    
    return v_w, m_w, r_w

v_w, m_w, r_w = calculate_weights(vix_val, mdd_val, rsi_val)
total_weight = v_w + m_w + r_w
final_buy = base_amount * total_weight

# 5. UI 출력
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("VIX (변동성)", f"{vix_val:.2f}", f"가중치: {v_w}")
with col2:
    st.metric("MDD (낙폭)", f"{mdd_val:.2f}%", f"가중치: {m_w}")
with col3:
    st.metric("RSI (강도)", f"{rsi_val:.2f}", f"가중치: {r_w}")

st.markdown("---")
st.subheader("📢 오늘의 권장 매수 금액")
st.markdown(f'<div class="buy-box">{final_buy:,.0f} 원</div>', unsafe_allow_html=True)
st.write(f"💡 현재 **합산 가중치 배수**는 **{total_weight:.2f}배** 입니다.")

with st.expander("ℹ️ 전략 가이드 보기"):
    st.write("- **기본 공식:** 기본 매수액 × (VIX 가중치 + MDD 가중치 + RSI 가중치)")
    st.write("- **데이터 출처:** Yahoo Finance (S&P 500 실시간 데이터)")
    st.write("- **업데이트 주기:** 매 1시간마다 새로운 데이터를 가져옵니다.")
