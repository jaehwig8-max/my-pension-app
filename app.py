import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # 필수: 라이브러리 설치 필요 (pandas-ta)
from datetime import datetime

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
    </style>
    """, unsafe_allow_html=True)

st.title("📊 S&P 500 실시간 분할매수 계산기")
st.caption("실시간 시장 지표를 반영한 Retirement Traveler 전용 전략")

# 2. 사이드바 설정
st.sidebar.header("💰 나의 투자 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)
invest_period = st.sidebar.number_input("매수 기간 (일)", value=180, min_value=1)
base_amount = total_budget / invest_period

st.sidebar.divider()
st.sidebar.write(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원")

# 3. 데이터 로드 함수 (예외 처리 강화)
@st.cache_data(ttl=3600)
def get_live_data():
    try:
        # S&P 500 및 VIX 데이터
        spy_df = yf.download("^GSPC", period="1y", interval="1d", progress=False)
        vix_df = yf.download("^VIX", period="5d", interval="1d", progress=False)
        
        if spy_df.empty or vix_df.empty:
            return None, None, None

        # 1. RSI (14일) - pandas_ta 사용
        # yfinance 데이터 구조 대응 (MultiIndex 방지)
        close_prices = spy_df['Close'].squeeze() 
        rsi_series = ta.rsi(close_prices, length=14)
        current_rsi = rsi_series.iloc[-1]
        
        # 2. MDD 계산
        rolling_max = close_prices.cummax()
        drawdown = (close_prices - rolling_max) / rolling_max * 100
        current_mdd = drawdown.iloc[-1]
        
        # 3. VIX (최신 종가)
        current_vix = vix_df['Close'].squeeze().iloc[-1]
        
        return float(current_vix), float(current_mdd), float(current_rsi)
    except Exception as e:
        st.error(f"데이터 로드 중 상세 에러 발생: {e}")
        return None, None, None

# 데이터 호출 및 검증
vix_val, mdd_val, rsi_val = get_live_data()

if vix_val is None:
    st.warning("⚠️ 현재 야후 파이낸스에서 데이터를 가져올 수 없습니다. 잠시 후 다시 시도하거나 인터넷 연결을 확인하세요.")
    st.stop()

# 4. 가중치 로직 (기존과 동일)
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

with st.expander("ℹ️ 가중치 산정 기준"):
    st.write(f"- VIX({vix_val:.2f}): {v_w} / MDD({mdd_val:.2f}%): {m_w} / RSI({rsi_val:.2f}): {r_w}")
    st.write("- 공식: 기본 매수액 × (VIX 가중치 + MDD 가중치 + RSI 가중치)")
