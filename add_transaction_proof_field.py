#!/usr/bin/env python3
"""
إضافة حقل transaction_proof إلى جدول WalletDepositRequest
يجب تشغيل هذا الملف من مجلد المشروع الرئيسي
"""

import sqlite3
import os

def add_transaction_proof_field():
    """إضافة حقل transaction_proof إلى جدول wallet_deposit_request"""
    
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'es_gift.db')
    
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود الجدول
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='wallet_deposit_request'
        """)
        
        if not cursor.fetchone():
            print("❌ جدول wallet_deposit_request غير موجود")
            return False
        
        # التحقق من وجود الحقل
        cursor.execute("PRAGMA table_info(wallet_deposit_request)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'transaction_proof' in columns:
            print("✅ حقل transaction_proof موجود بالفعل")
            return True
        
        # إضافة الحقل الجديد
        cursor.execute("""
            ALTER TABLE wallet_deposit_request 
            ADD COLUMN transaction_proof VARCHAR(300)
        """)
        
        # حفظ التغييرات
        conn.commit()
        print("✅ تم إضافة حقل transaction_proof بنجاح")
        
        # التحقق من النتيجة
        cursor.execute("PRAGMA table_info(wallet_deposit_request)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'transaction_proof' in columns:
            print("✅ تم التأكد من إضافة الحقل بنجاح")
            return True
        else:
            print("❌ فشل في إضافة الحقل")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """الدالة الرئيسية"""
    print("🔧 بدء إضافة حقل transaction_proof...")
    print("-" * 50)
    
    if add_transaction_proof_field():
        print("-" * 50)
        print("🎉 تم تحديث قاعدة البيانات بنجاح!")
        print("📝 ملاحظة: تأكد من إعادة تشغيل الخادم لتطبيق التغييرات")
    else:
        print("-" * 50)
        print("❌ فشل في تحديث قاعدة البيانات")

if __name__ == "__main__":
    main()
