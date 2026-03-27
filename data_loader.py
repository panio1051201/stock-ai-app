import pandas as pd
from FinMind.data import DataLoader
import datetime
import re
from cachetools import cached, TTLCache
import time
import requests
import yfinance as yf  # 備用方案

# --- 引入錯誤處理模組 ---
import error_handler as eh

# --- 設定 FinMind API Token ---
import os
API_TOKEN = os.environ.get("FINMIND_API_TOKEN", "")

# 全域變數
STOCK_MAP_NAME_TO_ID = {}
STOCK_MAP_ID_TO_NAME = {}
CATEGORY_MAP = {}


def fetch_data_yf(stock_code, days=5):
    """使用 yfinance 取得股價（備用方案）"""
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        df = ticker.history(period=f"{days}d")
        if df.empty:
            return None
        df = df.rename(columns={'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'})
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    except Exception as e:
        eh.logger.error("YFinance", f"取得 {stock_code} 失敗: {e}")
        return None


def init_stock_list():
    global STOCK_MAP_NAME_TO_ID, STOCK_MAP_ID_TO_NAME, CATEGORY_MAP
    eh.logger.info("System", "正在更新台股清單...")
    
    try:
        dl = DataLoader()
        if API_TOKEN: 
            dl.login_by_token(api_token=API_TOKEN)
        
        df = dl.taiwan_stock_info()
        
        if not df.empty:
            df['stock_name'] = df['stock_name'].astype(str).str.strip()
            df['stock_id'] = df['stock_id'].astype(str).str.strip()
            STOCK_MAP_NAME_TO_ID = dict(zip(df['stock_name'], df['stock_id']))
            STOCK_MAP_ID_TO_NAME = dict(zip(df['stock_id'], df['stock_name']))
            
            # 建立分類地圖
            cat_dict = {}
            for _, row in df.iterrows():
                cat = str(row.get('industry_category', '未分類')).strip()
                if not cat or cat == 'nan': cat = '未分類'
                if cat not in cat_dict: cat_dict[cat] = []
                cat_dict[cat].append({'code': row['stock_id'], 'name': row['stock_name']})
            CATEGORY_MAP = cat_dict
            
            eh.logger.success("System", f"已載入 {len(df)} 檔股票資料, 分為 {len(CATEGORY_MAP)} 類。")
        else:
            eh.logger.warning("System", "警告：股票清單下載失敗 (Empty)。")
            
    except Exception as e:
        if "'data'" in str(e): 
            eh.logger.error("System", "Token 失效，切換至訪客模式。")
        else: 
            eh.logger.error("System", "股票清單初始化失敗", {'error': str(e)})

# 初始化執行
try:
    init_stock_list()
except:
    pass

# Fallback: 基本股票清單
if not CATEGORY_MAP:
    CATEGORY_MAP = {
        '半導體': [
            {'code': '2330', 'name': '台積電'},
            {'code': '2317', 'name': '鴻海'},
            {'code': '2454', 'name': '聯發科'},
            {'code': '2303', 'name': '聯電'},
            {'code': '3034', 'name': '台積電'},
        ],
        '電子': [
            {'code': '2352', 'name': '藍天'},
            {'code': '2377', 'name': '微星'},
            {'code': '2382', 'name': '廣達'},
        ],
        '金控': [
            {'code': '2881', 'name': '富邦金'},
            {'code': '2882', 'name': '國泰金'},
            {'code': '2883', 'name': '開發金'},
            {'code': '2884', 'name': '玉山金'},
            {'code': '2885', 'name': '元大金'},
        ],
        '傳產': [
            {'code': '2002', 'name': '中鋼'},
            {'code': '1301', 'name': '台塑'},
            {'code': '1326', 'name': '台化'},
            {'code': '1215', 'name': '卜蜂'},
        ],
        '其他': [
            {'code': '0050', 'name': '元大台灣50'},
            {'code': '0056', 'name': '元大高股息'},
            {'code': '00878', 'name': '國泰永續高股息'},
        ]
    }
    # 建立名稱映射
    for cat, stocks in CATEGORY_MAP.items():
        for s in stocks:
            STOCK_MAP_ID_TO_NAME[s['code']] = s['name']
            STOCK_MAP_NAME_TO_ID[s['name']] = s['code']

def get_stock_name(input_str):
    input_str = str(input_str).strip()
    clean_code = input_str.replace('.TW', '').replace('.TWO', '').strip()
    
    if clean_code.isdigit():
        name = STOCK_MAP_ID_TO_NAME.get(clean_code, f"台股 {clean_code}")
        return name, clean_code

    if input_str in STOCK_MAP_NAME_TO_ID:
        return input_str, STOCK_MAP_NAME_TO_ID[input_str]

    for name, code in STOCK_MAP_NAME_TO_ID.items():
        if input_str in name: return name, code

    return input_str, input_str

