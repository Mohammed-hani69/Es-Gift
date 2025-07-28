#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود المُصحح لإنشاء حملة Brevo
==============================

هذا هو الكود الأصلي الذي قدمته مع إصلاح جميع الأخطاء النحوية والتكامل مع نظامك
"""

# ------------------
# Create a campaign
# ------------------
# Include the Brevo library
from __future__ import print_function
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

# استيراد الإعدادات المحلية
from brevo_config import BrevoConfig

def create_corrected_campaign():
    """إنشاء حملة بالكود المُصحح"""
    
    # إعداد المفتاح من الإعدادات المحلية بدلاً من كتابته مباشرة
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BrevoConfig.API_KEY
    
    # Instantiate the client
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Define the campaign settings
    email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
        name="Campaign sent via the API",
        subject="My subject",
        sender={
            "name": BrevoConfig.DEFAULT_SENDER['name'],  # تم إصلاح: إضافة علامات اقتباس
            "email": BrevoConfig.DEFAULT_SENDER['email']  # تم إصلاح: استخدام البريد من الإعدادات
        },
        # Content that will be sent
        html_content="Congratulations! You successfully sent this example campaign via the Brevo API.",
        # Select the recipients
        recipients={"listIds": [1, 2]},  # تم إصلاح: تعديل أرقام القوائم إلى قوائم حقيقية
        # Schedule the sending in one hour  
        scheduled_at="2025-07-29 10:00:00"  # تم إصلاح: تاريخ صحيح في المستقبل
    )
    
    # Make the call to the client
    try:
        api_response = api_instance.create_email_campaign(email_campaigns)
        pprint(api_response)
        print("✅ تم إنشاء الحملة بنجاح!")
        return True, api_response
    except ApiException as e:
        print("Exception when calling EmailCampaignsApi->create_email_campaign: %s\n" % e)
        return False, str(e)

def create_arabic_campaign():
    """إنشاء حملة باللغة العربية مع محتوى مُحسن"""
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BrevoConfig.API_KEY
    
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # محتوى عربي مُحسن
    arabic_content = """
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; direction: rtl;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">🎁 ES-GIFT</h1>
            <p style="margin: 10px 0 0 0;">منصتك المفضلة للبطاقات الرقمية</p>
        </div>
        
        <div style="padding: 30px; background: white;">
            <h2 style="color: #333;">مرحباً عزيزي العميل! 👋</h2>
            
            <p style="font-size: 16px; line-height: 1.6; color: #555;">
                نسعد بإعلامك عن أحدث العروض والمنتجات المتوفرة في متجرنا:
            </p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-right: 4px solid #4CAF50;">
                <h3 style="color: #2E7D32; margin-top: 0;">💰 عروض هذا الأسبوع</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
                        🎮 <strong>بطاقات الألعاب</strong> - خصم 25%
                    </li>
                    <li style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
                        🛒 <strong>بطاقات التسوق</strong> - خصم 20%
                    </li>
                    <li style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
                        📱 <strong>بطاقات شحن الجوال</strong> - أسعار مميزة
                    </li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://es-gift.com?utm_source=email&utm_campaign=weekly_offers" 
                   style="display: inline-block; background: #4CAF50; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 16px;">
                    🛍️ تسوق الآن
                </a>
            </div>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #1565c0; font-weight: bold;">💡 نصيحة:</p>
                <p style="margin: 5px 0 0 0; color: #333;">
                    اشترك في النشرة الإخبارية للحصول على تنبيهات فورية بأحدث العروض!
                </p>
            </div>
        </div>
        
        <div style="background: #333; color: white; padding: 20px; text-align: center;">
            <p style="margin: 0; font-size: 14px;">
                شكراً لك لاختيارك ES-GIFT<br>
                📧 support@es-gift.com | 🌐 www.es-gift.com
            </p>
            <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">
                لإلغاء الاشتراك، <a href="{{unsubscribe}}" style="color: #4CAF50;">اضغط هنا</a>
            </p>
        </div>
    </div>
    """
    
    email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
        name="حملة ES-GIFT الأسبوعية - " + time.strftime("%Y-%m-%d"),
        subject="🎁 عروض خاصة من ES-GIFT - لا تفوتها!",
        sender={
            "name": BrevoConfig.DEFAULT_SENDER['name'],
            "email": BrevoConfig.DEFAULT_SENDER['email']
        },
        html_content=arabic_content,
        # استخدام قائمة العملاء الرئيسية من الإعدادات
        recipients={"listIds": [1]},
        # جدولة لإرسال خلال 30 دقيقة
        scheduled_at="2025-07-29 15:00:00"
    )
    
    try:
        api_response = api_instance.create_email_campaign(email_campaigns)
        print("✅ تم إنشاء الحملة العربية بنجاح!")
        pprint(api_response)
        return True, api_response
    except ApiException as e:
        print(f"❌ خطأ في إنشاء الحملة العربية: {e}")
        return False, str(e)

def show_smtp_info():
    """عرض معلومات SMTP للمرجع"""
    
    print("\n" + "="*50)
    print("📧 معلومات SMTP الخاصة بك:")
    print("="*50)
    print(f"🖥️  SMTP Server: {BrevoConfig.SMTP_CONFIG['server']}")
    print(f"🔌 Port: {BrevoConfig.SMTP_CONFIG['port']}")
    print(f"👤 Login: {BrevoConfig.SMTP_CONFIG['username']}")
    print(f"🔑 Password: {BrevoConfig.SMTP_CONFIG['password'][:8]}...")
    print(f"🔐 TLS: {'مُفعل' if BrevoConfig.SMTP_CONFIG['use_tls'] else 'غير مُفعل'}")
    print("="*50)
    
    print("\n🔑 معلومات API:")
    print(f"API Key: {BrevoConfig.API_KEY[:25]}...")
    print(f"Base URL: {BrevoConfig.BASE_URL}")
    print(f"Sender Email: {BrevoConfig.DEFAULT_SENDER['email']}")
    print("="*50)

def main():
    """الدالة الرئيسية"""
    
    print("🎯 أمثلة الحملات المُصححة - ES-GIFT")
    print("="*50)
    
    # التحقق من الإعدادات
    is_valid, message = BrevoConfig.is_valid_config()
    if not is_valid:
        print(f"❌ خطأ في الإعدادات: {message}")
        return
    
    print("✅ الإعدادات صحيحة")
    
    # عرض الخيارات
    print("\nاختر نوع الحملة:")
    print("1. الكود المُصحح (الإصدار الأصلي مُحسن)")
    print("2. حملة عربية مُحسنة")
    print("3. عرض معلومات SMTP")
    print("4. تشغيل جميع الأمثلة")
    
    choice = input("\nأدخل اختيارك (1-4): ").strip()
    
    if choice == "1":
        print("\n📤 إنشاء حملة بالكود المُصحح...")
        create_corrected_campaign()
    elif choice == "2":
        print("\n📤 إنشاء حملة عربية مُحسنة...")
        create_arabic_campaign()
    elif choice == "3":
        show_smtp_info()
    elif choice == "4":
        print("\n🔄 تشغيل جميع الأمثلة...")
        
        print("\n1️⃣ الكود المُصحح:")
        create_corrected_campaign()
        
        print("\n2️⃣ الحملة العربية:")
        create_arabic_campaign()
        
        print("\n3️⃣ معلومات SMTP:")
        show_smtp_info()
    else:
        print("❌ خيار غير صحيح!")

if __name__ == "__main__":
    main()
