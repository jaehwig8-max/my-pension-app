import streamlit as st
import yfinance as yf
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="지적 나침반 (Intellectual Compass)", layout="wide")

# --- 커스텀 스타일 (가독성 개선) ---
st.markdown("""
    <style>
    /* 메인 배경색 */
    .stApp { background-color: #fcfcfc; }
    
    /* 상단 지표 박스 스타일 */
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 권장 매수액 박스 (고대비 수정) */
    .recommendation-box {
        padding: 25px;
        border-radius: 15px;
        background-color: #1e293b; /* 어두운 네이비 배경 */
        color: #ffffff;           /* 흰색 글자 */
        text-align: center;
        margin-top: 20px;
    }
    .amount-text {
        font-size: 2.5rem;
        font-weight: 800;
        color: #fbbf24; /* 밝은 노란색으로 강조 */
        margin: 10px 0;
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

@st.cache_data(ttl=300) # 5분마다 데이터 갱신
def get_all_metrics():
    tickers = {"QQQ": "QQQ", "SPY": "SPY", "VIX": "^VIX"}
    results = {}
    for name, sym in tickers.items():
        t = yf.Ticker(sym)
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

# --- 데이터 로드 ---
metrics = get_all_metrics()

# --- 상단 대시보드 (상시 표시) ---
st.title("🧭 지적 나침반 (Intellectual Compass)")
st.subheader("📊 실시간 시장 지표 상황판")

m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.markdown(f"""<div class="metric-card">
    <h4 style='color:#3b82f6;'>NASDAQ 100 (QQQ)</h4>
    <p><b>RSI:</b> {metrics['QQQ']['rsi']:.1f} | <b>MDD:</b> {metrics['QQQ']['mdd']:.1f}%</p>
    </div>""", unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""<div class="metric-card">
    <h4 style='color:#10b981;'>S&P 500 (SPY)</h4>
    <p><b>RSI:</b> {metrics['SPY']['rsi']:.1f} | <b>MDD:</b> {metrics['SPY']['mdd']:.1f}%</p>
    </div>""", unsafe_allow_html=True)

with m_col3:
    vix_val = metrics['VIX']['price']
    vix_color = "#ef4444" if vix_val > 25 else "#6b7280"
    st.markdown(f"""<div class="metric-card">
    <h4 style='color:{vix_color};'>VIX (공포지수)</h4>
    <p style='font-size:1.2rem; font-weight:bold;'>{vix_val:.2f}</p>
    </div>""", unsafe_allow_html=True)

st.divider()

# --- 사이드바 및 설정 ---
st.sidebar.header("⚙️ 투자 환경 설정")
total_budget = st.sidebar.number_input("총 운용 자산 (원)", min_value=0, value=10000000, step=1000000)
total_rounds = st.sidebar.number_input("목표 매수 기간 (회차)", min_value=1, value=20)
base_unit = total_budget / total_rounds

# --- 메인 계산 영역 ---
col_set, col_res = st.columns([1, 1.2])

with col_set:
    st.write("### 1. 전략 선택")
    mode = st.radio("매수 대상 선택", ["나스닥 (QQQ)", "S&P 500 (SPY)"])
    target_key = "QQQ" if "나스닥" in mode else "SPY"
    
    st.write("### 2. 계산하기")
    if st.button("🚀 현재가 기준 매수액 산출"):
        # 지표 가져오기
        rsi = metrics[target_key]['rsi']
        mdd = metrics[target_key]['mdd']
        vix = metrics['VIX']['price']
        
        # 가중치 알고리즘
        rsi_w = 1.6 if rsi < 30 else (1.3 if rsi < 40 else 1.0)
        mdd_w = 1.5 if mdd < -15 else (1.2 if mdd < -10 else 1.0)
        vix_w = 1.4 if vix > 30 else (1.2 if vix > 20 else 1.0)
        
        multiplier = (rsi_w + mdd_w + vix_w) / 3
        final_amount = base_unit * multiplier

        with col_res:
            st.write("### 3. 분석 결과")
            # 결과 박스 (어두운 배경에 밝은 글씨로 수정)
            st.markdown(f"""
                <div class="recommendation-box">
                    <div style="font-size: 1.1rem; opacity: 0.8;">권장 매수 배수: {multiplier:.2f}x</div>
                    <div style="margin: 10px 0; font-size: 1.2rem;">오늘의 권장 매수액</div>
                    <div class="amount-text">{final_amount:,.0f} 원</div>
                    <div style="margin-top: 15px; font-weight: bold; color: #6EE7B7;">
                        분석 모드: {mode}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 투자 의견 보조 설명
            opinion = "강력 매수" if multiplier >= 1.4 else ("분할 매수" if multiplier >= 1.0 else "보수적 관망")
            st.success(f"💡 **AI 가이드 의견:** 현재 시장은 **[{opinion}]** 단계입니다.")

st.divider()
st.caption("※ 본 앱은 투자 참고용이며, 모든 투자의 책임은 본인에게 있습니다. 데이터는 Yahoo Finance에서 실시간으로 제공됩니다.")
