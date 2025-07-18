#!/usr/bin/env python3
"""
ترقية قاعدة البيانات لإضافة حقول KYC الجديدة
"""

import sqlite3
import os
from datetime import datetime

def upgrade_database():
    """ترقية قاعدة البيانات لإضافة حقول KYC الجديدة"""
    
    db_path = os.path.join('instance', 'es_gift.db')
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود!")
        return False
    
    try:
        # إنشاء نسخة احتياطية
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق من الحقول الموجودة
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"الحقول الموجودة حالياً: {existing_columns}")
        
        # قائمة الحقول الجديدة المطلوب إضافتها
        new_columns = [
            ('document_type', 'VARCHAR(50)'),
            ('passport_image', 'VARCHAR(200)'),
            ('driver_license_image', 'VARCHAR(200)'),
            ('face_photo_front', 'VARCHAR(200)'),
            ('face_photo_right', 'VARCHAR(200)'),
            ('face_photo_left', 'VARCHAR(200)')
        ]
        
        # إضافة الحقول الجديدة
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"✅ تم إضافة حقل: {column_name}")
                except sqlite3.Error as e:
                    print(f"❌ خطأ في إضافة حقل {column_name}: {e}")
            else:
                print(f"⚠️  الحقل {column_name} موجود بالفعل")
        
        # حفظ التغييرات
        conn.commit()
        
        # التحقق من النتيجة النهائية
        cursor.execute("PRAGMA table_info(user)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"\nالحقول النهائية: {final_columns}")
        
        # إنشاء المجلدات المطلوبة للملفات
        upload_dirs = [
            'static/uploads/kyc-documents',
            'static/uploads/face-verification'
        ]
        
        for upload_dir in upload_dirs:
            os.makedirs(upload_dir, exist_ok=True)
            print(f"✅ تم إنشاء مجلد: {upload_dir}")
        
        conn.close()
        
        if added_columns:
            print(f"\n🎉 تمت ترقية قاعدة البيانات بنجاح!")
            print(f"تم إضافة {len(added_columns)} حقل جديد: {', '.join(added_columns)}")
        else:
            print("\n✅ قاعدة البيانات محدثة بالفعل - لا حاجة لترقية")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في ترقية قاعدة البيانات: {e}")
        return False

if __name__ == '__main__':
    print("🔄 بدء ترقية قاعدة البيانات...")
    success = upgrade_database()
    
    if success:
        print("\n✅ تمت العملية بنجاح!")
        print("يمكنك الآن تشغيل التطبيق واستخدام نظام KYC المحدث")
    else:
        print("\n❌ فشلت عملية الترقية!")
