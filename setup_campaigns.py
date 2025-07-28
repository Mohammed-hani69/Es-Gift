#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد سريع للحملات البريدية - ES-GIFT
====================================

هذا الملف يساعدك في إعداد الحملات البريدية بسرعة
"""

import os
import sys
from datetime import datetime, timedelta

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_campaign_lists():
    """إعداد قوائم الاتصال الأساسية"""
    print("📋 إعداد قوائم جهات الاتصال...")
    
    try:
        from brevo_campaigns import campaign_service
        
        # قوائم الاتصال المطلوبة لـ ES-GIFT
        required_lists = [
            "عملاء ES-GIFT الرئيسيون",
            "عملاء VIP", 
            "مشتركي النشرة الإخبارية",
            "الموزعون والشركاء",
            "عملاء البطائق الرقمية",
            "عملاء بطائق الألعاب"
        ]
        
        created_lists = []
        
        # الحصول على القوائم الموجودة أولاً
        success, existing_lists = campaign_service.get_contact_lists()
        existing_names = [lst.get('name', '') for lst in existing_lists] if success else []
        
        for list_name in required_lists:
            if list_name not in existing_names:
                success, response = campaign_service.create_contact_list(list_name)
                
                if success:
                    list_id = response.get('id')
                    print(f"✅ تم إنشاء قائمة: {list_name} (ID: {list_id})")
                    created_lists.append({'name': list_name, 'id': list_id})
                else:
                    print(f"⚠️ فشل في إنشاء قائمة {list_name}: {response}")
            else:
                print(f"ℹ️ القائمة موجودة بالفعل: {list_name}")
        
        if created_lists:
            print(f"\n✅ تم إنشاء {len(created_lists)} قائمة جديدة")
            
            # عرض معرفات القوائم للتحديث في الإعدادات
            print("\n📝 قم بتحديث هذه المعرفات في brevo_config.py:")
            for lst in created_lists:
                var_name = lst['name'].replace(' ', '_').replace('ES-GIFT', 'es_gift').lower()
                print(f"   '{var_name}': {lst['id']},")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إعداد القوائم: {str(e)}")
        return False

def create_sample_campaigns():
    """إنشاء حملات نموذجية"""
    print("\n📧 إنشاء حملات نموذجية...")
    
    try:
        from brevo_campaigns import create_es_gift_campaign
        
        # حملات نموذجية لـ ES-GIFT
        sample_campaigns = [
            {
                'name': 'ترحيب بالعملاء الجدد - ES-GIFT',
                'subject': '🎉 أهلاً وسهلاً بك في ES-GIFT!',
                'content': '''
                <h2>🎉 مرحباً بك في عائلة ES-GIFT!</h2>
                <p>شكراً لك على انضمامك إلى أكبر متجر للبطائق والهدايا الرقمية في المنطقة.</p>
                
                <div style="background: linear-gradient(135deg, #FF0033, #667eea); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <h3>🎁 هدية ترحيب خاصة!</h3>
                    <p>احصل على خصم 15% على أول عملية شراء</p>
                    <p><strong>كود الخصم: WELCOME15</strong></p>
                </div>
                
                <h3>🛍️ ماذا ستجد في ES-GIFT:</h3>
                <ul>
                    <li>🎮 بطائق الألعاب الرقمية</li>
                    <li>🛒 بطائق التسوق والهدايا</li>
                    <li>📱 شحن الجوالات</li>
                    <li>💳 البطائق المصرفية الرقمية</li>
                </ul>
                '''
            },
            {
                'name': 'عروض الأسبوع - ES-GIFT',
                'subject': '🔥 عروض حصرية لهذا الأسبوع!',
                'content': '''
                <h2>🔥 عروض الأسبوع الحصرية!</h2>
                <p>لا تفوت هذه الفرصة الذهبية للحصول على أفضل البطائق بأسعار مذهلة.</p>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4>🎮 بطائق الألعاب</h4>
                        <p style="color: #FF0033; font-size: 24px; font-weight: bold;">خصم 25%</p>
                    </div>
                    <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center;">
                        <h4>🛒 بطائق التسوق</h4>
                        <p style="color: #FF0033; font-size: 24px; font-weight: bold;">خصم 20%</p>
                    </div>
                </div>
                
                <p>⏰ العرض ساري حتى نهاية الأسبوع فقط!</p>
                '''
            },
            {
                'name': 'نشرة إخبارية شهرية - ES-GIFT',
                'subject': '📰 أخبار ES-GIFT الشهرية',
                'content': '''
                <h2>📰 نشرة ES-GIFT الشهرية</h2>
                <p>إليك ملخص أهم الأخبار والتحديثات لهذا الشهر.</p>
                
                <h3>🆕 ما الجديد:</h3>
                <ul>
                    <li>✨ إضافة بطائق جديدة من أشهر المتاجر</li>
                    <li>⚡ تحسينات على سرعة الموقع</li>
                    <li>🔐 ميزات أمان محسنة</li>
                    <li>📱 تطبيق الجوال قريباً!</li>
                </ul>
                
                <h3>📊 إحصائيات الشهر:</h3>
                <ul>
                    <li>🛍️ +50,000 بطاقة مباعة</li>
                    <li>😊 رضا العملاء: 98%</li>
                    <li>⚡ متوسط وقت التسليم: 30 ثانية</li>
                </ul>
                '''
            }
        ]
        
        created_campaigns = []
        
        for campaign in sample_campaigns:
            success, response = create_es_gift_campaign(
                campaign_name=campaign['name'],
                campaign_subject=campaign['subject'],
                campaign_content=campaign['content']
                # لا نحدد target_lists لتستخدم القوائم المتاحة تلقائياً
            )
            
            if success:
                campaign_id = response.get('id')
                print(f"✅ تم إنشاء: {campaign['name']} (ID: {campaign_id})")
                created_campaigns.append({'name': campaign['name'], 'id': campaign_id})
            else:
                print(f"⚠️ فشل في إنشاء: {campaign['name']} - {response}")
        
        if created_campaigns:
            print(f"\n✅ تم إنشاء {len(created_campaigns)} حملة نموذجية")
            print("\n💡 يمكنك الآن:")
            print("   1️⃣ تعديل الحملات في لوحة Brevo")
            print("   2️⃣ إضافة المستقبلين المناسبين")
            print("   3️⃣ جدولة الإرسال أو الإرسال فوراً")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الحملات النموذجية: {str(e)}")
        return False

def show_usage_examples():
    """عرض أمثلة الاستخدام"""
    print("\n" + "="*60)
    print("💻 أمثلة الاستخدام")
    print("="*60)
    
    print("\n1️⃣ إنشاء حملة بسيطة:")
    print("""
