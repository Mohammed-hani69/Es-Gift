#!/usr/bin/env python3
"""
Migration script لإضافة حقل serial_number إلى جدول ProductCode
يجب تشغيل هذا السكريبت بعد تحديث models.py
"""

import sqlite3
import os
from datetime import datetime

def add_serial_number_column():
    """إضافة عمود serial_number إلى جدول product_code"""
    
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'es_gift.db')
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود!")
        return False
    
    try:
        # إنشاء نسخة احتياطية
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # نسخ الملف الأصلي
        import shutil
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
        cursor.execute("""
            ALTER TABLE product_code 
            ADD COLUMN serial_number VARCHAR(200)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ تم إضافة عمود serial_number بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إضافة العمود: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 بدء إضافة عمود serial_number...")
    
    if add_serial_number_column():
        print("🎉 تم إنجاز المهمة بنجاح!")
        print("📝 يمكنك الآن تشغيل الموقع بدون أخطاء")
    else:
        print("❌ فشل في إنجاز المهمة")
        print("💡 تأكد من وجود ملف قاعدة البيانات وصلاحيات الكتابة")
