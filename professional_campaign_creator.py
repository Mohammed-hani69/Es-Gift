#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مثال عملي نهائي لإنشاء حملة Brevo - ES-GIFT
===========================================

هذا المثال يُظهر الطريقة الصحيحة والمُحسنة لإنشاء حملة بريدية 
باستخدام النظام المُتكامل مع ES-GIFT
"""

import os
import sys
import time
from datetime import datetime, timedelta

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد المكتبات المحلية
from brevo_config import BrevoConfig
from brevo_campaigns import BrevoCampaignService, CampaignRecipients, CampaignSettings

def create_promotional_campaign():
    """إنشاء حملة ترويجية احترافية"""
    
    print("🚀 إنشاء حملة ترويجية لـ ES-GIFT...")
    
    try:
        # إنشاء خدمة الحملات
        campaign_service = BrevoCampaignService()
        
        # تحديد تاريخ الإرسال (غداً في الساعة 10 صباحاً)
        tomorrow = datetime.now() + timedelta(days=1)
        scheduled_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        scheduled_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # تحديد المستقبلين - قائمة العملاء الرئيسية
        recipients = CampaignRecipients(
            list_ids=[1],  # قائمة العملاء الرئيسية
            # يمكن إضافة قوائم أخرى: [1, 3] مثلاً
        )
        
        # المحتوى الاحترافي للحملة
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>عروض ES-GIFT الحصرية</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; box-shadow: 0 0 20px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <header style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               color: white; padding: 40px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 32px; font-weight: bold;">🎁 ES-GIFT</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">
                        منصتك المفضلة للبطاقات الرقمية
                    </p>
                </header>
                
                <!-- Hero Section -->
                <div style="padding: 40px 30px; text-align: center; background: linear-gradient(45deg, #FFF8E1, #F3E5F5);">
                    <h2 style="color: #2E7D32; font-size: 28px; margin: 0 0 15px 0;">
                        🔥 عروض حصرية لفترة محدودة!
                    </h2>
                    <p style="font-size: 18px; color: #555; line-height: 1.6; margin: 0;">
                        استفد من خصومات تصل إلى <span style="color: #E91E63; font-weight: bold; font-size: 24px;">50%</span> 
                        على جميع البطاقات الرقمية
                    </p>
                </div>
                
                <!-- Products Section -->
                <div style="padding: 40px 30px;">
                    <h3 style="color: #333; font-size: 24px; text-align: center; margin-bottom: 30px;">
                        💎 المنتجات المميزة
                    </h3>
                    
                    <div style="display: grid; gap: 20px;">
                        <!-- Gaming Cards -->
                        <div style="background: linear-gradient(45deg, #E3F2FD, #F1F8E9); 
                                    padding: 25px; border-radius: 15px; border-right: 5px solid #4CAF50;">
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="font-size: 32px; margin-left: 15px;">🎮</span>
                                <h4 style="color: #1976D2; margin: 0; font-size: 20px;">بطاقات الألعاب</h4>
                            </div>
                            <p style="color: #666; margin: 10px 0; line-height: 1.6;">
                                PlayStation, Xbox, Nintendo, Steam - جميع أنواع بطاقات الألعاب
                            </p>
                            <div style="background: white; padding: 10px; border-radius: 8px; text-align: center;">
                                <span style="color: #E91E63; font-weight: bold; font-size: 18px;">خصم 35%</span>
                            </div>
                        </div>
                        
                        <!-- Shopping Cards -->
                        <div style="background: linear-gradient(45deg, #FFF3E0, #E8F5E8); 
                                    padding: 25px; border-radius: 15px; border-right: 5px solid #FF9800;">
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="font-size: 32px; margin-left: 15px;">🛒</span>
                                <h4 style="color: #F57C00; margin: 0; font-size: 20px;">بطاقات التسوق</h4>
                            </div>
                            <p style="color: #666; margin: 10px 0; line-height: 1.6;">
                                Amazon, iTunes, Google Play - لجميع احتياجاتك الرقمية
                            </p>
                            <div style="background: white; padding: 10px; border-radius: 8px; text-align: center;">
                                <span style="color: #E91E63; font-weight: bold; font-size: 18px;">خصم 25%</span>
                            </div>
                        </div>
                        
                        <!-- Mobile Cards -->
                        <div style="background: linear-gradient(45deg, #FCE4EC, #F3E5F5); 
                                    padding: 25px; border-radius: 15px; border-right: 5px solid #E91E63;">
                            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                <span style="font-size: 32px; margin-left: 15px;">📱</span>
                                <h4 style="color: #C2185B; margin: 0; font-size: 20px;">بطاقات شحن الجوال</h4>
                            </div>
                            <p style="color: #666; margin: 10px 0; line-height: 1.6;">
                                جميع الشبكات المحلية والدولية - أسعار تنافسية
                            </p>
                            <div style="background: white; padding: 10px; border-radius: 8px; text-align: center;">
                                <span style="color: #E91E63; font-weight: bold; font-size: 18px;">عروض خاصة</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- CTA Section -->
                <div style="padding: 40px 30px; text-align: center; background: #f8f9fa;">
                    <h3 style="color: #333; margin-bottom: 20px;">لا تفوت الفرصة!</h3>
                    <p style="color: #666; margin-bottom: 25px; font-size: 16px;">
                        العروض محدودة حتى {{CURRENT_DATE | date_add:7}} فقط
                    </p>
                    
                    <a href="https://es-gift.com?utm_source=email&utm_campaign=promotional_offer&utm_medium=email" 
                       style="display: inline-block; background: linear-gradient(45deg, #4CAF50, #45a049); 
                              color: white; padding: 18px 40px; text-decoration: none; border-radius: 30px; 
                              font-weight: bold; font-size: 18px; box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
                              transition: all 0.3s; text-transform: uppercase;">
                        🛍️ تسوق الآن واستفد
                    </a>
                    
                    <p style="margin-top: 20px; font-size: 14px; color: #999;">
                        أو استخدم الكود: <strong style="color: #E91E63;">SAVE50</strong> عند الشراء
                    </p>
                </div>
                
                <!-- Features Section -->
                <div style="padding: 30px; background: #263238; color: white;">
                    <h4 style="text-align: center; margin-bottom: 25px; color: #4CAF50;">
                        ⭐ لماذا نحن الأفضل؟
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: center;">
                        <div>
                            <div style="font-size: 24px; margin-bottom: 10px;">⚡</div>
                            <strong>تسليم فوري</strong><br>
                            <small style="opacity: 0.8;">خلال دقائق من الشراء</small>
                        </div>
                        <div>
                            <div style="font-size: 24px; margin-bottom: 10px;">🔒</div>
                            <strong>آمان مضمون</strong><br>
                            <small style="opacity: 0.8;">حماية كاملة للبيانات</small>
                        </div>
                        <div>
                            <div style="font-size: 24px; margin-bottom: 10px;">💰</div>
                            <strong>أفضل الأسعار</strong><br>
                            <small style="opacity: 0.8;">ضمان أقل سعر في السوق</small>
                        </div>
                        <div>
                            <div style="font-size: 24px; margin-bottom: 10px;">🎧</div>
                            <strong>دعم 24/7</strong><br>
                            <small style="opacity: 0.8;">خدمة عملاء متاحة دائماً</small>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <footer style="background: #1a1a1a; color: white; padding: 30px; text-align: center;">
                    <div style="margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #4CAF50;">ES-GIFT</h4>
                        <p style="margin: 0; opacity: 0.8; font-size: 14px;">
                            وجهتك الأولى للبطاقات الرقمية في الشرق الأوسط
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <a href="mailto:support@es-gift.com" 
                           style="color: #4CAF50; text-decoration: none; margin: 0 10px;">
                            📧 support@es-gift.com
                        </a>
                        <a href="https://es-gift.com" 
                           style="color: #4CAF50; text-decoration: none; margin: 0 10px;">
                            🌐 www.es-gift.com
                        </a>
                    </div>
                    
                    <div style="font-size: 12px; opacity: 0.6; padding-top: 20px; border-top: 1px solid #333;">
                        <p style="margin: 0;">
                            تم إرسال هذه الرسالة إلى {{email}} لأنك مشترك في نشرتنا الإخبارية.<br>
                            لإلغاء الاشتراك، <a href="{{unsubscribe}}" style="color: #4CAF50;">اضغط هنا</a> |
                            لتحديث بياناتك، <a href="{{update_profile}}" style="color: #4CAF50;">اضغط هنا</a>
                        </p>
                        <p style="margin: 10px 0 0 0;">
                            © {datetime.now().year} ES-GIFT. جميع الحقوق محفوظة.
                        </p>
                    </div>
                </footer>
                
            </div>
        </body>
        </html>
        """
        
        # إنشاء الحملة
        print(f"📅 جدولة الحملة للإرسال في: {scheduled_str}")
        
        success, result = campaign_service.create_email_campaign(
            name=f"حملة ES-GIFT الترويجية - {datetime.now().strftime('%Y-%m-%d')}",
            subject="🔥 عروض حصرية من ES-GIFT - خصم يصل إلى 50%!",
            html_content=html_content,
            sender={
                "name": "فريق ES-GIFT",
                "email": BrevoConfig.DEFAULT_SENDER['email']
            },
            recipients=recipients,
            scheduled_at=scheduled_str,
            tag="promotional_campaign",
            reply_to="support@es-gift.com"
        )
        
        if success:
            campaign_id = result.get('id', 'غير محدد')
            print("✅ تم إنشاء الحملة الترويجية بنجاح!")
            print(f"📋 معرف الحملة: {campaign_id}")
            print(f"📧 عدد المستقبلين المستهدفين: قائمة العملاء الرئيسية")
            print(f"📅 موعد الإرسال المجدول: {scheduled_str}")
            
            # عرض تفاصيل إضافية
            if isinstance(result, dict):
                print(f"🔗 رابط المعاينة: {result.get('previewUrl', 'غير متوفر')}")
            
            return True, result
        else:
            print(f"❌ فشل في إنشاء الحملة الترويجية: {result}")
            return False, result
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء الحملة الترويجية: {str(e)}")
        return False, str(e)

