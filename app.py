import streamlit as st

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="S&P 500 분할매수 가이드", layout="centered")

# 사용자 정의 CSS (형광색 포인트 및 깔끔한 레이아웃)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stNumberInput, .stSlider { margin-bottom: 20px; }
    .buy-amount { 
        font-size: 2.5rem; 
        font-weight: bold; 
        color: #EAFF00; 
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 S&P 500 초정밀 분할매수 계산기")
st.caption("퇴직여행자(Retirement Traveler) 전용 전략 가이드")

# 2. 사이드바: 기본 설정
st.sidebar.header("⚙️ 기본 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (원)", value=80000000, step=1000000)
invest_days = st.sidebar.number_input("총 투자 기간 (일)", value=180)
base_amount = total_budget / invest_days

st.sidebar.write(f"**기본 매수액:** {base_amount:,.0f}원 / 일")

# 3. 메인 화면: 지표 입력
st.subheader("📝 오늘의 시장 지표 입력")

col1, col2, col3 = st.columns(3)

with col1:
    vix = st.number_input("VIX (변동성)", value=15.0, step=0.1)
with col2:
    mdd = st.number_input("MDD (고점대비 %)", value=0.0, step=0.1, help="현재 하락폭을 마이너스(-)로 입력하세요.")
with col3:
    rsi = st.number_input("RSI (14일 기준)", value=50.0, step=0.1)

# 4. 가중치 로직 함수
def get_weights(vix, mdd, rsi):
    # VIX 가중치
    if vix >= 35: v_w = 3.0
    elif vix >= 28: v_w = 2.2
    elif vix >= 22: v_w = 1.5
    elif vix >= 18: v_w = 1.0
    else: v_w = 0.6

    # MDD 가중치
    if mdd <= -20: m_w = 5.0
    elif mdd <= -15: m_w = 3.5
    elif mdd <= -10: m_w = 2.5
    elif mdd <= -5: m_w = 1.5
    elif mdd <= -2: m_w = 0.8
    else: m_w = 0.3

    # RSI 가중치
    if rsi <= 25: r_w = 4.0
    elif rsi <= 35: r_w = 3.0
    elif rsi <= 45: r_w = 1.8
    elif rsi <= 55: r_w = 1.0
    elif rsi <= 65: r_w = 0.6
    else: r_w = 0.3
    
    return v_w, m_w, r_w

v_w, m_w, r_w = get_weights(vix, mdd, rsi)
total_weight = v_w + m_w + r_w
final_buy = base_amount * total_weight

# 5. 결과 출력
st.markdown("---")
st.subheader("💰 오늘의 최종 매수 권장액")
st.markdown(f'<div class="buy-amount">{final_buy:,.0f} 원</div>', unsafe_allow_html=True)

st.write(f"**현재 총 가중치 배수:** {total_weight:.1f}배")

# 6. 지표별 상세 가중치 리포트
with st.expander("🔍 가중치 적용 상세 내역 확인"):
    st.write(f"- VIX 가중치: `{v_w}`")
    st.write(f"- MDD 가중치: `{m_w}`")
    st.write(f"- RSI 가중치: `{r_w}`")
    st.info("오늘의 매수액 = 기본 매수액 × (VIX + MDD + RSI)")
