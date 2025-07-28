#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مثال صحيح لإنشاء حملة بريدية باستخدام Brevo API
==============================================

هذا المثال يُظهر الطريقة الصحيحة لإنشاء حملة بريدية باستخدام مكتبة Brevo
مع التكامل مع النظام الموجود في ES-GIFT
"""

from __future__ import print_function
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from datetime import datetime, timedelta

# استيراد إعدادات Brevo المحلية
from brevo_config import BrevoConfig
from brevo_campaigns import BrevoCampaignService, CampaignRecipients

def create_campaign_with_sib_sdk():
    """إنشاء حملة باستخدام مكتبة sib_api_v3_sdk (الطريقة الأصلية المُصححة)"""
    
    print("🚀 إنشاء حملة باستخدام مكتبة Brevo الرسمية...")
    
    # إعداد API Key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BrevoConfig.API_KEY
    
    # إنشاء مثيل API
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # تحديد تاريخ الجدولة (ساعة واحدة من الآن)
    scheduled_time = datetime.now() + timedelta(hours=1)
    scheduled_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # إعداد بيانات الحملة
    email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
        name="حملة ES-GIFT الترويجية",
        subject="عروض خاصة من ES-GIFT! 🎁",
        sender={
            "name": BrevoConfig.DEFAULT_SENDER['name'], 
            "email": BrevoConfig.DEFAULT_SENDER['email']
        },
        type="classic",
        # المحتوى الذي سيتم إرساله
        html_content="""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; direction: rtl;">
            <h1 style="color: #2E7D32; text-align: center;">🎁 مرحباً بك في ES-GIFT</h1>
            <p style="font-size: 18px; color: #333;">عزيزي العميل،</p>
            <p>نتشرف بإعلامك بأحدث العروض والمنتجات الرقمية المتوفرة لدينا:</p>
            
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #1976D2;">💎 عروض خاصة هذا الأسبوع</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 10px 0;">🎮 بطاقات الألعاب - خصم 20%</li>
                    <li style="margin: 10px 0;">🛒 بطاقات التسوق - خصم 15%</li>
                    <li style="margin: 10px 0;">📱 بطاقات شحن الجوال - عروض حصرية</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://es-gift.com" style="background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">تسوق الآن</a>
            </div>
            
            <p style="color: #666; font-size: 14px; text-align: center;">
                شكراً لك لاختيارك ES-GIFT - وجهتك الأولى للبطاقات الرقمية
            </p>
        </div>
        """,
        # تحديد المستقبلين (قائمة العملاء الرئيسية)
        recipients={"listIds": [BrevoConfig.CONTACT_LISTS['main_customers']]},
        # جدولة الإرسال
        scheduled_at=scheduled_str
    )
    
    # إجراء الطلب
    try:
        api_response = api_instance.create_email_campaign(email_campaigns)
        print("✅ تم إنشاء الحملة بنجاح!")
        pprint(api_response)
        return True, api_response
    except ApiException as e:
        print(f"❌ خطأ في إنشاء الحملة: {e}")
        return False, str(e)

def create_campaign_with_local_service():
    """إنشاء حملة باستخدام خدمة ES-GIFT المحلية"""
    
    print("🛠️ إنشاء حملة باستخدام خدمة ES-GIFT المحلية...")
    
    try:
        # إنشاء مثيل الخدمة
        campaign_service = BrevoCampaignService()
        
        # تحديد المستقبلين
        recipients = CampaignRecipients(
            list_ids=[BrevoConfig.CONTACT_LISTS['main_customers']]
        )
        
        # تحديد تاريخ الجدولة
        scheduled_time = datetime.now() + timedelta(hours=2)
        scheduled_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # المحتوى العربي المُحسن
        html_content = """
        <div style="max-width: 600px; margin: 0 auto; font-family: 'Segoe UI', Tahoma, Arial, sans-serif; direction: rtl; background: #f8f9fa;">
            <header style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🎁 ES-GIFT</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">وجهتك الأولى للبطاقات الرقمية</p>
            </header>
            
            <main style="padding: 30px; background: white;">
                <h2 style="color: #333; font-size: 24px; margin-bottom: 20px;">مرحباً {{FNAME | default:'عزيزي العميل'}},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 25px;">
                    نسعد بإعلامك عن أحدث العروض الحصرية والمنتجات الجديدة المتوفرة في متجرنا.
                </p>
                
                <div style="background: linear-gradient(45deg, #FFF3E0, #E8F5E8); padding: 25px; border-radius: 10px; margin: 25px 0; border-right: 5px solid #4CAF50;">
                    <h3 style="color: #2E7D32; margin-top: 0; font-size: 20px;">💰 عروض هذا الأسبوع</h3>
                    <div style="display: grid; gap: 15px;">
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <strong style="color: #1976D2;">🎮 بطاقات PlayStation & Xbox</strong><br>
                            <span style="color: #666;">خصم يصل إلى 25% على جميع بطاقات الألعاب</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <strong style="color: #F57C00;">🛒 بطاقات Amazon & iTunes</strong><br>
                            <span style="color: #666;">عروض حصرية لفترة محدودة</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <strong style="color: #E91E63;">📱 بطاقات شحن الجوال</strong><br>
                            <span style="color: #666;">أسعار مميزة لجميع الشبكات</span>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="https://es-gift.com?utm_source=email&utm_campaign=weekly_offers" 
                       style="display: inline-block; background: linear-gradient(45deg, #4CAF50, #45a049); color: white; 
                              padding: 15px 40px; text-decoration: none; border-radius: 30px; font-weight: bold; 
                              font-size: 18px; box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3); transition: all 0.3s;">
                        🛍️ تسوق الآن واستفد من العروض
                    </a>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 25px 0;">
                    <h4 style="color: #333; margin-top: 0;">💡 نصائح للحصول على أفضل العروض:</h4>
                    <ul style="color: #666; line-height: 1.6;">
                        <li>اشترك في النشرة الإخبارية للحصول على إشعارات فورية</li>
                        <li>تابعنا على وسائل التواصل الاجتماعي</li>
                        <li>استخدم كوبونات الخصم المتاحة</li>
                    </ul>
                </div>
            </main>
            
            <footer style="background: #333; color: white; padding: 25px; text-align: center; border-radius: 0 0 10px 10px;">
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">
                    شكراً لك لاختيارك ES-GIFT<br>
                    <a href="mailto:support@es-gift.com" style="color: #4CAF50;">support@es-gift.com</a> | 
                    <a href="https://es-gift.com" style="color: #4CAF50;">www.es-gift.com</a>
                </p>
                <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.7;">
                    إذا لم تعد ترغب في تلقي هذه الرسائل، 
                    <a href="{{unsubscribe}}" style="color: #4CAF50;">ألغِ الاشتراك هنا</a>
                </p>
            </footer>
        </div>
        """
        
        # إنشاء الحملة
        success, result = campaign_service.create_email_campaign(
            name="حملة ES-GIFT الأسبوعية",
            subject="🎁 عروض خاصة من ES-GIFT - لا تفوتها!",
            html_content=html_content,
            recipients=recipients,
            scheduled_at=scheduled_str,
            tag="weekly_offers"
        )
        
        if success:
            print("✅ تم إنشاء الحملة بنجاح باستخدام الخدمة المحلية!")
            print(f"📋 معرف الحملة: {result.get('id', 'غير محدد')}")
            return True, result
        else:
            print(f"❌ فشل في إنشاء الحملة: {result}")
            return False, result
            
    except Exception as e:
        print(f"❌ خطأ في الخدمة المحلية: {str(e)}")
        return False, str(e)

def create_simple_test_campaign():
    """إنشاء حملة اختبار بسيطة"""
    
    print("🧪 إنشاء حملة اختبار بسيطة...")
    
    try:
        campaign_service = BrevoCampaignService()
        
        # محتوى بسيط للاختبار
        simple_html = """
        <div style="max-width: 500px; margin: 0 auto; font-family: Arial, sans-serif; direction: rtl; padding: 20px;">
            <h2 style="color: #4CAF50; text-align: center;">🧪 رسالة اختبار من ES-GIFT</h2>
            <p>هذه رسالة اختبار للتأكد من عمل النظام بشكل صحيح.</p>
            <p style="background: #f0f0f0; padding: 15px; border-radius: 5px;">
                ✅ تم إرسال هذه الرسالة بنجاح باستخدام Brevo API<br>
                📅 تاريخ الإرسال: {{CURRENT_DATE}}<br>
                🔑 API Key: مُفعل ويعمل بشكل صحيح
            </p>
            <p style="text-align: center; color: #666; font-size: 14px;">
                ES-GIFT - اختبار النظام
            </p>
        </div>
        """
        
        # إرسال فوري (بدون جدولة)
        success, result = campaign_service.create_email_campaign(
            name="اختبار النظام - " + datetime.now().strftime("%Y-%m-%d %H:%M"),
            subject="🧪 اختبار: تأكيد عمل نظام Brevo",
            html_content=simple_html,
            recipients=CampaignRecipients(list_ids=[1]),  # قائمة الاختبار
            tag="system_test"
        )
        
        if success:
            print("✅ تم إنشاء حملة الاختبار بنجاح!")
            
            # محاولة إرسال فوري
            campaign_id = result.get('id')
            if campaign_id:
                print(f"📤 محاولة إرسال الحملة فوراً... (ID: {campaign_id})")
                send_success, send_result = campaign_service.send_campaign_now(campaign_id)
                
                if send_success:
                    print("✅ تم إرسال الحملة فوراً!")
                else:
                    print(f"⚠️ تم إنشاء الحملة ولكن فشل الإرسال الفوري: {send_result}")
            
            return True, result
        else:
            print(f"❌ فشل في إنشاء حملة الاختبار: {result}")
            return False, result
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء حملة الاختبار: {str(e)}")
        return False, str(e)

def main():
    """الدالة الرئيسية لتشغيل الأمثلة"""
    
    print("="*60)
    print("🎯 أمثلة إنشاء الحملات البريدية - ES-GIFT")
    print("="*60)
    
    # التحقق من إعدادات Brevo أولاً
    is_valid, message = BrevoConfig.is_valid_config()
    if not is_valid:
        print(f"❌ خطأ في الإعدادات: {message}")
        print("📝 يرجى مراجعة ملف brevo_config.py وتحديث API Key وبريد المرسل")
        return
    
    print(f"✅ الإعدادات صحيحة")
    print(f"🔑 API Key: {BrevoConfig.API_KEY[:20]}...")
    print(f"📧 المرسل: {BrevoConfig.DEFAULT_SENDER['email']}")
    print()
    
    # قائمة الخيارات
    print("اختر نوع الحملة المراد إنشاؤها:")
    print("1. حملة باستخدام مكتبة sib_api_v3_sdk الرسمية")
    print("2. حملة باستخدام خدمة ES-GIFT المحلية") 
    print("3. حملة اختبار بسيطة")
    print("4. تشغيل جميع الأمثلة")
    
    choice = input("\nأدخل اختيارك (1-4): ").strip()
    
    print("\n" + "-"*50)
    
    if choice == "1":
        create_campaign_with_sib_sdk()
    elif choice == "2":
        create_campaign_with_local_service()
    elif choice == "3":
        create_simple_test_campaign()
    elif choice == "4":
        print("🔄 تشغيل جميع الأمثلة...\n")
        
        print("1️⃣ المثال الأول: مكتبة sib_api_v3_sdk")
        create_campaign_with_sib_sdk()
        
        print("\n" + "-"*50)
        print("2️⃣ المثال الثاني: خدمة ES-GIFT المحلية")
        create_campaign_with_local_service()
        
        print("\n" + "-"*50)
        print("3️⃣ المثال الثالث: حملة اختبار")
        create_simple_test_campaign()
    else:
        print("❌ خيار غير صحيح!")
    
    print("\n" + "="*60)
    print("✨ انتهى تشغيل الأمثلة")
    print("📚 لمزيد من المعلومات، راجع BREVO_INTEGRATION_GUIDE.md")
    print("="*60)

if __name__ == "__main__":
    main()
