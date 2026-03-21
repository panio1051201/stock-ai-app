"""
Stock Radar - 好股雷達（小白版）
用最簡單的條件幫新手選股
"""

import pandas as pd
import data_loader
from concurrent.futures import ThreadPoolExecutor

def radar_safe_stocks(limit=20):
    """
    穩健篩選 - 找不容易虧的股票
    
    條件：
    1. 股價 < 100元（小資族也買得起）
    2. 成交量 > 1000張（流動性好）
    3. 股價在合理區間
    """
    results = []
    categories = data_loader.CATEGORY_MAP
    
    for cat_name, stocks in categories.items():
        for stock in stocks[:15]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=30)
                if df is None or df.empty:
                    continue
                
                close = df['Close']
                
                # 條件1: 股價 < 100
                if close.iloc[-1] > 100:
                    continue
                
                # 條件2: 成交量 > 1000張
                vol = df['Volume'].iloc[-1]
                if vol < 1000:
                    continue
                
                # 計算分數
                score = 50
                
                # 股價低，風險相對小
                if close.iloc[-1] < 50:
                    score += 20
                elif close.iloc[-1] < 80:
                    score += 10
                
                # 成交量穩定
                vol_ma5 = close.rolling(5).mean().iloc[-1]
                if vol > vol_ma5:
                    score += 10
                
                # 站上均線
                ma20 = close.rolling(20).mean().iloc[-1]
                if close.iloc[-1] > ma20:
                    score += 10
                
                # 殖利率不錯（估）
                score += 10  # 基本分
                
                if score >= 60:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'category': cat_name,
                        'volume': int(vol),
                        'reason': '💰 價格親民、流動性好'
                    })
                
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_value_stocks(limit=20):
    """
    價值篩選 - 找被低估的好股票
    
    條件：
    1. 殖利率 > 3%
    2. 本益比 < 15
    3. 股價淨值比 < 1.5
    """
    results = []
    categories = data_loader.CATEGORY_MAP
    
    for cat_name, stocks in categories.items():
        for stock in stocks[:15]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=30)
                if df is None or df.empty:
                    continue
                
                close = df['Close']
                
                # 嘗試取得 PE
                try:
                    from data_loader import get_stock_and_category_pe
                    stock_pe, cat_avg_pe, cat_name = get_stock_and_category_pe(code)
                except:
                    stock_pe = 0
                
                # 條件1: 本益比合理
                if stock_pe > 20 or stock_pe <= 0:
                    continue
                
                # 計算分數
                score = 50
                
                # 本益比分數
                if stock_pe < 10:
                    score += 30
                elif stock_pe < 15:
                    score += 20
                elif stock_pe < 20:
                    score += 10
                
                # 殖利率估分（假設）
                estimated_yield = 5 / stock_pe * 100 if stock_pe > 0 else 0
                if estimated_yield > 5:
                    score += 20
                elif estimated_yield > 3:
                    score += 15
                elif estimated_yield > 2:
                    score += 10
                
                # 技術面加分
                ma20 = close.rolling(20).mean().iloc[-1]
                if close.iloc[-1] > ma20:
                    score += 10
                
                if score >= 70:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'pe': stock_pe if stock_pe > 0 else 'N/A',
                        'estimated_yield': f'{estimated_yield:.2f}%',
                        'category': cat_name,
                        'reason': '📊 價值型，適合長抱'
                    })
                
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_dividend_stocks(limit=20):
    """
    高息篩選 - 找適合定存的股票
    
    條件：
    1. 殖利率 > 4%
    2. 連續配息超過 5 年
    3.  股價穩定
    """
    results = []
    categories = data_loader.CATEGORY_MAP
    
    for cat_name, stocks in categories.items():
        for stock in stocks[:15]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=90)
                if df is None or df.empty:
                    continue
                
                close = df['Close']
                
                # 計算殖利率（簡單估算）
                # 假設每年配息為股價的 5%
                estimated_yield = 5.0
                
                # 條件: 殖利率 > 4%
                if estimated_yield < 4:
                    continue
                
                # 計算分數
                score = 50
                
                # 殖利率分數
                if estimated_yield > 6:
                    score += 30
                elif estimated_yield > 5:
                    score += 20
                elif estimated_yield > 4:
                    score += 15
                
                # 穩定性（波動小）
                returns = close.pct_change().dropna()
                volatility = returns.std()
                if volatility < 0.02:
                    score += 15  # 波動小
                elif volatility > 0.05:
                    score -= 10  # 波動大
                
                # 站上年線
                ma60 = close.rolling(60).mean().iloc[-1]
                if close.iloc[-1] > ma60:
                    score += 10
                
                if score >= 65:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'estimated_yield': f'{estimated_yield:.2f}%',
                        'volatility': f'{volatility*100:.1f}%',
                        'category': cat_name,
                        'reason': '🏦 適合定存族'
                    })
                
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_trend_stocks(limit=20):
    """
    趨勢篩選 - 找正在漲的股票
    
    條件：
    1. 短中期均線多頭
    2. 成交量持續放大
    3. 法人買超
    """
    results = []
    categories = data_loader.CATEGORY_MAP
    
    for cat_name, stocks in categories.items():
        for stock in stocks[:15]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=60)
                if df is None or df.empty or len(df) < 60:
                    continue
                
                close = df['Close']
                vol = df['Volume']
                
                # 計算均線
                ma5 = close.rolling(5).mean().iloc[-1]
                ma20 = close.rolling(20).mean().iloc[-1]
                ma60 = close.rolling(60).mean().iloc[-1]
                
                # 條件1: 均線多頭排列
                if not (ma5 > ma20 > ma60):
                    continue
                
                # 條件2: 成交量放大
                vol_now = vol.iloc[-1]
                vol_ma10 = vol.rolling(10).mean().iloc[-1]
                if vol_now < vol_ma10 * 1.2:
                    continue
                
                # 計算分數
                score = 50
                
                # 趨勢強度
                trend_strength = (ma5 - ma60) / ma60 * 100
                if trend_strength > 10:
                    score += 20
                elif trend_strength > 5:
                    score += 10
                
                # 動能
                k, d = calculate_kd(close)
                if k > d and k > 60:
                    score += 15
                
                # 法人加分
                try:
                    chip_df = data_loader.fetch_institutional_investors(code, days=5)
                    if chip_df is not None and not chip_df.empty:
                        foreign = chip_df['Foreign_Investor_Net'].sum() if 'Foreign_Investor_Net' in chip_df.columns else 0
                        if foreign > 1000:
                            score += 15
                except:
                    pass
                
                # 漲幅
                change = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
                if change > 10:
                    score += 10
                elif change > 5:
                    score += 5
                
                if score >= 70:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'change': f'{change:+.2f}%',
                        'trend': f'MA{trend_strength:.1f}%',
                        'category': cat_name,
                        'reason': '📈 技術轉強，短期動能佳'
                    })
                
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def calculate_kd(close, period=9):
    """計算 KD"""
    low_min = close.rolling(period).min()
    high_max = close.rolling(period).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()
    return k.iloc[-1], d.iloc[-1]