def create_newsletter_campaign():
    """إنشاء حملة نشرة إخبارية"""
    
    print("📰 إنشاء نشرة إخبارية لـ ES-GIFT...")
    
    try:
        campaign_service = BrevoCampaignService()
        
        # إرسال فوري للنشرة الإخبارية
        recipients = CampaignRecipients(
            list_ids=[3],  # قائمة النشرة الإخبارية
        )
        
        # محتوى النشرة الإخبارية
        newsletter_content = """
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; direction: rtl;">
            <header style="background: #2E7D32; color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0;">📰 نشرة ES-GIFT الإخبارية</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">آخر الأخبار والتحديثات</p>
            </header>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #2E7D32;">🔥 أحدث المنتجات</h2>
                <p>تم إضافة مجموعة جديدة من البطاقات الرقمية لمتجرنا...</p>
                
                <h2 style="color: #1976D2;">💡 نصائح وحيل</h2>
                <p>كيفية الاستفادة القصوى من بطاقاتك الرقمية...</p>
                
                <h2 style="color: #E91E63;">🎉 قصص النجاح</h2>
                <p>اكتشف كيف ساعدت ES-GIFT عملاءنا في تحقيق أهدافهم...</p>
            </div>
            
            <footer style="background: #f5f5f5; padding: 20px; text-align: center; color: #666;">
                <p>شكراً لاشتراكك في نشرتنا الإخبارية</p>
                <p><a href="{{unsubscribe}}" style="color: #2E7D32;">إلغاء الاشتراك</a></p>
            </footer>
        </div>
        """
        
        success, result = campaign_service.create_email_campaign(
            name=f"نشرة ES-GIFT الإخبارية - {datetime.now().strftime('%B %Y')}",
            subject="📰 نشرة ES-GIFT: أحدث المنتجات والعروض",
            html_content=newsletter_content,
            recipients=recipients,
            tag="newsletter"
        )
        
        if success:
            print("✅ تم إنشاء النشرة الإخبارية بنجاح!")
            print(f"📋 معرف الحملة: {result.get('id', 'غير محدد')}")
            return True, result
        else:
            print(f"❌ فشل في إنشاء النشرة الإخبارية: {result}")
            return False, result
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء النشرة الإخبارية: {str(e)}")
        return False, str(e)

