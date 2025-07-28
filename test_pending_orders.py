#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام الطلبات المعلقة
==========================

هذا الملف لاختبار النظام الجديد للطلبات التي تحتاج أكواد
"""

from app import app, db
from models import Order, ProductCode, OrderItem
from brevo_integration import send_admin_notification

def test_pending_order_system():
    """اختبار النظام الجديد للطلبات المعلقة"""
    
    with app.app_context():
        print("🔍 اختبار نظام الطلبات المعلقة...")
        
        # البحث عن طلبات معلقة
        pending_orders = Order.query.filter_by(status='pending_codes').all()
        print(f"📋 عدد الطلبات المعلقة: {len(pending_orders)}")
        
        # البحث عن طلبات جزئية
        partial_orders = Order.query.filter_by(status='partial_codes').all()
        print(f"📋 عدد الطلبات الجزئية: {len(partial_orders)}")
        
        # عرض تفاصيل الطلبات المعلقة
        for order in pending_orders[:5]:  # أول 5 طلبات فقط
            print(f"\n🔸 طلب رقم {order.id}:")
            print(f"   - البريد: {order.email}")
            print(f"   - الحالة: {order.status}")
            print(f"   - إجمالي المبلغ: {order.total_amount}")
            
            # عدد العناصر المطلوبة
            total_items = sum(item.quantity for item in order.items)
            print(f"   - إجمالي العناصر: {total_items}")
            
            # عدد الأكواد المتوفرة
            available_codes = ProductCode.query.filter_by(
                order_id=order.id, 
                is_used=False
            ).count()
            print(f"   - الأكواد المتوفرة: {available_codes}")
            print(f"   - الأكواد المطلوبة: {total_items - available_codes}")

def test_admin_notification():
    """اختبار إشعارات الإدارة"""
    print("\n📧 اختبار إشعارات الإدارة...")
    
    with app.app_context():
        # البحث عن أول طلب معلق
        order = Order.query.filter_by(status='pending_codes').first()
        
        if order:
            print(f"📧 إرسال إشعار للإدارة عن الطلب {order.id}")
            success = send_admin_notification(order.id, order.email, order.status)
            print(f"✅ نتيجة الإشعار: {'نجح' if success else 'فشل'}")
        else:
            print("❌ لا توجد طلبات معلقة لاختبار الإشعار")

def check_product_codes_availability():
    """فحص توفر أكواد المنتجات"""
    print("\n🔍 فحص توفر أكواد المنتجات...")
    
    with app.app_context():
        # عدد الأكواد المتوفرة لكل منتج
        from sqlalchemy import func
        
        available_codes = db.session.query(
            ProductCode.product_name,
            func.count(ProductCode.id).label('count')
        ).filter_by(
            is_used=False,
            order_id=None
        ).group_by(ProductCode.product_name).all()
        
        print("📊 الأكواد المتوفرة:")
        for product_name, count in available_codes:
            print(f"   - {product_name}: {count} كود")
        
        if not available_codes:
            print("⚠️ لا توجد أكواد متوفرة!")

if __name__ == "__main__":
    print("🚀 بدء اختبار نظام الطلبات المعلقة")
    print("=" * 50)
    
    test_pending_order_system()
    check_product_codes_availability()
    test_admin_notification()
    
    print("\n" + "=" * 50)
    print("✅ انتهى الاختبار")
