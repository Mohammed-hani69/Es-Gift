/**
 * تم إيقاف أيقونة الدعم الفني العائمة
 * تم استبدالها بأيقونة Tawk.to المتقدمة
 * جميع الوظائف معطلة لتجنب التعارض
 */

// إيقاف جميع وظائف الأيقونة العائمة
class FloatingSupportIcon {
    constructor() {
        console.log('🚫 أيقونة الدعم العائمة معطلة - استخدم Tawk.to بدلاً من ذلك');
        this.disabled = true;
        return this;
    }

    // جميع الوظائف معطلة وترجع null
    getCurrentPage() { return null; }
    shouldShowIcon() { return false; }
    createIcon() { return null; }
    addKeyboardSupport() { return null; }
    addSoundEffects() { return null; }
    playHoverSound() { return null; }
    bindEvents() { return null; }
    handleClick() { return null; }
    handleMouseEnter() { return null; }
    handleMouseLeave() { return null; }
    openSupportChat() { return null; }
    generateWhatsAppMessage() { return null; }
    logChatStart() { return null; }
    sendUserInfo() { return null; }
    getPageArabicName() { return null; }
    hideNotification() { return null; }
    showNotification() { return null; }
    show() { return null; }
    ensureFixedPosition() { return null; }
    hide() { return null; }
    logSupportClick() { return null; }
    changePosition() { return null; }
    startAdvancedMovement() { return null; }
    attractAttention() { return null; }
    init() { return null; }
    setup() { return null; }
    destroy() { return null; }
}

// منع تشغيل أي كود للأيقونة العائمة
if (typeof window !== 'undefined') {
    // إخفاء أي أيقونات موجودة عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🧹 تنظيف أيقونات الشات القديمة...');
        
        var selectors = [
            '.floating-support-icon',
            '.es-chat-floating-icon',
            '.support-icon',
            '.chat-icon',
            '.floating-chat',
            '.whatsapp-icon',
            '.support-floating',
            '.chat-widget',
            '[class*="floating-support"]',
            '[class*="chat-floating"]',
            '[class*="support-floating"]'
        ];
        
        selectors.forEach(function(selector) {
            var elements = document.querySelectorAll(selector);
            elements.forEach(function(el) {
                if (el && !el.id.includes('tawk')) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                    el.remove();
                }
            });
        });
        
        console.log('✅ تم تنظيف الأيقونات القديمة');
    });
    
    // منع أي محاولة لإنشاء أيقونة عائمة جديدة
    window.FloatingSupportIcon = FloatingSupportIcon;
    
    // متغير عام لمنع التشغيل
    window.floatingSupportDisabled = true;
}

// تصدير الكلاس المعطل
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FloatingSupportIcon;
}
