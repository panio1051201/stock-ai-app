/**
 * 小白功能 JS - 新增功能介面
 */

// ================================
// 1. 股票健檢功能
// ================================

async function showStockReview() {
    const code = document.getElementById('stock-input').value.trim();
    if (!code) {
        alert('請輸入股票代碼');
        return;
    }
    
    const buyPrice = prompt('輸入您的成本價（可選）:', '');
    
    showLoading('分析中...');
    
    try {
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                code: code,
                buy_price: buyPrice ? parseFloat(buyPrice) : null
            })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        displayReviewResult(data);
        
    } catch (error) {
        hideLoading();
        showError('網路錯誤，請稍後再試');
    }
}

function displayReviewResult(data) {
    const resultArea = document.getElementById('result-area');
    
    const ratingColor = {
        '🟢': '#3fb950',
        '🟡': '#f1c40f', 
        '🔴': '#f85149'
    };
    
    const color = ratingColor[data.rating] || '#8b949e';
    
    const reasonsHtml = (data.reasons || []).map(r => `<li>${r}</li>`).join('');
    
    let profitHtml = '';
    if (data.profit && data.profit.roi !== undefined) {
        const profitColor = data.profit.roi >= 0 ? '#3fb950' : '#f85149';
        profitHtml = `
            <div class="profit-info" style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-top: 15px;">
                <div style="color: #8b949e; font-size: 12px;">您的持倉</div>
                <div style="font-size: 14px; margin-top: 5px;">
                    成本: <span style="color: #fff">$${data.profit.buy_price}</span> → 
                    現價: <span style="color: #fff">$${data.profit.current_price}</span>
                </div>
                <div style="font-size: 20px; font-weight: bold; margin-top: 10px; color: ${profitColor}">
                    ${data.profit.roi >= 0 ? '🟢' : '🔴'} ${data.profit.profit_text}
                </div>
            </div>
        `;
    }
    
    resultArea.innerHTML = `
        <div class="card" style="border-left: 4px solid ${color};">
            <div style="text-align: center; padding: 20px 0;">
                <div style="font-size: 48px; margin-bottom: 10px;">${data.rating}</div>
                <div style="font-size: 28px; font-weight: bold; color: ${color};">${data.rating_text}</div>
                <div style="color: #8b949e; margin-top: 10px;">總分 ${data.total_score} 分</div>
            </div>
            
            <div style="text-align: center; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 15px;">
                <div style="font-size: 14px; color: #8b949e;">適合</div>
                <div style="font-size: 18px; color: #fff; margin-top: 5px;">${data.for_who || '一般投資人'}</div>
            </div>
            
            <div class="signal-box sig-${data.rating === '🟢' ? 'buy' : data.rating === '🔴' ? 'sell' : 'hold'}">
                <div style="font-size: 14px; margin-bottom: 10px;">參考原因：</div>
                <ul style="margin: 0; padding-left: 20px; text-align: left; font-size: 13px;">
                    ${reasonsHtml || '<li>資料不足</li>'}
                </ul>
            </div>
            
            ${profitHtml}
            
            <div style="margin-top: 20px; padding: 15px; background: #0d1117; border-radius: 8px; font-size: 14px; line-height: 1.8;">
                <div style="color: #58a6ff; font-weight: bold; margin-bottom: 10px;">📝 簡單說：</div>
                <div style="white-space: pre-line; color: #c9d1d9;">${data.beginner_summary || '分析中...'}</div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 15px; font-size: 12px; color: #8b949e;">
                <div style="text-align: center;">
                    <div>技術面</div>
                    <div style="color: #fff; font-size: 16px;">${data.details?.tech_score || 'N/A'}</div>
                </div>
                <div style="text-align: center;">
                    <div>價值面</div>
                    <div style="color: #fff; font-size: 16px;">${data.details?.value_score || 'N/A'}</div>
                </div>
                <div style="text-align: center;">
                    <div>籌碼面</div>
                    <div style="color: #fff; font-size: 16px;">${data.details?.chip_score || 'N/A'}</div>
                </div>
            </div>
        </div>
    `;
    
    resultArea.style.display = 'block';
    window.scrollTo({top: resultArea.offsetTop - 20, behavior: 'smooth'});
}

