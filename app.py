import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="미국 지수 실시간 분할매수 계산기", layout="wide")

st.title("📈 실시간 지수 연동 분할매수 가이드")
st.write("나스닥100(QQQ) 및 S&P500(SPY)의 실시간 데이터를 기반으로 매수액을 계산합니다.")

# --- 사이드바: 사용자 설정 ---
st.sidebar.header("💰 투자 예산 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (원)", min_value=0, value=10000000, step=1000000)
split_days = st.sidebar.number_input("분할 매수 기간 (일)", min_value=1, value=20, step=1)
base_amount = total_budget // split_days

st.sidebar.divider()
asset_choice = st.sidebar.selectbox("대상 지수 선택", ["NASDAQ 100 (QQQ)", "S&P 500 (SPY)"])
ticker_symbol = "QQQ" if "NASDAQ" in asset_choice else "SPY"

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_live_indicators(ticker_symbol):
    # 1. 가격 데이터 가져오기 (RSI, MDD 계산용)
    df = yf.download(ticker_symbol, period="1y", interval="1d")
    
    # RSI (14) 계산
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1].values[0]
    
    # MDD 계산 (1년 최고점 대비)
    rolling_max = df['Close'].cummax()
    drawdown = (df['Close'] - rolling_max) / rolling_max
    current_mdd = drawdown.iloc[-1].values[0] * 100
    
    # 2. VIX 지수 가져오기
    vix_df = yf.download("^VIX", period="1d")
    current_vix = vix_df['Close'].iloc[-1]
    
    return round(rsi, 2), round(current_mdd, 2), round(current_vix, 2)

# --- 실행 버튼 및 로직 ---
if st.button("🔄 실시간 지표 불러오기 및 계산"):
    with st.spinner('야후 파이낸스에서 데이터를 가져오는 중...'):
        rsi_val, mdd_val, vix_val = get_live_indicators(ticker_symbol)
        
        # 가중치 판단 로직 (제시해주신 표 기준)
        # 1. RSI 가중치
        if rsi_val <= 30: rsi_w = 3.5
        elif rsi_val <= 40: rsi_w = 2.2
        elif rsi_val <= 50: rsi_w = 1.2
        elif rsi_val <= 60: rsi_w = 0.8
        else: rsi_w = 0.5

        # 2. MDD 가중치
        if "NASDAQ" in asset_choice:
            if mdd_val <= -25: mdd_w = 5.0
            elif mdd_val <= -15: mdd_w = 3.0
            elif mdd_val <= -8: mdd_w = 1.5
            elif mdd_val <= -3: mdd_w = 0.8
            else: mdd_w = 0.4
        else: # S&P 500
            if mdd_val <= -20: mdd_w = 5.0
            elif mdd_val <= -12: mdd_w = 3.0
            elif mdd_val <= -5: mdd_w = 1.5
            elif mdd_val <= -2: mdd_w = 0.8
            else: mdd_w = 0.4

        # 3. VIX 가중치
        if vix_val >= 35: vix_w = 3.0
        elif vix_val >= 25: vix_w = 1.8
        elif vix_val >= 18: vix_w = 1.2
        else: vix_w = 0.7

        total_multiplier = round(rsi_w + mdd_w + vix_w, 2)
        today_buy = int(base_amount * total_multiplier)

        # 결과 화면 출력
        st.success(f"데이터 업데이트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("현재 RSI", f"{rsi_val}")
        col2.metric("현재 MDD", f"{mdd_val}%")
        col3.metric("현재 VIX", f"{vix_val}")
        col4.metric("합산 가중치", f"{total_multiplier}x")

        st.divider()
        
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.info(f"**기본 1일 매수액:** {base_amount:,} 원")
            st.write(f"(계산식: 총 예산 {total_budget:,}원 ÷ {split_days}일)")
        
        with res_col2:
            st.warning(f"### 🎯 오늘 최종 매수액: {today_buy:,} 원")
            st.write(f"계산: 기본 {base_amount:,}원 × {total_multiplier}배")

else:
    st.info("왼쪽 사이드바에서 예산을 설정한 후 '실시간 지표 불러오기' 버튼을 눌러주세요.")

st.divider()
st.caption("참고: 실시간 데이터는 Yahoo Finance API를 통해 제공되며 10~15분 정도 지연될 수 있습니다.")
