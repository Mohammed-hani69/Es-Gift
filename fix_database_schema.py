#!/usr/bin/env python3
"""
إدارة قاعدة البيانات - إضافة عمود serial_number
يدعم Flask-Migrate إذا كان متاحاً
"""

import os
import sys
from datetime import datetime

def run_flask_migrate():
    """تشغيل Flask-Migrate لإنشاء المايقريشن"""
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_migrate import Migrate, init, migrate, upgrade
        
        # إعداد التطبيق
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/es_gift.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        migrate = Migrate(app, db)
        
        with app.app_context():
            # إنشاء مجلد migrations إذا لم يكن موجوداً
            if not os.path.exists('migrations'):
                print("🔄 إنشاء مجلد المايقريشن...")
                init()
            
            # إنشاء مايقريشن جديدة
            print("🔄 إنشاء مايقريشن لإضافة serial_number...")
            migrate(message="Add serial_number to ProductCode")
            
            # تطبيق المايقريشن
            print("🔄 تطبيق المايقريشن...")
            upgrade()
            
            print("✅ تم إنجاز المايقريشن بنجاح!")
            return True
            
    except ImportError:
        print("⚠️ Flask-Migrate غير متاح، سيتم استخدام الطريقة البديلة")
        return False
    except Exception as e:
        print(f"❌ خطأ في Flask-Migrate: {str(e)}")
        return False

def run_direct_sql():
    """تشغيل SQL مباشرة لإضافة العمود"""
    import sqlite3
    import shutil
    
    db_path = os.path.join('instance', 'es_gift.db')
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود!")
        return False
    
    try:
        # إنشاء نسخة احتياطية
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود العمود
        cursor.execute("PRAGMA table_info(product_code)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'serial_number' in columns:
            print("✅ العمود serial_number موجود مسبقاً")
            conn.close()
            return True
        
        # إضافة العمود الجديد
        cursor.execute("ALTER TABLE product_code ADD COLUMN serial_number VARCHAR(200)")
        conn.commit()
        conn.close()
        
        print("✅ تم إضافة عمود serial_number بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إضافة العمود: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🔧 ES-Gift Database Migration Tool")
    print("📝 إضافة عمود serial_number إلى جدول ProductCode")
    print("-" * 50)
    
    # محاولة Flask-Migrate أولاً
    if run_flask_migrate():
        return
    
    # الطريقة البديلة
    print("🔄 استخدام الطريقة البديلة...")
    if run_direct_sql():
        print("🎉 تم إنجاز المهمة بنجاح!")
    else:
        print("❌ فشل في إنجاز المهمة")

if __name__ == "__main__":
    main()
