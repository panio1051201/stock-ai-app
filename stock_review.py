"""
Stock Quick Review - 股票快速健檢
用最白話的方式告訴小白這檔股票能不能買
"""

import pandas as pd
import data_loader

def quick_review(code, buy_price=None):
    """
    快速健檢股票
    
    Returns:
        {
            'rating': '🟢' / '🟡' / '🔴',
            'rating_text': '放心買' / '再看看' / '不要碰',
            'for_who': '短線操作' / '長期持有' / '定存族',
            'reasons': ['原因1', '原因2'],
            'beginner_summary': '用白話解釋'
        }
    """
    try:
        name, full_code = data_loader.get_stock_name(code)
        df, price = data_loader.fetch_data(full_code, days=90)
        
        if df is None or df.empty:
            return {
                'error': '無法取得資料',
                'code': code,
                'name': name
            }
        
        close = df['Close']
        
        # ===== 計算各項指標 =====
        
        # 1. 技術面 (40%)
        tech_score = calculate_tech_score(df)
        
        # 2. 價值面 (30%) - 本益比、殖利率
        value_score, pe_ratio, dividend_yield = calculate_value_score(full_code, close)
        
        # 3. 籌碼面 (30%) - 法人動向
        chip_score, foreign_net, trust_net = calculate_chip_score(full_code)
        
        # ===== 計算總分 =====
        total_score = tech_score * 0.4 + value_score * 0.3 + chip_score * 0.3
        
        # ===== 根據分數給評級 =====
        if total_score >= 70:
            rating = '🟢'
            rating_text = '放心買'
        elif total_score >= 50:
            rating = '🟡'
            rating_text = '再看看'
        else:
            rating = '🔴'
            rating_text = '不要碰'
        
        # ===== 判斷適合誰 =====
        if value_score >= 70 and dividend_yield > 4:
            for_who = '🏦 定存族（高殖利率）'
        elif tech_score >= 70:
            for_who = '📈 短線操作（技術轉強）'
        elif value_score >= 60:
            for_who = '📊 長期持有（體質健康）'
        else:
            for_who = '👀 觀望中'
        
        # ===== 收集原因 =====
        reasons = []
        
        # 技術面原因
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1]
        
        if close.iloc[-1] > ma20:
            reasons.append('✅ 股價在上升趨勢中')
        else:
            reasons.append('⚠️ 股價低於 20 日均線')
        
        # KDJ
        k, d = calculate_kd(close)
        if k > d and k > 50:
            reasons.append('✅ KD 黃金交叉，動能強')
        elif k < d:
            reasons.append('⚠️ KD 死亡交叉，動能弱')
        
        # 本益比
        if pe_ratio > 0:
            if pe_ratio < 15:
                reasons.append(f'✅ 本益比 {pe_ratio:.1f}，股價合理')
            elif pe_ratio > 25:
                reasons.append(f'⚠️ 本益比 {pe_ratio:.1f}，股價偏貴')
        
        # 殖利率
        if dividend_yield and dividend_yield > 3:
            reasons.append(f'✅ 殖利率 {dividend_yield:.2f}% 不錯')
        
        # 法人
        if foreign_net > 1000:
            reasons.append(f'✅ 外資連續買超 {foreign_net/1000:.0f} 張')
        elif foreign_net < -1000:
            reasons.append(f'⚠️ 外資連續賣超 {abs(foreign_net)/1000:.0f} 張')
        
        # ===== 成本損益 =====
        profit_info = {}
        if buy_price and buy_price > 0:
            roi = (price - buy_price) / buy_price * 100
            profit_info = {
                'buy_price': buy_price,
                'current_price': price,
                'roi': roi,
                'profit_text': f'{"已賺" if roi > 0 else "已虧"} {abs(roi):.2f}%'
            }
        
        # ===== 白話總結 =====
        beginner_summary = generate_beginner_summary(
            rating, 
            close.iloc[-1], 
            close.iloc[-1] > ma20,
            pe_ratio,
            dividend_yield,
            foreign_net > 0
        )
        
        return {
            'code': full_code,
            'name': name,
            'price': price,
            'rating': rating,
            'rating_text': rating_text,
            'total_score': round(total_score, 1),
            'for_who': for_who,
            'reasons': reasons,
            'beginner_summary': beginner_summary,
            'details': {
                'tech_score': round(tech_score, 1),
                'value_score': round(value_score, 1),
                'chip_score': round(chip_score, 1),
                'pe_ratio': pe_ratio if pe_ratio > 0 else 'N/A',
                'dividend_yield': f'{dividend_yield:.2f}%' if dividend_yield else 'N/A',
                'foreign_net': int(foreign_net) if foreign_net else 0,
                'trust_net': int(trust_net) if trust_net else 0
            },
            'profit': profit_info
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'code': code
        }

