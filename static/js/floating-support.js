/**
 * إدارة أيقونة الدعم الفني الثابتة
 * تظهر فقط في صفحات محددة وتبقى ثابتة في الأسفل اليمين
 * لا تتحرك في مواضع مختلفة، تبقى في مكان واحد مع التمرير
 */

class FloatingSupportIcon {
    constructor() {
        this.icon = null;
        this.isVisible = false;
        this.allowedPages = ['profile', 'index', 'cart'];
        this.currentPage = this.getCurrentPage();
        this.init();
    }

    // تحديد الصفحة الحالية
    getCurrentPage() {
        const path = window.location.pathname;
        const body = document.body;
        
        // فحص إضافي باستخدام title أو body class
        if (path === '/' || path === '/index' || path.includes('index') || 
            document.title.includes('Es-Gift - متجر') || body.classList.contains('home-page')) {
            return 'index';
        } else if (path.includes('profile') || document.title.includes('الملف الشخصي') || 
                   body.classList.contains('profile-page')) {
            return 'profile';
        } else if (path.includes('cart') || document.title.includes('السلة') || 
                   body.classList.contains('cart-page')) {
            return 'cart';
        }
        return null;
    }

    // التحقق من إمكانية عرض الأيقونة في الصفحة الحالية
    shouldShowIcon() {
        return this.allowedPages.includes(this.currentPage);
    }

    // إنشاء عنصر الأيقونة
    createIcon() {
        const iconHTML = `
            <div class="floating-support-icon" 
                 id="floatingSupportIcon"
                 role="button"
                 tabindex="0"
                 aria-label="دعم فني مباشر - اضغط للمساعدة"
                 title="دعم فني 24/7">
                <i class="fas fa-headset" aria-hidden="true"></i>
                <div class="support-tooltip">دعم فني 24/7 - اضغط للمساعدة</div>
                <div class="support-notification" aria-label="إشعار جديد">!</div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', iconHTML);
        this.icon = document.getElementById('floatingSupportIcon');
        
        // إضافة تأثيرات صوتية (اختيارية)
        this.addSoundEffects();
        
        // إضافة دعم لوحة المفاتيح
        this.addKeyboardSupport();
    }
    
    // إضافة دعم لوحة المفاتيح
    addKeyboardSupport() {
        if (!this.icon) return;
        
        this.icon.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.handleClick();
            } else if (event.key === 'Escape') {
                this.icon.blur();
            }
        });
    }
    
    // إضافة تأثيرات صوتية
    addSoundEffects() {
        // يمكن إضافة أصوات للنقر والهوفر هنا
        if (this.icon) {
            this.icon.addEventListener('mouseenter', () => {
                // تشغيل صوت خفيف عند الهوفر (اختياري)
                this.playHoverSound();
            });
        }
    }
    
    // تشغيل صوت عند الهوفر
    playHoverSound() {
        try {
            // إنشاء صوت بسيط باستخدام Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            // تجاهل الأخطاء إذا لم يكن الصوت مدعوماً
        }
    }

    // تفعيل الأحداث
    bindEvents() {
        if (!this.icon) return;

        // النقر على الأيقونة
        this.icon.addEventListener('click', () => {
            this.handleClick();
        });

        // تأثير عند دخول الماوس
        this.icon.addEventListener('mouseenter', () => {
            this.handleMouseEnter();
        });

        // تأثير عند خروج الماوس
        this.icon.addEventListener('mouseleave', () => {
            this.handleMouseLeave();
        });

        // إخفاء الإشعار عند التمرير وضمان الموقع الثابت
        window.addEventListener('scroll', () => {
            this.hideNotification();
            this.ensureFixedPosition(); // ضمان بقاء الأيقونة في مكانها
        });
    }

    // معالجة النقر
    handleClick() {
        if (!this.icon) return;

        // تأثير النقر
        this.icon.classList.add('clicked');
        setTimeout(() => {
            this.icon.classList.remove('clicked');
        }, 300);

        // فتح نافذة الدعم الفني
        this.openSupportChat();

        // إخفاء الإشعار
        this.hideNotification();

        // تسجيل الحدث
        this.logSupportClick();
    }

    // معالجة دخول الماوس
    handleMouseEnter() {
        if (!this.icon) return;
        
        // تأثيرات hover فقط - لا نوقف الحركة لأنها غير موجودة
        // يمكن إضافة تأثيرات إضافية هنا إذا لزم الأمر
    }

    // معالجة خروج الماوس
    handleMouseLeave() {
        if (!this.icon) return;
        
        // تأثيرات hover فقط - لا نستأنف الحركة لأنها غير موجودة
        // يمكن إضافة تأثيرات إضافية هنا إذا لزم الأمر
    }

    // فتح نافذة الدعم الفني
    openSupportChat() {
        // التحقق من وجود Tawk.to
        if (typeof Tawk_API !== 'undefined') {
            Tawk_API.toggle();
            
            // إرسال معلومات المستخدم إذا كان مسجل دخول
            this.sendUserInfo();
            
            // تسجيل بداية المحادثة
            this.logChatStart();
        } else {
            // فتح رابط بديل للدعم الفني (WhatsApp مثلاً)
            const message = this.generateWhatsAppMessage();
            const whatsappUrl = `https://wa.me/966123456789?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        }
    }
    