def main():
    """الدالة الرئيسية"""
    
    print("🎯 مُنشئ الحملات الاحترافي - ES-GIFT")
    print("="*50)
    
    # التحقق من الإعدادات
    is_valid, message = BrevoConfig.is_valid_config()
    if not is_valid:
        print(f"❌ خطأ في الإعدادات: {message}")
        print("📝 يرجى مراجعة ملف brevo_config.py")
        return
    
    print("✅ الإعدادات صحيحة")
    print(f"📧 المرسل: {BrevoConfig.DEFAULT_SENDER['email']}")
    print(f"🔑 API Key: {BrevoConfig.API_KEY[:25]}...")
    
    # خيارات الحملات
    print("\\nاختر نوع الحملة:")
    print("1. 🔥 حملة ترويجية احترافية")
    print("2. 📰 نشرة إخبارية")
    print("3. 🚀 كلا النوعين")
    
    choice = input("\\nأدخل اختيارك (1-3): ").strip()
    
    print("\\n" + "-"*50)
    
    if choice == "1":
        create_promotional_campaign()
    elif choice == "2":
        create_newsletter_campaign()
    elif choice == "3":
        print("🔄 إنشاء جميع أنواع الحملات...\\n")
        
        print("1️⃣ الحملة الترويجية:")
        success1, _ = create_promotional_campaign()
        
        print("\\n" + "-"*30)
        print("2️⃣ النشرة الإخبارية:")
        success2, _ = create_newsletter_campaign()
        
        print("\\n" + "="*50)
        if success1 and success2:
            print("🎉 تم إنشاء جميع الحملات بنجاح!")
        else:
            print("⚠️ تم إنشاء بعض الحملات بنجاح")
    else:
        print("❌ خيار غير صحيح!")
    
    print("\\n" + "="*50)
    print("✨ انتهى إنشاء الحملات")
    print("💡 يمكنك مراقبة الحملات من لوحة تحكم Brevo")
    print("🔗 https://app.brevo.com/campaign/list")
    print("="*50)

if __name__ == "__main__":
    main()
