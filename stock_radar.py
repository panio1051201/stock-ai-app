"""
Stock Radar - 好股雷達（小白版）
用最簡單的條件幫新手選股
"""

import pandas as pd
import data_loader
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def radar_safe_stocks(limit=20):
    """
    穩健篩選 - 找不容易虧的股票
    """
    results = []
    
    # 確保 CATEGORY_MAP 已載入
    _ensure_category_map()
    categories = getattr(data_loader, 'CATEGORY_MAP', {})
    
    if not categories:
        return {'error': '股票清單尚未載入，請稍後再試', 'results': []}
    
    # 只取部分類別，避免超時
    sample_cats = list(categories.keys())[:10]  # 最多10個類別
    
    for cat_name in sample_cats:
        for stock in categories[cat_name][:5]:  # 每類5檔
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=30)
                if df is None or df.empty or len(df) < 5:
                    continue
                
                close = df['Close']
                
                # 基本條件
                if close.iloc[-1] > 100:  # 股價 < 100
                    continue
                
                vol = df['Volume'].iloc[-1]
                if vol < 1000:  # 成交量 > 1000
                    continue
                
                # 計算分數
                score = 50
                if close.iloc[-1] < 50:
                    score += 20
                elif close.iloc[-1] < 80:
                    score += 10
                
                ma20 = close.rolling(20).mean().iloc[-1]
                if close.iloc[-1] > ma20:
                    score += 15
                
                if score >= 60:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'category': cat_name,
                        'reason': '價格親民'
                    })
                    
            except Exception as e:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_value_stocks(limit=20):
    """價值篩選 - 找被低估的好股票"""
    results = []
    
    _ensure_category_map()
    categories = getattr(data_loader, 'CATEGORY_MAP', {})
    
    if not categories:
        return {'error': '股票清單尚未載入', 'results': []}
    
    sample_cats = list(categories.keys())[:10]
    
    for cat_name in sample_cats:
        for stock in categories[cat_name][:5]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=30)
                if df is None or df.empty:
                    continue
                
                close = df['Close']
                
                # 基本條件
                if price > 100:
                    continue
                
                # 簡單價值評分
                score = 50
                
                # 股價低
                if price < 50:
                    score += 20
                elif price < 80:
                    score += 10
                
                # 站上均線
                ma20 = close.rolling(20).mean().iloc[-1]
                if close.iloc[-1] > ma20:
                    score += 15
                
                # 成交量穩定
                vol = df['Volume'].iloc[-1]
                vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
                if vol > vol_ma5 * 0.8:
                    score += 10
                
                if score >= 60:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(price) if price else 0,
                        'score': score,
                        'category': cat_name,
                        'reason': '價值型'
                    })
                    
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_dividend_stocks(limit=20):
    """高息篩選 - 找適合定存的股票"""
    results = []
    
    _ensure_category_map()
    categories = getattr(data_loader, 'CATEGORY_MAP', {})
    
    if not categories:
        return {'error': '股票清單尚未載入', 'results': []}
    
    sample_cats = list(categories.keys())[:10]
    
    for cat_name in sample_cats:
        for stock in categories[cat_name][:5]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=60)
                if df is None or df.empty:
                    continue
                
                close = df['Close']
                
                # 股價穩定
                volatility = close.pct_change().std()
                if volatility > 0.05:  # 波動太大
                    continue
                
                # 分數
                score = 50
                
                # 股價合理
                if 20 < close.iloc[-1] < 100:
                    score += 20
                elif close.iloc[-1] <= 20:
                    score += 30
                
                # 波動小
                if volatility < 0.02:
                    score += 20
                
                # 站上年線
                ma60 = close.rolling(60).mean().iloc[-1]
                if close.iloc[-1] > ma60:
                    score += 10
                
                if score >= 70:
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'category': cat_name,
                        'reason': '定存族'
                    })
                    
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def radar_trend_stocks(limit=20):
    """趨勢篩選 - 找正在漲的股票"""
    results = []
    
    _ensure_category_map()
    categories = getattr(data_loader, 'CATEGORY_MAP', {})
    
    if not categories:
        return {'error': '股票清單尚未載入', 'results': []}
    
    sample_cats = list(categories.keys())[:10]
    
    for cat_name in sample_cats:
        for stock in categories[cat_name][:5]:
            try:
                code = stock['code']
                name = stock['name']
                
                df, price = data_loader.fetch_data(code, days=60)
                if df is None or df.empty or len(df) < 60:
                    continue
                
                close = df['Close']
                
                # 計算均線
                ma5 = close.rolling(5).mean().iloc[-1]
                ma20 = close.rolling(20).mean().iloc[-1]
                ma60 = close.rolling(60).mean().iloc[-1]
                
                # 條件：多頭排列
                if not (ma5 > ma20 > ma60):
                    continue
                
                # 分數
                score = 50
                
                # 趨勢強度
                trend = (ma5 - ma60) / ma60 * 100
                if trend > 5:
                    score += 20
                elif trend > 2:
                    score += 10
                
                # 動能
                k, d = calculate_kd(close)
                if k > d and k > 50:
                    score += 15
                
                # 成交量
                vol = df['Volume'].iloc[-1]
                vol_ma10 = df['Volume'].rolling(10).mean().iloc[-1]
                if vol > vol_ma10 * 1.2:
                    score += 10
                
                if score >= 65:
                    change = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
                    results.append({
                        'code': code,
                        'name': name,
                        'price': float(close.iloc[-1]),
                        'score': score,
                        'change': f'{change:+.1f}%',
                        'category': cat_name,
                        'reason': '趨勢強'
                    })
                    
            except:
                continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def _ensure_category_map():
    """確保 CATEGORY_MAP 已載入"""
    categories = getattr(data_loader, 'CATEGORY_MAP', None)
    
    if categories is None or len(categories) == 0:
        try:
            # 嘗試初始化
            if hasattr(data_loader, 'init_stock_list'):
                data_loader.init_stock_list()
        except:
            pass


def calculate_kd(close, period=9):
    """計算 KD"""
    try:
        low_min = close.rolling(period).min()
        high_max = close.rolling(period).max()
        rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
        k = rsv.ewm(alpha=1/3).mean()
        d = k.ewm(alpha=1/3).mean()
        return k.iloc[-1], d.iloc[-1]
    except:
        return 50, 50


def get_all_radars():
    """一次取得所有雷達結果"""
    return {
        'safe': radar_safe_stocks(limit=20),
        'value': radar_value_stocks(limit=20),
        'dividend': radar_dividend_stocks(limit=20),
        'trend': radar_trend_stocks(limit=20)
    }
