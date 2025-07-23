# -*- coding: utf-8 -*-
"""
تحديث قاعدة البيانات لإصلاح أخطاء الجداول
==========================================

هذا الملف يحل مشاكل قاعدة البيانات ويضيف الأعمدة المفقودة

"""

import os
import sys
from datetime import datetime

# إضافة مسار المشروع إلى Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# استيراد التطبيق والنماذج
from app import create_app
from models import db, PaymentGateway, Currency, Category, Subcategory

def fix_database():
    """إصلاح قاعدة البيانات وإضافة الأعمدة المفقودة"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 بدء إصلاح قاعدة البيانات...")
            
            # حذف الجداول الموجودة وإعادة إنشائها
            print("🗄️ إعادة إنشاء الجداول...")
            
            # حذف جميع الجداول
            db.drop_all()
            print("  ✅ تم حذف الجداول القديمة")
            
            # إنشاء جميع الجداول من جديد
            db.create_all()
            print("  ✅ تم إنشاء الجداول الجديدة")
            
            print("✅ تم إصلاح قاعدة البيانات بنجاح!")
            print("الآن يمكنك تشغيل ملف init_sample_data.py لإضافة البيانات")
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح قاعدة البيانات: {str(e)}")
            raise

if __name__ == '__main__':
    print("🛠️ أداة إصلاح قاعدة البيانات لـ ES-Gift")
    print("=" * 50)
    
    confirm = input("⚠️ تحذير: سيتم حذف جميع البيانات الموجودة! هل تريد المتابعة؟ (y/n): ")
    if confirm.lower() in ['y', 'yes', 'نعم']:
        fix_database()
        print("\n" + "=" * 50)
        print("🎉 تم إصلاح قاعدة البيانات بنجاح!")
        print("التالي: python init_sample_data.py")
    else:
        print("تم إلغاء العملية.")
