# إعدادات البريد الإلكتروني المحدثة - ES-GIFT
# =================================================

## 📧 حل مشكلة البريد الإلكتروني نهائياً

### 🔍 المشكلة المكتشفة:
- Brevo API Key تم تعطيله: `{"message":"Key not found","code":"unauthorized"}`
- Gmail SMTP يحتاج كلمة مرور تطبيق صحيحة

### ✅ الحلول المتاحة:

#### 1. إصلاح Gmail SMTP (الحل الفوري):

```bash
# خطوات الحصول على كلمة مرور التطبيق:
1. اذهب إلى حساب Google الخاص بك
2. Security → 2-Step Verification (يجب تفعيلها أولاً)
3. App passwords → Generate new app password
4. اختر "Mail" و "Other (custom name)" → ES-GIFT
5. انسخ كلمة المرور المكونة من 16 رقم
```

#### 2. تحديث ملف .env:

```properties
# استبدل "your_app_password_here" بكلمة المرور الحقيقية
MAIL_PASSWORD=abcd efgh ijkl mnop  # 16 رقم من Google
```

#### 3. اختبار سريع:

```python
python -c "
import smtplib
from email.mime.text import MIMEText

msg = MIMEText('Test from ES-GIFT')
msg['Subject'] = 'اختبار'
msg['From'] = 'mohamedeloker9@gmail.com'
msg['To'] = 'mohamedeloker9@gmail.com'

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('mohamedeloker9@gmail.com', 'YOUR_APP_PASSWORD_HERE')
    server.send_message(msg)
    print('✅ نجح الإرسال!')
"
```

### 🔄 بدائل أخرى:

#### A. استخدام Brevo SMTP بدلاً من API:
```properties
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USERNAME=932dac001@smtp-brevo.com
MAIL_PASSWORD=O6RxAm3kJYp0BzE2
```

#### B. استخدام خدمة بريد أخرى:
- **SendGrid**: مجاني حتى 100 رسالة/يوم
- **Mailgun**: مجاني حتى 1000 رسالة/شهر
- **Amazon SES**: أسعار منخفضة جداً

### 🎯 الخطوة التالية:

**الحل الأسرع**: احصل على كلمة مرور تطبيق Gmail وحدث ملف .env

**كود الاختبار السريع**:
```python
# test_gmail_smtp.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail():
    # ضع كلمة مرور التطبيق هنا
    app_password = "YOUR_16_DIGIT_PASSWORD"
    
    msg = MIMEMultipart()
    msg['From'] = 'mohamedeloker9@gmail.com'
    msg['To'] = 'mohamedeloker9@gmail.com'
    msg['Subject'] = '🎉 اختبار ES-GIFT Gmail'
    
    body = """
    <h2>✅ نجح الإعداد!</h2>
    <p>Gmail SMTP يعمل بشكل صحيح الآن.</p>
    <p>يمكن إرسال رسائل التحقق والطلبات.</p>
    """
    
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('mohamedeloker9@gmail.com', app_password)
            server.send_message(msg)
        
        print("✅ Gmail SMTP يعمل بشكل مثالي!")
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

if __name__ == "__main__":
    test_gmail()
```

### 📝 ملاحظات مهمة:

1. **كلمة مرور التطبيق** مختلفة عن كلمة مرور Gmail العادية
2. **يجب تفعيل التحقق بخطوتين** في Google أولاً
3. **كلمة المرور تكون 16 حرف** بدون مسافات عند الاستخدام
4. **لا تشارك كلمة المرور** مع أي أحد

### 🚀 بعد الإصلاح:

سيعمل النظام كالتالي:
1. ✅ تسجيل المستخدمين الجدد
2. ✅ إرسال رسائل التحقق
3. ✅ تأكيد الطلبات
4. ✅ إرسال أكواد المنتجات

---

**هل تريد مني مساعدتك في الحصول على كلمة مرور التطبيق؟**
