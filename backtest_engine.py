import pandas as pd
import numpy as np

def calculate_drawdown(curve):
    if not curve: return 0.0
    arr = np.array(curve)
    peak = np.maximum.accumulate(arr)
    drawdowns = (arr - peak) / peak * 100
    return round(np.min(drawdowns), 2)

def calculate_buy_hold(df, initial_capital):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'portfolio_curve': []}
    first_price = df['Close'].iloc[0]
    shares = initial_capital / first_price
    
    portfolio_curve = []
    
    for _, row in df.iterrows():
        portfolio_curve.append(round(shares * row['Close'], 2))
        
    final_value = portfolio_curve[-1] if portfolio_curve else initial_capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    return {
        'total_return': round(total_return, 2),
        'max_drawdown': calculate_drawdown(portfolio_curve),
        'portfolio_curve': portfolio_curve
    }

def calculate_dca(df, initial_capital, freq='monthly'):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'portfolio_curve': []}
    
    dates = df.index.tolist()
    if freq == 'monthly': invest_dates = df.resample('ME').first().index.tolist()
    else: invest_dates = df.resample('W').first().index.tolist()
        
    invest_dates = [d for d in invest_dates if d >= dates[0] and d <= dates[-1]]
    if not invest_dates: invest_dates = [dates[0]]
    
    per_period_amount = initial_capital / len(invest_dates)
    total_invested = 0
    total_shares = 0
    portfolio_curve = []
    invest_set = set(invest_dates)
    
    for date, row in df.iterrows():
        if date in invest_set:
            total_invested += per_period_amount
            total_shares += per_period_amount / row['Close']
            
        current_value = total_shares * row['Close']
        cash_left = initial_capital - total_invested
        portfolio_curve.append(round(current_value + cash_left, 2))
        
    final_value = portfolio_curve[-1] if portfolio_curve else initial_capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    return {
        'total_return': round(total_return, 2),
        'max_drawdown': calculate_drawdown(portfolio_curve),
        'portfolio_curve': portfolio_curve
    }

def calculate_strategy(df, initial_capital, strategy_name):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'win_rate': 0, 'portfolio_curve': []}
    
    cash = float(initial_capital)
    shares = 0.0
    portfolio_curve = []
    signals = np.zeros(len(df))
    close = df['Close']
    
    if strategy_name == 'ma_cross' or strategy_name == 'MA':
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        for i in range(1, len(df)):
            if ma5.iloc[i] > ma20.iloc[i] and ma5.iloc[i-1] <= ma20.iloc[i-1]: signals[i] = 1
            elif ma5.iloc[i] < ma20.iloc[i] and ma5.iloc[i-1] >= ma20.iloc[i-1]: signals[i] = -1
                
    elif strategy_name == 'KD' or strategy_name == 'kd':
        high9 = df['High'].rolling(9).max()
        low9 = df['Low'].rolling(9).min()
        rsv = (close - low9) / (high9 - low9) * 100
        k, d = np.zeros(len(df)), np.zeros(len(df))
        k[0], d[0] = 50, 50
        for i in range(1, len(df)):
            if pd.isna(rsv.iloc[i]): k[i], d[i] = k[i-1], d[i-1]
            else:
                k[i] = k[i-1] * 2/3 + rsv.iloc[i] * 1/3
                d[i] = d[i-1] * 2/3 + k[i] * 1/3
                if k[i] > d[i] and k[i-1] <= d[i-1] and k[i] < 30: signals[i] = 1
                elif k[i] < d[i] and k[i-1] >= d[i-1] and k[i] > 70: signals[i] = -1
                
    elif strategy_name == 'MACD':
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        macd = dif.ewm(span=9, adjust=False).mean()
        osc = dif - macd
        for i in range(1, len(df)):
            if osc.iloc[i] > 0 and osc.iloc[i-1] <= 0: signals[i] = 1
            elif osc.iloc[i] < 0 and osc.iloc[i-1] >= 0: signals[i] = -1
                
    elif strategy_name == 'RSI':
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        for i in range(1, len(df)):
            if rsi.iloc[i] < 30 and rsi.iloc[i-1] >= 30: signals[i] = 1
            elif rsi.iloc[i] > 70 and rsi.iloc[i-1] <= 70: signals[i] = -1
                
    elif strategy_name == 'BOLLINGER':
        ma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = ma20 + (2 * std20)
        lower = ma20 - (2 * std20)
        for i in range(1, len(df)):
            if close.iloc[i] < lower.iloc[i] and close.iloc[i-1] >= lower.iloc[i-1]: signals[i] = 1
            elif close.iloc[i] > upper.iloc[i] and close.iloc[i-1] <= upper.iloc[i-1]: signals[i] = -1
            
    else:
        return calculate_buy_hold(df, initial_capital)
        
    trades_won, trades_total = 0, 0
    last_buy_price = 0
    
    for i in range(len(df)):
        price = float(df['Close'].iloc[i])
        if signals[i] == 1 and cash > 0:
            shares += cash / price
            cash = 0.0
            last_buy_price = price
        elif signals[i] == -1 and shares > 0:
            cash += shares * price
            shares = 0.0
            trades_total += 1
            if price > last_buy_price: trades_won += 1
            
        portfolio_curve.append(round(cash + (shares * price), 2))
        
    final_value = portfolio_curve[-1] if portfolio_curve else initial_capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    win_rate = (trades_won / trades_total * 100) if trades_total > 0 else 0
    
    return {
        'total_return': round(total_return, 2),
        'max_drawdown': calculate_drawdown(portfolio_curve),
        'win_rate': round(win_rate, 2),
        'portfolio_curve': portfolio_curve
    }


def run_backtest(df, initial_capital, strategy_type, dca_freq):
    res_bnh = calculate_buy_hold(df, initial_capital)
    res_dca = calculate_dca(df, initial_capital, dca_freq)
    res_str = calculate_strategy(df, initial_capital, strategy_type)
    
    dates = [d.strftime('%Y-%m-%d') for d in df.index]
    
    return {
        'dates': dates,
        'symbol': 'Local BT',
        'buy_hold': res_bnh,
        'dca': res_dca,
        'strategy': res_str
    }
