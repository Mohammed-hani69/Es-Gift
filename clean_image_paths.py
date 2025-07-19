#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت لتنظيف مسارات الصور في قاعدة البيانات
"""

from app import create_app
from models import db, MainOffer, GiftCardSection, OtherBrand

def clean_image_paths():
    """تنظيف مسارات الصور الخاطئة في قاعدة البيانات"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 بدء تنظيف مسارات الصور...")
        
        # تنظيف العروض الرئيسية
        print("\n📋 تنظيف العروض الرئيسية...")
        main_offers = MainOffer.query.all()
        for offer in main_offers:
            if offer.image_url and offer.image_url.startswith('/static/'):
                # إزالة /static/ من البداية واستخراج اسم الملف فقط
                old_path = offer.image_url
                # استخراج اسم الملف من المسار
                filename = old_path.split('/')[-1]
                offer.image_url = filename
                print(f"   ✅ تم تحديث: {old_path} → {filename}")
        
        # تنظيف بطاقات الهدايا
        print("\n🎁 تنظيف بطاقات الهدايا...")
        gift_cards = GiftCardSection.query.all()
        for card in gift_cards:
            if card.image_url and card.image_url.startswith('/static/'):
                old_path = card.image_url
                filename = old_path.split('/')[-1]
                card.image_url = filename
                print(f"   ✅ تم تحديث: {old_path} → {filename}")
        
        # تنظيف الماركات الأخرى
        print("\n🏷️ تنظيف الماركات الأخرى...")
        other_brands = OtherBrand.query.all()
        for brand in other_brands:
            if brand.image_url and brand.image_url.startswith('/static/'):
                old_path = brand.image_url
                filename = old_path.split('/')[-1]
                brand.image_url = filename
                print(f"   ✅ تم تحديث: {old_path} → {filename}")
        
        try:
            db.session.commit()
            print("\n✅ تم حفظ جميع التغييرات بنجاح!")
            print("🎉 تم تنظيف مسارات الصور بنجاح!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ خطأ في حفظ التغييرات: {e}")

def check_missing_images():
    """فحص الصور المفقودة"""
    import os
    
    app = create_app()
    
    with app.app_context():
        print("\n🔍 فحص الصور المفقودة...")
        
        uploads_path = os.path.join(app.root_path, 'static', 'uploads')
        
        # فحص العروض الرئيسية
        main_offers = MainOffer.query.all()
        for offer in main_offers:
            if offer.image_url and not offer.image_url.startswith('http'):
                file_path = os.path.join(uploads_path, offer.image_url)
                if not os.path.exists(file_path):
                    print(f"   ❌ صورة مفقودة: {offer.title} - {offer.image_url}")
                else:
                    print(f"   ✅ صورة موجودة: {offer.title}")
        
        # فحص بطاقات الهدايا
        gift_cards = GiftCardSection.query.all()
        for card in gift_cards:
            if card.image_url and not card.image_url.startswith('http'):
                file_path = os.path.join(uploads_path, card.image_url)
                if not os.path.exists(file_path):
                    print(f"   ❌ صورة مفقودة: {card.title} - {card.image_url}")
                else:
                    print(f"   ✅ صورة موجودة: {card.title}")

if __name__ == "__main__":
    print("🚀 بدء تنظيف قاعدة البيانات...")
    clean_image_paths()
    check_missing_images()
    print("\n🎊 انتهى التنظيف!")