// ================================
// 2. 我的持股功能
// ================================

let portfolioData = null;

async function showPortfolio() {
    showLoading('載入中...');
    
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        hideLoading();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        portfolioData = data;
        displayPortfolio(data);
        
    } catch (error) {
        hideLoading();
        showError('載入失敗');
    }
}

function displayPortfolio(data) {
    const resultArea = document.getElementById('result-area');
    
    const totalClass = data.profit_rate >= 0 ? 'profit' : 'loss';
    const totalEmoji = data.profit_rate >= 0 ? '🟢' : '🔴';
    const totalSign = data.profit_rate >= 0 ? '+' : '';
    
    let stocksHtml = '';
    if (data.stocks && data.stocks.length > 0) {
        stocksHtml = data.stocks.map(s => {
            const rowClass = s.profit >= 0 ? 'profit' : 'loss';
            const emoji = s.profit >= 0 ? '🟢' : '🔴';
            return `
                <tr class="${rowClass}" style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 12px;">
                        <div style="font-weight: bold;">${s.code}</div>
                        <div style="font-size: 12px; color: #8b949e;">${s.name}</div>
                    </td>
                    <td style="text-align: center;">${s.shares}</td>
                    <td style="text-align: right;">$${s.buy_price.toFixed(2)}</td>
                    <td style="text-align: right;">$${s.current_price.toFixed(2)}</td>
                    <td style="text-align: right; font-weight: bold;">
                        ${emoji} $${Math.abs(s.profit).toFixed(0)}
                        <div style="font-size: 11px; color: ${s.profit >= 0 ? '#3fb950' : '#f85149'}">${totalSign}${s.profit_rate.toFixed(2)}%</div>
                    </td>
                </tr>
            `;
        }).join('');
    } else {
        stocksHtml = '<tr><td colspan="5" style="text-align: center; padding: 30px; color: #8b949e;">目前沒有持股</td></tr>';
    }
    
    resultArea.innerHTML = `
        <div class="card">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: #0d1117; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 12px; color: #8b949e;">總資產</div>
                    <div style="font-size: 24px; font-weight: bold; color: #fff;">$${data.total_assets?.toLocaleString() || 0}</div>
                </div>
                <div style="background: #0d1117; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 12px; color: #8b949e;">總賺虧</div>
                    <div style="font-size: 24px; font-weight: bold; color: ${totalClass === 'profit' ? '#3fb950' : '#f85149'};">
                        ${totalEmoji} $${Math.abs(data.total_profit || 0).toLocaleString()}
                    </div>
                    <div style="font-size: 12px; color: ${totalClass === 'profit' ? '#3fb950' : '#f85149'}">${totalSign}${(data.profit_rate || 0).toFixed(2)}%</div>
                </div>
            </div>
            
            <button onclick="showAddStockModal()" style="
                width: 100%; padding: 12px; background: #238636; color: #fff; 
                border: none; border-radius: 8px; cursor: pointer; font-size: 14px; margin-bottom: 15px;">
                ➕ 新增持股
            </button>
            
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background: #21262d;">
                        <th style="padding: 10px; text-align: left;">股票</th>
                        <th style="padding: 10px; text-align: center;">股數</th>
                        <th style="padding: 10px; text-align: right;">成本</th>
                        <th style="padding: 10px; text-align: right;">現價</th>
                        <th style="padding: 10px; text-align: right;">賺虧</th>
                    </tr>
                </thead>
                <tbody>
                    ${stocksHtml}
                </tbody>
            </table>
        </div>
    `;
    
    resultArea.style.display = 'block';
}

function showAddStockModal() {
    const code = prompt('股票代碼:');
    if (!code) return;
    
    const shares = prompt('股數:');
    if (!shares) return;
    
    const price = prompt('買入價格:');
    if (!price) return;
    
    addStockToPortfolio(code, parseInt(shares), parseFloat(price));
}

async function addStockToPortfolio(code, shares, price) {
    try {
        const response = await fetch('/api/portfolio/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                code: code,
                shares: shares,
                buy_price: price
            })
        });
        
        const data = await response.json();
        alert(data.message);
        
        if (data.success) {
            showPortfolio();
        }
    } catch (error) {
        alert('新增失敗');
    }
}

