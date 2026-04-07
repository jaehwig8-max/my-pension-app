import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Index Buy Strategy",
    page_icon="🧭",
    layout="centered"
)

# 2. 스타일 커스텀
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🧭 지수별 분할매수 전략 계산기")
st.info("시장의 공포와 과열을 지표로 판단하여 최적의 매수 비중을 제안합니다.")

# 3. 사이드바: 투자 설정
with st.sidebar:
    st.header("💰 나의 투자 설정")
    total_budget = st.number_input("총 투자 예정 금액 (원)", min_value=0, value=10000000, step=1000000)
    buy_count = st.number_input("총 매수 횟수 (회)", min_value=1, value=20)
    
    # 표준 매수 금액 계산 (1.0x)
    standard_unit = total_budget / buy_count
    st.divider()
    st.metric("표준 매수 금액 (1.0x)", f"{standard_unit:,.0f}원")
    st.caption("※ 시장 지표가 '중립'일 때 매수할 기준 금액입니다.")

# 4. 메인: 지표 입력
st.subheader("📊 실시간 시장 지표 입력")
col_idx1, col_idx2, col_idx3 = st.columns(3)

with col_idx1:
    rsi = st.slider("RSI (상대강도지수)", 0, 100, 50, help="70 이상 과열, 30 이하 과매도")
with col_idx2:
    mdd = st.number_input("MDD (현재 낙폭 %)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
with col_idx3:
    vix = st.number_input("VIX (변동성 지수)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)

# 5. 전략 판단 로직
def calculate_strategy(target, rsi, mdd, vix):
    # 나스닥 100 (QQQ) 로직
    if target == "QQQ":
        if rsi <= 35 or mdd >= 20 or vix >= 30:
            return "공포 (Panic)", 2.5, "🔥 강력 매수 (공격적 기회 포착)"
        elif 40 <= rsi <= 50 or 8 <= mdd <= 15 or 20 <= vix <= 28:
            return "조정 (Correction)", 1.75, "📈 하락 시 추가 매수 (비중 확대)"
        elif rsi >= 70 or mdd < 2 or vix < 12:
            return "과열 (Overheat)", 0.3, "⚠️ 매수 최소화, 현금 비중 확대"
        else:
            return "중립 (Neutral)", 1.0, "✅ 계획된 수량만큼 정기 매수"
    
    # S&P 500 (SPY) 로직
    else:
        if rsi <= 30 or mdd >= 15 or vix >= 28:
            return "기회 (Opportunity)", 2.0, "💎 저점 분할 매수 찬스"
        elif 35 <= rsi <= 45 or 6 <= mdd <= 10 or 19 <= vix <= 25:
            return "약세 (Weakness)", 1.5, "🔍 하단 지지선 확인 후 비중 확대"
        elif rsi >= 70 or mdd < 1 or vix < 12:
            return "고점 (Peak)", 0.3, "🛑 추격 매수 금지, 수익 실현 고려"
        else:
            return "안정 (Stable)", 1.0, "🏠 자산 배분 원칙 준수 매수"

# 6. 결과 출력 섹션
st.divider()
tab1, tab2 = st.tabs(["나스닥 100 (QQQ)", "S&P 500 (SPY)"])

with tab1:
    state, weight, action = calculate_strategy("QQQ", rsi, mdd, vix)
    final_buy = standard_unit * weight
    
    c1, c2 = st.columns([1, 2])
    c1.metric("시장 상태", state)
    c1.metric("권장 가중치", f"{weight}x")
    c2.success(f"**오늘의 QQQ 매수 제안액**\n### {final_buy:,.0f} 원")
    st.info(f"**Action Plan:** {action}")

with tab2:
    state, weight, action = calculate_strategy("SPY", rsi, mdd, vix)
    final_buy = standard_unit * weight
    
    c1, c2 = st.columns([1, 2])
    c1.metric("시장 상태", state)
    c1.metric("권장 가중치", f"{weight}x")
    c2.primary_container = True
    c2.info(f"**오늘의 SPY 매수 제안액**\n### {final_buy:,.0f} 원")
    st.info(f"**Action Plan:** {action}")

# 7. 현금 관리 로그 가이드
st.sidebar.divider()
if weight < 1.0:
    saved_cash = standard_unit - final_buy
    st.sidebar.warning(f"💡 오늘은 평소보다 아낀 매수금 **{saved_cash:,.0f}원**을 파킹통장에 적립하세요!")
