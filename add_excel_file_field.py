#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة حقل ملف Excel للطلبات
"""

from app import app, db
from models import Order
from sqlalchemy import text

def add_excel_file_field():
    """إضافة حقل excel_file_path لجدول Order"""
    try:
        with app.app_context():
            # فحص إذا كان الحقل موجود بالفعل
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order')]
            
            if 'excel_file_path' not in columns:
                print("إضافة حقل excel_file_path...")
                # إضافة الحقل باستخدام طريقة صحيحة
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE "order" ADD COLUMN excel_file_path VARCHAR(500)'))
                    conn.commit()
                print("✓ تم إضافة حقل excel_file_path بنجاح")
            else:
                print("✓ حقل excel_file_path موجود بالفعل")
                
    except Exception as e:
        print(f"❌ خطأ في إضافة الحقل: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 بدء إضافة حقل ملف Excel للطلبات...")
    
    if add_excel_file_field():
        print("✅ تم تحديث قاعدة البيانات بنجاح")
    else:
        print("❌ فشل في تحديث قاعدة البيانات")
