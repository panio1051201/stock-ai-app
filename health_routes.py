# 健康檢查路由 - 可直接加到 app.py

@app.route('/api/health')
def health_check():
    """服務健康檢查"""
    result = eh.health_checker.check()
    
    status_code = 200 if result['healthy'] else 503
    return jsonify(result), status_code

@app.route('/api/status')
def status_page():
    """系統狀態頁面"""
    health = eh.health_checker.check()
    
    # 基本資訊
    info = {
        'status': 'healthy' if health['healthy'] else 'degraded',
        'uptime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'active_users': len(USAGE_DB),
        'total_logs': len(ACCESS_LOG),
        'api_quota_remaining': LIMIT_COUNT_GUEST - USAGE_DB.get(request.remote_addr, {}).get('count', 0) if request.remote_addr in USAGE_DB else LIMIT_COUNT_GUEST,
    }
    
    # 電路熔斷器狀態
    circuits = {}
    for name, cb in eh.circuit_breakers.items():
        circuits[name] = {
            'state': cb.state,
            'failures': cb.failures
        }
    
    return jsonify({
        'info': info,
        'health': health,
        'circuits': circuits
    })

@app.route('/api/logs/errors')
def get_error_logs():
    """取得錯誤日誌"""
    try:
        with open('error_log.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 只取最後 100 行
            return jsonify({
                'logs': lines[-100:] if len(lines) > 100 else lines,
                'total': len(lines)
            })
    except:
        return jsonify({'logs': [], 'total': 0})
