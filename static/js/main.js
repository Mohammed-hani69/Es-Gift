// Es-Gift Main JavaScript
console.log("Es-Gift loaded successfully");
var homeSwiper = new Swiper(".home-swiper", {
  slidesPerView: 2,
  spaceBetween: 30,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
  navigation: {
    nextEl: ".custom-next",
    prevEl: ".custom-prev",
  },
  breakpoints: {
    320: { slidesPerView: 1 },
    640: { slidesPerView: 2 },
    1124: { slidesPerView: 3 },
  },
});

var iconSwiper = new Swiper(".icon-slider", {
  slidesPerView: 2,
  spaceBetween: 10,
  freeMode: true,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
  navigation: {
    nextEl: ".gift-swiper-custom-next",
    prevEl: ".gift-swiper-custom-prev",
  },
  breakpoints: {
    320: { slidesPerView: 4 },
    640: { slidesPerView: 3 },
    1124: { slidesPerView: 10 },
  },
});

const productsSwiper = new Swiper(".products-swiper", {
  direction: "horizontal",
  spaceBetween: 10,
  watchOverflow: true,
  slidesPerGroup: 1, // 🔥 Slide one by one

  rtl: true, // قد لا يعمل دائمًا، فاستخدم CSS direction أيضاً
  navigation: {
    nextEl: ".product-swiper-custom-next",
    prevEl: ".product-swiper-custom-prev",
  },
  breakpoints: {
    // when window width is >= 320px (phones)
    320: {
      slidesPerView: 2,
    },
    // when window width is >= 640px (small tablets)
    640: {
      slidesPerView: 2,
    },
    // when window width is >= 1024px (desktops)
    1124: {
      slidesPerView: 6,
    },
  },
});

const giftSwiper = new Swiper(".gift-swiper", {
  direction: "horizontal",
  spaceBetween: 12,

  loop: false,
  rtl: true,
  navigation: {
    nextEl: ".gift-swiper-custom-next",
    prevEl: ".gift-swiper-custom-prev",
  },
  breakpoints: {
    320: { slidesPerView: 2 },
    640: { slidesPerView: 3 },
    1124: { slidesPerView: 8 },
  },
});

const offersSwiper = new Swiper(".offers-swiper", {
  direction: "horizontal",
  loop: true,
  loopAdditionalSlides: 10,
  watchSlidesProgress: true,
  spaceBetween: 16,
  slidesPerGroup: 1,
  rtl: true, // هذه هي الإضافة الأساسية
  resistanceRatio: 0,
  touchReleaseOnEdges: true,
  freeMode: false, // تأكد أنها false
  speed: 300, // سرعة الانتقال
  touchRatio: 1, // حساسية اللمس
  simulateTouch: true, // تمكين السحب باللمس
  shortSwipes: true, // سوائب قصيرة
  longSwipes: false, // تعطيل السوائب الطويلة
  navigation: {
    nextEl: ".offers-swiper-custom-next",
    prevEl: ".offers-swiper-custom-prev",
  },
  breakpoints: {
    320: {
      slidesPerView: 2,
    },
    768: {
      slidesPerView: 5,
    },
    1124: {
      slidesPerView: 7,
    },
  },
});

//

const tabs = document.querySelectorAll(".tab");
const swiperWrapper = document.querySelector(".gift-swiper .swiper-wrapper");
const allSlides = Array.from(document.querySelectorAll(".swiper-slide.item"));

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const filter = tab.getAttribute("data-filter");

    // نظّف السلايدر
    giftSwiper.removeAllSlides();

    // جهز السلايدات الجديدة
    const filteredSlides = allSlides.filter(
      (item) => filter === "all" || item.classList.contains(filter)
    );

    // أضف السلايدات الجديدة
    filteredSlides.forEach((slide) => {
      giftSwiper.appendSlide(slide.outerHTML); // لازم .outerHTML لأن Swiper ينتظر HTML string
    });

    // إعادة التهيئة
    giftSwiper.update();
  });
});

// another marks

const btnMarks = document.querySelector(".btn");
const hiddenMarks = document.querySelector(".hidden-marks");
const btnText = document.querySelector(".btn-text");
const btnIcon = document.querySelector(".changed-icon");

btnMarks.addEventListener("click", () => {
  hiddenMarks.classList.toggle("active-marks");

  const isVisible = hiddenMarks.classList.contains("active-marks");

  btnText.textContent = isVisible ? "اخفاء" : "اعرض اكتر";
  btnIcon.className = isVisible
    ? "fa-solid fa-arrow-up"
    : "fa-solid fa-arrow-down";
});

// sidebar

const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");
const openBtn = document.getElementById("openSidebar");
const closeBtn = document.getElementById("closeSidebar");

openBtn.addEventListener("click", () => {
  sidebar.classList.add("open");
  overlay.classList.add("show");
});

