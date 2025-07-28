/**
 * Tawk.io Simple Manager - Es-Gift
 * إدارة بسيطة وفعالة لضمان ظهور الأيقونة
 */

(function() {
    'use strict';
    
    console.log('🚀 بدء تحميل Tawk.io - Es-Gift');
    
    // حذف الأيقونات الأخرى
    function removeOtherChatIcons() {
        const selectors = [
            '.floating-support-icon',
            '.es-chat-floating-icon', 
            '.support-icon',
            '.chat-icon',
            '.floating-chat',
            '.whatsapp-icon',
            '.support-floating',
            '[class*="chat-floating"]',
            '[class*="support-floating"]'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el && !el.id.includes('tawk')) {
                    el.style.display = 'none';
                    el.remove();
                }
            });
        });
    }
    
    // ضبط موقع الأيقونة بنفس خصائص WhatsApp Float
    function fixTawkPosition() {
        const bubble = document.querySelector('#tawk-bubble');
        if (bubble) {
            bubble.style.cssText = `
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                z-index: 999 !important;
                cursor: pointer !important;
                background-color: #ff0033 !important;
                border-radius: 50% !important;
                padding: 10px !important;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
                transition: transform 0.2s !important;
                width: 60px !important;
                height: 60px !important;
                margin: 0 !important;
                top: auto !important;
                left: auto !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transform: translateZ(0) !important;
                will-change: transform !important;
                backface-visibility: hidden !important;
            `;
            
            // إضافة تأثير الهوفر
            bubble.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1) translateZ(0)';
            });
            
            bubble.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) translateZ(0)';
            });
            
            console.log('✅ تم ضبط موقع أيقونة Tawk.io بنمط WhatsApp Float');
            return true;
        }
        return false;
    }
    
    // إعداد Tawk API
    if (typeof window.Tawk_API === 'undefined') {
        window.Tawk_API = {};
    }
    
    if (typeof window.Tawk_LoadStart === 'undefined') {
        window.Tawk_LoadStart = new Date();
    }
    
    // تحميل سكريبت Tawk.to
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://embed.tawk.to/687e2b2c4fc0181916b601e1/1j0mdhak3';
    script.charset = 'UTF-8';
    script.setAttribute('crossorigin', '*');
    
    script.onload = function() {
        console.log('✅ تم تحميل Tawk.io بنجاح');
        
        // ضبط الموقع بعد التحميل
        setTimeout(() => {
            removeOtherChatIcons();
            fixTawkPosition();
        }, 1000);
        
        // فحص دوري
        setInterval(() => {
            removeOtherChatIcons();
            fixTawkPosition();
        }, 3000);
    };
    
    script.onerror = function() {
        console.error('❌ فشل في تحميل Tawk.io');
    };
    
    // إضافة السكريبت للصفحة
    const firstScript = document.getElementsByTagName('script')[0];
    firstScript.parentNode.insertBefore(script, firstScript);
    
    // إعدادات Tawk عند التحميل
    window.Tawk_API.onLoad = function() {
        console.log('✅ Tawk.io جاهز للاستخدام');
        
        setTimeout(() => {
            removeOtherChatIcons();
            fixTawkPosition();
        }, 500);
    };
    
    // دالة عامة لفتح الشات
    window.openEsGiftChat = function() {
        if (typeof window.Tawk_API !== 'undefined' && window.Tawk_API.maximize) {
            window.Tawk_API.maximize();
            return true;
        }
        console.warn('⚠️ Tawk.io غير متاح');
        return false;
    };
    
    // تنظيف عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        removeOtherChatIcons();
        
        // فحص دوري للتأكد
        setTimeout(() => {
            removeOtherChatIcons();
            fixTawkPosition();
        }, 2000);
    });
    
    // تنظيف عند تحميل النافذة
    window.addEventListener('load', function() {
        setTimeout(() => {
            removeOtherChatIcons();
            fixTawkPosition();
        }, 1500);
    });
    
    console.log('📦 Tawk.io Manager تم تحميله');
    
})();
