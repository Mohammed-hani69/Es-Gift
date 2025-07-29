#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار المفتاح الجديد المحدث
============================
"""

import requests
import json

def test_latest_key():
    """اختبار المفتاح الأحدث"""
    
    # المفتاح الجديد المحدث من الرسالة الأخيرة
    api_key = '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'
    
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    
    print("🔑 اختبار المفتاح الأحدث...")
    print("=" * 50)
    print(f"🔗 المفتاح: {api_key[:20]}...{api_key[-20:]}")
    
    try:
        response = requests.get('https://api.brevo.com/v3/account', headers=headers, timeout=10)
        
        print(f"📊 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            print("✅ المفتاح صالح!")
            print(f"📧 البريد: {account_info.get('email', 'غير محدد')}")
            
            # التحقق من نوع البيانات
            plan_info = account_info.get('plan', {})
            if isinstance(plan_info, list) and len(plan_info) > 0:
                plan_type = plan_info[0].get('type', 'غير محدد')
            elif isinstance(plan_info, dict):
                plan_type = plan_info.get('type', 'غير محدد')
            else:
                plan_type = 'غير محدد'
                
            print(f"📊 نوع الخطة: {plan_type}")
            print(f"👤 اسم الشركة: {account_info.get('companyName', 'غير محدد')}")
            return True, account_info
            
        elif response.status_code == 401:
            print("❌ مفتاح API غير صالح أو منتهي الصلاحية")
            print(f"📝 الخطأ: {response.text}")
            return False, response.text
            
        else:
            print(f"⚠️ خطأ HTTP {response.status_code}")
            print(f"📝 الرد: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return False, str(e)

def update_brevo_config_file(api_key):
    """تحديث ملف brevo_config.py بالمفتاح الجديد"""
    try:
        config_file = "brevo_config.py"
        
        # قراءة الملف الحالي
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # البحث عن السطر الذي يحتوي على API_KEY والتحديث
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if 'API_KEY = os.getenv(' in line and 'BREVO_API_KEY' in line:
                updated_lines.append(f"    API_KEY = os.getenv('BREVO_API_KEY', '{api_key}')")
            else:
                updated_lines.append(line)
        
        # حفظ الملف المحدث
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"✅ تم تحديث {config_file} بالمفتاح الجديد")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تحديث الملف: {str(e)}")
        return False

if __name__ == '__main__':
    success, result = test_latest_key()
    
    if success:
        print("\n🎉 اختبار المفتاح نجح!")
        
        # تحديث ملف الإعدادات
        api_key = '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'
        update_brevo_config_file(api_key)
        
    else:
        print("\n❌ فشل الاختبار")
        print("🔧 تحقق من صحة المفتاح في لوحة تحكم Brevo")