    // إنشاء رسالة WhatsApp
    generateWhatsAppMessage() {
        const pageArabic = this.getPageArabicName();
        const userData = window.currentUserData || {};
        
        let message = `السلام عليكم، أحتاج مساعدة في Es-Gift\n`;
        message += `📍 الصفحة: ${pageArabic}\n`;
        
        if (userData.name && userData.name !== 'زائر') {
            message += `👤 الاسم: ${userData.name}\n`;
        }
        
        if (userData.email) {
            message += `📧 البريد: ${userData.email}\n`;
        }
        
        if (userData.cartItems && this.currentPage === 'cart') {
            message += `🛒 عدد المنتجات في السلة: ${userData.cartItems}\n`;
            if (userData.cartTotal) {
                message += `💰 إجمالي السلة: ${userData.cartTotal}\n`;
            }
        }
        
        message += `🕐 الوقت: ${new Date().toLocaleString('ar-SA')}\n`;
        message += `\nكيف يمكنكم مساعدتي؟`;
        
        return message;
    }
    
    // تسجيل بداية المحادثة
    logChatStart() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'chat_started', {
                'page': this.currentPage,
                'user_type': window.currentUserData?.type || 'guest',
                'timestamp': new Date().toISOString()
            });
        }
    }

    // إرسال معلومات المستخدم للدعم
    sendUserInfo() {
        if (typeof Tawk_API !== 'undefined' && window.currentUserData) {
            const userData = window.currentUserData;
            const message = `مرحباً، أنا ${userData.name || 'مستخدم'} وأحتاج مساعدة في ${this.getPageArabicName()}`;
            
            Tawk_API.addEvent('تسجيل دخول', {
                'صفحة': this.getPageArabicName(),
                'مستخدم': userData.email || 'غير محدد',
                'وقت': new Date().toLocaleString('ar-SA')
            });
        }
    }

    // الحصول على اسم الصفحة بالعربية
    getPageArabicName() {
        const pageNames = {
            'index': 'الصفحة الرئيسية',
            'profile': 'الملف الشخصي',
            'cart': 'السلة'
        };
        return pageNames[this.currentPage] || 'الموقع';
    }

    // إخفاء الإشعار
    hideNotification() {
        if (!this.icon) return;
        
        const notification = this.icon.querySelector('.support-notification');
        if (notification) {
            notification.style.display = 'none';
        }
    }

    // إظهار الإشعار
    showNotification() {
        if (!this.icon) return;
        
        const notification = this.icon.querySelector('.support-notification');
        if (notification) {
            notification.style.display = 'flex';
        }
    }

    // عرض الأيقونة مع تأثير - مع ضمان الموقع الثابت
    show() {
        if (!this.icon || this.isVisible) return;

        this.icon.classList.add('fade-in', 'show');
        this.isVisible = true;

        // ضمان الموقع الثابت
        this.ensureFixedPosition();

        // إظهار الإشعار بعد 3 ثوانٍ
        setTimeout(() => {
            this.showNotification();
        }, 3000);
    }

    // ضمان بقاء الأيقونة في موقعها الثابت (الأسفل اليمين)
    ensureFixedPosition() {
        if (!this.icon) return;
        
        // إزالة أي inline styles قد تؤثر على الموقع
        this.icon.style.bottom = '';
        this.icon.style.right = '';
        this.icon.style.left = '';
        this.icon.style.top = '';
        this.icon.style.position = '';
        
        // إضافة class للموقع الثابت
        this.icon.classList.add('fixed-position');
        
        // ضمان CSS properties مباشرة أيضاً
        this.icon.style.setProperty('position', 'fixed', 'important');
        this.icon.style.setProperty('bottom', '20px', 'important');
        this.icon.style.setProperty('right', '20px', 'important');
        this.icon.style.setProperty('top', 'auto', 'important');
        this.icon.style.setProperty('left', 'auto', 'important');
    }

    // إخفاء الأيقونة
    hide() {
        if (!this.icon || !this.isVisible) return;

        this.icon.classList.add('fade-out');
        this.icon.classList.remove('show');
        
        setTimeout(() => {
            this.icon.classList.remove('fade-in', 'fade-out');
            this.isVisible = false;
        }, 500);
    }

    // تسجيل نقرة الدعم الفني
    logSupportClick() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'support_click', {
                'page': this.currentPage,
                'timestamp': new Date().toISOString()
            });
        }
    }

    // تغيير موقع الأيقونة - معطل للبقاء ثابتة في الأسفل اليمين
    changePosition() {
        // لا نغير الموقع - نبقي الأيقونة ثابتة في مكانها بالأسفل اليمين
        if (!this.icon) return;
        
        // ضمان بقاء الأيقونة في موقعها الثابت
        this.ensureFixedPosition();
        return;
    }
    
    // حركة متقدمة للأيقونة - معطلة للبقاء ثابتة في الأسفل اليمين
    startAdvancedMovement() {
        if (!this.icon) return;
        
        // ضمان الموقع الثابت دائماً
        this.ensureFixedPosition();
        
        // نبقي فقط تنبيه جذب الانتباه بدون تغيير الموقع
        let idleTimer = setTimeout(() => {
            this.attractAttention();
        }, 30000); // إذا لم يتفاعل المستخدم خلال 30 ثانية
        
        // إعادة تعيين المؤقت عند التفاعل
        this.icon.addEventListener('click', () => {
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => {
                this.attractAttention();
            }, 60000); // إعادة تنبيه بعد دقيقة
        });
        
        // فحص دوري للتأكد من بقاء الأيقونة في موقعها
        setInterval(() => {
            this.ensureFixedPosition();
        }, 5000); // كل 5 ثوانٍ
    }
    
    // جذب الانتباه - بدون تغيير موقع، ثابت في الأسفل اليمين
    attractAttention() {
        if (!this.icon || !this.isVisible) return;
        
        // ضمان الموقع الثابت قبل التأثير
        this.ensureFixedPosition();
        
        // تأثير نبضة قوية بدون تغيير موقع
        this.icon.style.animation = 'attractAttention 2s ease-in-out, pulse 2s ease-in-out infinite alternate';
        
        // إظهار الإشعار
        this.showNotification();
        
        // تغيير النص المساعد
        const tooltip = this.icon.querySelector('.support-tooltip');
        if (tooltip) {
            const originalText = tooltip.textContent;
            tooltip.textContent = 'هل تحتاج مساعدة؟ 🤔';
            
            setTimeout(() => {
                tooltip.textContent = originalText;
            }, 5000);
        }
        
        setTimeout(() => {
            this.icon.style.animation = 'pulse 2s ease-in-out infinite alternate';
            // ضمان الموقع الثابت بعد التأثير
            this.ensureFixedPosition();
        }, 2000);
    }

    // تهيئة الأيقونة
    init() {
        // التحقق من إمكانية عرض الأيقونة
        if (!this.shouldShowIcon()) {
            return;
        }

        // انتظار تحميل الصفحة
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setup();
            });
        } else {
            this.setup();
        }
    }

    // إعداد الأيقونة - ثابتة في الأسفل اليمين
    setup() {
        // إنشاء الأيقونة
        this.createIcon();
        
        // تفعيل الأحداث
        this.bindEvents();
        
        // ضمان الموقع الثابت فوراً
        this.ensureFixedPosition();
        
        // عرض الأيقونة بعد ثانيتين
        setTimeout(() => {
            this.show();
        }, 2000);

        // تفعيل تنبيهات جذب الانتباه (بدون حركة)
        setTimeout(() => {
            this.startAdvancedMovement();
        }, 5000);
    }

    // تدمير الأيقونة
    destroy() {
        if (this.icon) {
            this.hide();
            setTimeout(() => {
                if (this.icon && this.icon.parentNode) {
                    this.icon.parentNode.removeChild(this.icon);
                }
                this.icon = null;
            }, 500);
        }
    }
}

// تهيئة الأيقونة العائمة
let floatingSupportIcon;

// تشغيل الأيقونة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    floatingSupportIcon = new FloatingSupportIcon();
});

// تنظيف عند مغادرة الصفحة
window.addEventListener('beforeunload', function() {
    if (floatingSupportIcon) {
        floatingSupportIcon.destroy();
    }
});

// إعادة تهيئة عند تغيير الصفحة (للـ SPA)
window.addEventListener('popstate', function() {
    if (floatingSupportIcon) {
        floatingSupportIcon.destroy();
    }
    setTimeout(() => {
        floatingSupportIcon = new FloatingSupportIcon();
    }, 100);
});

// تصدير للاستخدام العام
window.FloatingSupportIcon = FloatingSupportIcon;
