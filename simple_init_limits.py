#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to initialize financial limits system
"""

from app import app
from models import db, GlobalLimits, UserLimits
from decimal import Decimal

def init_financial_limits():
    """Initialize the financial limits system"""
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check if global limits already exist
            existing_limits = GlobalLimits.query.count()
            
            if existing_limits == 0:
                # Create default global limits
                default_limits = [
                    {
                        'user_type': 'normal',
                        'display_name': 'عملاء عاديين',
                        'daily_limit_usd': Decimal('3000.00'),
                        'monthly_limit_usd': Decimal('90000.00'),
                        'description': 'حدود إنفاق افتراضية للعملاء العاديين'
                    },
                    {
                        'user_type': 'kyc',
                        'display_name': 'عملاء محققين (KYC)',
                        'daily_limit_usd': Decimal('6000.00'),
                        'monthly_limit_usd': Decimal('180000.00'),
                        'description': 'حدود إنفاق محسنة للعملاء المحققين'
                    },
                    {
                        'user_type': 'distributor',
                        'display_name': 'موزعين',
                        'daily_limit_usd': Decimal('10000.00'),
                        'monthly_limit_usd': Decimal('300000.00'),
                        'description': 'حدود إنفاق عالية للموزعين'
                    }
                ]
                
                for limit_data in default_limits:
                    global_limit = GlobalLimits(**limit_data)
                    db.session.add(global_limit)
                
                db.session.commit()
                print("✅ تم إنشاء الحدود الافتراضية بنجاح")
            else:
                print("ℹ️ الحدود الافتراضية موجودة مسبقاً")
            
            print("✅ تم تهيئة نظام الحدود المالية بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في تهيئة النظام: {e}")
            db.session.rollback()

if __name__ == "__main__":
    init_financial_limits()
