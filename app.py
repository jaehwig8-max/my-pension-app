import streamlit as st
import yfinance as yf
import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# --- 페이지 설정 ---
st.set_page_config(page_title="지적 나침반 (Stability Mode)", layout="wide")

# --- 블랙 테마 커스텀 스타일 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #ffffff !important; }
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
    section[data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #222; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none;
        padding: 15px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 안정적인 데이터 수집을 위한 세션 설정 ---
def get_session():
    session = Session()
    # 서버 차단을 피하기 위해 브라우저인 척 위장합니다.
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    # 재시도 로직 설정
    retry = Retry(
        total=5, 
        backoff_factor=1, 
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Streamlit 자체 캐시 기능을 사용하여 요청 횟수를 조절합니다 (1시간 유지)
@st.cache_data(ttl=3600)
def get_market_data():
    results = {}
    session = get_session()
    tickers = {"QQQ": "QQQ", "SPY": "SPY", "VIX": "^VIX"}
    
    try:
        for name, ticker_symbol in tickers.items():
            t = yf.Ticker(ticker_symbol, session=session)
            # 데이터 범위를 늘려 안정적으로 가져옵니다.
            hist = t.history(period="2y") 
            if hist.empty:
                return None, f"{name} 데이터를 가져오는 데 실패했습니다."
                
            curr = hist['Close'].iloc[-1]
            if name != "VIX":
                high = hist['Close'].max()
                rsi = calculate_rsi(hist['Close']).iloc[-1]
                mdd = ((curr - high) / high) * 100
                results[name] = {"price": curr, "rsi": rsi, "mdd": mdd}
            else:
                results[name] = {"price": curr}
        return results, None
    except Exception as e:
        return None, str(e)

# --- 앱 실행 로직 ---
metrics, error_msg = get_market_data()

st.title("🧭 지적 나침반 (Stability Mode)")

# 에러가 발생했을 경우 안내
if error_msg:
    st.error(f"⚠️ 데이터 로드 중 오류가 발생했습니다.")
    st.info("잠시 후 페이지를 새로고침(F5) 해주세요. 야후 서버 상태에 따라 수 분이 소요될 수 있습니다.")
    st.stop()

# 1. 사이드바 설정
with st.sidebar:
    st.header("💰 투자 예산 설정")
    user_total_budget = st.number_input("총 투자 예산 (원)", min_value=0, value=10000000, step=1000000)
    user_total_rounds = st.number_input("분할 매수 기간 (회차)", min_value=1, value=20)
    base_unit = user_total_budget / user_total_rounds if user_total_rounds > 0 else 0
    st.metric("1회 기본 매수액", f"{base_unit:,.0f} 원")

# 2. 메인 화면 지표 표시
m_col1, m_col2, m_col3 = st.columns(3)
if metrics:
    with m_col1:
        st.markdown(f'<div class="metric-card"><h4 style="color:#60a5fa;">QQQ (나스닥)</h4><p>RSI: {metrics["QQQ"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["QQQ"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-card"><h4 style="color:#34d399;">SPY (S&P500)</h4><p>RSI: {metrics["SPY"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["SPY"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-card"><h4 style="color:#fbbf24;">VIX (공포지수)</h4><p style="font-size:1.5rem; font-weight:bold;">{metrics["VIX"]["price"]:.2f}</p></div>', unsafe_allow_html=True)

st.divider()

# 3. 매수 계산 로직
def get_weights(target, rsi, mdd, vix):
    # RSI 가중치
    if rsi <= 30: rw = 3.5
    elif rsi <= 40: rw = 2.2
    elif rsi <= 50: rw = 1.2
    elif rsi <= 60: rw = 0.8
    else: rw = 0.5
    # MDD 가중치
    if target == "QQQ":
        if mdd <= -25: mw = 5.0
        elif mdd <= -15: mw = 3.0
        elif mdd <= -8: mw = 1.5
        elif mdd <= -3: mw = 0.8
        else: mw = 0.4
    else: # SPY
        if mdd <= -20: mw = 5.0
        elif mdd <= -12: mw = 3.0
        elif mdd <= -5: mw = 1.5
        elif mdd <= -2: mw = 0.8
        else: mw = 0.4
    # VIX 가중치
    if vix >= 35: vw = 3.0
    elif vix >= 25: vw = 1.8
    elif vix >= 18: vw = 1.2
    else: vw = 0.7
    return rw, mw, vw

col_l, col_r = st.columns([1, 1.2])
with col_l:
    st.markdown("### 🎯 금일 매수 전략")
    target_mode = st.radio("매수 대상", ["나스닥 100 (QQQ)", "S&P 500 (SPY)"], horizontal=True)
    target_key = "QQQ" if "나스닥" in target_mode else "SPY"
    
    if st.button("📈 금액 산출하기"):
        r, m, v = metrics[target_key]['rsi'], metrics[target_key]['mdd'], metrics['VIX']['price']
        rw, mw, vw = get_weights(target_key, r, m, v)
        final_mult = rw + mw + vw
        final_amt = base_unit * final_mult

        with col_r:
            st.markdown(f"""
                <div class="recommendation-box">
                    <div style="font-size: 1.1rem; color: #94a3b8;">합산 배수: {final_mult:.1f}x</div>
                    <div class="amount-text">{final_amt:,.0f} 원</div>
                    <div style="color:#94a3b8;">RSI({rw}) + MDD({mw}) + VIX({vw})</div>
                </div>
                """, unsafe_allow_html=True)

st.divider()
st.caption(f"데이터 기준: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | 1시간 간격 자동 갱신")
