# Error Handling Module - 強化穩定性
# 提供結構化日誌、API 重試、熔斷器、用戶友善錯誤

import time
import logging
import functools
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable, Any, Optional

# ================================
# 1. 結構化日誌系統
# ================================

class StructuredLogger:
    """統一日誌格式"""
    
    def __init__(self, name: str = "StockAI"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重複 handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 寫入檔案
        self.error_file = "error_log.txt"
        self.access_file = "access_log.txt"
    
    def error(self, module: str, message: str, details: dict = None):
        """記錄錯誤"""
        msg = f"[{module}] {message}"
        if details:
            msg += f" | 詳情: {details}"
        self.logger.error(msg)
        self._write_to_file(self.error_file, f"[ERROR] {msg}")
    
    def warning(self, module: str, message: str):
        """記錄警告"""
        self.logger.warning(f"[{module}] {message}")
    
    def info(self, module: str, message: str):
        """記錄資訊"""
        self.logger.info(f"[{module}] {message}")
    
    def success(self, module: str, message: str):
        """記錄成功"""
        self.logger.info(f"[{module}] ✓ {message}")
    
    def _write_to_file(self, filename: str, message: str):
        """寫入日誌檔案"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
        except:
            pass

# 全域日誌實例
logger = StructuredLogger()

# ================================
# 2. API 熔斷器 (Circuit Breaker)
# ================================

class CircuitBreaker:
    """
    熔斷器：防止 API 過載
    狀態：CLOSE（正常）→ OPEN（熔斷）→ HALF_OPEN（測試）
    """
    
    CLOSE = "CLOSE"      # 正常
    OPEN = "OPEN"         # 熔斷中
    HALF_OPEN = "HALF_OPEN"  # 測試中
    
    def __init__(self, name: str, failure_threshold: int = 5, timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold  # 失敗多少次後熔斷
        self.timeout = timeout  # 熔斷多久（秒）
        self.failures = 0
        self.last_failure_time = None
        self.state = self.CLOSE
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """執行函式並保護"""
        
        # 檢查是否需要轉換狀態
        self._check_state_transition()
        
        # 如果是熔斷狀態，直接拒絕
        if self.state == self.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN. Try later.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """成功時重置"""
        self.failures = 0
        self.state = self.CLOSE
    
    def _on_failure(self):
        """失敗時計數"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning("CircuitBreaker", f"{self.name} 熔斷開啟！連續 {self.failures} 次失敗")
    
    def _check_state_transition(self):
        """檢查狀態轉換"""
        if self.state == self.OPEN and self.last_failure_time:
            if (datetime.now() - self.last_failure_time).seconds >= self.timeout:
                self.state = self.HALF_OPEN
                logger.info("CircuitBreaker", f"{self.name} 進入 HALF_OPEN 測試模式")

class CircuitOpenError(Exception):
    """熔斷器開啟錯誤"""
    pass

# API 熔斷器實例
circuit_breakers = {
    'finmind': CircuitBreaker('FinMind', failure_threshold=5, timeout=60),
    'twse': CircuitBreaker('TWSE', failure_threshold=3, timeout=30),
    'tpex': CircuitBreaker('TPEx', failure_threshold=3, timeout=30),
}

# ================================
# 3. 重試機制 (Retry)
# ================================

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    重試修飾器
    
    Args:
        max_attempts: 最大嘗試次數
        delay: 初始延遲（秒）
        backoff: 延遲倍增
        exceptions: 需要重試的異常
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(func.__name__, f"已重試 {max_attempts} 次，仍失敗", {'error': str(e)})
                        raise
                    
                    logger.warning(func.__name__, f"第 {attempt} 次失敗，{current_delay:.1f}秒後重試", {'error': str(e)})
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
        return wrapper
    return decorator

# ================================
# 4. Rate Limiter - 流量限制
# ================================

class RateLimiter:
    """簡單的流量限制器"""
    
    def __init__(self, max_calls: int = 100, window: int = 60):
        self.max_calls = max_calls  # 視窗內最大呼叫
        self.window = window  # 視窗秒數
        self.calls = defaultdict(list)  # ip -> [時間戳列表]
    
    def is_allowed(self, key: str) -> bool:
        """檢查是否允許呼叫"""
        now = time.time()
        # 清理過期記錄
        self.calls[key] = [t for t in self.calls[key] if now - t < self.window]
        
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        self.calls[key].append(now)
        return True
    
    def get_reset_time(self, key: str) -> Optional[int]:
        """取得剩餘時間（秒）"""
        if key not in self.calls or not self.calls[key]:
            return None
        
        now = time.time()
        oldest = min(self.calls[key])
        reset = self.window - (now - oldest)
        return int(reset) if reset > 0 else None

# 全域流量限制
rate_limiter = RateLimiter(max_calls=100, window=60)

# ================================
# 5. 用戶友善錯誤訊息
# ================================

class UserFriendlyError(Exception):
    """用戶友善錯誤"""
    
    # 錯誤碼對應訊息
    ERRORS = {
        'STOCK_NOT_FOUND': {
            'message': '找不到這檔股票',
            'suggestion': '請檢查股票代碼是否正確，或嘗試搜尋股票名稱'
        },
        'DATA_NOT_AVAILABLE': {
            'message': '暫時無法取得資料',
            'suggestion': '可能是今日非交易日，或 API 忙碌中，請稍後再試'
        },
        'STRATEGY_ERROR': {
            'message': '策略執行失敗',
            'suggestion': '可能資料不足，請嘗試其他股票或稍後再試'
        },
        'RATE_LIMITED': {
            'message': '操作太頻繁',
            'suggestion': '請稍後再試，或聯繫管理員提升權限'
        },
        'INVALID_CODE': {
            'message': '股票代碼格式錯誤',
            'suggestion': '請輸入正確的股票代碼（如：2330、2317）'
        },
        'API_ERROR': {
            'message': '資料來源暫時異常',
            'suggestion': 'API 忙碌中，系統已自動重試，若持續出現請通知管理員'
        },
        'NETWORK_ERROR': {
            'message': '網路連線異常',
            'suggestion': '請檢查網路連線後再試'
        }
    }
    
    def __init__(self, error_code: str, extra_info: dict = None):
        self.error_code = error_code
        self.extra_info = extra_info or {}
        error = self.ERRORS.get(error_code, {
            'message': '發生未知錯誤',
            'suggestion': '請聯繫管理員'
        })
        self.message = error['message']
        self.suggestion = error['suggestion']
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'error': True,
            'code': self.error_code,
            'message': self.message,
            'suggestion': self.suggestion,
            **self.extra_info
        }
    
    @staticmethod
    def format_error(e: Exception) -> dict:
        """格式化任何錯誤為用戶友善格式"""
        if isinstance(e, UserFriendlyError):
            return e.to_dict()
        
        error_str = str(e).lower()
        
        # 根據錯誤內容映射
        if 'stock' in error_str or 'not found' in error_str:
            return UserFriendlyError('STOCK_NOT_FOUND').to_dict()
        elif 'timeout' in error_str or 'connection' in error_str:
            return UserFriendlyError('NETWORK_ERROR').to_dict()
        elif 'limit' in error_str or 'quota' in error_str:
            return UserFriendlyError('RATE_LIMITED').to_dict()
        else:
            return UserFriendlyError('API_ERROR', {'details': str(e)}).to_dict()

