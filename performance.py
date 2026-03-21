"""
Performance Optimization Module - 效能優化
策略計算加速、資料庫、快取優化
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# ================================
# 1. 計算結果快取
# ================================

class CalculationCache:
    """策略計算結果快取"""
    
    _cache = {}
    _max_size = 100
    
    @classmethod
    def get(cls, key):
        """取得快取"""
        return cls._cache.get(key)
    
    @classmethod
    def set(cls, key, value):
        """設定快取"""
        if len(cls._cache) > cls._max_size:
            # 清除最舊的
            cls._cache.pop(next(iter(cls._cache)))
        cls._cache[key] = value
    
    @classmethod
    def clear(cls):
        """清除快取"""
        cls._cache.clear()
    
    @classmethod
    def make_key(cls, stock_code, strategy, days=60):
        """產生快取鍵"""
        return f"{stock_code}_{strategy}_{days}"

# ================================
# 2. 向量化計算（加速 Pandas）
# ================================

def vectorized_ma(df, periods=[5, 10, 20, 60]):
    """一次計算多條均線"""
    close = df['Close']
    result = {}
    for p in periods:
        result[f'ma{p}'] = close.rolling(p).mean()
    return result

def vectorized_indicators(df):
    """一次計算所有技術指標"""
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    result = {}
    
    # 均線
    result['ma5'] = close.rolling(5).mean()
    result['ma10'] = close.rolling(10).mean()
    result['ma20'] = close.rolling(20).mean()
    result['ma60'] = close.rolling(60).mean()
    
    # KD (Fast)
    low_min = low.rolling(9).min()
    high_max = high.rolling(9).max()
    result['rsv'] = (close - low_min) / (high_max - low_min + 1e-10) * 100
    result['k'] = result['rsv'].ewm(alpha=1/3).mean()
    result['d'] = result['k'].ewm(alpha=1/3).mean()
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    result['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = close.ewm(span=12, adjust=False).mean()
    exp26 = close.ewm(span=26, adjust=False).mean()
    result['macd'] = exp12 - exp26
    result['signal'] = result['macd'].ewm(span=9, adjust=False).mean()
    result['histogram'] = result['macd'] - result['signal']
    
    # 布林通道
    result['bb_mid'] = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    result['bb_upper'] = result['bb_mid'] + 2 * bb_std
    result['bb_lower'] = result['bb_mid'] - 2 * bb_std
    
    return result

# ================================
# 3. 快速評估函式
# ================================

def fast_evaluate(df, buy_price=None):
    """
    快速評估股票狀態（不呼叫完整策略）
    用途：快速篩選、排序
    """
    if df is None or df.empty or len(df) < 20:
        return None
    
    try:
        close = df['Close']
        current_price = float(close.iloc[-1])
        
        # 基礎技術指標（只算一次）
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1]
        
        # 簡單評分
        score = 0
        if current_price > ma20: score += 20
        if current_price > ma60: score += 20
        if ma20 > ma60: score += 10
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        if rsi > 50: score += 15
        if rsi < 30: score -= 10
        
        # 成交量
        vol = df['Volume'].iloc[-1]
        vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
        if vol > vol_ma5 * 1.5: score += 10
        
        # 成本評估
        if buy_price:
            roi = (current_price - buy_price) / buy_price * 100
            if roi > 10: score += 15
            if roi < -10: score -= 15
        
        return {
            'price': current_price,
            'ma20': ma20,
            'ma60': ma60,
            'score': score,
            'signal': '偏多' if score >= 40 else '偏空' if score <= 20 else '中立'
        }
    except:
        return None

def batch_evaluate(stocks_df_list):
    """
    批量快速評估
    用途：一次評估多檔股票
    """
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fast_evaluate, df) for df in stocks_df_list]
        for future in futures:
            results.append(future.result())
    return results

# ================================
# 4. 資料預處理優化
# ================================

def preprocess_data(df):
    """
    預處理資料，確保格式正確
    加速後續計算
    """
    if df is None or df.empty:
        return df
    
    # 確保必要的欄位存在
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_cols):
        return df
    
    # 轉換數值型態（一次完成）
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 移除 NaN
    df = df.dropna(subset=['Close'])
    
    # 確保日期索引
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
    
    return df

# ================================
# 5. 快取裝飾器（用於策略）
# ================================

def cached_strategy(ttl_seconds=300):
    """
    策略結果快取裝飾器
    
    用法:
    @cached_strategy(ttl_seconds=600)
    def my_strategy(df):
        # ... 計算 ...
        return result
    """
    cache = {}
    timestamps = {}
    
    def decorator(func):
        def wrapper(stock_code, *args, **kwargs):
            key = f"{stock_code}_{func.__name__}"
            now = pd.Timestamp.now()
            
            # 檢查快取
            if key in cache:
                if (now - timestamps[key]).seconds < ttl_seconds:
                    return cache[key]
            
            # 執行計算
            result = func(stock_code, *args, **kwargs)
            
            # 儲存快取
            cache[key] = result
            timestamps[key] = now
            
            return result
        return wrapper
    return decorator

# ================================
# 6. 記憶體優化
# ================================

def optimize_dataframe_memory(df):
    """
    優化 DataFrame 記憶體使用
    """
    if df is None or df.empty:
        return df
    
    # 降低數值精度
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    
    return df

def get_memory_usage(df):
    """取得 DataFrame 記憶體使用量（MB）"""
    if df is None or df.empty:
        return 0
    return df.memory_usage(deep=True).sum() / 1024 / 1024

# ================================
# 7. 非同步資料載入
# ================================

def async_load_data(load_func, *args, **kwargs):
    """
    非同步載入資料（不阻塞）
    使用執行緒池
    """
    import threading
    
    result = {}
    error = [None]
    
    def worker():
        try:
            result['data'] = load_func(*args, **kwargs)
        except Exception as e:
            error[0] = e
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=30)  # 30秒超時
    
    if error[0]:
        raise error[0]
    
    return result.get('data')

# ================================
# 8. 效能監控
# ================================

class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self):
        self.records = []
    
    def record(self, name, duration_ms, memory_mb=None):
        """記錄效能數據"""
        self.records.append({
            'name': name,
            'duration_ms': duration_ms,
            'memory_mb': memory_mb,
            'timestamp': pd.Timestamp.now()
        })
    
    def get_stats(self):
        """取得統計"""
        if not self.records:
            return {}
        
        df = pd.DataFrame(self.records)
        return {
            'avg_duration': df['duration_ms'].mean(),
            'max_duration': df['duration_ms'].max(),
            'total_calls': len(df),
            'slowest': df.loc[df['duration_ms'].idxmax(), 'name']
        }
    
    def report(self):
        """輸出報告"""
        stats = self.get_stats()
        if not stats:
            print("No performance data")
            return
        
        print("\n📊 Performance Report:")
        print(f"  Total Calls: {stats['total_calls']}")
        print(f"  Avg Duration: {stats['avg_duration']:.2f} ms")
        print(f"  Max Duration: {stats['max_duration']:.2f} ms")
        print(f"  Slowest: {stats['slowest']}")

# 全域監控器
perf_monitor = PerformanceMonitor()

# ================================
# 9. 加速裝飾器
# ================================

def timer(func):
    """計時裝飾器"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        
        perf_monitor.record(func.__name__, duration)
        
        if duration > 1000:  # 超過1秒警告
            print(f"⚠️ {func.__name__} took {duration:.0f}ms")
        
        return result
    return wrapper

# ================================
# 10. 批量處理優化
# ================================

def parallel_apply(df, func, n_jobs=4, chunk_size=100):
    """
    平行處理 DataFrame
    適用於需要對每行/每列執行的計算
    """
    if len(df) < chunk_size:
        return df.apply(func, axis=1)
    
    # 分塊處理
    chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        results = list(executor.map(func, chunks))
    
    return pd.concat(results)

# 使用範例
EXAMPLE = '''
# 1. 快速評估多檔股票
stocks = [df1, df2, df3, ...]
results = batch_evaluate(stocks)

# 2. 一次計算所有指標
indicators = vectorized_indicators(df)
ma20 = indicators['ma20']
rsi = indicators['rsi']

# 3. 快取策略結果
@cached_strategy(ttl_seconds=600)
def my_strategy(stock_code):
    # ... 不會每分鐘都重新計算
    return result

# 4. 效能監控
perf_monitor.report()
'''

if __name__ == "__main__":
    print("✅ Performance Optimization Module Loaded")
    print("   - Vectorized calculations")
    print("   - Strategy caching")
    print("   - Parallel processing")
    print("   - Memory optimization")
