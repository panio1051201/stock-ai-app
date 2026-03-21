# Strategies Module - 策略模組

# 基礎策略
from strategies.basic import ma, kd, rsi, qqe, macd, box, regression, value, financial, chips, fibonacci, support_resistance, gap, pattern, bollinger

# 進階策略
from strategies.advanced import kd_rsi, ma_macd, macd_rsi, summary, find_demon, find_foreign_buy

# 篩選策略
try:
    from strategies.screener import screen_strong_stocks, screen_weak_stocks, get_stock_alert
    SCREENER_AVAILABLE = True
except ImportError:
    SCREENER_AVAILABLE = False

# 可用策略映射
STRATEGIES = {
    'MA': ma,
    'KD': kd,
    'RSI': rsi,
    'QQE': qqe,
    'MACD': macd,
    'BOX': box,
    'REG': regression,
    'VALUE': value,
    'FINANCIAL': financial,
    'CHIPS': chips,
    'FIB': fibonacci,
    'SR': support_resistance,
    'GAP': gap,
    'PATTERN': pattern,
    'BOLLINGER': bollinger,
    'KDRSI': kd_rsi,
    'MAKD': ma_macd,
    'MACDRSI': macd_rsi,
    'SUMMARY': summary,
    'DEMON': find_demon,
    'FOREIGN_BUY': find_foreign_buy,
}

if SCREENER_AVAILABLE:
    STRATEGIES['STRONG'] = type('obj', (object,), {'analyze': lambda df: screen_strong_stocks()})()
    STRATEGIES['WEAK'] = type('obj', (object,), {'analyze': lambda df: screen_weak_stocks()})()
