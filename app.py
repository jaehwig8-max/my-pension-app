import streamlit as st
import yfinance as yf
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="지적 나침반 (Budget Mode)", layout="wide")

# --- 블랙 테마 커스텀 스타일 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #ffffff !important; }
    
    /* 입력창 라벨 색상 강제 지정 */
    .stNumberInput label { color: #3b82f6 !important; font-weight: bold !important; }
    
    .metric-card {
        background-color: #111111;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333333;
        text-align: center;
    }
    
    .recommendation-box {
        padding: 30px;
        border-radius: 20px;
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border: 2px solid #fbbf24;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 0 30px rgba(251, 191, 36, 0.2);
    }
    
    .amount-text {
        font-size: 3.2rem;
        font-weight: 900;
        color: #fbbf24;
        text-shadow: 0 0 15px rgba(251, 191, 36, 0.6);
        margin: 10px 0;
    }

    .weight-info {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 5px;
    }
    
    section[data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #222; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none;
        padding: 15px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 수집 함수 ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=300)
def get_market_data():
    results = {}
    tickers = {"QQQ": "QQQ", "SPY": "SPY", "VIX": "^VIX"}
    for name, ticker in tickers.items():
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        curr = hist['Close'].iloc[-1]
        if name != "VIX":
            high = hist['Close'].max()
            rsi = calculate_rsi(hist['Close']).iloc[-1]
            mdd = ((curr - high) / high) * 100
            results[name] = {"price": curr, "rsi": rsi, "mdd": mdd}
        else:
            results[name] = {"price": curr}
    return results

# --- 가중치 로직 ---
def get_weights(target, rsi, mdd, vix):
    # RSI 가중치
    if rsi <= 30: r_w = 3.5
    elif rsi <= 40: r_w = 2.2
    elif rsi <= 50: r_w = 1.2
    elif rsi <= 60: r_w = 0.8
    else: r_w = 0.5
    
    # MDD 가중치
    if target == "QQQ":
        if mdd <= -25: m_w = 5.0
        elif mdd <= -15: m_w = 3.0
        elif mdd <= -8: m_w = 1.5
        elif mdd <= -3: m_w = 0.8
        else: m_w = 0.4
    else: # SPY
        if mdd <= -20: m_w = 5.0
        elif mdd <= -12: m_w = 3.0
        elif mdd <= -5: m_w = 1.5
        elif mdd <= -2: m_w = 0.8
        else: m_w = 0.4
        
    # VIX 가중치
    if vix >= 35: v_w = 3.0
    elif vix >= 25: v_w = 1.8
    elif vix >= 18: v_w = 1.2
    else: v_w = 0.7
    
    return r_w, m_w, v_w

# --- 화면 구성 ---
metrics = get_market_data()

st.title("🧭 지적 나침반 (Intellectual Compass)")

# 1. 사이드바: 예산 및 기간 입력
with st.sidebar:
    st.header("💰 투자 예산 설정")
    st.markdown("---")
    user_total_budget = st.number_input("총 투자 예산 (원)", min_value=0, value=10000000, step=1000000, help="전체 투자할 총 금액을 입력하세요.")
    user_total_rounds = st.number_input("분할 매수 기간 (회차)", min_value=1, value=20, step=1, help="총 몇 번에 나누어 매수할지 입력하세요.")
    
    base_unit = user_total_budget / user_total_rounds if user_total_rounds > 0 else 0
    
    st.markdown("---")
    st.write("### 📋 계산 기준")
    st.metric("1회 기본 매수액", f"{base_unit:,.0f} 원")
    st.caption("위 금액에 지표별 가중치가 곱해집니다.")

# 2. 메인 화면: 실시간 지표 상시 표시
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.markdown(f'<div class="metric-card"><h4 style="color:#60a5fa;">QQQ (나스닥)</h4><p>RSI: {metrics["QQQ"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["QQQ"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
with m_col2:
    st.markdown(f'<div class="metric-card"><h4 style="color:#34d399;">SPY (S&P500)</h4><p>RSI: {metrics["SPY"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["SPY"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
with m_col3:
    v_val = metrics["VIX"]["price"]
    st.markdown(f'<div class="metric-card"><h4 style="color:#fbbf24;">VIX (공포지수)</h4><p style="font-size:1.5rem; font-weight:bold;">{v_val:.2f}</p></div>', unsafe_allow_html=True)

st.divider()

# 3. 매수 계산 로직
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.markdown("### 🎯 금일 매수 전략")
    target_mode = st.radio("매수 대상을 선택하세요", ["나스닥 100 (QQQ)", "S&P 500 (SPY)"], horizontal=True)
    target_key = "QQQ" if "나스닥" in target_mode else "SPY"
    
    if st.button("📈 오늘의 매수 금액 확인하기"):
        r_val = metrics[target_key]['rsi']
        m_val = metrics[target_key]['mdd']
        v_val = metrics['VIX']['price']
        
        # 가중치 계산
        rw, mw, vw = get_weights(target_key, r_val, m_val, v_val)
        final_multiplier = rw + mw + vw
        final_amount = base_unit * final_multiplier

        with col_r:
            st.markdown(f"""
                <div class="recommendation-box">
                    <div style="font-size: 1.1rem; color: #94a3b8;">합산 배수: {final_multiplier:.1f}x</div>
                    <div style="margin: 5px 0; font-size: 1.4rem; font-weight: bold;">오늘의 권장 매수액</div>
                    <div class="amount-text">{final_amount:,.0f} 원</div>
                    <div class="weight-info">
                        RSI({rw:.1f}x) + MDD({mw:.1f}x) + VIX({vw:.1f}x)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 투자 조언 메시지
            if final_multiplier >= 5.0:
                st.error("🚨 **강력 매수 구간:** 지표가 매우 저평가되어 있습니다.")
            elif final_multiplier >= 3.0:
                st.warning("⚠️ **적극 매수 구간:** 하락 추세 속 매수 기회입니다.")
            else:
                st.info("✅ **정기 매수 구간:** 원칙에 따른 분할 매수 단계입니다.")

st.divider()
st.caption(f"최종 업데이트: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | 실시간 Yahoo Finance 데이터 기반")
