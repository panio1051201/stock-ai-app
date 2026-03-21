"""
Strong/Weak Stocks Screener - 強弱股篩選器
根據技術面、籌碼面、消息面挑選強勢股/弱勢股
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import data_loader

def screen_strong_stocks(market='TW', limit=20):
    """
    篩選強勢股
    
    條件：
    1. 股價站上所有均線 (MA5, MA20, MA60)
    2. MA 多頭排列 (MA5 > MA20 > MA60)
    3. KD黃金交叉
    4. 成交量放大 (> 1.5倍均量)
    5. 三大法人買超
    """
    results = []
    
    # 取得分類股票
    categories = data_loader.CATEGORY_MAP
    if not categories:
        return {'error': '股票清單尚未載入'}
    
    processed = 0
    for cat_name, stocks in categories.items():
        for stock in stocks[:10]:  # 每類最多10檔
            try:
                code = stock['code']
                name = stock['name']
                
                # 抓資料
                df, price = data_loader.fetch_data(code, days=90)
                if df is None or df.empty or len(df) < 60:
                    continue
                
                # 計算指標
                close = df['Close']
                ma5 = close.rolling(5).mean().iloc[-1]
                ma20 = close.rolling(20).mean().iloc[-1]
                ma60 = close.rolling(60).mean().iloc[-1]
                
                # 基本條件
                if close.iloc[-1] < ma5:
                    continue
                
                # MA 多頭排列
                is_bullish_ma = ma5 > ma20 > ma60
                
                # KD 黃金交叉
                k, d = calculate_kd(close)
                kd_golden = k > d and k > 50
                
                # 成交量放大
                vol = df['Volume'].iloc[-1]
                vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
                vol_surge = vol > vol_ma5 * 1.5
                
                # 計算分數
                score = 0
                if close.iloc[-1] > ma20: score += 20
                if close.iloc[-1] > ma60: score += 20
                if is_bullish_ma: score += 30
                if kd_golden: score += 15
                if vol_surge: score += 15
                
                # 漲幅
                change_pct = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
                score += min(max(change_pct, 0), 20)  # 最多加20分
                
                if score >= 60:  # 只取60分以上的
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'change': f"{change_pct:+.2f}%",
                        'score': score,
                        'ma_status': '多頭' if is_bullish_ma else '震盪',
                        'kd_status': '黃金交叉' if kd_golden else '中立',
                        'volume': '放量' if vol_surge else '正常',
                        'category': cat_name
                    })
                
                processed += 1
                
            except Exception as e:
                continue
    
    # 排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'type': 'strong',
        'title': '強勢股',
        'count': len(results),
        'top': results[:limit],
        'total_processed': processed,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def screen_weak_stocks(market='TW', limit=20):
    """
    篩選弱勢股
    
    條件：
    1. 股價跌破所有均線
    2. MA 空頭排列
    3. KD 死亡交叉
    4. 成交量萎縮
    """
    results = []
    
    categories = data_loader.CATEGORY_MAP
    if not categories:
        return {'error': '股票清單尚未載入'}
    
    processed = 0
    for cat_name, stocks in categories.items():
        for stock in stocks[:10]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=90)
                if df is None or df.empty or len(df) < 60:
                    continue
                
                close = df['Close']
                ma5 = close.rolling(5).mean().iloc[-1]
                ma20 = close.rolling(20).mean().iloc[-1]
                ma60 = close.rolling(60).mean().iloc[-1]
                
                # 基本條件：低於均線
                if close.iloc[-1] > ma5:
                    continue
                
                # MA 空頭排列
                is_bearish_ma = ma5 < ma20 < ma60
                
                # KD 死亡交叉
                k, d = calculate_kd(close)
                kd_dead = k < d and k < 50
                
                # 成交量萎縮
                vol = df['Volume'].iloc[-1]
                vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
                vol_shrink = vol < vol_ma5 * 0.7
                
                # 計算分數 (越低越弱)
                score = 100
                if close.iloc[-1] < ma20: score -= 20
                if close.iloc[-1] < ma60: score -= 20
                if is_bearish_ma: score -= 30
                if kd_dead: score -= 15
                if vol_shrink: score -= 15
                
                # 跌幅
                change_pct = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
                score += max(change_pct, -20)  # 最多扣20分
                
                if score <= 40:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'change': f"{change_pct:+.2f}%",
                        'score': score,
                        'ma_status': '空頭' if is_bearish_ma else '震盪',
                        'kd_status': '死亡交叉' if kd_dead else '中立',
                        'volume': '縮量' if vol_shrink else '正常',
                        'category': cat_name
                    })
                
                processed += 1
                
            except Exception as e:
                continue
    
    # 排序（分數越低越弱）
    results.sort(key=lambda x: x['score'])
    
    return {
        'type': 'weak',
        'title': '弱勢股',
        'count': len(results),
        'top': results[:limit],
        'total_processed': processed,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def calculate_kd(close, period=9):
    """計算 KD 值"""
    low_min = close.rolling(period).min()
    high_max = close.rolling(period).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()
    return k.iloc[-1], d.iloc[-1]

def get_stock_alert(code):
    """
    取得個股警示
    """
    try:
        name, full_code = data_loader.get_stock_name(code)
        df, price = data_loader.fetch_data(full_code, days=30)
        
        if df is None or df.empty:
            return {'error': '無法取得資料'}
        
        close = df['Close']
        
        # 警示條件
        alerts = []
        
        # 1. 三大法人買超
        try:
            chip_df = data_loader.fetch_institutional_investors(full_code, days=5)
            if chip_df is not None and not chip_df.empty:
                foreign = chip_df['Foreign_Investor_Net'].sum() if 'Foreign_Investor_Net' in chip_df.columns else 0
                if foreign > 1000:  # 超過1000張
                    alerts.append({
                        'type': 'positive',
                        'title': '外資買超',
                        'detail': f'近5日買超 {foreign/1000:.1f} 張'
                    })
                elif foreign < -1000:
                    alerts.append({
                        'type': 'negative',
                        'title': '外资賣超',
                        'detail': f'近5日賣超 {abs(foreign)/1000:.1f} 張'
                    })
        except:
            pass
        
        # 2. 融券大增
        try:
            # ... 融资融券資料
            pass
        except:
            pass
        
        # 3. 技術面警示
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        
        if close.iloc[-1] > ma5 * 1.1:
            alerts.append({
                'type': 'warning',
                'title': '偏離均線',
                'detail': '股價偏離5日線超過10%'
            })
        
        # 4. 成交量異常
        vol = df['Volume'].iloc[-1]
        vol_ma20 = df['Volume'].rolling(20).mean().iloc[-1]
        if vol > vol_ma20 * 3:
            alerts.append({
                'type': 'info',
                'title': '成交量暴增',
                'detail': '成交量為20日均量的3倍'
            })
        
        return {
            'code': full_code,
            'name': name,
            'price': price,
            'alerts': alerts,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    print("強勢股篩選中...")
    result = screen_strong_stocks()
    print(f"找到 {result['count']} 檔強勢股")
    
    print("\n弱勢股篩選中...")
    result = screen_weak_stocks()
    print(f"找到 {result['count']} 檔弱勢股")
