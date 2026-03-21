/**
 * UI Enhancements - 使用者體驗增強
 * 可直接加入 index.html 或作為外部腳本
 */

const UIEnhancements = (function() {
    'use strict';
    
    // ================================
    // 1. Toast 通知系統
    // ================================
    const Toast = {
        container: null,
        
        init() {
            if (this.container) return;
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 320px;
            `;
            document.body.appendChild(this.container);
        },
        
        show(message, type = 'info', duration = 3000) {
            this.init();
            
            const toast = document.createElement('div');
            const colors = {
                success: { bg: 'rgba(46, 160, 67, 0.95)', icon: 'fa-check-circle' },
                error: { bg: 'rgba(218, 54, 51, 0.95)', icon: 'fa-exclamation-circle' },
                warning: { bg: 'rgba(210, 153, 34, 0.95)', icon: 'fa-exclamation-triangle' },
                info: { bg: 'rgba(88, 166, 255, 0.95)', icon: 'fa-info-circle' }
            };
            
            const color = colors[type] || colors.info;
            
            toast.style.cssText = `
                background: ${color.bg};
                color: white;
                padding: 14px 20px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease;
                font-size: 14px;
                backdrop-filter: blur(10px);
            `;
            
            toast.innerHTML = `
                <i class="fas ${color.icon}" style="font-size: 18px;"></i>
                <span>${message}</span>
            `;
            
            this.container.appendChild(toast);
            
            // 自動移除
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },
        
        success(msg) { this.show(msg, 'success'); },
        error(msg) { this.show(msg, 'error', 5000); },
        warning(msg) { this.show(msg, 'warning', 4000); },
        info(msg) { this.show(msg, 'info'); }
    };
    
    // ================================
    // 2. 載入動畫
    // ================================
    const Loading = {
        overlay: null,
        
        show(text = '載入中...') {
            if (this.overlay) return;
            
            this.overlay = document.createElement('div');
            this.overlay.id = 'loading-overlay';
            this.overlay.style.cssText = `
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(13, 17, 23, 0.9);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                backdrop-filter: blur(5px);
            `;
            
            this.overlay.innerHTML = `
                <div style="
                    width: 50px; height: 50px;
                    border: 3px solid #30363d;
                    border-top-color: #58a6ff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <p style="color: #c9d1d9; margin-top: 20px; font-size: 14px;">${text}</p>
            `;
            
            document.body.appendChild(this.overlay);
        },
        
        hide() {
            if (this.overlay) {
                this.overlay.remove();
                this.overlay = null;
            }
        }
    };
    
    // ================================
    // 3. 確認對話框
    // ================================
    const Confirm = {
        show(options) {
            return new Promise((resolve) => {
                const { title = '確認', message, confirmText = '確認', cancelText = '取消', type = 'warning' } = options;
                
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.7);
                    display: flex; align-items: center; justify-content: center;
                    z-index: 10001; backdrop-filter: blur(5px);
                `;
                
                const colors = {
                    warning: '#f1c40f',
                    danger: '#e74c3c',
                    info: '#3498db'
                };
                
                overlay.innerHTML = `
                    <div style="
                        background: #161b22;
                        border: 1px solid #30363d;
                        border-radius: 16px;
                        padding: 24px;
                        max-width: 320px;
                        width: 90%;
                        text-align: center;
                        animation: popIn 0.2s ease;
                    ">
                        <i class="fas fa-${type === 'danger' ? 'exclamation-circle' : 'question-circle'}" 
                           style="font-size: 48px; color: ${colors[type] || colors.info}; margin-bottom: 16px;"></i>
                        <h3 style="color: #fff; margin: 0 0 12px 0;">${title}</h3>
                        <p style="color: #8b949e; margin: 0 0 24px 0; font-size: 14px;">${message}</p>
                        <div style="display: flex; gap: 12px;">
                            <button id="confirm-cancel" style="
                                flex: 1; padding: 12px; border-radius: 8px;
                                border: 1px solid #30363d; background: #21262d;
                                color: #c9d1d9; cursor: pointer; font-size: 14px;
                            ">${cancelText}</button>
                            <button id="confirm-ok" style="
                                flex: 1; padding: 12px; border-radius: 8px;
                                border: none; background: ${colors[type] || colors.info};
                                color: #fff; cursor: pointer; font-size: 14px; font-weight: bold;
                            ">${confirmText}</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(overlay);
                
                const close = (result) => {
                    overlay.remove();
                    resolve(result);
                };
                
                overlay.querySelector('#confirm-cancel').onclick = () => close(false);
                overlay.querySelector('#confirm-ok').onclick = () => close(true);
                overlay.onclick = (e) => { if (e.target === overlay) close(false); };
            });
        }
    };
    
    // ================================
    // 4. 手指滑動支援
    // ================================
    const SwipeHandler = {
        element: null,
        startX: 0,
        startY: 0,
        
        init(element, options = {}) {
            this.element = element;
            
            element.addEventListener('touchstart', (e) => {
                this.startX = e.touches[0].clientX;
                this.startY = e.touches[0].clientY;
            }, { passive: true });
            
            element.addEventListener('touchend', (e) => {
                const deltaX = e.changedTouches[0].clientX - this.startX;
                const deltaY = e.changedTouches[0].clientY - this.startY;
                
                // 水平滑動
                if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY)) {
                    if (deltaX > 0 && options.onSwipeRight) {
                        options.onSwipeRight();
                    } else if (deltaX < 0 && options.onSwipeLeft) {
                        options.onSwipeLeft();
                    }
                }
                
                // 垂直滑動
                if (Math.abs(deltaY) > 50 && Math.abs(deltaY) > Math.abs(deltaX)) {
                    if (deltaY > 0 && options.onSwipeDown) {
                        options.onSwipeDown();
                    } else if (deltaY < 0 && options.onSwipeUp) {
                        options.onSwipeUp();
                    }
                }
            }, { passive: true });
        }
    };
    
    // ================================
    // 5. 快捷鍵支援
    // ================================
    const Keyboard = {
        shortcuts: {},
        
        register(key, callback, desc = '') {
            this.shortcuts[key] = { callback, desc };
        },
        
        init() {
            document.addEventListener('keydown', (e) => {
                const key = e.key.toLowerCase();
                
                // Ctrl/Cmd + Key
                if (e.ctrlKey || e.metaKey) {
                    const shortcut = `ctrl+${key}`;
                    if (this.shortcuts[shortcut]) {
                        e.preventDefault();
                        this.shortcuts[shortcut].callback();
                    }
                }
                
                // Alt + Key
                if (e.altKey) {
                    const shortcut = `alt+${key}`;
                    if (this.shortcuts[shortcut]) {
                        e.preventDefault();
                        this.shortcuts[shortcut].callback();
                    }
                }
                
                // Solo Key
                if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
                    if (this.shortcuts[key]) {
                        this.shortcuts[key].callback();
                    }
                }
            });
        },
        
        help() {
            let text = '⌨️ 快捷鍵:\n';
            for (const [key, data] of Object.entries(this.shortcuts)) {
                text += `${key}: ${data.desc}\n`;
            }
            alert(text);
        }
    };
    
    // ================================
    // 6. 鍵盤快捷鍵說明
    // ================================
    Keyboard.register('?', () => Keyboard.help(), '顯示快捷鍵說明');
    Keyboard.register('ctrl+s', () => Toast.info('已儲存'), '儲存');
    Keyboard.register('ctrl+r', () => location.reload(), '重新整理');
    
    // ================================
    // 7. 懶載入圖片
    // ================================
    const LazyImage = {
        init() {
            if ('IntersectionObserver' in window) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            if (img.dataset.src) {
                                img.src = img.dataset.src;
                                img.removeAttribute('data-src');
                            }
                            observer.unobserve(img);
                        }
                    });
                });
                
                document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
            }
        }
    };
    
    // ================================
    // 8. 手指導航指示器
    // ================================
    const NavigationHint = {
        show() {
            const hint = document.createElement('div');
            hint.id = 'nav-hint';
            hint.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(22, 27, 34, 0.95);
                color: #8b949e;
                padding: 12px 20px;
                border-radius: 24px;
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 9998;
                animation: fadeInUp 0.3s ease;
                border: 1px solid #30363d;
            `;
            
            hint.innerHTML = `
                <i class="fas fa-hand-point-up" style="color: #58a6ff;"></i>
                <span>左右滑動切換功能</span>
            `;
            
            document.body.appendChild(hint);
            
            setTimeout(() => {
                hint.style.animation = 'fadeOut 0.3s ease forwards';
                setTimeout(() => hint.remove(), 300);
            }, 4000);
        }
    };
    
    // ================================
    // 9. 訂閱進度指示器
    // ================================
    const QuotaIndicator = {
        element: null,
        maxRequests: 25,
        currentRequests: 0,
        
        init(max, current = 0) {
            this.maxRequests = max;
            this.currentRequests = current;
            
            // 在導航列添加額度顯示
            const navbar = document.querySelector('.navbar');
            if (!navbar) return;
            
            this.element = document.createElement('div');
            this.element.id = 'quota-indicator';
            this.element.style.cssText = `
                font-size: 12px;
                color: #8b949e;
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                background: #21262d;
                border-radius: 16px;
            `;
            
            this.update(current);
            navbar.appendChild(this.element);
        },
        
        update(current, resetTime = null) {
            this.currentRequests = current;
            const remaining = this.maxRequests - current;
            const percent = (remaining / this.maxRequests) * 100;
            
            let color = '#3fb950';
            if (percent < 50) color = '#f1c40f';
            if (percent < 20) color = '#f85149';
            
            this.element.innerHTML = `
                <i class="fas fa-bolt" style="color: ${color};"></i>
                <span style="color: ${color};">${remaining}</span>
                <span>/ ${this.maxRequests}</span>
                ${resetTime ? `<span style="font-size: 10px;">| ${resetTime}重置</span>` : ''}
            `;
            
            // 添加動畫
            this.element.style.transform = 'scale(1.05)';
            setTimeout(() => {
                this.element.style.transform = 'scale(1)';
            }, 100);
        }
    };
    
    // ================================
    // 10. 捷徑功能表 (長按/右鍵)
    // ================================
    const ContextMenu = {
        menu: null,
        
        init() {
            this.menu = document.createElement('div');
            this.menu.id = 'context-menu';
            this.menu.style.cssText = `
                position: fixed;
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 8px 0;
                min-width: 180px;
                z-index: 10002;
                display: none;
                box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            `;
            document.body.appendChild(this.menu);
            
            document.addEventListener('click', () => this.hide());
        },
        
        show(x, y, items) {
            this.menu.innerHTML = items.map(item => `
                <div class="context-item ${item.danger ? 'danger' : ''}" 
                     data-action="${item.action}"
                     style="padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px;
                            color: ${item.danger ? '#f85149' : '#c9d1d9'};
                            font-size: 13px;"
                     onmouseover="this.style.background='#21262d'"
                     onmouseout="this.style.background='transparent'">
                    <i class="fas ${item.icon || 'fa-chevron-right'}" style="width: 16px;"></i>
                    <span>${item.label}</span>
                </div>
            `).join('');
            
            // 事件
            this.menu.querySelectorAll('.context-item').forEach(el => {
                el.onclick = () => {
                    const action = el.dataset.action;
                    this.hide();
                    items.find(i => i.action === action)?.callback();
                };
            });
            
            // 位置
            this.menu.style.left = `${Math.min(x, window.innerWidth - 200)}px`;
            this.menu.style.top = `${Math.min(y, window.innerHeight - 200)}px`;
            this.menu.style.display = 'block';
        },
        
        hide() {
            this.menu.style.display = 'none';
        },
        
        add(target, items) {
            target.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.show(e.clientX, e.clientY, items);
            });
            
            // 長按支援 (手機)
            let pressTimer;
            target.addEventListener('touchstart', (e) => {
                pressTimer = setTimeout(() => {
                    this.show(e.touches[0].clientX, e.touches[0].clientY, items);
                }, 500);
            });
            target.addEventListener('touchend', () => clearTimeout(pressTimer));
            target.addEventListener('touchmove', () => clearTimeout(pressTimer));
        }
    };
    
    // ================================
    // 初始化
    // ================================
    function init() {
        Keyboard.init();
        ContextMenu.init();
        LazyImage.init();
        
        // 添加動畫樣式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @keyframes popIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            @keyframes fadeInUp {
                from { transform: translate(-50%, 20px); opacity: 0; }
                to { transform: translate(-50%, 0); opacity: 1; }
            }
            @keyframes fadeOut {
                to { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        console.log('✅ UI Enhancements 已啟用');
    }
    
    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 對外暴露介面
    return {
        Toast,
        Loading,
        Confirm,
        SwipeHandler,
        Keyboard,
        NavigationHint,
        QuotaIndicator,
        ContextMenu
    };
})();

// 全域捷徑
const { Toast, Loading, Confirm, SwipeHandler, Keyboard, NavigationHint, QuotaIndicator, ContextMenu } = UIEnhancements;
