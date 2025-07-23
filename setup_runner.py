# -*- coding: utf-8 -*-
"""
تشغيل سريع لإعداد النظام كاملاً - ES-Gift
=====================================

هذا الملف ينفذ جميع عمليات الإعداد بأمر واحد

"""

import os
import sys
import subprocess
from datetime import datetime

def run_setup():
    """تشغيل إعداد النظام كاملاً"""
    print("🚀 مرحباً بك في نظام الإعداد السريع لـ ES-Gift")
    print("=" * 60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # قائمة العمليات
    operations = [
        {
            'name': 'إنشاء قاعدة البيانات',
            'command': 'python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print(\'✅ تم إنشاء قاعدة البيانات\')"',
            'description': 'إنشاء جداول قاعدة البيانات'
        },
        {
            'name': 'إضافة البيانات الأساسية',
            'command': 'python init_sample_data.py',
            'description': 'إضافة الأقسام والمنتجات والعروض'
        },
        {
            'name': 'إضافة بيانات النظام المالي',
            'command': 'python init_financial_data.py',
            'description': 'إضافة المستخدمين والحدود المالية والموظفين'
        },
        {
            'name': 'تنظيم الصور',
            'command': 'python image_manager.py',
            'description': 'تنظيم وإدارة الصور في المجلدات'
        }
    ]
    
    print("العمليات المتاحة:")
    for i, op in enumerate(operations, 1):
        print(f"{i}. {op['name']} - {op['description']}")
    
    print("\nخيارات التشغيل:")
    print("A. تشغيل جميع العمليات")
    print("1-4. تشغيل عملية محددة")
    print("Q. خروج")
    
    choice = input("\nاختيارك: ").strip().upper()
    
    if choice == 'Q':
        print("👋 وداعاً!")
        return
    
    if choice == 'A':
        # تشغيل جميع العمليات
        print("\n🔄 بدء تشغيل جميع العمليات...")
        for i, op in enumerate(operations, 1):
            print(f"\n⏳ {i}/4: {op['name']}...")
            try:
                if 'image_manager.py' in op['command']:
                    # تشغيل تنظيم الصور تلقائياً
                    exec_auto_image_manager()
                else:
                    result = os.system(op['command'])
                    if result == 0:
                        print(f"✅ {op['name']} - مكتمل")
                    else:
                        print(f"❌ {op['name']} - فشل")
            except Exception as e:
                print(f"❌ خطأ في {op['name']}: {str(e)}")
        
        print("\n🎉 انتهت جميع العمليات!")
        
    elif choice in ['1', '2', '3', '4']:
        # تشغيل عملية محددة
        op_index = int(choice) - 1
        op = operations[op_index]
        
        print(f"\n⏳ تشغيل: {op['name']}...")
        try:
            if 'image_manager.py' in op['command']:
                exec_auto_image_manager()
            else:
                result = os.system(op['command'])
                if result == 0:
                    print(f"✅ {op['name']} - مكتمل")
                else:
                    print(f"❌ {op['name']} - فشل")
        except Exception as e:
            print(f"❌ خطأ في {op['name']}: {str(e)}")
    
    else:
        print("❌ اختيار غير صحيح")

def exec_auto_image_manager():
    """تشغيل إدارة الصور تلقائياً"""
    try:
        # استيراد وتشغيل دوال إدارة الصور
        sys.path.append(os.getcwd())
        import image_manager
        
        print("  📁 إنشاء مجلدات الصور...")
        image_manager.create_default_images()
        
        print("  📦 تنظيم الصور...")
        image_manager.organize_images()
        
        print("  📸 عرض الصور المتاحة...")
        image_manager.list_available_images()
        
        print("✅ تم تنظيم الصور بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في تنظيم الصور: {str(e)}")

def show_system_info():
    """عرض معلومات النظام"""
    print("\n📊 معلومات النظام:")
    print("=" * 30)
    
    # فحص الملفات المطلوبة
    required_files = [
        'app.py',
        'models.py', 
        'init_sample_data.py',
        'init_financial_data.py',
        'image_manager.py'
    ]
    
    print("📂 الملفات المطلوبة:")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - مفقود")
    
    # فحص المجلدات
    required_dirs = [
        'static/uploads',
        'static/uploads/categories',
        'static/uploads/subcategories',
        'static/uploads/gift-cards',
        'static/uploads/main-offers',
        'templates',
        'templates/admin'
    ]
    
    print("\n📁 المجلدات المطلوبة:")
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - مفقود")

def create_run_script():
    """إنشاء ملف تشغيل للويندوز"""
    bat_content = '''@echo off
chcp 65001 > nul
echo 🚀 تشغيل ES-Gift Setup
echo ==================
python setup_runner.py
pause
'''
    
    with open('run_setup.bat', 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ تم إنشاء ملف run_setup.bat")

if __name__ == '__main__':
    try:
        # تحديد ترميز UTF-8 للكونسول
        if os.name == 'nt':  # Windows
            os.system('chcp 65001 > nul')
        
        # عرض معلومات النظام أولاً
        show_system_info()
        
        # إنشاء ملف تشغيل
        create_run_script()
        
        # تشغيل الإعداد
        run_setup()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ تم إيقاف العملية بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ عام: {str(e)}")
    
    input("\nاضغط Enter للمتابعة...")
