#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار مفتاح Brevo API الجديد
==============================
"""

import requests
import json

def test_new_brevo_key():
    """اختبار مفتاح Brevo API الجديد"""
    
    # المفتاح الجديد الذي ذكره المستخدم
    api_key = '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'
    
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    
    print("🔑 اختبار مفتاح Brevo API الجديد...")
    print("=" * 50)
    
    try:
        response = requests.get('https://api.brevo.com/v3/account', headers=headers, timeout=10)
        
        print(f"📊 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            print("✅ المفتاح صالح!")
            print(f"📧 الخطة: {account_info.get('plan', {}).get('type', 'غير محدد')}")
            print(f"👤 الاسم: {account_info.get('companyName', 'غير محدد')}")
            print(f"📊 حد الرسائل: {account_info.get('plan', {}).get('creditsType', 'غير محدد')}")
            return True
            
        elif response.status_code == 401:
            print("❌ مفتاح API غير صالح أو منتهي الصلاحية")
            print(f"📝 الرد: {response.text}")
            return False
            
        else:
            print(f"⚠️ خطأ HTTP {response.status_code}")
            print(f"📝 الرد: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return False

if __name__ == '__main__':
    test_new_brevo_key()
