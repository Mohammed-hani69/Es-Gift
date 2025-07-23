"""
تشغيل وتهيئة الصفحات الثابتة
"""

from app import create_app
from models import db, StaticPage
from datetime import datetime

def init_static_pages():
    """تهيئة الصفحات الثابتة بالبيانات الافتراضية"""
    app = create_app()
    
    with app.app_context():
        # إنشاء الجداول
        db.create_all()
        
        # البيانات الافتراضية للصفحات
        default_pages = [
            {
                'title': 'سياسة الخصوصية',
                'slug': 'privacy-policy',
                'content': '''
<h2>سياسة الخصوصية لمتجر Es-Gift</h2>

<p>نحن في Es-Gift نولي أهمية قصوى لحماية خصوصيتك وبياناتك الشخصية. تشرح هذه السياسة كيفية جمعنا واستخدامنا وحماية معلوماتك الشخصية.</p>

<h3>جمع المعلومات</h3>
<p>نقوم بجمع المعلومات التالية:</p>
<ul>
    <li>المعلومات الشخصية: الاسم، البريد الإلكتروني، رقم الهاتف</li>
    <li>معلومات الحساب: كلمة المرور، تفضيلات الحساب</li>
    <li>معلومات المعاملات: تاريخ الشراء، المنتجات المشتراة</li>
    <li>معلومات تقنية: عنوان IP، نوع المتصفح، نظام التشغيل</li>
</ul>

<h3>استخدام المعلومات</h3>
<p>نستخدم معلوماتك لـ:</p>
<ul>
    <li>معالجة الطلبات وتقديم الخدمات</li>
    <li>تحسين تجربة المستخدم</li>
    <li>إرسال التحديثات والعروض الخاصة</li>
    <li>ضمان أمان الموقع ومنع الاحتيال</li>
</ul>

<h3>حماية البيانات</h3>
<p>نتخذ إجراءات أمنية متقدمة لحماية بياناتك، بما في ذلك:</p>
<ul>
    <li>تشفير البيانات الحساسة</li>
    <li>الوصول المحدود للموظفين المصرح لهم</li>
    <li>مراجعة أمنية منتظمة للأنظمة</li>
    <li>استخدام بروتوكولات أمان متقدمة</li>
</ul>

<h3>حقوقك</h3>
<p>يمكنك:</p>
<ul>
    <li>الوصول إلى بياناتك الشخصية</li>
    <li>تحديث أو تصحيح معلوماتك</li>
    <li>حذف حسابك ومعلوماتك</li>
    <li>إلغاء الاشتراك في النشرات الإخبارية</li>
</ul>

<h3>ملفات تعريف الارتباط</h3>
<p>نستخدم ملفات تعريف الارتباط لتحسين تجربتك وتذكر تفضيلاتك. يمكنك التحكم في إعدادات ملفات تعريف الارتباط من خلال متصفحك.</p>

<h3>مشاركة المعلومات</h3>
<p>لا نقوم ببيع أو تأجير معلوماتك الشخصية لأطراف ثالثة. قد نشارك المعلومات في الحالات التالية:</p>
<ul>
    <li>مع مقدمي الخدمات المعتمدين لمعالجة الطلبات</li>
    <li>عند الضرورة القانونية أو لحماية حقوقنا</li>
    <li>في حالة دمج أو استحواذ الشركة</li>
</ul>

<h3>الاتصال بنا</h3>
<p>إذا كان لديك أي استفسار حول سياسة الخصوصية، يمكنك التواصل معنا عبر:</p>
<ul>
    <li>البريد الإلكتروني: privacy@es-gift.com</li>
    <li>الهاتف: +966123456789</li>
    <li>نموذج الاتصال في الموقع</li>
</ul>

<p><strong>آخر تحديث:</strong> {{ "now"|date("Y-m-d") }}</p>
                ''',
                'meta_description': 'سياسة الخصوصية لمتجر Es-Gift - تعرف على كيفية حماية بياناتك الشخصية',
                'meta_keywords': 'سياسة الخصوصية, حماية البيانات, Es-Gift, خصوصية المستخدم',
                'show_in_footer': True,
                'display_order': 1
            },
            {
                'title': 'اتصل بنا',
                'slug': 'contact-us',
                'content': '''
<h2>تواصل مع فريق Es-Gift</h2>

<p>نحن هنا لمساعدتك! فريق دعم Es-Gift متاح على مدار الساعة لتقديم أفضل خدمة عملاء.</p>

<div class="contact-methods">
    <div class="contact-card">
        <h3><i class="fas fa-headset"></i> الدعم الفني المباشر</h3>
        <p>متاح 24/7 عبر الشات المباشر في الموقع</p>
        <button onclick="openEsGiftChat()" class="contact-btn">
            ابدأ الدردشة الآن
        </button>
    </div>

    <div class="contact-card">
        <h3><i class="fas fa-envelope"></i> البريد الإلكتروني</h3>
        <p>للاستفسارات العامة والدعم التقني</p>
        <p>📧 support@es-gift.com</p>
        <p>📧 info@es-gift.com</p>
    </div>

    <div class="contact-card">
        <h3><i class="fas fa-phone"></i> الهاتف</h3>
        <p>خدمة العملاء متاحة من 8:00 ص إلى 12:00 م</p>
        <p>📞 +966 11 123 4567</p>
        <p>📞 +966 50 987 6543</p>
    </div>

    <div class="contact-card">
        <h3><i class="fas fa-map-marker-alt"></i> العنوان</h3>
        <p>مكاتب Es-Gift الرئيسية</p>
        <p>الرياض، المملكة العربية السعودية</p>
        <p>📮 ص.ب 12345</p>
    </div>
</div>

<h3>نموذج الاتصال السريع</h3>
<form class="contact-form" action="/contact-submit" method="POST">
    <div class="form-row">
        <div class="form-group">
            <label for="name">الاسم الكامل</label>
            <input type="text" id="name" name="name" required>
        </div>
        <div class="form-group">
            <label for="email">البريد الإلكتروني</label>
            <input type="email" id="email" name="email" required>
        </div>
    </div>
    
    <div class="form-group">
        <label for="subject">الموضوع</label>
        <select id="subject" name="subject" required>
            <option value="">اختر الموضوع</option>
            <option value="support">دعم تقني</option>
            <option value="sales">استفسارات المبيعات</option>
            <option value="billing">الفواتير والمدفوعات</option>
            <option value="partnership">الشراكات</option>
            <option value="other">أخرى</option>
        </select>
    </div>
    
    <div class="form-group">
        <label for="message">الرسالة</label>
        <textarea id="message" name="message" rows="5" required placeholder="اكتب رسالتك هنا..."></textarea>
    </div>
    
    <button type="submit" class="submit-btn">
        <i class="fas fa-paper-plane"></i>
        إرسال الرسالة
    </button>
</form>

<h3>أوقات العمل</h3>
<div class="work-hours">
    <div class="day-schedule">
        <span class="day">الأحد - الخميس:</span>
        <span class="time">8:00 ص - 12:00 م</span>
    </div>
    <div class="day-schedule">
        <span class="day">الجمعة:</span>
        <span class="time">2:00 م - 11:00 م</span>
    </div>
    <div class="day-schedule">
        <span class="day">السبت:</span>
        <span class="time">10:00 ص - 10:00 م</span>
    </div>
    <div class="day-schedule emergency">
        <span class="day">الطوارئ:</span>
        <span class="time">متاح 24/7 عبر الدردشة</span>
    </div>
</div>

<h3>وسائل التواصل الاجتماعي</h3>
<div class="social-links">
    <a href="#" class="social-link twitter">
        <i class="fab fa-twitter"></i>
        تويتر
    </a>
    <a href="#" class="social-link telegram">
        <i class="fab fa-telegram"></i>
        تليجرام
    </a>
    <a href="#" class="social-link instagram">
        <i class="fab fa-instagram"></i>
        إنستجرام
    </a>
    <a href="#" class="social-link linkedin">
        <i class="fab fa-linkedin"></i>
        لينكد إن
    </a>
</div>

<style>
.contact-methods {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

.contact-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 10px;
    padding: 25px;
    text-align: center;
}

.contact-card h3 {
    color: #ff0033;
    margin-bottom: 15px;
}

.contact-btn {
    background: linear-gradient(135deg, #ff0033, #cc0027);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 10px;
}

.contact-form {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 10px;
    padding: 30px;
    margin: 30px 0;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #fff;
    font-weight: bold;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #333;
    border-radius: 5px;
    background: #222;
    color: #fff;
}

.submit-btn {
    background: linear-gradient(135deg, #ff0033, #cc0027);
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

.work-hours {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}

.day-schedule {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #333;
}

.day-schedule.emergency {
    color: #ff0033;
    font-weight: bold;
}

.social-links {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin: 30px 0;
}

.social-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 15px;
    background: #333;
    color: #fff;
    text-decoration: none;
    border-radius: 5px;
    transition: all 0.3s ease;
}

.social-link:hover {
    transform: translateY(-2px);
    background: #ff0033;
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
    }
    
    .social-links {
        flex-wrap: wrap;
    }
}
</style>
                ''',
                'meta_description': 'تواصل مع فريق Es-Gift - دعم فني 24/7 عبر الدردشة المباشرة والهاتف والبريد الإلكتروني',
                'meta_keywords': 'اتصل بنا, دعم فني, Es-Gift, خدمة العملاء, تواصل',
                'show_in_footer': True,
                'display_order': 2
            },
            {
                'title': 'من نحن',
                'slug': 'about-us',
                'content': '''
<h2>Es-Gift - رحلتنا في عالم الألعاب الرقمية</h2>

<div class="hero-section">
    <p class="lead">نحن أكثر من مجرد متجر ألعاب، نحن شغف يقود الابتكار في عالم الترفيه الرقمي</p>
</div>

<h3>قصتنا</h3>
<p>بدأت Es-Gift في عام 2020 كحلم بسيط: جعل الألعاب الرقمية وبطاقات الهدايا متاحة للجميع في المنطقة العربية بسهولة وأمان. ما بدأ كفكرة صغيرة نما ليصبح واحداً من أكبر المتاجر الرقمية في المملكة العربية السعودية.</p>

<h3>رؤيتنا</h3>
<div class="vision-card">
    <i class="fas fa-eye"></i>
    <p>أن نكون المنصة الرائدة في المنطقة العربية لتوفير المحتوى الرقمي والألعاب الإلكترونية بجودة عالية وأسعار تنافسية.</p>
</div>

<h3>مهمتنا</h3>
<div class="mission-cards">
    <div class="mission-card">
        <i class="fas fa-shield-alt"></i>
        <h4>الأمان أولاً</h4>
        <p>نضمن حماية معلوماتك ومعاملاتك بأعلى معايير الأمان</p>
    </div>
    
    <div class="mission-card">
        <i class="fas fa-bolt"></i>
        <h4>التسليم الفوري</h4>
        <p>احصل على مشترياتك فوراً بعد الدفع بدون انتظار</p>
    </div>
    
    <div class="mission-card">
        <i class="fas fa-heart"></i>
        <h4>خدمة عملاء استثنائية</h4>
        <p>فريق دعم متخصص متاح 24/7 لمساعدتك</p>
    </div>
    
    <div class="mission-card">
        <i class="fas fa-star"></i>
        <h4>جودة المنتجات</h4>
        <p>نختار أفضل الألعاب والمنتجات الرقمية لعملائنا</p>
    </div>
</div>

<h3>إنجازاتنا</h3>
<div class="achievements">
    <div class="achievement">
        <div class="number">100,000+</div>
        <div class="label">عميل راضٍ</div>
    </div>
    <div class="achievement">
        <div class="number">500,000+</div>
        <div class="label">معاملة ناجحة</div>
    </div>
    <div class="achievement">
        <div class="number">1,000+</div>
        <div class="label">منتج رقمي</div>
    </div>
    <div class="achievement">
        <div class="number">24/7</div>
        <div class="label">دعم فني</div>
    </div>
</div>

<h3>شركاؤنا</h3>
<p>نفتخر بشراكاتنا مع أكبر الشركات في عالم الألعاب والترفيه الرقمي:</p>
<div class="partners">
    <div class="partner-logo">PlayStation</div>
    <div class="partner-logo">Xbox</div>
    <div class="partner-logo">Steam</div>
    <div class="partner-logo">Google Play</div>
    <div class="partner-logo">App Store</div>
    <div class="partner-logo">Netflix</div>
</div>

<h3>فريق العمل</h3>
<p>يضم فريق Es-Gift نخبة من المتخصصين الشغوفين بعالم التقنية والألعاب:</p>
<div class="team-stats">
    <div class="stat">
        <i class="fas fa-users"></i>
        <span>25+ موظف متخصص</span>
    </div>
    <div class="stat">
        <i class="fas fa-graduation-cap"></i>
        <span>خبرة تزيد عن 10 سنوات</span>
    </div>
    <div class="stat">
        <i class="fas fa-clock"></i>
        <span>دعم فني متواصل</span>
    </div>
</div>

<h3>التزامنا</h3>
<div class="commitments">
    <div class="commitment">
        <h4>🌱 البيئة</h4>
        <p>نلتزم بممارسات صديقة للبيئة في جميع عملياتنا</p>
    </div>
    <div class="commitment">
        <h4>🤝 المجتمع</h4>
        <p>ندعم المجتمع المحلي من خلال برامج التدريب والتوظيف</p>
    </div>
    <div class="commitment">
        <h4>🔒 الخصوصية</h4>
        <p>نحمي بيانات عملائنا بأعلى معايير الأمان</p>
    </div>
</div>

<h3>اتصل بنا</h3>
<p>نحن دائماً متاحون للاستماع إلى آرائكم واقتراحاتكم:</p>
<div class="contact-info">
    <div class="contact-item">
        <i class="fas fa-envelope"></i>
        <a href="mailto:info@es-gift.com">info@es-gift.com</a>
    </div>
    <div class="contact-item">
        <i class="fas fa-phone"></i>
        <span>+966 11 123 4567</span>
    </div>
    <div class="contact-item">
        <i class="fas fa-map-marker-alt"></i>
        <span>الرياض، المملكة العربية السعودية</span>
    </div>
</div>

<style>
.hero-section {
    background: linear-gradient(135deg, #ff0033, #cc0027);
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    margin: 30px 0;
}

.lead {
    font-size: 1.2em;
    color: white;
    font-weight: 300;
}

.vision-card {
    background: rgba(255, 0, 51, 0.1);
    border-left: 4px solid #ff0033;
    padding: 20px;
    margin: 20px 0;
    border-radius: 5px;
}

.vision-card i {
    color: #ff0033;
    font-size: 2em;
    margin-bottom: 10px;
}

.mission-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

.mission-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 10px;
    padding: 25px;
    text-align: center;
    transition: transform 0.3s ease;
}

.mission-card:hover {
    transform: translateY(-5px);
    border-color: #ff0033;
}

.mission-card i {
    color: #ff0033;
    font-size: 2.5em;
    margin-bottom: 15px;
}

.achievements {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

.achievement {
    text-align: center;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
}

.number {
    font-size: 2.5em;
    font-weight: bold;
    color: #ff0033;
    margin-bottom: 10px;
}

.label {
    font-size: 1.1em;
    color: #ccc;
}

.partners {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: center;
    margin: 30px 0;
}

.partner-logo {
    background: #333;
    padding: 15px 25px;
    border-radius: 5px;
    color: #fff;
    font-weight: bold;
}

.team-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin: 20px 0;
}

.stat {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.05);
    padding: 15px;
    border-radius: 5px;
}

.stat i {
    color: #ff0033;
}

.commitments {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

.commitment {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 10px;
    padding: 20px;
}

.commitment h4 {
    color: #ff0033;
    margin-bottom: 10px;
    font-size: 1.2em;
}

.contact-info {
    display: flex;
    flex-wrap: wrap;
    gap: 30px;
    margin: 30px 0;
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 10px;
}

.contact-item i {
    color: #ff0033;
}

.contact-item a {
    color: #fff;
    text-decoration: none;
}

.contact-item a:hover {
    color: #ff0033;
}

@media (max-width: 768px) {
    .mission-cards,
    .achievements,
    .commitments {
        grid-template-columns: 1fr;
    }
    
    .contact-info {
        flex-direction: column;
        gap: 15px;
    }
    
    .partners {
        justify-content: flex-start;
    }
}
</style>
                ''',
                'meta_description': 'تعرف على Es-Gift - قصتنا ورحلتنا في عالم الألعاب الرقمية وبطاقات الهدايا',
                'meta_keywords': 'من نحن, Es-Gift, قصة الشركة, رؤية الشركة, فريق العمل',
                'show_in_footer': True,
                'display_order': 3
            },
            {
                'title': 'الشروط والأحكام',
                'slug': 'terms-of-service',
                'content': '''
<h2>الشروط والأحكام - متجر Es-Gift</h2>

<p class="intro">مرحباً بك في Es-Gift. باستخدام موقعنا الإلكتروني وخدماتنا، فإنك توافق على الالتزام بهذه الشروط والأحكام.</p>

<h3>1. تعريفات أساسية</h3>
<div class="terms-section">
    <ul>
        <li><strong>الموقع:</strong> منصة Es-Gift الإلكترونية ومحتوياتها</li>
        <li><strong>المستخدم:</strong> أي شخص يزور أو يستخدم خدمات الموقع</li>
        <li><strong>الخدمات:</strong> جميع المنتجات والخدمات المقدمة عبر الموقع</li>
        <li><strong>المحتوى الرقمي:</strong> الألعاب وبطاقات الهدايا والاشتراكات</li>
    </ul>
</div>

<h3>2. قبول الشروط</h3>
<div class="terms-section">
    <p>باستخدام موقع Es-Gift، فإنك تؤكد أنك:</p>
    <ul>
        <li>بلغت سن الرشد القانوني (18 سنة أو أكثر)</li>
        <li>تملك الأهلية القانونية لإبرام العقود</li>
        <li>توافق على جميع الشروط والأحكام المذكورة</li>
        <li>تتحمل المسؤولية الكاملة عن استخدام الحساب</li>
    </ul>
</div>

<h3>3. التسجيل والحساب</h3>
<div class="terms-section">
    <p><strong>إنشاء الحساب:</strong></p>
    <ul>
        <li>يجب تقديم معلومات صحيحة وحديثة</li>
        <li>كلمة مرور قوية وآمنة</li>
        <li>عدم مشاركة بيانات الحساب مع الغير</li>
        <li>إشعارنا فوراً في حالة اختراق الحساب</li>
    </ul>
    
    <p><strong>مسؤولية المستخدم:</strong></p>
    <ul>
        <li>الحفاظ على سرية بيانات الدخول</li>
        <li>تحديث المعلومات الشخصية عند تغييرها</li>
        <li>استخدام الحساب للأغراض القانونية فقط</li>
    </ul>
</div>

<h3>4. المنتجات والخدمات</h3>
<div class="terms-section">
    <p><strong>أنواع المنتجات:</strong></p>
    <ul>
        <li>بطاقات الألعاب الرقمية (PlayStation, Xbox, Steam)</li>
        <li>اشتراكات الخدمات (Netflix, Spotify, YouTube Premium)</li>
        <li>بطاقات الهدايا لمتاجر مختلفة</li>
        <li>عملات الألعاب والمحتوى الإضافي</li>
    </ul>
    
    <p><strong>شروط الشراء:</strong></p>
    <ul>
        <li>الأسعار معروضة بالريال السعودي ما لم يُذكر خلاف ذلك</li>
        <li>الأسعار قابلة للتغيير دون إشعار مسبق</li>
        <li>التوفر غير مضمون ويخضع لسياسة الكمية المحدودة</li>
    </ul>
</div>

<h3>5. الدفع والتسليم</h3>
<div class="terms-section">
    <p><strong>طرق الدفع المقبولة:</strong></p>
    <ul>
        <li>بطاقات الائتمان والخصم (Visa, MasterCard)</li>
        <li>مدى والدفع الإلكتروني</li>
        <li>التحويل البنكي</li>
        <li>المحافظ الرقمية المعتمدة</li>
    </ul>
    
    <p><strong>التسليم:</strong></p>
    <ul>
        <li>المنتجات الرقمية تُسلم فوراً بعد تأكيد الدفع</li>
        <li>إرسال الرموز عبر البريد الإلكتروني و/أو رسائل SMS</li>
        <li>الاحتفاظ بنسخة من المشتريات في حسابك</li>
    </ul>
</div>

<h3>6. سياسة الاسترداد</h3>
<div class="terms-section">
    <p><strong>حالات الاسترداد:</strong></p>
    <ul>
        <li>عدم تسليم المنتج خلال 24 ساعة</li>
        <li>تسليم منتج معطل أو غير صالح</li>
        <li>خطأ في المنتج المطلوب</li>
    </ul>
    
    <p><strong>شروط الاسترداد:</strong></p>
    <ul>
        <li>تقديم طلب الاسترداد خلال 7 أيام</li>
        <li>تقديم إثبات الشراء والمشكلة</li>
        <li>عدم استخدام المنتج أو تفعيله</li>
        <li>الاسترداد يتم خلال 5-10 أيام عمل</li>
    </ul>
</div>

<h3>7. القيود والحظر</h3>
<div class="terms-section">
    <p><strong>الاستخدام المحظور:</strong></p>
    <ul>
        <li>بيع أو إعادة توزيع المنتجات المشتراة</li>
        <li>استخدام وسائل احتيالية أو غير قانونية</li>
        <li>محاولة اختراق أو إلحاق الضرر بالموقع</li>
        <li>انتهاك حقوق الملكية الفكرية</li>
    </ul>
    
    <p><strong>عواقب المخالفة:</strong></p>
    <ul>
        <li>إيقاف الحساب مؤقتاً أو نهائياً</li>
        <li>إلغاء الطلبات القائمة</li>
        <li>اتخاذ إجراءات قانونية عند الضرورة</li>
    </ul>
</div>

<h3>8. الملكية الفكرية</h3>
<div class="terms-section">
    <p>جميع المحتويات والتصاميم والعلامات التجارية محمية بموجب قوانين الملكية الفكرية:</p>
    <ul>
        <li>شعار وعلامة Es-Gift التجارية</li>
        <li>تصميم ومحتوى الموقع</li>
        <li>البرمجيات والتطبيقات</li>
        <li>المحتوى النصي والمرئي</li>
    </ul>
</div>

<h3>9. إخلاء المسؤولية</h3>
<div class="terms-section">
    <p>Es-Gift غير مسؤول عن:</p>
    <ul>
        <li>مشاكل تقنية خارجة عن سيطرتنا</li>
        <li>أخطاء في المعلومات المقدمة من العملاء</li>
        <li>استخدام المنتجات خارج الشروط المحددة</li>
        <li>قرارات الحظر أو التقييد من جهات خارجية</li>
    </ul>
</div>

<h3>10. القانون الحاكم</h3>
<div class="terms-section">
    <p>تخضع هذه الشروط والأحكام لـ:</p>
    <ul>
        <li>قوانين المملكة العربية السعودية</li>
        <li>الأنظمة واللوائح ذات الصلة</li>
        <li>المحاكم السعودية لحل النزاعات</li>
    </ul>
</div>

<h3>11. التعديل والتحديث</h3>
<div class="terms-section">
    <p>نحتفظ بالحق في:</p>
    <ul>
        <li>تعديل هذه الشروط في أي وقت</li>
        <li>إشعار المستخدمين بالتغييرات</li>
        <li>طلب الموافقة على الشروط الجديدة</li>
    </ul>
</div>

<h3>12. التواصل</h3>
<div class="contact-section">
    <p>لأي استفسارات حول الشروط والأحكام:</p>
    <div class="contact-options">
        <div class="contact-option">
            <i class="fas fa-envelope"></i>
            <span>legal@es-gift.com</span>
        </div>
        <div class="contact-option">
            <i class="fas fa-phone"></i>
            <span>+966 11 123 4567</span>
        </div>
        <div class="contact-option">
            <i class="fas fa-comments"></i>
            <span>الدردشة المباشرة في الموقع</span>
        </div>
    </div>
</div>

<div class="last-update">
    <p><strong>آخر تحديث:</strong> {{ "now"|date("Y-m-d") }}</p>
    <p><em>ننصح بمراجعة هذه الشروط بشكل دوري للاطلاع على أي تحديثات</em></p>
</div>

<style>
.intro {
    background: rgba(255, 0, 51, 0.1);
    border-left: 4px solid #ff0033;
    padding: 20px;
    margin: 20px 0;
    border-radius: 5px;
    font-size: 1.1em;
}

.terms-section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 8px;
    padding: 25px;
    margin: 20px 0;
}

.terms-section ul {
    margin: 15px 0;
    padding-right: 20px;
}

.terms-section li {
    margin: 10px 0;
    line-height: 1.6;
}

.terms-section strong {
    color: #ff0033;
}

.contact-section {
    background: linear-gradient(135deg, #ff0033, #cc0027);
    color: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    margin: 30px 0;
}

.contact-options {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-top: 20px;
    flex-wrap: wrap;
}

.contact-option {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.1);
    padding: 15px 20px;
    border-radius: 5px;
}

.contact-option i {
    font-size: 1.2em;
}

.last-update {
    background: #222;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    margin: 30px 0;
}

.last-update em {
    color: #999;
    font-size: 0.9em;
}

h3 {
    color: #ff0033;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
    margin-top: 40px;
    margin-bottom: 20px;
}

@media (max-width: 768px) {
    .contact-options {
        flex-direction: column;
        gap: 15px;
    }
    
    .terms-section {
        padding: 20px;
    }
}
</style>
                ''',
                'meta_description': 'الشروط والأحكام لمتجر Es-Gift - تعرف على شروط الاستخدام والحقوق والواجبات',
                'meta_keywords': 'شروط الاستخدام, أحكام, Es-Gift, قوانين الاستخدام, حقوق المستخدم',
                'show_in_footer': True,
                'display_order': 4
            }
        ]
        
        print("🔧 تهيئة الصفحات الثابتة...")
        
        # التحقق من وجود الصفحات وإنشاؤها إذا لم تكن موجودة
        for page_data in default_pages:
            existing_page = StaticPage.query.filter_by(slug=page_data['slug']).first()
            
            if not existing_page:
                page = StaticPage(
                    title=page_data['title'],
                    slug=page_data['slug'],
                    content=page_data['content'],
                    meta_description=page_data.get('meta_description', ''),
                    meta_keywords=page_data.get('meta_keywords', ''),
                    show_in_footer=page_data.get('show_in_footer', False),
                    show_in_header=page_data.get('show_in_header', False),
                    display_order=page_data.get('display_order', 0),
                    is_active=True,
                    created_by=1  # افتراض أن admin user له ID = 1
                )
                db.session.add(page)
                print(f"✅ تم إنشاء صفحة: {page_data['title']}")
            else:
                print(f"📋 صفحة موجودة: {page_data['title']}")
        
        try:
            db.session.commit()
            print("✅ تم حفظ جميع الصفحات الثابتة بنجاح!")
            
            # عرض إحصائيات
            total_pages = StaticPage.query.count()
            active_pages = StaticPage.query.filter_by(is_active=True).count()
            footer_pages = StaticPage.query.filter_by(show_in_footer=True).count()
            
            print(f"📊 إحصائيات الصفحات الثابتة:")
            print(f"  - إجمالي الصفحات: {total_pages}")
            print(f"  - الصفحات النشطة: {active_pages}")
            print(f"  - صفحات الفوتر: {footer_pages}")
            
            print("\n📖 الخطوات التالية:")
            print("1. اذهب إلى /admin/static-pages لإدارة الصفحات")
            print("2. يمكنك تعديل المحتوى والإعدادات")
            print("3. الصفحات متاحة الآن في الفوتر والروابط المباشرة")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في حفظ البيانات: {str(e)}")

if __name__ == '__main__':
    init_static_pages()
