import streamlit as st
import yfinance as yf
import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# --- 1. 페이지 및 테마 설정 ---
st.set_page_config(page_title="미국 지수 ETF 분할매수 가이드", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, h5, p, span, label { color: #ffffff !important; }
    .stNumberInput label { color: #3b82f6 !important; font-weight: bold !important; }
    
    .metric-container {
        background-color: #111111;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333333;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .result-card {
        padding: 30px;
        border-radius: 20px;
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border: 2px solid #fbbf24;
        text-align: center;
        box-shadow: 0 0 25px rgba(251, 191, 36, 0.2);
    }
    
    .final-amount {
        font-size: 3.5rem;
        font-weight: 900;
        color: #fbbf24;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
        margin: 10px 0;
    }
    
    .formula-badge {
        background-color: #334155;
        padding: 5px 15px;
        border-radius: 50px;
        font-size: 0.9rem;
        color: #cbd5e1;
    }

    section[data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 수집 로직 (에러 방지 적용) ---
def get_safe_session():
    session = Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'})
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def fetch_market_metrics():
    session = get_safe_session()
    data = {}
    try:
        for name, ticker in {"QQQ": "QQQ", "SPY": "SPY", "VIX": "^VIX"}.items():
            obj = yf.Ticker(ticker, session=session)
            hist = obj.history(period="2y")
            if hist.empty: return None, f"{name} 데이터를 불러오지 못했습니다."
            
            curr = hist['Close'].iloc[-1]
            if name != "VIX":
                peak = hist['Close'].max()
                rsi = calculate_rsi(hist['Close']).iloc[-1]
                mdd = ((curr - peak) / peak) * 100
                data[name] = {"price": curr, "rsi": rsi, "mdd": mdd}
            else:
                data[name] = {"price": curr}
        return data, None
    except Exception as e:
        return None, str(e)

# --- 3. 가중치 계산 엔진 (가이드라인 반영) ---
def get_strategy_weights(target, rsi, mdd, vix):
    # RSI 가중치 (공통)
    if rsi <= 30: rw = 3.5
    elif rsi <= 40: rw = 2.2
    elif rsi <= 50: rw = 1.2
    elif rsi <= 60: rw = 0.8
    else: rw = 0.5
    
    # MDD 가중치 (나스닥 vs S&P500 차등 적용)
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
        
    # VIX 가중치 (공통)
    if vix >= 35: vw = 3.0
    elif vix >= 25: vw = 1.8
    elif vix >= 18: vw = 1.2
    else: vw = 0.7
    
    return rw, mw, vw

# --- 4. 메인 화면 구성 ---
metrics, error = fetch_market_metrics()

st.title("📊 미국 지수 ETF 분할매수 가이드")
st.markdown("<p style='color:#888;'>RSI + MDD + VIX 지표 기반 가중치 합산 전략</p>", unsafe_allow_html=True)

if error:
    st.error(f"⚠️ 데이터 로드 오류: {error}")
    st.info("야후 파이낸스 접속량이 많습니다. 잠시 후 새로고침 해주세요.")
    st.stop()

# 상단 대시보드
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="metric-container"><h4 style="color:#60a5fa;">QQQ (NASDAQ)</h4><p>RSI: {metrics["QQQ"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["QQQ"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-container"><h4 style="color:#34d399;">SPY (S&P 500)</h4><p>RSI: {metrics["SPY"]["rsi"]:.1f} | MDD: <span style="color:#f87171;">{metrics["SPY"]["mdd"]:.1f}%</span></p></div>', unsafe_allow_html=True)
with c3:
    v_val = metrics["VIX"]["price"]
    st.markdown(f'<div class="metric-container"><h4 style="color:#fbbf24;">VIX (공포지수)</h4><p style="font-size:1.4rem; font-weight:bold;">{v_val:.2f}</p></div>', unsafe_allow_html=True)

st.divider()

# 입력 및 계산부
with st.sidebar:
    st.header("⚙️ 투자 설정")
    total_budget = st.number_input("총 투자 예산 (원)", min_value=0, value=10000000, step=1000000)
    total_rounds = st.number_input("분할 매수 기간 (회차)", min_value=1, value=20)
    base_amount = total_budget / total_rounds if total_rounds > 0 else 0
    st.markdown(f"**1회 기본 매수액:** `{base_amount:,.0f}원`")

col_l, col_r = st.columns([1, 1.3])

with col_l:
    st.subheader("🎯 전략 선택")
    target_sel = st.selectbox("투자할 지수 ETF를 선택하세요", ["나스닥 100 (QQQ)", "S&P 500 (SPY)"])
    target_key = "QQQ" if "나스닥" in target_sel else "SPY"
    
    if st.button("🚀 금일 매수 금액 산출하기"):
        r_val, m_val, v_val = metrics[target_key]['rsi'], metrics[target_key]['mdd'], metrics['VIX']['price']
        rw, mw, vw = get_strategy_weights(target_key, r_val, m_val, v_val)
        
        final_mult = rw + mw + vw
        final_buy = base_amount * final_mult

        with col_r:
            st.markdown(f"""
                <div class="result-card">
                    <span class="formula-badge">최종 가중치: {final_mult:.1f}배</span>
                    <div style="margin-top:15px; font-size:1.2rem; color:#cbd5e1;">오늘의 권장 매수액</div>
                    <div class="final-amount">{final_buy:,.0f} 원</div>
                    <div style="color:#94a3b8; font-size:0.9rem; margin-top:10px;">
                        산출 근거: RSI({rw:.1f}x) + MDD({mw:.1f}x) + VIX({vw:.1f}x)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 전략 메시지
            if final_mult >= 5.0:
                st.error("🚨 **적극적 비중 확대:** 시장이 매우 저평가되었습니다.")
            elif final_mult >= 3.0:
                st.warning("⚠️ **분할 매수 강화:** 하락장을 이용한 수량 확보 구간입니다.")
            else:
                st.info("✅ **정기 분할 매수:** 원칙에 따라 매수를 진행하세요.")

st.divider()
st.caption(f"데이터 갱신: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | 실시간 지표 기반 가이드")
