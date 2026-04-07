import streamlit as st
import yfinance as yf
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="지적 나침반 (Intellectual Compass)", layout="wide")

# --- 스타일 적용 (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .recommendation-box { padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; background-color: #eff6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 계산 로직 함수 ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_market_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="1y")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    current_price = hist['Close'].iloc[-1]
    high_price = hist['Close'].max()
    
    rsi = calculate_rsi(hist['Close']).iloc[-1]
    mdd = ((current_price - high_price) / high_price) * 100
    
    return current_price, rsi, mdd, vix

# --- 사이드바: 투자 환경 설정 ---
st.sidebar.header("⚙️ 나의 투자 환경 설정")
total_budget = st.sidebar.number_input("총 운용 자산 (원)", min_value=0, value=10000000, step=1000000)
total_rounds = st.sidebar.number_input("목표 매수 기간 (회차)", min_value=1, value=20)
base_unit = total_budget / total_rounds

st.sidebar.markdown(f"**기본 표준 유닛:** {base_unit:,.0f}원")

# --- 메인 화면 ---
st.title("🧭 지적 나침반 (Intellectual Compass)")
st.caption("RSI, MDD, VIX 기반 스마트 투자 가이드")

col1, col2 = st.columns([1, 1])

with col1:
    mode = st.radio("📊 분석 모드 선택", ["나스닥 (QQQ)", "S&P 500 (SPY)"])
    ticker_map = {"나스닥 (QQQ)": "QQQ", "S&P 500 (SPY)": "SPY"}
    selected_ticker = ticker_map[mode]

if st.button("🔄 현재 시장 지표 자동 수집"):
    with st.spinner("데이터 분석 중..."):
        price, rsi, mdd, vix = get_market_data(selected_ticker)
        
        # 가중치 계산 로직 (예시 알고리즘)
        # 1. RSI 가중치: 30이하(과매도)일 때 높음
        rsi_weight = 1.5 if rsi < 30 else (1.2 if rsi < 40 else 1.0)
        # 2. MDD 가중치: 하락폭이 클수록 높음
        mdd_weight = 1.4 if mdd < -15 else (1.2 if mdd < -10 else 1.0)
        # 3. VIX 가중치: 공포지수 30이상일 때 높음
        vix_weight = 1.3 if vix > 30 else (1.1 if vix > 20 else 1.0)
        
        final_multiplier = (rsi_weight + mdd_weight + vix_weight) / 3
        recommended_amount = base_unit * final_multiplier

        # 결과 표시
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"${price:.2f}")
        c2.metric("RSI (상대강도)", f"{rsi:.1f}")
        c3.metric("MDD (낙폭)", f"{mdd:.1f}%")
        c4.metric("VIX (공포)", f"{vix:.1f}")

        st.subheader("🎯 최종 투자 전략")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.write(f"### 권장 매수 배수: **{final_multiplier:.2f}x**")
            st.markdown(f"""
            <div class="recommendation-box">
                <h2 style='margin:0;'>권장 매수액</h2>
                <h1 style='color:#3b82f6; margin:10px 0;'>{recommended_amount:,.0f} 원</h1>
            </div>
            """, unsafe_allow_html=True)

        with res_col2:
            opinion = "적극 매수" if final_multiplier >= 1.3 else ("분할 매수" if final_multiplier >= 1.0 else "관망/비중 축소")
            st.info(f"**투자 의견:** {opinion}")
            st.write("알고리즘 분석 결과, 현재 시장은 " + 
                     ("과매도 구간으로 공격적인 진입이 유리합니다." if opinion == "적극 매수" 
                      else "평온한 상태이며 원칙대로 분할 매수를 권장합니다."))

st.divider()
st.warning("⚠️ 본 앱은 투자 참고용 가이드라인이며, 최종 투자 결정과 그에 따른 책임은 투자자 본인에게 있습니다.")
