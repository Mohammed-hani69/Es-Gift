#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتهيئة نظام المحفظة وإنشاء محافظ للمستخدمين الموجودين
"""

from app import create_app
from models import db, User, UserWallet, Currency, GlobalLimits
from wallet_utils import get_or_create_wallet
from decimal import Decimal

def init_wallet_system():
    """تهيئة نظام المحفظة"""
    app = create_app()
    
    with app.app_context():
        print("🚀 بدء تهيئة نظام المحفظة...")
        
        # إنشاء العملات الأساسية إذا لم تكن موجودة
        currencies = [
            {'code': 'USD', 'name': 'الدولار الأمريكي', 'symbol': '$', 'exchange_rate': 3.75},
            {'code': 'SAR', 'name': 'الريال السعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0},
            {'code': 'EUR', 'name': 'اليورو', 'symbol': '€', 'exchange_rate': 4.10},
            {'code': 'GBP', 'name': 'الجنيه الإسترليني', 'symbol': '£', 'exchange_rate': 4.60},
        ]
        
        for curr_data in currencies:
            existing = Currency.query.filter_by(code=curr_data['code']).first()
            if not existing:
                currency = Currency(**curr_data, is_active=True)
                db.session.add(currency)
                print(f"✅ تم إنشاء عملة: {curr_data['name']}")
        
        # إنشاء الحدود الافتراضية للمستخدمين
        limits = [
            {
                'user_type': 'regular',
                'display_name': 'عميل عادي',
                'daily_limit_usd': Decimal('1000.00'),
                'monthly_limit_usd': Decimal('30000.00'),
                'description': 'الحدود الافتراضية للعملاء العاديين'
            },
            {
                'user_type': 'kyc',
                'display_name': 'عميل موثق',
                'daily_limit_usd': Decimal('5000.00'),
                'monthly_limit_usd': Decimal('150000.00'),
                'description': 'الحدود الافتراضية للعملاء الموثقين'
            },
            {
                'user_type': 'reseller',
                'display_name': 'موزع',
                'daily_limit_usd': Decimal('10000.00'),
                'monthly_limit_usd': Decimal('300000.00'),
                'description': 'الحدود الافتراضية للموزعين'
            }
        ]
        
        for limit_data in limits:
            existing = GlobalLimits.query.filter_by(user_type=limit_data['user_type']).first()
            if not existing:
                limit_obj = GlobalLimits(**limit_data, is_active=True)
                db.session.add(limit_obj)
                print(f"✅ تم إنشاء حدود: {limit_data['display_name']}")
        
        db.session.commit()
        
        # إنشاء محافظ للمستخدمين الموجودين
        users = User.query.all()
        wallets_created = 0
        wallets_updated = 0
        
        for user in users:
            existing_wallet = UserWallet.query.filter_by(user_id=user.id).first()
            
            if not existing_wallet:
                # إنشاء محفظة جديدة مع رصيد تجريبي
                wallet = get_or_create_wallet(user)
                
                # إضافة رصيد تجريبي للمحفظة (1000 دولار)
                wallet.balance = Decimal('1000.00')
                wallet.currency = 'USD'
                db.session.commit()
                
                wallets_created += 1
                print(f"✅ تم إنشاء محفظة للمستخدم: {user.email} - رصيد: $1000")
            else:
                # تحديث المحفظة الموجودة إذا لم تكن تحتوي على رصيد
                if existing_wallet.balance == 0:
                    existing_wallet.balance = Decimal('1000.00')
                    existing_wallet.currency = 'USD'
                    db.session.commit()
                    wallets_updated += 1
                    print(f"✅ تم تحديث محفظة المستخدم: {user.email} - رصيد جديد: $1000")
        
        print(f"\n🎉 تم الانتهاء من تهيئة نظام المحفظة:")
        print(f"📊 المحافظ المنشأة: {wallets_created}")
        print(f"🔄 المحافظ المحدثة: {wallets_updated}")
        print(f"👥 إجمالي المستخدمين: {len(users)}")

if __name__ == '__main__':
    init_wallet_system()
