#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد سريع لـ Brevo
===================

هذا الملف يساعدك في إعداد Brevo بسرعة
"""

import os

def setup_brevo():
    """معالج الإعداد السريع لـ Brevo"""
    
    print("🚀 مرحباً بك في معالج إعداد Brevo لـ ES-GIFT!")
    print("=" * 60)
    
    # جمع المعلومات من المستخدم
    print("\n📝 يرجى إدخال المعلومات التالية:")
    
    api_key = input("\n🔑 API Key من Brevo (يبدأ بـ xkeysib-): ").strip()
    if not api_key.startswith('xkeysib-'):
        print("⚠️ تأكد أن API Key يبدأ بـ xkeysib-")
        api_key = input("🔑 API Key مرة أخرى: ").strip()
    
    sender_email = input("📧 بريد المرسل المتحقق منه في Brevo: ").strip()
    sender_name = input("👤 اسم المرسل (افتراضي: ES-GIFT): ").strip()
    if not sender_name:
        sender_name = "ES-GIFT"
    
    plan = input("📊 خطة Brevo (free/starter/business/enterprise) [افتراضي: free]: ").strip()
    if not plan:
        plan = "free"
    
    test_mode = input("🧪 تفعيل وضع الاختبار؟ (y/n) [افتراضي: y]: ").strip().lower()
    test_mode = test_mode in ['y', 'yes', 'نعم', ''] 
    
    test_email = ""
    if test_mode:
        test_email = input("📧 بريد الاختبار (سيتم إرسال جميع الرسائل إليه): ").strip()
    
    # تحديث ملف الإعدادات
    print("\n⚙️ تحديث إعدادات Brevo...")
    
    try:
        # قراءة ملف الإعدادات الحالي
        config_file = "brevo_config.py"
        
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # تحديث القيم
        content = content.replace(
            "API_KEY = os.getenv('BREVO_API_KEY', 'xkeysib-YOUR_REAL_API_KEY_HERE-REPLACE_WITH_ACTUAL_KEY')",
            f"API_KEY = os.getenv('BREVO_API_KEY', '{api_key}')"
        )
        
        content = content.replace(
            "'email': os.getenv('BREVO_SENDER_EMAIL', 'your-verified-email@yourdomain.com')",
            f"'email': os.getenv('BREVO_SENDER_EMAIL', '{sender_email}')"
        )
        
        content = content.replace(
            "'name': 'ES-GIFT'",
            f"'name': '{sender_name}'"
        )
        
        content = content.replace(
            "CURRENT_PLAN = os.getenv('BREVO_PLAN', 'free')",
            f"CURRENT_PLAN = os.getenv('BREVO_PLAN', '{plan}')"
        )
        
        content = content.replace(
            "TEST_MODE = os.getenv('BREVO_TEST_MODE', 'False').lower() == 'true'",
            f"TEST_MODE = os.getenv('BREVO_TEST_MODE', '{str(test_mode).lower()}').lower() == 'true'"
        )
        
        if test_email:
            content = content.replace(
                "TEST_EMAIL = os.getenv('BREVO_TEST_EMAIL', 'test@es-gift.com')",
                f"TEST_EMAIL = os.getenv('BREVO_TEST_EMAIL', '{test_email}')"
            )
        
        # حفظ الملف المحدث
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ تم تحديث إعدادات Brevo بنجاح!")
        
        # إنشاء ملف .env
        env_content = f"""# إعدادات Brevo - ES-GIFT
BREVO_API_KEY={api_key}
BREVO_SENDER_EMAIL={sender_email}
BREVO_PLAN={plan}
BREVO_TEST_MODE={str(test_mode).lower()}
"""
        if test_email:
            env_content += f"BREVO_TEST_EMAIL={test_email}\n"
        
        with open('.env.brevo', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ تم إنشاء ملف .env.brevo")
        
        # اختبار الإعدادات
        print("\n🧪 اختبار الإعدادات...")
        
        # استيراد واختبار
        try:
            from brevo_integration import test_brevo_integration
            success, message = test_brevo_integration()
            
            if success:
                print(f"✅ اختبار ناجح: {message}")
                
                # اختبار إرسال بريد
                if test_email:
                    print(f"\n📧 إرسال بريد اختبار إلى {test_email}...")
                    
                    from brevo_integration import send_email_brevo
                    
                    test_success = send_email_brevo(
                        test_email,
                        "اختبار إعداد Brevo - ES-GIFT",
                        f"""
                        <div style="font-family: Arial, sans-serif; direction: rtl; padding: 20px;">
                            <h2 style="color: #FF0033;">🎉 تم إعداد Brevo بنجاح!</h2>
                            <p>مرحباً من ES-GIFT!</p>
                            <p>تم إعداد التكامل مع Brevo بنجاح. النظام جاهز للاستخدام.</p>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 20px 0;">
                                <h3>الإعدادات:</h3>
                                <ul>
                                    <li>المرسل: {sender_name} &lt;{sender_email}&gt;</li>
                                    <li>الخطة: {plan}</li>
                                    <li>وضع الاختبار: {'مُفعل' if test_mode else 'غير مُفعل'}</li>
                                </ul>
                            </div>
                            <p>يمكنك الآن استخدام جميع ميزات البريد الإلكتروني في ES-GIFT!</p>
                        </div>
                        """
                    )
                    
                    if test_success:
                        print("✅ تم إرسال بريد الاختبار بنجاح!")
                        print("📬 تحقق من صندوق الوارد")
                    else:
                        print("⚠️ فشل في إرسال بريد الاختبار")
                
            else:
                print(f"❌ فشل الاختبار: {message}")
                print("💡 تحقق من الإعدادات وحاول مرة أخرى")
                
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {str(e)}")
        
        # الخلاصة
        print("\n" + "=" * 60)
        print("🎉 تم إعداد Brevo بنجاح!")
        print("=" * 60)
        
        print(f"\n📊 ملخص الإعدادات:")
        print(f"   🔑 API Key: {api_key[:20]}...")
        print(f"   📧 المرسل: {sender_name} <{sender_email}>")
        print(f"   📊 الخطة: {plan}")
        print(f"   🧪 وضع الاختبار: {'مُفعل' if test_mode else 'غير مُفعل'}")
        if test_email:
            print(f"   📬 بريد الاختبار: {test_email}")
        
        print(f"\n📁 الملفات المُحدثة:")
        print(f"   ✅ brevo_config.py")
        print(f"   ✅ .env.brevo")
        
        print(f"\n🚀 الخطوات التالية:")
        print(f"   1️⃣ اختبر النظام بـ: python test_brevo.py")
        print(f"   2️⃣ شغل التطبيق: python app.py")
        print(f"   3️⃣ جرب التسجيل والتحقق من البريد")
        
        if test_mode:
            print(f"\n⚠️ تذكير: وضع الاختبار مُفعل")
            print(f"   جميع الرسائل ستذهب إلى: {test_email}")
            print(f"   لإيقافه، غيّر TEST_MODE إلى False")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تحديث الإعدادات: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        setup_brevo()
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إلغاء الإعداد")
    except Exception as e:
        print(f"\n❌ خطأ عام: {str(e)}")
        print("💡 تأكد من وجود ملف brevo_config.py")
