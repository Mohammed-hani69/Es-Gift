/**
 * Tawk.io Manager - Es-Gift
 * إدارة متقدمة ومحسنة لنظام الشات
 */

(function() {
    'use strict';
    
    // متغيرات النظام
    let tawkInitialized = false;
    let cleanupInterval = null;
    let positionCheckInterval = null;
    let mutationObserver = null;
    
    // إعدادات النظام
    const TAWK_CONFIG = {
        WIDGET_ID: '687e2b2c4fc0181916b601e1/1j0mdhak3',
        POSITION: {
            desktop: { bottom: '25px', right: '25px', size: '65px' },
            tablet: { bottom: '20px', right: '20px', size: '60px' },
            mobile: { bottom: '18px', right: '18px', size: '55px' }
        },
        Z_INDEX: 2147483647,
        CLEANUP_INTERVAL: 3000,
        POSITION_CHECK_INTERVAL: 1000
    };
    
    // كشف نوع الجهاز
    function getDeviceType() {
        const width = window.innerWidth;
        if (width <= 480) return 'mobile';
        if (width <= 768) return 'tablet';
        return 'desktop';
    }
    
    // حذف جميع أيقونات الشات الأخرى
    function removeOtherChatIcons() {
        const selectors = [
            '.floating-support-icon',
            '.es-chat-floating-icon',
            '.support-icon',
            '.chat-icon',
            '.floating-chat',
            '.whatsapp-icon',
            '.support-floating',
            '.chat-widget',
            '.live-chat',
            '.help-icon',
            '.customer-support-icon',
            '[class*="floating-support"]',
            '[class*="chat-floating"]',
            '[class*="support-floating"]',
            '[class*="whatsapp-icon"]',
            '[class*="chat-widget"]',
            '[class*="live-chat"]',
            '[class*="help-icon"]',
            '[data-chat]:not([id*="tawk"])',
            '[data-support]:not([id*="tawk"])'
        ];
        
        let removedCount = 0;
        
        selectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    if (element && 
                        !element.id.includes('tawk') && 
                        !element.className.includes('tawk')) {
                        
                        // إخفاء فوري
                        element.style.cssText = `
                            display: none !important;
                            visibility: hidden !important;
                            opacity: 0 !important;
                            pointer-events: none !important;
                            position: absolute !important;
                            top: -9999px !important;
                            left: -9999px !important;
                            z-index: -999 !important;
                            width: 0 !important;
                            height: 0 !important;
                        `;
                        
                        // حذف من DOM
                        setTimeout(() => {
                            if (element.parentNode) {
                                element.parentNode.removeChild(element);
                            }
                        }, 100);
                        
                        removedCount++;
                    }
                });
            } catch (error) {
                console.warn('خطأ في حذف أيقونة الشات:', selector, error);
            }
        });
        
        if (removedCount > 0) {
            console.log(`✅ تم حذف ${removedCount} أيقونة شات غير مرغوب فيها`);
        }
    }
    
    // ضبط موقع وتصميم أيقونة Tawk.io
    function ensureTawkPosition() {
        const tawkBubble = document.querySelector('#tawk-bubble');
        if (!tawkBubble) return false;
        
        const deviceType = getDeviceType();
        const config = TAWK_CONFIG.POSITION[deviceType];
        
        // تطبيق الستايل المحسن
        tawkBubble.style.cssText = `
            position: fixed !important;
            bottom: ${config.bottom} !important;
            right: ${config.right} !important;
            width: ${config.size} !important;
            height: ${config.size} !important;
            z-index: ${TAWK_CONFIG.Z_INDEX} !important;
            background: linear-gradient(135deg, #ff0033 0%, #ff1a4d 50%, #cc0027 100%) !important;
            border: 3px solid #ffffff !important;
            border-radius: 50% !important;
            box-shadow: 
                0 8px 32px rgba(255, 0, 51, 0.4),
                0 4px 16px rgba(255, 0, 51, 0.3),
                0 2px 8px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
            will-change: transform, box-shadow !important;
            transform: translateZ(0) scale(1) !important;
            backface-visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            top: auto !important;
            left: auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: 'Cairo', sans-serif !important;
            cursor: pointer !important;
            animation: tawk-gentle-pulse 6s ease-in-out infinite !important;
            user-select: none !important;
            pointer-events: auto !important;
        `;
        
        return true;
    }
    
    // إعداد مراقب DOM للتغييرات
    function setupMutationObserver() {
        if (mutationObserver) {
            mutationObserver.disconnect();
        }
        
        mutationObserver = new MutationObserver(function(mutations) {
            let needsCleanup = false;
            let needsPositionCheck = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // فحص العقد المضافة
                    if (mutation.addedNodes.length > 0) {
                        for (let node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // فحص إذا كان عنصر شات جديد
                                const chatClasses = ['chat', 'support', 'floating', 'tawk'];
                                const hasChat = chatClasses.some(cls => 
                                    node.className && node.className.includes(cls)
                                );
                                
                                if (hasChat) {
                                    if (node.id && node.id.includes('tawk')) {
                                        needsPositionCheck = true;
                                    } else {
                                        needsCleanup = true;
                                    }
                                }
                            }
                        }
                    }
                }
                
                // فحص تغييرات الخصائص
                if (mutation.type === 'attributes' && 
                    mutation.target.id === 'tawk-bubble') {
                    needsPositionCheck = true;
                }
            });
            
            // تشغيل التنظيف والفحص حسب الحاجة
            if (needsCleanup) {
                setTimeout(removeOtherChatIcons, 50);
            }
            
            if (needsPositionCheck) {
                setTimeout(ensureTawkPosition, 100);
            }
        });
        
        // بدء المراقبة
        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class', 'id']
        });
    }
    
    // تحميل سكريبت Tawk.io
    function loadTawkScript() {
        return new Promise((resolve, reject) => {
            if (typeof Tawk_API !== 'undefined') {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.async = true;
            script.src = `https://embed.tawk.to/${TAWK_CONFIG.WIDGET_ID}`;
            script.charset = 'UTF-8';
            script.setAttribute('crossorigin', '*');
            
            script.onload = () => {
                console.log('✅ Tawk.io script loaded successfully');
                resolve();
            };
            
            script.onerror = (error) => {
                console.error('❌ Failed to load Tawk.io script:', error);
                reject(error);
            };
            
            const firstScript = document.getElementsByTagName('script')[0];
            firstScript.parentNode.insertBefore(script, firstScript);
        });
    }
    
    // إعداد Tawk.io API
    function setupTawkAPI() {
        if (typeof Tawk_API === 'undefined') {
            window.Tawk_API = {};
        }
        
        if (typeof Tawk_LoadStart === 'undefined') {
            window.Tawk_LoadStart = new Date();
        }
        
        // إعدادات الموقع والتصميم
        Tawk_API.customStyle = {
            visibility: {
                desktop: {
                    position: 'br',
                    xOffset: 25,
                    yOffset: 25
                },
                mobile: {
                    position: 'br',
                    xOffset: 18,
                    yOffset: 18
                }
            },
            zIndex: TAWK_CONFIG.Z_INDEX,
            bubble: {
                position: 'fixed',
                backgroundColor: '#ff0033',
                borderRadius: '50%',
                width: '65px',
                height: '65px'
            }
        };
        
        // عند تحميل Tawk.io
        Tawk_API.onLoad = function() {
            console.log('✅ Tawk.io loaded - Es-Gift Support System');
            tawkInitialized = true;
            
            // تنظيف فوري
            setTimeout(() => {
                removeOtherChatIcons();
                ensureTawkPosition();
            }, 500);
            
            // تأكيد إضافي
            setTimeout(() => {
                ensureTawkPosition();
            }, 2000);
        };
        
        // عند بدء المحادثة
        Tawk_API.onChatStarted = function() {
            console.log('💬 Chat session started');
            
            // إرسال معلومات الصفحة
            const pageInfo = `الصفحة الحالية: ${document.title}\nالرابط: ${window.location.href}`;
            setTimeout(() => {
                if (typeof Tawk_API.addEvent === 'function') {
                    Tawk_API.addEvent('chatMessageSystem', pageInfo);
                }
            }, 1000);
        };
        
        // عند تكبير/تصغير النافذة
        Tawk_API.onChatMaximized = function() {
            console.log('🔼 Chat window maximized');
        };
        
        Tawk_API.onChatMinimized = function() {
            console.log('🔽 Chat window minimized');
        };
        
        // عند تغيير الحالة
        Tawk_API.onStatusChange = function(status) {
            console.log('📡 Tawk.io status changed:', status);
        };
    }
    
    // بدء الفترات الدورية
    function startIntervals() {
        // تنظيف دوري
        if (cleanupInterval) clearInterval(cleanupInterval);
        cleanupInterval = setInterval(() => {
            removeOtherChatIcons();
        }, TAWK_CONFIG.CLEANUP_INTERVAL);
        
        // فحص الموقع دورياً
        if (positionCheckInterval) clearInterval(positionCheckInterval);
        positionCheckInterval = setInterval(() => {
            if (tawkInitialized) {
                ensureTawkPosition();
            }
        }, TAWK_CONFIG.POSITION_CHECK_INTERVAL);
    }
    
    // تنظيف الموارد
    function cleanup() {
        if (cleanupInterval) {
            clearInterval(cleanupInterval);
            cleanupInterval = null;
        }
        
        if (positionCheckInterval) {
            clearInterval(positionCheckInterval);
            positionCheckInterval = null;
        }
        
        if (mutationObserver) {
            mutationObserver.disconnect();
            mutationObserver = null;
        }
    }
    
    // إعادة الحجم عند تغيير حجم النافذة
    function handleResize() {
        if (tawkInitialized) {
            setTimeout(ensureTawkPosition, 300);
        }
    }
    
    // تهيئة النظام
    async function initializeSystem() {
        try {
            console.log('🚀 بدء تهيئة نظام Tawk.io - Es-Gift');
            
            // تنظيف أولي
            removeOtherChatIcons();
            
            // إعداد API
            setupTawkAPI();
            
            // تحميل السكريبت
            await loadTawkScript();
            
            // إعداد المراقبة
            setupMutationObserver();
            
            // بدء الفترات الدورية
            startIntervals();
            
            // مراقبة تغيير حجم النافذة
            window.addEventListener('resize', handleResize);
            
            // تنظيف عند إغلاق الصفحة
            window.addEventListener('beforeunload', cleanup);
            
            console.log('✅ تم تهيئة نظام Tawk.io بنجاح');
            
        } catch (error) {
            console.error('❌ فشل في تهيئة نظام Tawk.io:', error);
        }
    }
    
    // دوال مساعدة للوصول العام
    window.EsGiftChat = {
        open: function() {
            if (typeof Tawk_API !== 'undefined' && typeof Tawk_API.maximize === 'function') {
                Tawk_API.maximize();
                return true;
            }
            console.warn('⚠️ Tawk.io غير متاح حالياً');
            return false;
        },
        
        close: function() {
            if (typeof Tawk_API !== 'undefined' && typeof Tawk_API.minimize === 'function') {
                Tawk_API.minimize();
                return true;
            }
            return false;
        },
        
        sendMessage: function(message) {
            if (typeof Tawk_API !== 'undefined' && typeof Tawk_API.addEvent === 'function') {
                Tawk_API.addEvent('chatMessageVisitor', message);
                Tawk_API.maximize();
                return true;
            }
            return false;
        },
        
        isOnline: function() {
            if (typeof Tawk_API !== 'undefined' && typeof Tawk_API.getStatus === 'function') {
                return Tawk_API.getStatus() === 'online';
            }
            return false;
        },
        
        getStatus: function() {
            if (typeof Tawk_API !== 'undefined' && typeof Tawk_API.getStatus === 'function') {
                return Tawk_API.getStatus();
            }
            return 'unknown';
        },
        
        forceCleanup: function() {
            removeOtherChatIcons();
            ensureTawkPosition();
            console.log('🧹 تم تشغيل التنظيف اليدوي');
        },
        
        reinitialize: function() {
            cleanup();
            setTimeout(initializeSystem, 1000);
            console.log('🔄 إعادة تهيئة النظام...');
        }
    };
    
    // بدء التهيئة عند تحميل DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSystem);
    } else {
        // DOM محمل بالفعل
        setTimeout(initializeSystem, 100);
    }
    
    // تهيئة إضافية عند تحميل النافذة
    window.addEventListener('load', function() {
        setTimeout(() => {
            removeOtherChatIcons();
            ensureTawkPosition();
        }, 1500);
    });
    
    console.log('📦 Es-Gift Tawk.io Manager loaded');
    
})();
