<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>지적 나침반: 맞춤형 자산 & 기간 설정 투자 앱</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
        body { font-family: 'Noto Sans KR', sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; overflow-x: hidden; }
        .card { background: #1e293b; border-radius: 1.5rem; border: 1px solid #334155; }
        .accent-gradient { background: linear-gradient(135deg, #3b82f6, #8b5cf6); }
        input[type="range"] { accent-color: #3b82f6; height: 12px; border-radius: 6px; }
        input[type="number"] { background: #0f172a; border: 1px solid #334155; color: #f8fafc; border-radius: 0.75rem; padding: 0.5rem 1rem; outline: none; }
        input[type="number"]:focus { border-color: #3b82f6; ring: 2px; ring-color: #3b82f6; }
        .sync-loading { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body class="p-4 md:p-8 min-h-screen flex items-center justify-center">
    <div class="max-w-4xl w-full mx-auto">
        <!-- Header -->
        <header class="mb-10 text-center">
            <h1 class="text-4xl font-extrabold mb-3 tracking-tight">지적 나침반 <span class="text-blue-500 font-mono">Custom</span></h1>
            <p class="text-slate-400 font-light text-sm">개인별 운용 자산 및 기간 맞춤 매수 전략</p>
        </header>

        <!-- Live Sync Button -->
        <div class="flex flex-col items-center mb-8">
            <button id="btn-sync" onclick="syncMarketData()" class="accent-gradient hover:opacity-90 text-white px-8 py-4 rounded-2xl font-bold shadow-2xl flex items-center transition-all transform hover:scale-105 active:scale-95 group">
                <svg id="sync-icon" class="w-6 h-6 mr-3 group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span id="sync-text">현재 시장 지표 자동 수집</span>
            </button>
            <p id="last-update" class="text-[11px] text-slate-500 mt-3 italic font-medium">상태: 연결 대기 중</p>
        </div>

        <!-- Strategy Settings (New) -->
        <div class="card p-8 mb-8 border-t-4 border-blue-500">
            <h2 class="text-sm font-bold mb-6 text-blue-400 uppercase tracking-widest flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                나의 투자 환경 설정
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="flex flex-col space-y-2">
                    <label class="text-[10px] text-slate-500 font-black uppercase">기본 운용 자산 (원)</label>
                    <input type="number" id="input-total-asset" value="100000000" step="1000000" oninput="calculate()" placeholder="예: 100,000,000">
                </div>
                <div class="flex flex-col space-y-2">
                    <label class="text-[10px] text-slate-500 font-black uppercase">목표 매수 기간 (회차)</label>
                    <input type="number" id="input-buy-count" value="100" step="1" min="1" oninput="calculate()" placeholder="예: 100회">
                </div>
                <div class="flex flex-col space-y-2">
                    <label class="text-[10px] text-slate-500 font-black uppercase">계산된 표준 유닛 (1회)</label>
                    <div id="display-unit" class="text-xl font-bold text-white py-2 px-1">0원</div>
                </div>
            </div>
        </div>

        <!-- Asset Selection -->
        <div class="flex space-x-2 p-1 bg-slate-900 rounded-2xl border border-slate-700 mb-8 max-w-sm mx-auto">
            <button id="btn-nasdaq" onclick="switchMode('nasdaq')" class="flex-1 py-3 rounded-xl font-bold transition-all bg-blue-600 text-white shadow-lg text-sm">나스닥 (QQQ)</button>
            <button id="btn-snp500" onclick="switchMode('snp500')" class="flex-1 py-3 rounded-xl font-bold transition-all text-slate-500 hover:text-white text-sm">S&P 500 (SPY)</button>
        </div>

        <!-- Main Dashboard -->
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
            <div class="lg:col-span-3 card p-8 relative overflow-hidden">
                <div id="loading-overlay" class="absolute inset-0 bg-slate-900/90 backdrop-blur-md z-20 flex flex-col items-center justify-center hidden">
                    <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4 shadow-[0_0_15px_#3b82f6]"></div>
                    <div class="text-blue-400 font-bold animate-pulse text-sm tracking-widest uppercase">실시간 지표 검색 중...</div>
                </div>
                
                <h2 class="text-lg font-bold mb-8 flex items-center text-blue-400">
                    <span class="w-2 h-5 bg-blue-500 rounded-full mr-3 shadow-[0_0_10px_#3b82f6]"></span>
                    지표 수동 조정
                </h2>
                <div class="space-y-12">
                    <div>
                        <div class="flex justify-between items-end mb-4">
                            <label class="text-xs font-bold text-blue-300/70 uppercase">RSI (Relative Strength)</label>
                            <span id="val-rsi" class="text-3xl font-black text-blue-400">50</span>
                        </div>
                        <input type="range" id="input-rsi" min="10" max="90" step="0.1" value="50" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer" oninput="calculate()">
                    </div>
                    <div>
                        <div class="flex justify-between items-end mb-4">
                            <label class="text-xs font-bold text-red-300/70 uppercase">MDD (Drawdown)</label>
                            <span id="val-mdd" class="text-3xl font-black text-red-400">0%</span>
                        </div>
                        <input type="range" id="input-mdd" min="0" max="50" step="0.1" value="0" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer" oninput="calculate()">
                    </div>
                    <div>
                        <div class="flex justify-between items-end mb-4">
                            <label class="text-xs font-bold text-orange-300/70 uppercase">VIX (Volatility)</label>
                            <span id="val-vix" class="text-3xl font-black text-orange-400">15</span>
                        </div>
                        <input type="range" id="input-vix" min="10" max="60" step="0.1" value="15" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer" oninput="calculate()">
                    </div>
                </div>
            </div>

            <!-- Investment Verdict -->
            <div class="lg:col-span-2 card p-8 flex flex-col justify-between border-2 border-blue-500/30 shadow-[0_0_40px_rgba(59,130,246,0.1)]">
                <div>
                    <p class="text-[10px] text-slate-500 mb-2 font-black uppercase tracking-widest">금일 권장 매수액</p>
                    <h3 id="final-amount" class="text-4xl font-black text-white mb-2 tracking-tighter">0원</h3>
                    <div id="final-multiplier" class="inline-block px-3 py-1 rounded-lg bg-blue-500/10 text-blue-400 text-[10px] font-black border border-blue-500/20">
                        가중치 합계: 1.0X
                    </div>
                </div>

                <div class="mt-8 space-y-3">
                    <div class="flex justify-between text-[11px] p-3 bg-slate-900/50 rounded-xl border border-slate-700/50">
                        <span class="text-slate-500 font-bold">RSI 비중</span>
                        <span id="m-rsi" class="font-mono font-bold text-blue-400">0.4x</span>
                    </div>
                    <div class="flex justify-between text-[11px] p-3 bg-slate-900/50 rounded-xl border border-slate-700/50">
                        <span class="text-slate-500 font-bold">MDD 비중</span>
                        <span id="m-mdd" class="font-mono font-bold text-red-400">0.4x</span>
                    </div>
                    <div class="flex justify-between text-[11px] p-3 bg-slate-900/50 rounded-xl border border-slate-700/50">
                        <span class="text-slate-500 font-bold">VIX 비중</span>
                        <span id="m-vix" class="font-mono font-bold text-orange-400">0.2x</span>
                    </div>
                    <div class="pt-6 mt-2">
                        <div class="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl">
                            <p id="status-desc" class="text-xs text-blue-200/90 leading-relaxed font-medium">
                                자산과 기간을 설정한 후 실시간 지표를 수집해 보세요.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="text-center text-[10px] text-slate-600 uppercase tracking-widest opacity-50">
            실시간 인베스팅 및 네이버 금융 데이터 연동 시스템
        </footer>
    </div>

    <script>
        let currentMode = 'nasdaq';
        const apiKey = ""; 

        const config = {
            nasdaq: {
                rsi: [ {t: 70, m: 0.1}, {t: 60, m: 0.2}, {t: 50, m: 0.4}, {t: 40, m: 0.8}, {t: 30, m: 1.5}, {t: 0, m: 2.5} ],
                mdd: [ {t: 20, m: 2.0}, {t: 15, m: 1.5}, {t: 10, m: 1.0}, {t: 5, m: 0.5}, {t: 0, m: 0.2} ],
                vix: [ {t: 40, m: 1.5}, {t: 30, m: 1.0}, {t: 25, m: 0.5}, {t: 20, m: 0.2}, {t: 0, m: 0.1} ]
            },
            snp500: {
                rsi: [ {t: 70, m: 0.1}, {t: 60, m: 0.3}, {t: 50, m: 0.6}, {t: 40, m: 1.2}, {t: 30, m: 2.0}, {t: 0, m: 3.0} ],
                mdd: [ {t: 15, m: 2.0}, {t: 10, m: 1.2}, {t: 7, m: 0.8}, {t: 3, m: 0.4}, {t: 0, m: 0.2} ],
                vix: [ {t: 35, m: 1.5}, {t: 28, m: 1.0}, {t: 22, m: 0.6}, {t: 18, m: 0.3}, {t: 0, m: 0.1} ]
            }
        };

        async function syncMarketData() {
            const btn = document.getElementById('btn-sync');
            const icon = document.getElementById('sync-icon');
            const text = document.getElementById('sync-text');
            const statusLabel = document.getElementById('last-update');
            const overlay = document.getElementById('loading-overlay');
            
            btn.disabled = true;
            icon.classList.add('animate-spin');
            overlay.classList.remove('hidden');
            text.innerText = "시장 데이터 조회 중...";
            statusLabel.innerText = "상태: 실시간 지표를 분석하고 있습니다...";

            const modeName = currentMode === 'nasdaq' ? "나스닥100 QQQ" : "S&P500 SPY";
            const prompt = `오늘의 ${modeName} 시장 지표를 분석해주세요. 
            필수 항목: 14일 RSI 수치, 52주 신고가 대비 하락률(MDD %), 현재 VIX 지수.
            JSON 형식으로만 답변: {"rsi": 숫자, "mdd": 숫자, "vix": 숫자}`;

            try {
                const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{ parts: [{ text: prompt }] }],
                        tools: [{ "google_search": {} }]
                    })
                });

                const result = await response.json();
                const jsonMatch = result.candidates[0].content.parts[0].text.match(/\{[\s\S]*?\}/);
                
                if (jsonMatch) {
                    const data = JSON.parse(jsonMatch[0]);
                    document.getElementById('input-rsi').value = data.rsi;
                    document.getElementById('input-mdd').value = Math.abs(data.mdd);
                    document.getElementById('input-vix').value = data.vix;
                    
                    statusLabel.innerText = `성공: ${new Date().toLocaleTimeString()} 업데이트 완료`;
                    statusLabel.className = "text-[11px] text-green-400 mt-3 italic font-bold";
                    calculate();
                }
            } catch (error) {
                statusLabel.innerText = "오류: 데이터 수집에 실패했습니다. 수동 조절을 이용하세요.";
                statusLabel.className = "text-[11px] text-red-400 mt-3 italic font-bold";
            } finally {
                btn.disabled = false;
                icon.classList.remove('animate-spin');
                overlay.classList.add('hidden');
                text.innerText = "현재 시장 지표 자동 수집";
            }
        }

        function switchMode(mode) {
            currentMode = mode;
            const isNasdaq = mode === 'nasdaq';
            document.getElementById('btn-nasdaq').className = isNasdaq ? 'flex-1 py-3 rounded-xl font-bold transition-all bg-blue-600 text-white shadow-lg text-sm' : 'flex-1 py-3 rounded-xl font-bold text-slate-500 hover:text-white text-sm';
            document.getElementById('btn-snp500').className = !isNasdaq ? 'flex-1 py-3 rounded-xl font-bold transition-all bg-blue-600 text-white shadow-lg text-sm' : 'flex-1 py-3 rounded-xl font-bold text-slate-500 hover:text-white text-sm';
            calculate();
        }

        function getMultiplier(type, value) {
            const rules = config[currentMode][type];
            for(let rule of rules) {
                if(value >= rule.t) return rule.m;
            }
            return rules[rules.length-1].m;
        }

        function calculate() {
            // Inputs
            const totalAsset = parseFloat(document.getElementById('input-total-asset').value) || 0;
            const buyCount = parseFloat(document.getElementById('input-buy-count').value) || 1;
            
            // Calculate Standard Unit
            const standardUnit = totalAsset / buyCount;
            document.getElementById('display-unit').innerText = Math.round(standardUnit).toLocaleString() + '원';

            // Market Indicators
            const rsi = parseFloat(document.getElementById('input-rsi').value);
            const mdd = parseFloat(document.getElementById('input-mdd').value);
            const vix = parseFloat(document.getElementById('input-vix').value);

            document.getElementById('val-rsi').innerText = rsi.toFixed(1);
            document.getElementById('val-mdd').innerText = mdd.toFixed(1) + '%';
            document.getElementById('val-vix').innerText = vix.toFixed(1);

            const mRsi = getMultiplier('rsi', rsi);
            const mMdd = getMultiplier('mdd', mdd);
            const mVix = getMultiplier('vix', vix);

            document.getElementById('m-rsi').innerText = mRsi.toFixed(1) + 'x';
            document.getElementById('m-mdd').innerText = mMdd.toFixed(1) + 'x';
            document.getElementById('m-vix').innerText = mVix.toFixed(1) + 'x';

            const totalMultiplier = mRsi + mMdd + mVix;
            const finalAmount = Math.round(standardUnit * totalMultiplier);

            document.getElementById('final-amount').innerText = finalAmount.toLocaleString() + '원';
            document.getElementById('final-multiplier').innerText = `가중치 합계: ${totalMultiplier.toFixed(1)}X`;

            let desc = "";
            if(totalMultiplier < 1.0) desc = "⚠️ 시장 과열 구간입니다. 추가 매수보다는 현금을 비축하며 조정을 기다리세요.";
            else if(totalMultiplier < 2.5) desc = "✅ 안정적인 분할 매수 구간입니다. 자산 배분 원칙에 따라 꾸준히 수량을 늘리세요.";
            else desc = "🔥 강력 매수 기회! 공포 지수가 높고 낙폭이 큽니다. 비중 확대를 적극 고려할 시점입니다.";
            document.getElementById('status-desc').innerText = desc;
        }

        window.onload = calculate;
    </script>
</body>
</html>