@cached(cache=TTLCache(maxsize=500, ttl=3600))
def fetch_data(stock_code, days=730):
    """ 抓取股價 (Price) - 支援 FinMind + yfinance 備用 """

    # 熔斷器保護
    def _fetch():
        code = str(stock_code).replace('.TW', '').strip()
        if not code.isdigit():
             match = re.match(r"(\d+)", code)
             code = match.group(1) if match else code

        # 先嘗試 FinMind
        dl = DataLoader()
        if API_TOKEN:
            dl.login_by_token(api_token=API_TOKEN)

        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        eh.logger.info("FinMind", f"下載股價: {code} from {start_date} ...")

        try:
            df = dl.taiwan_stock_daily(stock_id=code, start_date=start_date)

            if df is not None and not df.empty:
                eh.logger.info("FinMind", f"FinMind 成功取得 {len(df)} 筆資料")
                df = df.rename(columns={'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'})
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df, df['Close'].iloc[-1]
        except Exception as e:
            eh.logger.error("FinMind", f"FinMind 失敗: {e}")

        # Fallback: 使用 yfinance
        eh.logger.info("YFinance", f"嘗試 yfinance取得 {code}...")
        try:
            ticker = yf.Ticker(f"{code}.TW")
            df = ticker.history(period=f"{min(days, 60)}d")
            if df is not None and not df.empty:
                eh.logger.info("YFinance", f"yfinance 成功取得 {len(df)} 筆資料")
                df = df.rename(columns={'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'})
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df, df['Close'].iloc[-1]
        except Exception as e:
            eh.logger.error("YFinance", f"yfinance 也失敗: {e}")

        return pd.DataFrame(), 0

    try:
        result = eh.circuit_breakers['finmind'].call(_fetch)
        return result

    except eh.CircuitOpenError:
        eh.logger.warning("FinMind", "API 熔斷中")
        return pd.DataFrame(), 0

    except Exception as e:
        code_str = str(stock_code).replace('.TW', '').strip()
        eh.logger.error("DataFetch", f"取得 {code_str} 失敗: {e}")
        return pd.DataFrame(), 0
        code_str = str(stock_code).replace('.TW', '').strip()
        eh.logger.error("FinMind", f"下載股價失敗: {code_str}", {'error': str(e)})
        return pd.DataFrame(), 0

@cached(cache=TTLCache(maxsize=500, ttl=43200))
def fetch_financials(stock_code):
    """ 抓取財報 (Financial Statements) & 月營收 - 增強版 """
    
    def _fetch():
        clean_code = str(stock_code).replace('.TW', '').strip()
        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)

        start_date = (datetime.datetime.now() - datetime.timedelta(days=450)).strftime('%Y-%m-%d')
        
        eh.logger.info("FinMind", f"下載財報: {clean_code} ...")
        
        df_fin = dl.taiwan_stock_financial_statement(stock_id=clean_code, start_date=start_date)
        df_rev = dl.taiwan_stock_month_revenue(stock_id=clean_code, start_date=start_date)
        
        return df_fin, df_rev
    
    try:
        return eh.circuit_breakers['finmind'].call(_fetch)
        
    except eh.CircuitOpenError:
        eh.logger.warning("FinMind", "API 熔斷中，財報暫時無法取得")
        return pd.DataFrame(), pd.DataFrame()
        
    except Exception as e:
        eh.logger.error("FinMind", f"下載財報失敗: {stock_code}", {'error': str(e)})
        return pd.DataFrame(), pd.DataFrame()

@cached(cache=TTLCache(maxsize=500, ttl=3600))
def fetch_institutional_investors(stock_code, days=90):
    """ 抓取三大法人買賣超數據 - 增強版 """
    
    def _fetch():
        clean_code = str(stock_code).replace('.TW', '').strip()
        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        eh.logger.info("FinMind", f"下載法人籌碼: {clean_code} ...")
        
        # 抓取個股法人買賣超
        df = dl.taiwan_stock_institutional_investors(
            stock_id=clean_code, 
            start_date=start_date
        )
        
        if df.empty:
            eh.logger.warning("FinMind", f"股票 {clean_code} 籌碼資料為空")
            return pd.DataFrame()
        
        eh.logger.success("FinMind", f"股票 {clean_code} 取得 {len(df)} 筆籌碼資料")

        # 強制轉型：確保 buy/sell 是數字
        df['buy'] = pd.to_numeric(df['buy'], errors='coerce').fillna(0)
        df['sell'] = pd.to_numeric(df['sell'], errors='coerce').fillna(0)
        
        # 計算買賣超
        df['net'] = df['buy'] - df['sell']
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    try:
        return eh.circuit_breakers['finmind'].call(_fetch)
        
    except eh.CircuitOpenError:
        eh.logger.warning("FinMind", "API 熔斷中，籌碼暫時無法取得")
        return pd.DataFrame()
        
    except Exception as e:
        eh.logger.error("FinMind", f"下載籌碼失敗: {stock_code}", {'error': str(e)})
        return pd.DataFrame()