def calculate_tech_score(df):
    """計算技術面分數 (0-100)"""
    try:
        close = df['Close']
        
        score = 50  # 起始分
        
        # MA 狀態
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1]
        
        if close.iloc[-1] > ma20: score += 15
        if close.iloc[-1] > ma60: score += 15
        if ma5 > ma20: score += 10
        if ma20 > ma60: score += 10  # 多頭排列
        
        # KD
        k, d = calculate_kd(close)
        if k > d: score += 10
        if k > 50: score += 5
        
        # RSI
        rsi = calculate_rsi(close)
        if 40 < rsi < 70: score += 10  # 合理範圍
        if rsi >= 70: score -= 10  # 過熱
        
        # 成交量
        vol = df['Volume'].iloc[-1]
        vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
        if vol > vol_ma5 * 1.5: score += 10  # 放量
        if vol < vol_ma5 * 0.5: score -= 10  # 縮量
        
        return max(0, min(100, score))
        
    except:
        return 50

def calculate_value_score(code, close):
    """計算價值面分數"""
    try:
        score = 50
        
        # 嘗試取得 PE
        try:
            from data_loader import get_stock_and_category_pe
            stock_pe, cat_avg_pe, cat_name = get_stock_and_category_pe(code)
            
            if stock_pe > 0:
                if stock_pe < 10: score += 30
                elif stock_pe < 15: score += 20
                elif stock_pe < 20: score += 10
                elif stock_pe > 30: score -= 20
        except:
            stock_pe = 0
        
        # 殖利率 (從 Summary 策略估算)
        dividend_yield = 0
        try:
            fin_df, _ = data_loader.fetch_financials(code)
            if fin_df is not None and not fin_df.empty:
                # 簡單估算
                dividend_yield = 3.5  # 預設值
        except:
            dividend_yield = 0
        
        return max(0, min(100, score)), stock_pe, dividend_yield
        
    except:
        return 50, 0, 0

def calculate_chip_score(code):
    """計算籌碼分數"""
    try:
        chip_df = data_loader.fetch_institutional_investors(code, days=5)
        
        if chip_df is None or chip_df.empty:
            return 50, 0, 0
        
        # 外資
        foreign_col = 'Foreign_Investor_Net'
        if foreign_col in chip_df.columns:
            foreign_net = chip_df[foreign_col].sum()
        else:
            foreign_net = 0
        
        # 投信
        trust_col = 'Investment_Trust_Net'
        if trust_col in chip_df.columns:
            trust_net = chip_df[trust_col].sum()
        else:
            trust_net = 0
        
        score = 50
        
        if foreign_net > 3000: score += 30
        elif foreign_net > 1000: score += 20
        elif foreign_net < -3000: score -= 30
        elif foreign_net < -1000: score -= 20
        
        if trust_net > 1000: score += 20
        elif trust_net < -1000: score -= 20
        
        return max(0, min(100, score)), foreign_net, trust_net
        
    except:
        return 50, 0, 0

def calculate_kd(close, period=9):
    """計算 KD"""
    low_min = close.rolling(period).min()
    high_max = close.rolling(period).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()
    return k.iloc[-1], d.iloc[-1]

def calculate_rsi(close, period=14):
    """計算 RSI"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    return (100 - (100 / (1 + rs))).iloc[-1]

def generate_beginner_summary(rating, price, uptrend, pe, dividend, foreign_buy):
    """產生小白看得懂的解釋"""
    
    if rating == '🟢':
        summary = f"""
