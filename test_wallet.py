#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار صفحة المحفظة
"""

from app import app
from models import db, User, UserWallet, GlobalLimits
from wallet_routes import get_or_create_wallet

def test_wallet():
    """اختبار المحفظة"""
    with app.app_context():
        print('🔧 اختبار المحفظة...')
        
        # جلب أول مستخدم
        user = User.query.first()
        if not user:
            print('❌ لا يوجد مستخدمين في قاعدة البيانات')
            return
        
        try:
            # اختبار إنشاء المحفظة
            wallet = get_or_create_wallet(user)
            print(f'✅ تم إنشاء/جلب المحفظة للمستخدم: {user.email}')
            print(f'رصيد: {wallet.balance}')
            print(f'حد يومي: {wallet.daily_limit}')
            print(f'حد شهري: {wallet.monthly_limit}')
            print(f'منفق اليوم: {wallet.daily_spent_today}')
            print(f'منفق الشهر: {wallet.monthly_spent}')
            
            # اختبار الحدود الافتراضية
            limits = GlobalLimits.query.all()
            print(f'\n📋 الحدود الافتراضية:')
            for limit in limits:
                print(f'نوع: {limit.user_type}, يومي: {limit.daily_limit_usd}, شهري: {limit.monthly_limit_usd}')
                
        except Exception as e:
            print(f'❌ خطأ في اختبار المحفظة: {str(e)}')

if __name__ == '__main__':
    test_wallet()
