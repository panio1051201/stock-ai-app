import pandas as pd
import numpy as np

def calculate_drawdown(curve):
    if not curve: return 0.0
    arr = np.array(curve)
    peak = np.maximum.accumulate(arr)
    drawdowns = (arr - peak) / peak * 100
    return round(np.min(drawdowns), 2)

def process_dividends(date_str, shares, dividend_df):
    """
    處理單日的除權息，回傳獲得的現金股利與股票股利
    """
    cash_div = 0.0
    stock_div = 0.0
    
    if dividend_df is not None and not dividend_df.empty:
        # 檢查除息 (發現金)
        cash_match = dividend_df[dividend_df['CashExDividendTradingDate'] == date_str]
        if not cash_match.empty:
            cash_dist = cash_match.iloc[0]['CashEarningsDistribution']
            if pd.notna(cash_dist) and cash_dist > 0:
                cash_div = shares * cash_dist
                
        # 檢查除權 (發股票)，以面額10元計算配股比率
        stock_match = dividend_df[dividend_df['StockExDividendTradingDate'] == date_str]
        if not stock_match.empty:
            stock_dist = stock_match.iloc[0]['StockEarningsDistribution']
            if pd.notna(stock_dist) and stock_dist > 0:
                stock_div = shares * (stock_dist / 10.0)
                
    return cash_div, stock_div

def calculate_buy_hold(df, initial_capital, dividend_df=None):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'portfolio_curve': [], 'total_cash_dividend': 0}
    
    first_price = df['Close'].iloc[0]
    shares = initial_capital / first_price
    
    portfolio_curve = []
    total_cash_dividend = 0.0
    
    for date, row in df.iterrows():
        date_str = date.strftime('%Y-%m-%d')
        
        # 處理除權息
        cash_div, stock_div = process_dividends(date_str, shares, dividend_df)
        total_cash_dividend += cash_div
        shares += stock_div
        
        # 買進持有的日常淨值 = 目前股數 * 目前價 + 拿到的現金股利
        portfolio_curve.append(round(shares * row['Close'] + total_cash_dividend, 2))
        
    final_value = portfolio_curve[-1] if portfolio_curve else initial_capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    return {
        'total_return': round(total_return, 2),
        'max_drawdown': calculate_drawdown(portfolio_curve),
        'portfolio_curve': portfolio_curve,
        'total_cash_dividend': int(total_cash_dividend)
    }

def calculate_dca(df, initial_capital, freq='monthly', dca_amount=10000, dividend_df=None):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'portfolio_curve': [], 'total_cash_dividend': 0}
    
    dates = df.index.tolist()
    if freq == 'monthly': invest_dates = df.resample('ME').first().index.tolist()
    else: invest_dates = df.resample('W').first().index.tolist()
        
    invest_dates = [d for d in invest_dates if d >= dates[0] and d <= dates[-1]]
    if not invest_dates: invest_dates = [dates[0]]
    
    total_invested = initial_capital # 一開始本金
    cash_left = float(initial_capital)
    total_shares = 0.0
    portfolio_curve = []
    invest_set = set(invest_dates)
    total_cash_dividend = 0.0
    
    # 第一天初始建倉
    if cash_left > 0:
        first_price = df['Close'].iloc[0]
        total_shares += cash_left / first_price
        cash_left = 0
    
    for date, row in df.iterrows():
        date_str = date.strftime('%Y-%m-%d')
        
        # 處理除權息
        cash_div, stock_div = process_dividends(date_str, total_shares, dividend_df)
        total_cash_dividend += cash_div
        total_shares += stock_div
        
        # 處理額外定期定額投入
        # 判斷是不是定額日 (除了第一天已經 put All in)
        if date in invest_set and date != dates[0]:
            total_invested += dca_amount
            total_shares += dca_amount / row['Close']
            
        current_value = total_shares * row['Close'] + total_cash_dividend
        # 在此總報酬計算方式: (當前總市值 - 累計總投入) / 累計總投入
        # 為了跟其他圖表同基準畫線，我們畫的是「累計總現值 (包含拿到的現金股利)」
        portfolio_curve.append(round(current_value, 2))
        
    final_value = portfolio_curve[-1] if portfolio_curve else total_invested
    total_return = (final_value - total_invested) / total_invested * 100 if total_invested > 0 else 0
    
    return {
        'total_return': round(total_return, 2),
        'max_drawdown': calculate_drawdown(portfolio_curve),
        'portfolio_curve': portfolio_curve,
        'total_cash_dividend': int(total_cash_dividend)
    }

def calculate_strategy(df, initial_capital, strategy_name, dividend_df=None):
    if df.empty: return {'total_return': 0, 'max_drawdown': 0, 'win_rate': 0, 'portfolio_curve': [], 'total_cash_dividend': 0}
    
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
        return calculate_buy_hold(df, initial_capital, dividend_df)
        
    trades_won, trades_total = 0, 0
    last_buy_price = 0
    total_cash_dividend = 0.0
    
    for i in range(len(df)):
        price = float(df['Close'].iloc[i])
        date_str = df.index[i].strftime('%Y-%m-%d')
        
        # 處理除權息 (若目前有持股)
        if shares > 0:
            cash_div, stock_div = process_dividends(date_str, shares, dividend_df)
            total_cash_dividend += cash_div
            cash += cash_div # 現金股利直接入袋當備用金
            shares += stock_div
            
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
        'portfolio_curve': portfolio_curve,
        'total_cash_dividend': int(total_cash_dividend)
    }


def run_backtest(df, initial_capital, strategy_type, dca_freq, dca_amount=10000, dividend_df=None):
    res_bnh = calculate_buy_hold(df, initial_capital, dividend_df)
    res_dca = calculate_dca(df, initial_capital, dca_freq, dca_amount, dividend_df)
    res_str = calculate_strategy(df, initial_capital, strategy_type, dividend_df)
    
    dates = [d.strftime('%Y-%m-%d') for d in df.index]
    
    return {
        'dates': dates,
        'symbol': 'Local BT',
        'buy_hold': res_bnh,
        'dca': res_dca,
        'strategy': res_str
    }