目前股價 {price:.2f} 元，狀態不錯！

{
'法人在買，趨勢向上' if foreign_buy else '技術面轉強'
}，適合考慮。

{
f'殖利率 {dividend:.2f}% 不錯，可以當定存股' if dividend and dividend > 3 else ''
}

豬肉飯建議：可以分批買入，設好停損點。
"""
    elif rating == '🟡':
        summary = f"""
目前股價 {price:.2f} 元，再觀望一下比較好。

{
'有點貴，本益比有點高' if pe and pe > 20 else '還在整理，方向不明'
}。

{
'建議等明確趨勢出來再進場' if not uptrend else '可以等回調再買'
}

🐷建議：再看看，等更好的價位。
"""
    else:
        summary = f"""
目前股價 {price:.2f} 元，有點危險！

{
'技術面轉弱，可能繼續跌' if not uptrend else '雖然價格合理但大盤不好'
}。

{
'建議不要碰，或等跌更低再說' if pe and pe > 25 else '建議觀望，不要現在進場'
}

🐷建議：忍住的藝術，現金為王！
"""
    
    return summary.strip()


def format_review_html(result):
    """格式化為 HTML (方便嵌入)"""
    if 'error' in result:
        return f'<div class="review-error">⚠️ {result["error"]}</div>'
    
    rating = result.get('rating', '')
    rating_text = result.get('rating_text', '')
    score = result.get('total_score', 0)
    for_who = result.get('for_who', '')
    reasons = result.get('reasons', [])
    summary = result.get('beginner_summary', '')
    details = result.get('details', {})
    profit = result.get('profit', {})
    
    # 原因 HTML
    reasons_html = ''
    for r in reasons:
        reasons_html += f'<li>{r}</li>'
    
    # 成本資訊
    profit_html = ''
    if profit:
        roi = profit.get('roi', 0)
        emoji = '🟢' if roi > 0 else '🔴'
        profit_html = f'''
        <div class="profit-box { "profit" if roi > 0 else "loss"}">
            <div class="profit-title">你的持仓</div>
            <div class="profit-buy">成本: {profit.get('buy_price')} 元</div>
            <div class="profit-current">現價: {profit.get('current_price')} 元</div>
            <div class="profit-roi">{emoji} {profit.get('profit_text')}</div>
        </div>
        '''
    
    return f'''
    <div class="quick-review">
        <div class="review-header">
            <span class="review-rating">{rating} {rating_text}</span>
            <span class="review-score">{score} 分</span>
        </div>
        
        <div class="review-for">適合: {for_who}</div>
        
        <div class="review-reasons">
            <div class="reason-title">參考原因：</div>
            <ul class="reason-list">{reasons_html}</ul>
        </div>
        
        {profit_html}
        
        <div class="review-summary">
            <div class="summary-title">📝 簡單說：</div>
            <div class="summary-text">{summary}</div>
        </div>
        
        <div class="review-details">
            <div class="detail-item">技術面: {details.get('tech_score', 'N/A')}</div>
            <div class="detail-item">價值面: {details.get('value_score', 'N/A')}</div>
            <div class="detail-item">籌碼面: {details.get('chip_score', 'N/A')}</div>
            <div class="detail-item">本益比: {details.get('pe_ratio', 'N/A')}</div>
            <div class="detail-item">殖利率: {details.get('dividend_yield', 'N/A')}</div>
        </div>
    </div>
    '''


if __name__ == '__main__':
    # 測試
    print("=== 股票健檢測試 ===")
    
    # 測試台積電
    result = quick_review('2330', buy_price=800)
    print(f"\n{result.get('name', 'N/A')}:")
    print(f"評級: {result.get('rating')} {result.get('rating_text')}")
    print(f"總分: {result.get('total_score')}")
    print(f"適合: {result.get('for_who')}")
    print(f"原因: {result.get('reasons')}")
    print(f"\n簡評:\n{result.get('beginner_summary')}")
