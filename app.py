import streamlit as st

# 페이지 설정
st.set_page_config(page_title="미국 지수 ETF 분할매수 계산기", layout="centered")

st.title("📊 미국 지수 ETF 일단위 분할매수 가이드")
st.caption("RSI, MDD, VIX 가중치를 합산하여 최적의 매수 금액을 결정합니다.")

# 1. 입력 섹션
st.sidebar.header("🛠️ 입력 설정")
base_amount = st.sidebar.number_input("기본 매수액 (단위: 원)", min_value=0, value=100000, step=10000)
asset_choice = st.sidebar.selectbox("대상 지수 선택", ["NASDAQ 100", "S&P 500"])

st.subheader("🌐 오늘의 시장 지표 입력")
col1, col2, col3 = st.columns(3)

with col1:
    rsi_val = st.number_input("RSI (14)", min_value=0.0, max_value=100.0, value=40.0, help="상대강도지수")
with col2:
    mdd_val = st.number_input("MDD (%)", max_value=0.0, value=-5.0, help="고점 대비 하락률 (반드시 음수 입력)")
with col3:
    vix_val = st.number_input("VIX 지수", min_value=0.0, value=20.0, help="공포 지수/변동성 지수")

# 2. 가중치 계산 로직
def get_weights(asset, rsi, mdd, vix):
    # RSI 가중치 (공통)
    if rsi <= 30: rsi_w, rsi_msg = 3.5, "과매도: 공격적 추가 매수"
    elif rsi <= 40: rsi_w, rsi_msg = 2.2, "하락추세: 비중 확대"
    elif rsi <= 50: rsi_w, rsi_msg = 1.2, "중립이하: 정기 매수 유지"
    elif rsi <= 60: rsi_w, rsi_msg = 0.8, "중립이상: 비중 소폭 축소"
    else: rsi_w, rsi_msg = 0.5, "과열구간: 최소 수량 유지"

    # MDD 가중치 (지수별 차등)
    if asset == "NASDAQ 100":
        if mdd <= -25: mdd_w, mdd_msg = 5.0, "폭락: 자산 재배분 및 강력 매수"
        elif mdd <= -15: mdd_w, mdd_msg = 3.0, "강한 조정: 적극적 분할 매수"
        elif mdd <= -8: mdd_w, mdd_msg = 1.5, "건전한 조정: 비중 확대 시작"
        elif mdd <= -3: mdd_w, mdd_msg = 0.8, "일반적 변동: 비중 유지"
        else: mdd_w, mdd_msg = 0.4, "신고가 근접: 관망 및 현금 비축"
    else: # S&P 500
        if mdd <= -20: mdd_w, mdd_msg = 5.0, "폭락: 자산 재배분 및 강력 매수"
        elif mdd <= -12: mdd_w, mdd_msg = 3.0, "강한 조정: 적극적 분할 매수"
        elif mdd <= -5: mdd_w, mdd_msg = 1.5, "건전한 조정: 비중 확대 시작"
        elif mdd <= -2: mdd_w, mdd_msg = 0.8, "일반적 변동: 비중 유지"
        else: mdd_w, mdd_msg = 0.4, "신고가 근접: 관망 및 현금 비축"

    # VIX 가중치 (공통)
    if vix >= 35: vix_w, vix_msg = 3.0, "극도의 공포: 기계적 대량 매수"
    elif vix >= 25: vix_w, vix_msg = 1.8, "변동성 확대: 비중 확대 적극 고려"
    elif vix >= 18: vix_w, vix_msg = 1.2, "주의 필요: 완만한 분할 매수"
    else: vix_w, vix_msg = 0.7, "평온한 상태: 시장 관망 및 원칙 매수"

    return (rsi_w, rsi_msg), (mdd_w, mdd_msg), (vix_w, vix_msg)

(rsi_w, rsi_m), (mdd_w, mdd_m), (vix_w, vix_m) = get_weights(asset_choice, rsi_val, mdd_val, vix_val)
total_multiplier = round(rsi_w + mdd_w + vix_w, 2)
final_buy_amount = int(base_amount * total_multiplier)

# 3. 결과 출력
st.divider()
st.subheader("📝 계산 결과")

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric("합산 가중치 배수", f"{total_multiplier}x")
    st.write(f"계산식: {rsi_w}(RSI) + {mdd_w}(MDD) + {vix_w}(VIX)")

with res_col2:
    st.metric("오늘의 최종 매수액", f"{final_buy_amount:,} 원")
    st.write(f"기본 매수액: {base_amount:,} 원")

# 상세 분석 표
with st.expander("🔍 지표별 상세 대응 전략 확인"):
    st.write(f"**1. RSI ({rsi_val}):** {rsi_m} (가중치 {rsi_w}x)")
    st.write(f"**2. MDD ({mdd_val}%):** {mdd_m} (가중치 {mdd_w}x)")
    st.write(f"**3. VIX ({vix_val}):** {vix_m} (가중치 {vix_w}x)")

st.warning("⚠️ 본 앱은 사용자가 입력한 수치에 기반한 전략적 가이드일 뿐, 투자 결과에 대한 책임은 본인에게 있습니다.")
