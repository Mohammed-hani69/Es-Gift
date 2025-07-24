#!/usr/bin/env python3
"""
اختبار الوصول لحقل serial_number في ProductCode
"""

from flask import Flask
from models import db, ProductCode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/es_gift.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # البحث عن أول كود منتج
    product_code = ProductCode.query.first()
    
    if product_code:
        print("✅ تم العثور على كود منتج")
        print(f"ID: {product_code.id}")
        print(f"Product ID: {product_code.product_id}")
        print(f"Code: {product_code.code}")
        
        # اختبار الوصول للـ serial_number
        try:
            serial = product_code.serial_number
            print(f"✅ Serial Number: {serial}")
            print("✅ نجح الوصول لحقل serial_number!")
        except AttributeError as e:
            print(f"❌ خطأ في الوصول لحقل serial_number: {e}")
        except Exception as e:
            print(f"❌ خطأ عام: {e}")
    else:
        print("❌ لا يوجد أكواد منتجات في قاعدة البيانات")
        
        # إنشاء كود تجريبي للاختبار
        try:
            test_code = ProductCode(
                product_id=1,
                code="TEST123",
                serial_number="SN123456"
            )
            db.session.add(test_code)
            db.session.commit()
            print("✅ تم إنشاء كود تجريبي بنجاح")
        except Exception as e:
            print(f"❌ خطأ في إنشاء كود تجريبي: {e}")