// ================================
// 3. 好股雷達功能
// ================================

async function showStockRadar() {
    const resultArea = document.getElementById('result-area');
    resultArea.innerHTML = `
        <div class="card">
            <div style="margin-bottom: 15px;">
                <h3 style="margin: 0 0 15px 0;">📡 好股雷達</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="loadRadar('safe')" class="radar-btn" style="
                        flex: 1; min-width: 45%; padding: 12px; background: #21262d; 
                        border: 1px solid #30363d; color: #fff; border-radius: 8px; cursor: pointer;">
                        💰 穩健選股
                    </button>
                    <button onclick="loadRadar('value')" class="radar-btn" style="
                        flex: 1; min-width: 45%; padding: 12px; background: #21262d; 
                        border: 1px solid #30363d; color: #fff; border-radius: 8px; cursor: pointer;">
                        📊 價值挖掘
                    </button>
                    <button onclick="loadRadar('dividend')" class="radar-btn" style="
                        flex: 1; min-width: 45%; padding: 12px; background: #21262d; 
                        border: 1px solid #30363d; color: #fff; border-radius: 8px; cursor: pointer;">
                        🏦 高息定存
                    </button>
                    <button onclick="loadRadar('trend')" class="radar-btn" style="
                        flex: 1; min-width: 45%; padding: 12px; background: #21262d; 
                        border: 1px solid #30363d; color: #fff; border-radius: 8px; cursor: pointer;">
                        📈 趨勢追蹤
                    </button>
                </div>
            </div>
            <div id="radar-results" style="text-align: center; padding: 30px; color: #8b949e;">
                點擊上方按鈕開始篩選
            </div>
        </div>
    `;
    resultArea.style.display = 'block';
}

async function loadRadar(type) {
    const resultsDiv = document.getElementById('radar-results');
    resultsDiv.innerHTML = '<div style="padding: 30px;">載入中...</div>';
    
    try {
        const response = await fetch(`/api/radar?type=${type}`);
        const data = await response.json();
        
        if (data.error) {
            resultsDiv.innerHTML = `<div style="padding: 30px; color: #f85149;">${data.error}</div>`;
            return;
        }
        
        const titles = {
            safe: '💰 穩健選股',
            value: '📊 價值挖掘', 
            dividend: '🏦 高息定存',
            trend: '📈 趨勢追蹤'
        };
        
        let html = `<h4 style="margin: 0 0 15px 0;">${titles[type] || type}</h4>`;
        
        if (!data.results || data.results.length === 0) {
            html += '<div style="padding: 20px; color: #8b949e;">找不到符合條件的股票</div>';
        } else {
            data.results.forEach((stock, i) => {
                const scoreColor = stock.score >= 80 ? '#3fb950' : stock.score >= 70 ? '#f1c40f' : '#8b949e';
                html += `
                    <div style="
                        display: flex; align-items: center; padding: 12px; 
                        background: #0d1117; border-radius: 8px; margin-bottom: 8px;
                        border-left: 3px solid ${scoreColor};
                    ">
                        <div style="width: 30px; text-align: center; font-size: 12px; color: #8b949e;">#${i + 1}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: bold;">${stock.code} ${stock.name}</div>
                            <div style="font-size: 12px; color: #8b949e;">${stock.reason || ''}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: bold;">$${stock.price?.toFixed(2) || 'N/A'}</div>
                            <div style="font-size: 12px; color: ${scoreColor};">${stock.score}分</div>
                        </div>
                    </div>
                `;
            });
        }
        
        resultsDiv.innerHTML = html;
        
    } catch (error) {
        resultsDiv.innerHTML = '<div style="padding: 30px; color: #f85149;">載入失敗</div>';
    }
}

// ================================
// 4. 模擬炒股功能
// ================================

let traderData = null;

async function showVirtualTrader() {
    showLoading('載入中...');
    
    try {
        const response = await fetch('/api/trader/account');
        const data = await response.json();
        hideLoading();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        traderData = data;
        displayTrader(data);
        
    } catch (error) {
        hideLoading();
        showError('載入失敗');
    }
}

