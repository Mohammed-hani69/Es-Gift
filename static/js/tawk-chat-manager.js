/**
 * إدارة أيقونة Tawk.to وضمان ثباتها
 * حذف جميع الأيقونات الأخرى
 */

(function() {
    'use strict';
    
    // دالة حذف الأيقونات الأخرى
    function removeOtherChatIcons() {
        var selectors = [
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
            '[data-chat]',
            '[data-support]'
        ];
        
        selectors.forEach(function(selector) {
            try {
                var elements = document.querySelectorAll(selector);
                elements.forEach(function(element) {
                    if (element && !element.id.includes('tawk') && !element.className.includes('tawk')) {
                        element.style.display = 'none';
                        element.style.visibility = 'hidden';
                        element.style.opacity = '0';
                        element.style.pointerEvents = 'none';
                        element.remove();
                    }
                });
            } catch (e) {
                console.warn('Error removing chat icon:', e);
            }
        });
    }
    
    // دالة ضمان موقع Tawk.to
    function ensureTawkPosition() {
        var tawkBubble = document.querySelector('#tawk-bubble');
        if (tawkBubble) {
            tawkBubble.style.cssText = `
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                z-index: 999999 !important;
                transform: translateZ(0) !important;
                margin: 0 !important;
                padding: 0 !important;
                top: auto !important;
                left: auto !important;
            `;
        }
    }
    
    // تشغيل عند تحميل DOM
    document.addEventListener('DOMContentLoaded', function() {
        removeOtherChatIcons();
        ensureTawkPosition();
        
        // إعادة فحص كل 3 ثوان
        setInterval(function() {
            removeOtherChatIcons();
            ensureTawkPosition();
        }, 3000);
    });
    
    // مراقبة تغييرات DOM
    if (window.MutationObserver) {
        var observer = new MutationObserver(function(mutations) {
            var shouldCheck = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    shouldCheck = true;
                }
            });
            if (shouldCheck) {
                setTimeout(removeOtherChatIcons, 100);
                setTimeout(ensureTawkPosition, 200);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // تشغيل عند تحميل النافذة
    window.addEventListener('load', function() {
        setTimeout(function() {
            removeOtherChatIcons();
            ensureTawkPosition();
        }, 1000);
    });
    
    // دالة مساعدة للوصول العام
    window.EsGiftChat = {
        open: function() {
            if (typeof Tawk_API !== 'undefined') {
                Tawk_API.maximize();
            }
        },
        hide: function() {
            if (typeof Tawk_API !== 'undefined') {
                Tawk_API.minimize();
            }
        },
        sendMessage: function(message) {
            if (typeof Tawk_API !== 'undefined') {
                Tawk_API.addEvent('chatMessageVisitor', message);
                Tawk_API.maximize();
            }
        }
    };
    
    console.log('✅ Es-Gift Chat System initialized - Tawk.to only');
    
})();