closeBtn.addEventListener("click", () => {
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
});

overlay.addEventListener("click", () => {
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
});

// Authentication functions
function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('authModal').style.display = 'block';
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('authModal').style.display = 'block';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
}

// Handle login form submission
document.addEventListener('DOMContentLoaded', function() {
    // Close modal when clicking outside
    document.getElementById('authModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeAuthModal();
        }
    });

    // Close modal when clicking X
    document.querySelector('.close').addEventListener('click', closeAuthModal);

    // Handle login form
    document.getElementById('loginFormElement').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // إغلاق النافذة المنبثقة
                closeAuthModal();
                // إعادة التوجه للصفحة المحددة
                setTimeout(() => {
                    window.location.href = data.redirect || '/';
                }, 1000);
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('حدث خطأ في تسجيل الدخول', 'error');
        });
    });

    // Handle register form
    document.getElementById('registerFormElement').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (password !== confirmPassword) {
            showNotification('كلمة المرور غير متطابقة', 'error');
            return;
        }
        
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // إغلاق النافذة المنبثقة
                closeAuthModal();
                // إعادة التوجه للصفحة الرئيسية
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('حدث خطأ في إنشاء الحساب', 'error');
        });
    });
});

// Currency change function
function changeCurrency(currency) {
    // إضافة تأثير بصري
    const currencyWrapper = document.querySelector('.currency-selector-wrapper');
    const currencySelector = document.getElementById('currency-selector');
    
    if (currencyWrapper) {
        currencyWrapper.classList.add('currency-change-animation');
        
        // إظهار إشعار تحميل
        showNotification('جاري تغيير العملة...', 'info');
        
        // تأخير قصير لإظهار التأثير
        setTimeout(() => {
            window.location.href = `/set-currency/${currency}`;
        }, 300);
    } else {
        // fallback في حال عدم وجود العنصر
        window.location.href = `/set-currency/${currency}`;
    }
}

// Notification function
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add notification styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#17a2b8'};
        color: ${type === 'warning' ? '#000' : '#fff'};
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .notification button {
        background: none;
        border: none;
        color: inherit;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        margin: 0;
    }
    
    .modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.8);
    }
    
    .modal-content {
        background-color: #222;
        margin: 5% auto;
        padding: 30px;
        border-radius: 15px;
        width: 90%;
        max-width: 500px;
        position: relative;
    }
    
    .close {
        position: absolute;
        top: 15px;
        right: 20px;
        color: #aaa;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
    }
    
    .close:hover {
        color: #fff;
    }
    
    .auth-form {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    .auth-form h2 {
        color: #ff0033;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .auth-form input {
        padding: 12px;
        border: 2px solid #444;
        border-radius: 8px;
        background: #333;
        color: #fff;
        font-size: 16px;
    }
    
    .auth-form input:focus {
        outline: none;
        border-color: #ff0033;
    }
    
    .auth-form button {
        padding: 12px;
        background: linear-gradient(135deg, #ff0033, #ff6b6b);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .auth-form button:hover {
        background: linear-gradient(135deg, #e60029, #ff5252);
        transform: translateY(-2px);
    }
    
    .auth-form p {
        text-align: center;
        color: #ccc;
    }
    
    .auth-form a {
        color: #ff0033;
        text-decoration: none;
    }
    
    .auth-form a:hover {
        text-decoration: underline;
    }
`;
document.head.appendChild(style);

// تحديث عرض العملة المختارة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    const currencySelector = document.getElementById('currency-selector');
    if (currencySelector) {
        // إضافة تأثير للعملة المختارة حالياً
        const selectedOption = currencySelector.options[currencySelector.selectedIndex];
        if (selectedOption) {
            currencySelector.style.color = '#ff0033';
            setTimeout(() => {
                currencySelector.style.color = '#fff';
            }, 1000);
        }
        
        // إضافة تأثير عند تغيير الاختيار
        currencySelector.addEventListener('change', function() {
            this.style.color = '#ff0033';
        });
    }
});

// تفعيل قائمة المستخدم
document.addEventListener('DOMContentLoaded', function() {
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        // إغلاق القائمة عند النقر خارجها
        document.addEventListener('click', function(e) {
            if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }
});

// تحسين عداد السلة
function updateCartCount(count) {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count || 0;
        if (count > 0) {
            cartCountElement.classList.add('show');
            cartCountElement.classList.add('animate');
            setTimeout(() => {
                cartCountElement.classList.remove('animate');
            }, 600);
        } else {
            cartCountElement.classList.remove('show');
        }
    }
}

// تحسين أداء البحث
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('#search-input, .bottom-search-box input');
    let searchTimeout;
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // يمكن إضافة وظيفة البحث المباشر هنا
                console.log('البحث عن:', this.value);
            }, 500);
        });
    });
});