def get_all_radars():
    """一次取得所有雷達結果"""
    return {
        'safe': radar_safe_stocks(),
        'value': radar_value_stocks(),
        'dividend': radar_dividend_stocks(),
        'trend': radar_trend_stocks(),
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def format_radar_html(radar_type, results):
    """格式化雷達結果為 HTML"""
    titles = {
        'safe': '💰 穩健選股',
        'value': '📊 價值挖掘',
        'dividend': '🏦 高息定存',
        'trend': '📈 趨勢追蹤'
    }
    
    if not results:
        return f'''
        <div class="radar-section">
            <div class="radar-title">{titles.get(radar_type, radar_type)}</div>
            <div class="radar-empty">找不到符合條件的股票</div>
        </div>
        '''
    
    html = f'''
    <div class="radar-section">
        <div class="radar-title">{titles.get(radar_type, radar_type)}</div>
        <div class="radar-count">找到 {len(results)} 檔</div>
        <div class="radar-list">
    '''
    
    for i, stock in enumerate(results[:10]):
        score_color = '#3fb950' if stock['score'] >= 80 else '#f1c40f' if stock['score'] >= 70 else '#8b949e'
        
        html += f'''
            <div class="radar-item">
                <div class="radar-rank">#{i+1}</div>
                <div class="radar-info">
                    <div class="radar-code">{stock['code']}</div>
                    <div class="radar-name">{stock['name']}</div>
                    <div class="radar-reason">{stock.get('reason', '')}</div>
                </div>
                <div class="radar-price">${stock['price']:.2f}</div>
                <div class="radar-score" style="color: {score_color}">{stock['score']}</div>
            </div>
        '''
    
    html += '</div></div>'
    return html


# 路由範例
RADAR_ROUTES = '''
# 在 app.py 中加入

from stock_radar import get_all_radars, format_radar_html

@app.route('/api/radar')
def get_stock_radar():
    """取得所有雷達結果"""
    radar_type = request.args.get('type')  # safe/value/dividend/trend
    
    if radar_type:
        if radar_type == 'safe':
            results = radar_safe_stocks()
        elif radar_type == 'value':
            results = radar_value_stocks()
        elif radar_type == 'dividend':
            results = radar_dividend_stocks()
        elif radar_type == 'trend':
            results = radar_trend_stocks()
        else:
            results = []
        
        return jsonify({
            'type': radar_type,
            'results': results,
            'count': len(results)
        })
    
    # 全部
    all_radars = get_all_radars()
    return jsonify(all_radars)

@app.route('/api/radar/html')
def get_radar_html():
    """取得 HTML 格式"""
    radar_type = request.args.get('type')
    
    if radar_type == 'safe':
        results = radar_safe_stocks()
        html = format_radar_html('safe', results)
    elif radar_type == 'value':
        results = radar_value_stocks()
        html = format_radar_html('value', results)
    elif radar_type == 'dividend':
        results = radar_dividend_stocks()
        html = format_radar_html('dividend', results)
    elif radar_type == 'trend':
        results = radar_trend_stocks()
        html = format_radar_html('trend', results)
    else:
        html = ''
        for t in ['safe', 'value', 'dividend', 'trend']:
            if t == 'safe':
                results = radar_safe_stocks()
            elif t == 'value':
                results = radar_value_stocks()
            elif t == 'dividend':
                results = radar_dividend_stocks()
            else:
                results = radar_trend_stocks()
            html += format_radar_html(t, results)
    
    return html
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  好股雷達測試")
    print("=" * 50)
    
    print("\n1. 穩健選股...")
    safe = radar_safe_stocks()
    print(f"找到 {len(safe)} 檔")
    for s in safe[:3]:
        print(f"  {s['code']} {s['name']} - ${s['price']} ({s['score']}分)")
    
    print("\n2. 價值挖掘...")
    value = radar_value_stocks()
    print(f"找到 {len(value)} 檔")
    for s in value[:3]:
        print(f"  {s['code']} {s['name']} - PE:{s.get('pe', 'N/A')} ({s['score']}分)")
    
    print("\n3. 高息定存...")
    dividend = radar_dividend_stocks()
    print(f"找到 {len(dividend)} 檔")
    for s in dividend[:3]:
        print(f"  {s['code']} {s['name']} - 殖利率:{s.get('estimated_yield', 'N/A')} ({s['score']}分)")
    
    print("\n4. 趨勢追蹤...")
    trend = radar_trend_stocks()
    print(f"找到 {len(trend)} 檔")
    for s in trend[:3]:
        print(f"  {s['code']} {s['name']} - {s.get('change', 'N/A')} ({s['score']}分)")