function displayTrader(data) {
    const resultArea = document.getElementById('result-area');
    
    const totalClass = data.profit_rate >= 0 ? 'profit' : 'loss';
    const totalEmoji = data.profit_rate >= 0 ? '🟢' : '🔴';
    const totalSign = data.profit_rate >= 0 ? '+' : '';
    
    let positionsHtml = '';
    if (data.positions && data.positions.length > 0) {
        positionsHtml = data.positions.map(p => {
            const emoji = p.profit >= 0 ? '🟢' : '🔴';
            return `
                <div style="display: flex; justify-content: space-between; padding: 10px; background: #0d1117; border-radius: 6px; margin-bottom: 8px;">
                    <div>
                        <div style="font-weight: bold;">${p.code}</div>
                        <div style="font-size: 12px; color: #8b949e;">${p.shares} 股 @ $${p.avg_price.toFixed(2)}</div>
                    </div>
                    <div style="text-align: right;">
                        <div>$${p.value?.toLocaleString()}</div>
                        <div style="font-size: 12px; color: ${p.profit >= 0 ? '#3fb950' : '#f85149'};">
                            ${emoji} ${totalSign}${p.profit_rate.toFixed(2)}%
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        positionsHtml = '<div style="text-align: center; padding: 20px; color: #8b949e;">目前沒有持倉</div>';
    }
    
    resultArea.innerHTML = `
        <div class="card">
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 12px; color: #8b949e;">虛擬帳戶</div>
                <div style="font-size: 36px; font-weight: bold; color: #fff;">$${data.total_assets?.toLocaleString() || 0}</div>
                <div style="font-size: 18px; color: ${totalClass === 'profit' ? '#3fb950' : '#f85149'};">
                    ${totalEmoji} $${Math.abs(data.total_profit || 0).toLocaleString()} (${totalSign}${data.profit_rate?.toFixed(2)}%)
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; font-size: 12px;">
                <div style="text-align: center; padding: 10px; background: #0d1117; border-radius: 8px;">
                    <div style="color: #8b949e;">可用現金</div>
                    <div style="font-weight: bold; color: #fff;">$${data.cash?.toLocaleString()}</div>
                </div>
                <div style="text-align: center; padding: 10px; background: #0d1117; border-radius: 8px;">
                    <div style="color: #8b949e;">市值</div>
                    <div style="font-weight: bold; color: #fff;">$${data.stock_value?.toLocaleString()}</div>
                </div>
                <div style="text-align: center; padding: 10px; background: #0d1117; border-radius: 8px;">
                    <div style="color: #8b949e;">勝率</div>
                    <div style="font-weight: bold; color: #fff;">${data.win_count || 0}勝 ${data.lose_count || 0}敗</div>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <button onclick="showTradeModal('buy')" style="
                    flex: 1; padding: 12px; background: #238636; color: #fff; 
                    border: none; border-radius: 8px; cursor: pointer;">
                    📥 買入
                </button>
                <button onclick="showTradeModal('sell')" style="
                    flex: 1; padding: 12px; background: #da3633; color: #fff; 
                    border: none; border-radius: 8px; cursor: pointer;">
                    📤 賣出
                </button>
                <button onclick="resetTrader()" style="
                    padding: 12px 15px; background: #30363d; color: #fff; 
                    border: none; border-radius: 8px; cursor: pointer;">
                    🔄
                </button>
            </div>
            
            <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #8b949e;">持倉</h4>
            ${positionsHtml}
        </div>
    `;
    
    resultArea.style.display = 'block';
}

function showTradeModal(action) {
    const code = prompt('股票代碼:');
    if (!code) return;
    
    const shares = prompt('股數:');
    if (!shares) return;
    
    const price = prompt('價格:');
    if (!price) return;
    
    executeTrade(action, code, parseInt(shares), parseFloat(price));
}

async function executeTrade(action, code, shares, price) {
    try {
        const endpoint = action === 'buy' ? '/api/trader/buy' : '/api/trader/sell';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                code: code,
                shares: shares,
                price: price
            })
        });
        
        const data = await response.json();
        alert(data.message);
        
        if (data.success) {
            showVirtualTrader();
        }
    } catch (error) {
        alert('交易失敗');
    }
}

async function resetTrader() {
    if (!confirm('確定要重置帳戶嗎？所有資料將會清除！')) return;
    
    try {
        await fetch('/api/trader/reset');
        showVirtualTrader();
    } catch (error) {
        alert('重置失敗');
    }
}

// ================================
// 5. 價格警報功能
// ================================

async function showPriceAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        
        const resultArea = document.getElementById('result-area');
        
        let alertsHtml = '';
        if (data.alerts && data.alerts.length > 0) {
            alertsHtml = data.alerts.map(a => {
                const cond = a.condition === 'above' ? '⬆️ 突破' : '⬇️ 跌破';
                return `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #0d1117; border-radius: 8px; margin-bottom: 8px;">
                        <div>
                            <div style="font-weight: bold;">${a.code} ${a.name || ''}</div>
                            <div style="font-size: 12px; color: #8b949e;">${cond} $${a.target_price}</div>
                        </div>
                        <button onclick="removeAlert('${a.id}')" style="padding: 5px 10px; background: #30363d; border: none; color: #fff; border-radius: 4px; cursor: pointer;">刪除</button>
                    </div>
                `;
            }).join('');
        } else {
            alertsHtml = '<div style="text-align: center; padding: 30px; color: #8b949e;">目前沒有警報</div>';
        }
        
        resultArea.innerHTML = `
            <div class="card">
                <h3 style="margin: 0 0 15px 0;">🔔 價格警報</h3>
                
                <button onclick="showAddAlertModal()" style="
                    width: 100%; padding: 12px; background: #238636; color: #fff; 
                    border: none; border-radius: 8px; cursor: pointer; margin-bottom: 15px;">
                    ➕ 新增警報
                </button>
                
                ${alertsHtml}
            </div>
        `;
        
        resultArea.style.display = 'block';
        
    } catch (error) {
        showError('載入失敗');
    }
}

function showAddAlertModal() {
    const code = prompt('股票代碼:');
    if (!code) return;
    
    const price = prompt('目標價格:');
    if (!price) return;
    
    const condition = confirm('選擇條件：\n確定 = 高於\n取消 = 低於') ? 'above' : 'below';
    
    addAlert(code, parseFloat(price), condition);
}

async function addAlert(code, price, condition) {
    try {
        await fetch('/api/alerts/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                code: code,
                target_price: price,
                condition: condition
            })
        });
        
        showPriceAlerts();
    } catch (error) {
        alert('新增失敗');
    }
}

async function removeAlert(alertId) {
    try {
        await fetch(`/api/alerts/remove/${alertId}`);
        showPriceAlerts();
    } catch (error) {
        alert('刪除失敗');
    }
}

// ================================
// 輔助函式
// ================================

function showLoading(text = '載入中...') {
    const resultArea = document.getElementById('result-area');
    resultArea.innerHTML = `
        <div class="card" style="text-align: center; padding: 50px;">
            <div style="font-size: 24px; animation: pulse 1s infinite;">⏳</div>
            <div style="margin-top: 15px; color: #8b949e;">${text}</div>
        </div>
    `;
    resultArea.style.display = 'block';
}

function hideLoading() {
    // Loading會被replace掉
}

function showError(message) {
    const resultArea = document.getElementById('result-area');
    resultArea.innerHTML = `
        <div class="card" style="text-align: center; padding: 50px; border-left: 4px solid #f85149;">
            <div style="font-size: 24px;">❌</div>
            <div style="margin-top: 15px; color: #f85149;">${message}</div>
        </div>
    `;
    resultArea.style.display = 'block';
}

// 新功能按鈕樣式
const newFeatureStyles = document.createElement('style');
newFeatureStyles.textContent = `
    .new-feature-btn {
        background: linear-gradient(135deg, #238636, #2ea043) !important;
        border: none !important;
    }
    .new-feature-btn i {
        color: #fff !important;
    }
    .profit { color: #3fb950; }
    .loss { color: #f85149; }
`;
document.head.appendChild(newFeatureStyles);
