#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test User Limits Creation
========================

سكريبت اختبار لفحص إنشاء حدود المستخدمين عند التسجيل

Author: ES-Gift Development Team
Created: 2025
"""

from app import app
from models import db, User, UserLimits, GlobalLimits
from wallet_utils import create_user_limits, ensure_default_limits_exist
from werkzeug.security import generate_password_hash
import datetime

def test_user_limits_creation():
    """اختبار إنشاء حدود المستخدم عند التسجيل"""
    with app.app_context():
        print("🧪 بدء اختبار إنشاء حدود المستخدمين...")
        
        # التأكد من وجود الحدود الافتراضية
        print("📋 التحقق من الحدود الافتراضية...")
        ensure_default_limits_exist()
        
        # عرض الحدود الافتراضية الموجودة
        global_limits = GlobalLimits.query.all()
        print(f"✅ تم العثور على {len(global_limits)} نوع من الحدود الافتراضية:")
        for limit in global_limits:
            print(f"   - {limit.display_name} ({limit.user_type}): يومي ${limit.daily_limit_usd}, شهري ${limit.monthly_limit_usd}")
        
        # إنشاء مستخدم اختبار
        test_email = f"test_user_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        print(f"\n👤 إنشاء مستخدم اختبار: {test_email}")
        
        # حذف المستخدم الاختبار إذا كان موجوداً
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            UserLimits.query.filter_by(user_id=existing_user.id).delete()
            db.session.delete(existing_user)
            db.session.commit()
        
        # إنشاء المستخدم الجديد
        test_user = User(
            email=test_email,
            full_name="مستخدم اختبار",
            password_hash=generate_password_hash("test123"),
            created_at=datetime.datetime.utcnow()
        )
        
        db.session.add(test_user)
        db.session.flush()  # للحصول على ID
        
        print(f"✅ تم إنشاء المستخدم بـ ID: {test_user.id}")
        
        # إنشاء حدود المستخدم
        print("💰 إنشاء حدود المستخدم...")
        user_limits = create_user_limits(test_user)
        
        if user_limits:
            print("✅ تم إنشاء حدود المستخدم بنجاح:")
            print(f"   - الحد اليومي: ${user_limits.daily_limit_usd}")
            print(f"   - الحد الشهري: ${user_limits.monthly_limit_usd}")
            print(f"   - نوع الحدود: {'مخصصة' if user_limits.is_custom else 'افتراضية'}")
            print(f"   - المنفق اليومي: ${user_limits.daily_spent_usd}")
            print(f"   - المنفق الشهري: ${user_limits.monthly_spent_usd}")
        else:
            print("❌ فشل في إنشاء حدود المستخدم")
            return False
        
        # حفظ التغييرات
        db.session.commit()
        print("💾 تم حفظ البيانات في قاعدة البيانات")
        
        # التحقق من الحفظ
        saved_user = User.query.filter_by(email=test_email).first()
        saved_limits = UserLimits.query.filter_by(user_id=saved_user.id).first()
        
        if saved_user and saved_limits:
            print("✅ تم التحقق من حفظ البيانات بنجاح")
            print(f"   - المستخدم: {saved_user.email}")
            print(f"   - الحدود: يومي ${saved_limits.daily_limit_usd}, شهري ${saved_limits.monthly_limit_usd}")
        else:
            print("❌ فشل في التحقق من حفظ البيانات")
            return False
        
        # تنظيف بيانات الاختبار
        print("\n🧹 تنظيف بيانات الاختبار...")
        db.session.delete(saved_limits)
        db.session.delete(saved_user)
        db.session.commit()
        print("✅ تم تنظيف بيانات الاختبار")
        
        print("\n🎉 اكتمل الاختبار بنجاح! النظام يعمل بشكل صحيح.")
        return True

def show_all_limits():
    """عرض جميع الحدود الموجودة في النظام"""
    with app.app_context():
        print("📊 عرض جميع الحدود في النظام:")
        
        print("\n🌐 الحدود الافتراضية:")
        global_limits = GlobalLimits.query.order_by(GlobalLimits.user_type).all()
        for limit in global_limits:
            status = "نشط" if limit.is_active else "غير نشط"
            print(f"   - {limit.display_name} ({limit.user_type}): يومي ${limit.daily_limit_usd}, شهري ${limit.monthly_limit_usd} - {status}")
        
        print(f"\n👥 حدود المستخدمين (العدد الإجمالي: {UserLimits.query.count()}):")
        user_limits = UserLimits.query.join(User).limit(10).all()
        for limit in user_limits:
            limit_type = "مخصصة" if limit.is_custom else "افتراضية"
            print(f"   - {limit.user.email}: يومي ${limit.daily_limit_usd}, شهري ${limit.monthly_limit_usd} ({limit_type})")
        
        if UserLimits.query.count() > 10:
            print(f"   ... و {UserLimits.query.count() - 10} مستخدم آخر")

if __name__ == "__main__":
    print("🔧 بدء اختبار نظام حدود المستخدمين...")
    
    # عرض الحدود الموجودة
    show_all_limits()
    
    print("\n" + "="*60 + "\n")
    
    # اختبار إنشاء حدود جديدة
    success = test_user_limits_creation()
    
    if success:
        print(f"\n✅ جميع الاختبارات نجحت! النظام جاهز للاستخدام.")
    else:
        print(f"\n❌ فشل في بعض الاختبارات. يرجى مراجعة الأخطاء.")