@cached(cache=TTLCache(maxsize=1, ttl=600))
def get_latest_prices():
    """ 抓取上市櫃所有股票最新收盤價 - 增強版 """
    prices = {}
    
    @eh.retry(max_attempts=3, delay=1.0, exceptions=(requests.RequestException,))
    def _fetch_twse():
        r1 = requests.get('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL', timeout=10)
        r1.raise_for_status()
        return r1.json()
    
    @eh.retry(max_attempts=3, delay=1.0, exceptions=(requests.RequestException,))
    def _fetch_tpex():
        r2 = requests.get('https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes', timeout=10)
        r2.raise_for_status()
        return r2.json()
    
    try:
        data = _fetch_twse()
        for item in data:
            prices[item.get('Code')] = item.get('ClosingPrice')
        eh.logger.success("TWSE", f"取得 {len(data)} 檔上市股票價格")
    except Exception as e:
        eh.logger.error("TWSE", f"取得上市股票價格失敗", {'error': str(e)})
    
    try:
        data = _fetch_tpex()
        for item in data:
            prices[item.get('SecuritiesCompanyCode')] = item.get('Close')
        eh.logger.success("TPEx", f"取得 {len(data)} 檔上櫃股票價格")
    except Exception as e:
        eh.logger.error("TPEx", f"取得上櫃股票價格失敗", {'error': str(e)})
    
    return prices

@cached(cache=TTLCache(maxsize=1, ttl=3600))
def get_all_pe_ratios():
    """ 抓取上市櫃所有股票最新本益比 (PER) - 增強版 """
    pe_ratios = {}
    
    @eh.retry(max_attempts=3, delay=1.0, exceptions=(requests.RequestException,))
    def _fetch_twse_per():
        r1 = requests.get('https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL', timeout=10)
        r1.raise_for_status()
        return r1.json()
    
    @eh.retry(max_attempts=3, delay=1.0, exceptions=(requests.RequestException,))
    def _fetch_tpex_per():
        r2 = requests.get('https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis', timeout=10)
        r2.raise_for_status()
        return r2.json()
    
    try:
        data = _fetch_twse_per()
        for item in data:
            try:
                pe_ratios[item.get('Code')] = float(item.get('PEratio', '0').replace(',', ''))
            except ValueError:
                pass
        eh.logger.success("TWSE", f"取得 {len(data)} 檔上市股本益比")
    except Exception as e:
        eh.logger.error("TWSE", f"取得上市股本益比失敗", {'error': str(e)})
    
    try:
        data = _fetch_tpex_per()
        for item in data:
            try:
                pe = item.get('PriceEarningRatio') or item.get('PERatio') or item.get('PEratio') or '0'
                pe_ratios[item.get('SecuritiesCompanyCode')] = float(pe.replace(',', ''))
            except ValueError:
                pass
        eh.logger.success("TPEx", f"取得 {len(data)} 檔上櫃股本益比")
    except Exception as e:
        eh.logger.error("TPEx", f"取得上櫃股本益比失敗", {'error': str(e)})
    
    return pe_ratios

def get_stock_and_category_pe(stock_code):
    """ 取得個股與該類股的平均本益比 """
    pe_ratios = get_all_pe_ratios()
    stock_pe = pe_ratios.get(str(stock_code), 0.0)
    
    # 找尋所屬分類
    target_category = '未分類'
    for cat, stocks in CATEGORY_MAP.items():
        if any(s['code'] == str(stock_code) for s in stocks):
            target_category = cat
            break
            
    # 計算分類平均 PE (排除 <= 0)
    cat_pes = []
    if target_category != '未分類' and target_category in CATEGORY_MAP:
        for s in CATEGORY_MAP[target_category]:
            pe = pe_ratios.get(s['code'], 0)
            if pe > 0:
                cat_pes.append(pe)
                
    cat_avg_pe = sum(cat_pes) / len(cat_pes) if cat_pes else 0.0
    return stock_pe, cat_avg_pe, target_category

def evaluate_data_confidence(df):
    """
    評估股票資料的最新程度，給予信心標籤 - 增強版
    """
    if df is None or df.empty:
        return {"level": "低", "score": "<70%", "reason": "資料缺失"}

    try:
        # 取得資料最後一筆的日期
        last_date = df.index[-1].date()
        today = datetime.datetime.now().date()
        
        # 計算時間差
        days_diff = (today - last_date).days
        
        if days_diff == 0:
            return {"level": "高", "score": "95%", "reason": "當日即時報價"}
        elif days_diff <= 3:
            return {"level": "高", "score": "95%", "reason": f"前{days_diff}交易日資料 (可能為假日/週末)"}
        elif days_diff <= 7:
            return {"level": "中", "score": "75%", "reason": f"資料延遲 {days_diff} 天"}
        else:
            return {"level": "低", "score": "<70%", "reason": f"資料嚴重過期 ({days_diff} 天前)"}
            
    except Exception as e:
        eh.logger.error("DataEval", f"資料信心評估失敗", {'error': str(e)})
        return {"level": "低", "score": "<70%", "reason": "資料時間解析失敗"}

def health_check() -> bool:
    """ 健康檢查 """
    try:
        # 檢查基本功能
        if not STOCK_MAP_ID_TO_NAME:
            return False
        
        # 嘗試抓一筆測試資料
        prices = get_latest_prices()
        return len(prices) > 0
        
    except:
        return False

# 註冊健康檢查
eh.health_checker.register("DataLoader", health_check)
