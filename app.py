import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="실시간 지수 매수 전략", page_icon="📈", layout="wide")

# 2. 데이터 로드 함수 (캐싱 처리로 속도 향상)
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_live_indicators():
    # 티커 설정 (QQQ, SPY, VIX)
    tickers = ["QQQ", "SPY", "^VIX"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365) # 1년치 데이터
    
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    
    results = {}
    for ticker in ["QQQ", "SPY"]:
        # RSI (14일 기준)
        rsi = ta.rsi(data[ticker], length=14).iloc[-1]
        
        # MDD 계산 (최고점 대비 하락률)
        rolling_max = data[ticker].cummax()
        daily_drawdown = (data[ticker] / rolling_max) - 1.0
        mdd = abs(daily_drawdown.iloc[-1] * 100)
        
        results[ticker] = {"rsi": rsi, "mdd": mdd}
    
    # VIX 지수
    results["VIX"] = data["^VIX"].iloc[-1]
    return results

# 3. 전략 판단 로직 (제공해주신 가이드라인 기준)
def get_action_plan(ticker, rsi, mdd, vix):
    if ticker == "QQQ":
        if rsi <= 35 or mdd >= 20 or vix >= 30:
            return "공포 (Panic)", 2.5, "🔥 강력 매수 (공격적 기회 포착)"
        elif 40 <= rsi <= 50 or 8 <= mdd <= 15 or 20 <= vix <= 28:
            return "조정 (Correction)", 1.75, "📈 하락 시 추가 매수 (비중 확대)"
        elif rsi >= 70 or mdd < 2 or vix < 12:
            return "과열 (Overheat)", 0.3, "⚠️ 매수 최소화, 현금 비중 확대"
        else:
            return "중립 (Neutral)", 1.0, "✅ 계획된 수량만큼 정기 매수"
    else: # SPY
        if rsi <= 30 or mdd >= 15 or vix >= 28:
            return "기회 (Opportunity)", 2.0, "💎 저점 분할 매수 찬스"
        elif 35 <= rsi <= 45 or 6 <= mdd <= 10 or 19 <= vix <= 25:
            return "약세 (Weakness)", 1.5, "🔍 하단 지지선 확인 후 비중 확대"
        elif rsi >= 70 or mdd < 1 or vix < 12:
            return "고점 (Peak)", 0.3, "🛑 추격 매수 금지, 수익 실현 고려"
        else:
            return "안정 (Stable)", 1.0, "🏠 자산 배분 원칙 준수 매수"

# --- UI 시작 ---
st.title("🧭 실시간 지수별 분할매수 가이드")

# 데이터 불러오기
try:
    with st.spinner('실시간 시장 데이터를 불러오는 중...'):
        live_data = get_live_indicators()
    
    # 사이드바 투자 설정
    st.sidebar.header("💰 투자 설정")
    total_budget = st.sidebar.number_input("총 투자 원금 (원)", value=10000000, step=1000000)
    buy_period = st.sidebar.number_input("매수 기간 (회)", value=20, min_value=1)
    standard_unit = total_budget / buy_period
    
    st.sidebar.divider()
    st.sidebar.metric("표준 매수 금액 (1.0x)", f"{standard_unit:,.0f}원")

    # 메인 지표 현황
    st.subheader(f"📊 현재 시장 지표 (업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')})")
    c1, c2, c3 = st.columns(3)
    c1.metric("VIX (변동성)", f"{live_data['VIX']:.2f}")
    c2.metric("QQQ RSI", f"{live_data['QQQ']['rsi']:.2f}")
    c3.metric("SPY RSI", f"{live_data['SPY']['rsi']:.2f}")

    # 결과 분석
    st.divider()
    t1, t2 = st.tabs(["나스닥 100 (QQQ)", "S&P 500 (SPY)"])

    for tab, ticker in zip([t1, t2], ["QQQ", "SPY"]):
        with tab:
            rsi_val = live_data[ticker]['rsi']
            mdd_val = live_data[ticker]['mdd']
            vix_val = live_data['VIX']
            
            state, weight, action = get_action_plan(ticker, rsi_val, mdd_val, vix_val)
            today_buy = standard_unit * weight
            
            col_res1, col_res2 = st.columns([1, 1])
            with col_res1:
                st.markdown(f"### 현재 상태: **{state}**")
                st.write(f"- RSI: {rsi_val:.2f}")
                st.write(f"- MDD: {mdd_val:.2f}%")
                st.info(f"**전략: {action}**")
            
            with col_res2:
                st.metric("권장 매수 가중치", f"{weight}x")
                st.success(f"**오늘의 권장 매수액**\n## {today_buy:,.0f} 원")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("장 마감 시간이나 네트워크 상태를 확인해 주세요.")

st.caption("주의: 본 앱은 지표 기반 가이드라인일 뿐, 최종 투자 결정의 책임은 본인에게 있습니다.")
