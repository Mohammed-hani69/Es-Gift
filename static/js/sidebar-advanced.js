/* ملف JavaScript للوظائف المتقدمة للقائمة الجانبية */
/* Advanced Sidebar Functionality */

class SidebarManager {
    constructor() {
        this.sidebar = null;
        this.overlay = null;
        this.isAnimating = false;
        this.particleCount = 0;
        this.maxParticles = 20;
        
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.sidebar = document.getElementById('sidebar');
            this.overlay = document.getElementById('overlay');
            this.setupEventListeners();
            this.detectPerformanceMode();
            this.addAdvancedEffects();
        });
    }
    
    setupEventListeners() {
        // إضافة مستمعي الأحداث للحركة التفاعلية
        if (this.sidebar) {
            this.sidebar.addEventListener('mouseenter', () => this.onMouseEnter());
            this.sidebar.addEventListener('mouseleave', () => this.onMouseLeave());
            this.sidebar.addEventListener('mousemove', (e) => this.onMouseMove(e));
        }
        
        // تأثير التنفس للخلفية
        this.startBreathingEffect();
    }
    
    onMouseEnter() {
        if (this.sidebar.classList.contains('active')) {
            this.sidebar.classList.add('sidebar-shadow-dance');
            this.createInteractiveParticles();
        }
    }
    
    onMouseLeave() {
        this.sidebar.classList.remove('sidebar-shadow-dance');
        this.stopInteractiveParticles();
    }
    
    onMouseMove(e) {
        if (!this.sidebar.classList.contains('active')) return;
        
        const rect = this.sidebar.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        
        // تحديث موضع التأثيرات بناءً على موضع الفأرة
        this.updateDynamicEffects(x, y);
    }
    
    updateDynamicEffects(x, y) {
        // تأثير تغيير الخلفية بناءً على موضع الفأرة
        const hue = Math.floor(x * 60); // تغيير اللون
        const brightness = 0.9 + (y * 0.1); // تغيير السطوع
        
        this.sidebar.style.filter = `hue-rotate(${hue}deg) brightness(${brightness})`;
        
        // إنشاء جسيمات تفاعلية
        if (Math.random() > 0.95) { // إنشاء جسيم عشوائي
            this.createFollowParticle(x * 100, y * 100);
        }
    }
    
    createInteractiveParticles() {
        const particleInterval = setInterval(() => {
            if (this.particleCount < this.maxParticles && 
                this.sidebar.classList.contains('active')) {
                this.createFloatingParticle();
                this.particleCount++;
            } else {
                clearInterval(particleInterval);
            }
        }, 200);
        
        this.particleInterval = particleInterval;
    }
    
    stopInteractiveParticles() {
        if (this.particleInterval) {
            clearInterval(this.particleInterval);
        }
        this.particleCount = 0;
    }
    
    createFloatingParticle() {
        const particle = document.createElement('div');
        particle.className = 'floating-particle';
        
        const size = Math.random() * 6 + 2;
        const startX = Math.random() * 100;
        const duration = Math.random() * 3 + 2;
        
        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: radial-gradient(circle, 
                rgba(255, 255, 255, 0.8) 0%, 
                rgba(255, 0, 51, 0.6) 100%);
            border-radius: 50%;
            top: 100%;
            right: ${startX}%;
            pointer-events: none;
            z-index: 100;
            animation: floatUp ${duration}s ease-out forwards;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        `;
        
        this.sidebar.appendChild(particle);
        
        // إزالة الجسيم بعد انتهاء التأثير
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
                this.particleCount = Math.max(0, this.particleCount - 1);
            }
        }, duration * 1000);
    }
    
    createFollowParticle(x, y) {
        const particle = document.createElement('div');
        particle.className = 'follow-particle';
        
        particle.style.cssText = `
            position: absolute;
            width: 3px;
            height: 3px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            top: ${y}%;
            right: ${x}%;
            pointer-events: none;
            z-index: 99;
            animation: fadeOutParticle 1s ease-out forwards;
            box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
        `;
        
        this.sidebar.appendChild(particle);
        
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 1000);
    }
    
    startBreathingEffect() {
        if (!this.sidebar) return;
        
        let breathPhase = 0;
        const breatheInterval = setInterval(() => {
            if (this.sidebar.classList.contains('active')) {
                breathPhase += 0.05;
                const opacity = 0.1 + Math.sin(breathPhase) * 0.05;
                
                // تأثير التنفس للخلفية
                this.sidebar.style.boxShadow = `
                    inset 0 0 50px rgba(255, 255, 255, ${opacity}),
                    0 0 50px rgba(255, 0, 51, ${opacity * 2})
                `;
            }
        }, 50);
        
        this.breatheInterval = breatheInterval;
    }
    
    addAdvancedEffects() {
        // إضافة تأثيرات CSS الديناميكية
        const style = document.createElement('style');
        style.textContent = `
            @keyframes floatUp {
                0% {
                    transform: translateY(0) scale(0);
                    opacity: 0;
                }
                10% {
                    transform: translateY(-10px) scale(1);
                    opacity: 1;
                }
                100% {
                    transform: translateY(-200px) scale(0.5);
                    opacity: 0;
                }
            }
            
            @keyframes fadeOutParticle {
                0% {
                    transform: scale(1);
                    opacity: 1;
                }
                100% {
                    transform: scale(0);
                    opacity: 0;
                }
            }
            
            .floating-particle {
                will-change: transform, opacity;
            }
            
            .follow-particle {
                will-change: transform, opacity;
            }
            
            /* تأثير النص المتحرك */
            .sidebar-header h3 {
                background: linear-gradient(
                    45deg,
                    #ffffff 25%,
                    #ffccdd 50%,
                    #ffffff 75%
                );
                background-size: 200% 100%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: textShimmer 3s ease-in-out infinite;
            }
            
            @keyframes textShimmer {
                0%, 100% {
                    background-position: 200% 0;
                }
                50% {
                    background-position: -200% 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    detectPerformanceMode() {
        const isLowPerformance = 
            /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
            navigator.hardwareConcurrency < 4 ||
            window.innerWidth < 768;
            
        if (isLowPerformance) {
            document.body.classList.add('performance-mode');
            this.maxParticles = 5; // تقليل عدد الجسيمات
            
            // تقليل تعقيد التأثيرات
            const performanceStyle = document.createElement('style');
            performanceStyle.textContent = `
                .performance-mode .sidebar-shadow-dance::before,
                .performance-mode .sidebar-sparkle::before,
                .performance-mode .floating-particle {
                    display: none !important;
                }
                
                .performance-mode .sidebar * {
                    animation-duration: 0.2s !important;
                    transition-duration: 0.2s !important;
                }
            `;
            document.head.appendChild(performanceStyle);
        }
    }
    
    // دالة تنظيف الموارد
    cleanup() {
        if (this.breatheInterval) {
            clearInterval(this.breatheInterval);
        }
        if (this.particleInterval) {
            clearInterval(this.particleInterval);
        }
    }
}

// إنشاء مثيل من مدير القائمة الجانبية
const sidebarManager = new SidebarManager();

// دالة مساعدة لإضافة تأثيرات صوتية
class SoundEffects {
    constructor() {
        this.audioContext = null;
        this.init();
    }
    
    init() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Web Audio API غير مدعوم');
        }
    }
    
    playSuccess() {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // نغمة نجاح
        oscillator.frequency.setValueAtTime(523.25, this.audioContext.currentTime); // C5
        oscillator.frequency.setValueAtTime(659.25, this.audioContext.currentTime + 0.1); // E5
        oscillator.frequency.setValueAtTime(783.99, this.audioContext.currentTime + 0.2); // G5
        
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.3);
    }
    
    playClick() {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
        oscillator.type = 'square';
        
        gainNode.gain.setValueAtTime(0.05, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.1);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.1);
    }
}

// إنشاء مثيل من التأثيرات الصوتية
const soundEffects = new SoundEffects();

// تصدير للاستخدام العام
window.sidebarManager = sidebarManager;
window.soundEffects = soundEffects;

// تنظيف الموارد عند إغلاق الصفحة
window.addEventListener('beforeunload', () => {
    sidebarManager.cleanup();
});
