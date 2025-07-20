#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف إعداد الحدود الافتراضية لأنواع العملاء
"""

from app import app, db
from models import GlobalLimits, UserLimits, User

def init_global_limits():
    """إنشاء الحدود الافتراضية لأنواع العملاء"""
    
    # حدود العميل العادي
    normal_limits = GlobalLimits.query.filter_by(user_type='normal').first()
    if not normal_limits:
        normal_limits = GlobalLimits(
            user_type='normal',
            display_name='عميل عادي',
            description='حدود الشراء للعملاء العاديين (غير مفعلين)',
            daily_limit_usd=3000.00,
            monthly_limit_usd=90000.00,  # 30 × 3000
            is_active=True
        )
        db.session.add(normal_limits)
        print("تم إضافة حدود العميل العادي")
    
    # حدود عميل KYC
    kyc_limits = GlobalLimits.query.filter_by(user_type='kyc').first()
    if not kyc_limits:
        kyc_limits = GlobalLimits(
            user_type='kyc',
            display_name='عميل مفعل (KYC)',
            description='حدود الشراء للعملاء المفعلين بـ KYC',
            daily_limit_usd=6000.00,
            monthly_limit_usd=180000.00,  # 30 × 6000
            is_active=True
        )
        db.session.add(kyc_limits)
        print("تم إضافة حدود عميل KYC")
    
    # حدود الموزع
    distributor_limits = GlobalLimits.query.filter_by(user_type='distributor').first()
    if not distributor_limits:
        distributor_limits = GlobalLimits(
            user_type='distributor',
            display_name='موزع',
            description='حدود الشراء للموزعين',
            daily_limit_usd=10000.00,
            monthly_limit_usd=300000.00,  # 30 × 10000
            is_active=True
        )
        db.session.add(distributor_limits)
        print("تم إضافة حدود الموزع")
    
    db.session.commit()
    print("تم إنشاء جميع الحدود الافتراضية")

def assign_user_limits():
    """تعيين الحدود لجميع المستخدمين الموجودين"""
    
    users_without_limits = User.query.outerjoin(UserLimits).filter(UserLimits.user_id.is_(None)).all()
    
    for user in users_without_limits:
        # تحديد نوع المستخدم
        if hasattr(user, 'user_type') and user.user_type == 'distributor':
            user_type = 'distributor'
        elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
            user_type = 'distributor'
        elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
            user_type = 'kyc'
        else:
            user_type = 'normal'
        
        # الحصول على الحدود المناسبة
        global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
        if global_limit:
            user_limit = UserLimits(
                user_id=user.id,
                daily_limit_usd=global_limit.daily_limit_usd,
                monthly_limit_usd=global_limit.monthly_limit_usd,
                daily_spent_usd=0.00,
                monthly_spent_usd=0.00,
                is_custom=False
            )
            db.session.add(user_limit)
            print(f"تم تعيين حدود {global_limit.display_name} للمستخدم {user.email}")
    
    db.session.commit()
    print(f"تم تعيين الحدود لـ {len(users_without_limits)} مستخدم")

def main():
    """تشغيل جميع وظائف الإعداد"""
    with app.app_context():
        print("بدء إعداد نظام الحدود المالية...")
        
        # إنشاء الجداول إذا لم تكن موجودة
        db.create_all()
        
        # إنشاء الحدود الافتراضية
        init_global_limits()
        
        # تعيين الحدود للمستخدمين الموجودين
        assign_user_limits()
        
        print("تم الانتهاء من إعداد نظام الحدود المالية بنجاح!")

if __name__ == '__main__':
    main()