from brevo_campaigns import create_es_gift_campaign

success, response = create_es_gift_campaign(
    campaign_name="عرض خاص",
    campaign_subject="خصم 20% على جميع البطائق",
    campaign_content="<h1>عرض محدود!</h1><p>اشتري الآن...</p>",
    target_lists=[1, 2]  # قوائم محددة
)

if success:
    campaign_id = response['id']
    print(f"تم إنشاء الحملة: {campaign_id}")
""")
    
    print("\n2️⃣ إرسال حملة فوراً:")
    print("""
from brevo_campaigns import send_campaign_immediately

success, message = send_campaign_immediately(campaign_id)
if success:
    print("تم إرسال الحملة بنجاح!")
""")
    
    print("\n3️⃣ جدولة حملة:")
    print("""
from brevo_campaigns import schedule_campaign_later
from datetime import datetime, timedelta

# إرسال غداً الساعة 10 صباحاً
send_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0)
send_time_str = send_time.strftime('%Y-%m-%d %H:%M:%S')

success, message = schedule_campaign_later(campaign_id, send_time_str)
""")
    
    print("\n4️⃣ الحصول على إحصائيات:")
    print("""
from brevo_campaigns import get_campaign_statistics

success, stats = get_campaign_statistics(campaign_id)
if success:
    print(f"الحالة: {stats['status']}")
    print(f"عدد المرسل إليهم: {stats.get('statistics', {}).get('sent', 0)}")
""")

def main():
    """الدالة الرئيسية"""
    print("🚀 إعداد سريع للحملات البريدية - ES-GIFT")
    print("="*50)
    
    print("سيتم الآن إعداد النظام الأساسي للحملات البريدية...")
    print("هذا يشمل:")
    print("   📋 إنشاء قوائم جهات الاتصال الأساسية")
    print("   📧 إنشاء حملات نموذجية")
    print("   💻 عرض أمثلة الاستخدام")
    
    confirm = input("\nهل تريد المتابعة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', '']:
        print("تم إلغاء الإعداد.")
        return
    
    # تشغيل خطوات الإعداد
    steps = [
        ("إعداد قوائم الاتصال", setup_campaign_lists),
        ("إنشاء حملات نموذجية", create_sample_campaigns)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            print(f"\n🔄 {step_name}...")
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ خطأ في {step_name}: {str(e)}")
            results.append((step_name, False))
    
    # عرض النتائج
    print("\n" + "="*50)
    print("📊 نتائج الإعداد:")
    print("="*50)
    
    passed = 0
    for step_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {step_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 النتيجة النهائية: {passed}/{len(results)} خطوة ناجحة")
    
    if passed == len(results):
        print("🎉 تم إعداد نظام الحملات البريدية بنجاح!")
        print("\n🚀 الخطوات التالية:")
        print("   1️⃣ اختبر النظام: python test_brevo_campaigns.py")
        print("   2️⃣ راجع الحملات في لوحة Brevo")
        print("   3️⃣ أضف المستقبلين للقوائم")
        print("   4️⃣ ابدأ إرسال الحملات!")
    else:
        print("⚠️ بعض الخطوات فشلت. راجع الأخطاء وحاول مرة أخرى")
    
    # عرض أمثلة الاستخدام
    show_usage_examples()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إيقاف الإعداد بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ عام في الإعداد: {str(e)}")
        print("💡 تأكد من أن جميع الملفات موجودة والإعدادات صحيحة")