# ================================
# 6. 健康檢查
# ================================

class HealthChecker:
    """服務健康檢查"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = {}
    
    def register(self, name: str, check_func: Callable):
        """註冊健康檢查"""
        self.checks[name] = check_func
    
    def check(self) -> dict:
        """執行所有健康檢查"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = {'status': 'healthy' if result else 'unhealthy', 'last_check': datetime.now().isoformat()}
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {'status': 'error', 'error': str(e), 'last_check': datetime.now().isoformat()}
                overall_healthy = False
            
            self.last_check_time[name] = datetime.now()
        
        return {
            'healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }

# 全域健康檢查器
health_checker = HealthChecker()

# ================================
# 7. 輔助函式
# ================================

def safe_execute(func: Callable, default=None, error_code: str = 'API_ERROR') -> Any:
    """
    安全執行函式，失敗時返回預設值
    """
    try:
        return func()
    except Exception as e:
        logger.error(func.__name__, str(e))
        return default

def validate_stock_code(code: str) -> bool:
    """
    驗證股票代碼格式
    """
    if not code:
        return False
    
    # 移除空白和常見前綴
    code = str(code).strip().upper()
    code = code.replace('.TW', '').replace('.TWO', '').replace(' ', '')
    
    # 檢查是否為數字且長度合理
    return code.isdigit() and 4 <= len(code) <= 6

def get_error_response(error: Exception) -> dict:
    """
    取得標準錯誤回應
    """
    return UserFriendlyError.format_error(error)
