# -*- coding: utf-8 -*-
"""
إضافة بيانات تجريبية شاملة لنظام ES-Gift
=======================================

هذا الملف يحتوي على بيانات تجريبية للأقسام والمنتجات والعروض
والعملات وبوابات الدفع وغيرها من البيانات الأساسية

تشغيل الملف: python init_sample_data.py
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# إضافة مسار المشروع إلى Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# استيراد التطبيق والنماذج
from app import create_app
from models import *

def init_sample_data():
    """إضافة البيانات التجريبية"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 بدء إضافة البيانات التجريبية...")
            
            # 1. إضافة العملات
            add_currencies()
            
            # 2. إضافة بوابات الدفع
            add_payment_gateways()
            
            # 3. إضافة الأقسام الرئيسية
            add_main_categories()
            
            # 4. إضافة الأقسام الفرعية
            add_subcategories()
            
            # 5. إضافة المنتجات
            add_products()
            
            # 6. إضافة العروض الرئيسية
            add_main_offers()
            
            # 7. إضافة أقسام بطاقات الهدايا
            add_gift_card_sections()
            
            # 8. إضافة العلامات التجارية الأخرى
            add_other_brands()
            
            # 9. إضافة أكواد المنتجات
            add_product_codes()
            
            # 10. إضافة المستخدمين التجريبيين
            add_sample_users()
            
            # 11. إضافة الصفحات الثابتة
            add_static_pages()
            
            # 12. إضافة المقالات التجريبية
            add_sample_articles()  # تم التعليق لأن الدالة غير معرفة
            
            db.session.commit()
            print("✅ تم إضافة جميع البيانات التجريبية بنجاح!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إضافة البيانات: {str(e)}")
            raise

def add_currencies():
    """إضافة العملات الأساسية"""
    print("💰 إضافة العملات...")
    
    currencies_data = [
        {'code': 'SAR', 'name': 'ريال سعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0, 'is_active': True},
        {'code': 'USD', 'name': 'دولار أمريكي', 'symbol': '$', 'exchange_rate': 0.27, 'is_active': True},
        {'code': 'EUR', 'name': 'يورو', 'symbol': '€', 'exchange_rate': 0.24, 'is_active': True},
        {'code': 'GBP', 'name': 'جنيه إسترليني', 'symbol': '£', 'exchange_rate': 0.21, 'is_active': True},
        {'code': 'AED', 'name': 'درهم إماراتي', 'symbol': 'د.إ', 'exchange_rate': 0.98, 'is_active': True},
        {'code': 'EGP', 'name': 'جنيه مصري', 'symbol': 'ج.م', 'exchange_rate': 13.0, 'is_active': True},
        {'code': 'TRY', 'name': 'ليرة تركية', 'symbol': '₺', 'exchange_rate': 9.2, 'is_active': True},
    ]
    
    for curr_data in currencies_data:
        existing = Currency.query.filter_by(code=curr_data['code']).first()
        if not existing:
            currency = Currency(**curr_data)
            db.session.add(currency)
            print(f"  ✅ تم إضافة عملة: {curr_data['name']}")

def add_payment_gateways():
    """إضافة بوابات الدفع"""
    print("💳 إضافة بوابات الدفع...")
    
    gateways_data = [
        {
            'name': 'فيزا/ماستركارد',
            'provider': 'visa_mastercard',
            'is_active': True,
            'config': {
                'merchant_id': 'MERCHANT_ID',
                'api_key': 'API_KEY',
                'endpoint': 'https://api.payment.com/v1'
            },
            'supported_currencies': ['SAR', 'USD', 'EUR'],
            'min_amount': Decimal('1.00'),
            'max_amount': Decimal('10000.00'),
            'fee_percentage': Decimal('2.5'),
            'fee_fixed': Decimal('0.00')
        },
        {
            'name': 'مدى',
            'provider': 'mada',
            'is_active': True,
            'config': {
                'merchant_id': 'MADA_MERCHANT_ID',
                'terminal_id': 'TERMINAL_ID'
            },
            'supported_currencies': ['SAR'],
            'min_amount': Decimal('1.00'),
            'max_amount': Decimal('5000.00'),
            'fee_percentage': Decimal('1.5'),
            'fee_fixed': Decimal('0.00')
        },
        {
            'name': 'STC Pay',
            'provider': 'stc_pay',
            'is_active': True,
            'config': {
                'merchant_id': 'STC_MERCHANT_ID',
                'secret_key': 'SECRET_KEY'
            },
            'supported_currencies': ['SAR'],
            'min_amount': Decimal('1.00'),
            'max_amount': Decimal('3000.00'),
            'fee_percentage': Decimal('2.0'),
            'fee_fixed': Decimal('0.00')
        }
    ]
    
    for gateway_data in gateways_data:
        # التحقق بناءً على الاسم بدلاً من provider لتجنب خطأ العمود المفقود
        existing = PaymentGateway.query.filter_by(name=gateway_data['name']).first()
        if not existing:
            gateway = PaymentGateway(**gateway_data)
            db.session.add(gateway)
            print(f"  ✅ تم إضافة بوابة دفع: {gateway_data['name']}")
        else:
            print(f"  🔄 بوابة الدفع موجودة مسبقاً: {gateway_data['name']}")

def add_main_categories():
    """إضافة الأقسام الرئيسية"""
    print("📂 إضافة الأقسام الرئيسية...")
    
    categories_data = [
        {
            'name': 'بطاقات الألعاب',
            'name_en': 'Gaming Cards',
            'description': 'بطاقات شحن للألعاب الشهيرة مثل PUBG وفري فاير وفورتنايت',
            'icon_class': 'fas fa-gamepad',
            'image_url': 'categories/20250719_213012_28faf2ff-4c49-432b-8090-19245e9162ba.png',
            'is_active': True,
            'display_order': 1,
            'show_in_header': True,
            'show_in_footer': True
        },
        {
            'name': 'بطاقات التسوق',
            'name_en': 'Shopping Cards',
            'description': 'بطاقات هدايا للتسوق من أشهر المتاجر العالمية',
            'icon_class': 'fas fa-shopping-cart',
            'image_url': 'categories/20250719_213044_ab362732-7d9e-423c-b58e-c01d5b80705a.png',
            'is_active': True,
            'display_order': 2,
            'show_in_header': True,
            'show_in_footer': True
        },
        {
            'name': 'بطاقات الترفيه',
            'name_en': 'Entertainment Cards',
            'description': 'بطاقات للمنصات الترفيهية مثل نتفليكس وسبوتيفاي',
            'icon_class': 'fas fa-film',
            'image_url': 'categories/20250719_213137_568b3a94-13d6-4b7f-8668-7a44102af8a5.png',
            'is_active': True,
            'display_order': 3,
            'show_in_header': True,
            'show_in_footer': True
        },
        {
            'name': 'خدمات التطبيقات',
            'name_en': 'App Services',
            'description': 'بطاقات شحن لتطبيقات الهواتف الذكية',
            'icon_class': 'fas fa-mobile-alt',
            'image_url': 'default-category.png',
            'is_active': True,
            'display_order': 4,
            'show_in_header': True,
            'show_in_footer': False
        },
        {
            'name': 'بطاقات رصيد الهاتف',
            'name_en': 'Mobile Credit Cards',
            'description': 'بطاقات شحن الرصيد لجميع شبكات الاتصال',
            'icon_class': 'fas fa-phone',
            'image_url': 'default-category.png',
            'is_active': True,
            'display_order': 5,
            'show_in_header': True,
            'show_in_footer': False
        }
    ]
    
    for cat_data in categories_data:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
            db.session.flush()  # للحصول على ID
            print(f"  ✅ تم إضافة قسم: {cat_data['name']}")

def add_subcategories():
    """إضافة الأقسام الفرعية"""
    print("📁 إضافة الأقسام الفرعية...")
    
    # جلب الأقسام الرئيسية
    gaming_cat = Category.query.filter_by(name='بطاقات الألعاب').first()
    shopping_cat = Category.query.filter_by(name='بطاقات التسوق').first()
    entertainment_cat = Category.query.filter_by(name='بطاقات الترفيه').first()
    
    subcategories_data = [
        # أقسام فرعية للألعاب
        {
            'name': 'PUBG Mobile',
            'name_en': 'PUBG Mobile',
            'description': 'بطاقات شحن UC لـ PUBG Mobile',
            'category_id': gaming_cat.id if gaming_cat else 1,
            'icon_class': 'fas fa-crosshairs',
            'image_url': '',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'Free Fire',
            'name_en': 'Free Fire',
            'description': 'بطاقات شحن الماس لـ Free Fire',
            'category_id': gaming_cat.id if gaming_cat else 1,
            'icon_class': 'fas fa-fire',
            'image_url': '',
            'is_active': True,
            'display_order': 2
        },
        {
            'name': 'Fortnite',
            'name_en': 'Fortnite',
            'description': 'بطاقات V-Bucks لـ Fortnite',
            'category_id': gaming_cat.id if gaming_cat else 1,
            'icon_class': 'fas fa-hammer',
            'image_url': '',
            'is_active': True,
            'display_order': 3
        },
        # أقسام فرعية للتسوق
        {
            'name': 'Amazon',
            'name_en': 'Amazon',
            'description': 'بطاقات هدايا أمازون',
            'category_id': shopping_cat.id if shopping_cat else 2,
            'icon_class': 'fab fa-amazon',
            'image_url': '',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'iTunes',
            'name_en': 'iTunes',
            'description': 'بطاقات iTunes و App Store',
            'category_id': shopping_cat.id if shopping_cat else 2,
            'icon_class': 'fab fa-apple',
            'image_url': '',
            'is_active': True,
            'display_order': 2
        },
        # أقسام فرعية للترفيه
        {
            'name': 'Netflix',
            'name_en': 'Netflix',
            'description': 'بطاقات اشتراك نتفليكس',
            'category_id': entertainment_cat.id if entertainment_cat else 3,
            'icon_class': 'fas fa-tv',
            'image_url': '',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'Spotify',
            'name_en': 'Spotify',
            'description': 'بطاقات اشتراك سبوتيفاي',
            'category_id': entertainment_cat.id if entertainment_cat else 3,
            'icon_class': 'fab fa-spotify',
            'image_url': '',
            'is_active': True,
            'display_order': 2
        }
    ]
    
    for subcat_data in subcategories_data:
        existing = Subcategory.query.filter_by(name=subcat_data['name']).first()
        if not existing:
            subcategory = Subcategory(**subcat_data)
            db.session.add(subcategory)
            print(f"  ✅ تم إضافة قسم فرعي: {subcat_data['name']}")

def add_products():
    """إضافة المنتجات"""
    print("🎁 إضافة المنتجات...")
    
    # جلب الأقسام والأقسام الفرعية
    gaming_cat = Category.query.filter_by(name='بطاقات الألعاب').first()
    shopping_cat = Category.query.filter_by(name='بطاقات التسوق').first()
    entertainment_cat = Category.query.filter_by(name='بطاقات الترفيه').first()
    
    pubg_subcat = Subcategory.query.filter_by(name='PUBG Mobile').first()
    freefire_subcat = Subcategory.query.filter_by(name='Free Fire').first()
    amazon_subcat = Subcategory.query.filter_by(name='Amazon').first()
    netflix_subcat = Subcategory.query.filter_by(name='Netflix').first()
    
    products_data = [
        # منتجات PUBG
        {
            'name': 'PUBG Mobile - 60 UC',
            'name_en': 'PUBG Mobile - 60 UC',
            'description': 'بطاقة شحن 60 UC لـ PUBG Mobile - صالحة لجميع المناطق',
            'detailed_description': 'بطاقة شحن Unknown Cash (UC) لـ PUBG Mobile بقيمة 60 UC. يمكن استخدامها لشراء الأسلحة والملابس والعناصر الأخرى في اللعبة.',
            'regular_price': Decimal('15.00'),
            'sale_price': Decimal('12.00'),
            'category_id': gaming_cat.id if gaming_cat else 1,
            'subcategory_id': pubg_subcat.id if pubg_subcat else 1,
            'category': 'gaming',
            'image_url': '20250719_175934_WhatsApp_Image_2025-07-16_at_05.11.11_bcf4b990.jpg',
            'is_active': True,
            'stock_quantity': 100,
            'digital_delivery': True,
            'instant_delivery': True,
            'is_featured': True
        },
        {
            'name': 'PUBG Mobile - 300 UC',
            'name_en': 'PUBG Mobile - 300 UC',
            'description': 'بطاقة شحن 300 UC لـ PUBG Mobile - أفضل قيمة',
            'detailed_description': 'بطاقة شحن Unknown Cash (UC) لـ PUBG Mobile بقيمة 300 UC. قيمة ممتازة للحصول على المزيد من العملات في اللعبة.',
            'regular_price': Decimal('75.00'),
            'sale_price': Decimal('65.00'),
            'category_id': gaming_cat.id if gaming_cat else 1,
            'subcategory_id': pubg_subcat.id if pubg_subcat else 1,
            'category': 'gaming',
            'image_url': '20250719_202617_download.png',
            'is_active': True,
            'stock_quantity': 50,
            'digital_delivery': True,
            'instant_delivery': True,
            'is_featured': True
        },
        # منتجات Free Fire
        {
            'name': 'Free Fire - 100 Diamonds',
            'name_en': 'Free Fire - 100 Diamonds',
            'description': 'بطاقة شحن 100 ماسة لـ Free Fire',
            'detailed_description': 'بطاقة شحن الماس لـ Free Fire بقيمة 100 ماسة. يمكن استخدامها لشراء الشخصيات والأسلحة والإكسسوارات.',
            'regular_price': Decimal('20.00'),
            'sale_price': Decimal('18.00'),
            'category_id': gaming_cat.id if gaming_cat else 1,
            'subcategory_id': freefire_subcat.id if freefire_subcat else 2,
            'category': 'gaming',
            'image_url': '20250719_202648_WhatsApp_Image_2025-07-16_at_05.11.10_9463e9e5.jpg',
            'is_active': True,
            'stock_quantity': 75,
            'digital_delivery': True,
            'instant_delivery': True,
            'is_featured': False
        },
        # منتجات Amazon
        {
            'name': 'Amazon Gift Card - $25',
            'name_en': 'Amazon Gift Card - $25',
            'description': 'بطاقة هدايا أمازون بقيمة 25 دولار',
            'detailed_description': 'بطاقة هدايا أمازون الأمريكي بقيمة 25 دولار أمريكي. يمكن استخدامها لشراء أي منتج من أمازون.',
            'regular_price': Decimal('100.00'),
            'sale_price': Decimal('95.00'),
            'category_id': shopping_cat.id if shopping_cat else 2,
            'subcategory_id': amazon_subcat.id if amazon_subcat else 4,
            'category': 'shopping',
            'image_url': '20250719_202716_game1.jpeg',
            'is_active': True,
            'stock_quantity': 30,
            'digital_delivery': True,
            'instant_delivery': True,
            'is_featured': True
        },
        # منتجات Netflix
        {
            'name': 'Netflix - شهر واحد',
            'name_en': 'Netflix - 1 Month',
            'description': 'اشتراك نتفليكس لمدة شهر واحد',
            'detailed_description': 'بطاقة اشتراك نتفليكس لمدة شهر واحد. تتيح لك مشاهدة جميع الأفلام والمسلسلات على منصة نتفليكس.',
            'regular_price': Decimal('50.00'),
            'sale_price': Decimal('45.00'),
            'category_id': entertainment_cat.id if entertainment_cat else 3,
            'subcategory_id': netflix_subcat.id if netflix_subcat else 6,
            'category': 'entertainment',
            'image_url': '20250719_205932_ab362732-7d9e-423c-b58e-c01d5b80705a.png',
            'is_active': True,
            'stock_quantity': 40,
            'digital_delivery': True,
            'instant_delivery': False,
            'is_featured': True
        },
        # منتجات إضافية
        {
            'name': 'iTunes Gift Card - $10',
            'name_en': 'iTunes Gift Card - $10',
            'description': 'بطاقة هدايا iTunes بقيمة 10 دولار',
            'detailed_description': 'بطاقة هدايا iTunes و App Store بقيمة 10 دولار أمريكي. يمكن استخدامها لشراء التطبيقات والألعاب والموسيقى.',
            'regular_price': Decimal('40.00'),
            'sale_price': Decimal('38.00'),
            'category_id': shopping_cat.id if shopping_cat else 2,
            'subcategory_id': amazon_subcat.id if amazon_subcat else 4,
            'category': 'apps',
            'image_url': '20250719_210117_28faf2ff-4c49-432b-8090-19245e9162ba.png',
            'is_active': True,
            'stock_quantity': 60,
            'digital_delivery': True,
            'instant_delivery': True,
            'is_featured': False
        }
    ]
    
    for prod_data in products_data:
        existing = Product.query.filter_by(name=prod_data['name']).first()
        if not existing:
            product = Product(**prod_data)
            db.session.add(product)
            print(f"  ✅ تم إضافة منتج: {prod_data['name']}")

def add_main_offers():
    """إضافة العروض الرئيسية"""
    print("🔥 إضافة العروض الرئيسية...")
    
    offers_data = [
        {
            'title': 'عرض العودة للمدارس',
            'title_en': 'Back to School Offer',
            'description': 'خصم 25% على جميع بطاقات الألعاب',
            'image_url': '20250719_165231_game4.jpeg',
            'link_url': '/category/1/gaming-cards',
            'button_text': 'اشتري الآن',
            'is_active': True,
            'display_order': 1,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30)
        },
        {
            'title': 'عرض الصيف الحار',
            'title_en': 'Hot Summer Deal',
            'description': 'بطاقات هدايا مجانية مع كل طلب فوق 200 ريال',
            'image_url': '20250719_165402_game3.jpeg',
            'link_url': '/categories',
            'button_text': 'تسوق الآن',
            'is_active': True,
            'display_order': 2,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=45)
        },
        {
            'title': 'عرض اللاعبين المحترفين',
            'title_en': 'Pro Gamers Deal',
            'description': 'أسعار خاصة للاعبين - خصم يصل إلى 40%',
            'image_url': '20250719_165453_game2.jpeg',
            'link_url': '/category/1',
            'button_text': 'احصل على العرض',
            'is_active': True,
            'display_order': 3,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=15)
        }
    ]
    
    for offer_data in offers_data:
        existing = MainOffer.query.filter_by(title=offer_data['title']).first()
        if not existing:
            offer = MainOffer(**offer_data)
            db.session.add(offer)
            print(f"  ✅ تم إضافة عرض: {offer_data['title']}")

def add_gift_card_sections():
    """إضافة أقسام بطاقات الهدايا"""
    print("🎉 إضافة أقسام بطاقات الهدايا...")
    
    sections_data = [
        {
            'title': 'بطاقات الألعاب الشهيرة',
            'title_en': 'Popular Gaming Cards',
            'description': 'اشحن حسابك في أشهر الألعاب',
            'image_url': '20250717_141530_f4127485-0606-45bf-9770-7716f46b5d01.png',
            'link_url': '/category/1/gaming-cards',
            'button_text': 'تصفح الألعاب',
            'is_active': True,
            'display_order': 1
        },
        {
            'title': 'بطاقات التسوق العالمية',
            'title_en': 'Global Shopping Cards',
            'description': 'تسوق من أشهر المتاجر العالمية',
            'image_url': '20250717_153620_game1.jpeg',
            'link_url': '/category/2/shopping-cards',
            'button_text': 'ابدأ التسوق',
            'is_active': True,
            'display_order': 2
        },
        {
            'title': 'اشتراكات المنصات الترفيهية',
            'title_en': 'Entertainment Subscriptions',
            'description': 'نتفليكس، سبوتيفاي، وأكثر',
            'image_url': '20250719_230954_0bc1a40f-dced-4d7a-91ec-efff1f2e55c0.png',
            'link_url': '/category/3/entertainment-cards',
            'button_text': 'اشترك الآن',
            'is_active': True,
            'display_order': 3
        }
    ]
    
    for section_data in sections_data:
        existing = GiftCardSection.query.filter_by(title=section_data['title']).first()
        if not existing:
            section = GiftCardSection(**section_data)
            db.session.add(section)
            print(f"  ✅ تم إضافة قسم: {section_data['title']}")

def add_other_brands():
    """إضافة العلامات التجارية الأخرى"""
    print("🏷️ إضافة العلامات التجارية...")
    
    brands_data = [
        {
            'name': 'Steam',
            'name_en': 'Steam',
            'description': 'منصة الألعاب الأشهر على الكمبيوتر',
            'logo_url': 'payment_2_1_1747654210.jpeg',
            'image_url': 'payment_2_1_1747654210.jpeg',
            'link_url': 'https://store.steampowered.com',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'PlayStation Store',
            'name_en': 'PlayStation Store',
            'description': 'متجر ألعاب البلايستيشن الرسمي',
            'logo_url': 'download.png',
            'image_url': 'download.png',
            'link_url': 'https://store.playstation.com',
            'is_active': True,
            'display_order': 2
        },
        {
            'name': 'Xbox Live',
            'name_en': 'Xbox Live',
            'description': 'خدمات إكس بوكس لايف وGame Pass',
            'logo_url': 'car-service.jpg',
            'image_url': 'car-service.jpg',
            'link_url': 'https://www.xbox.com',
            'is_active': True,
            'display_order': 3
        }
    ]
    
    for brand_data in brands_data:
        existing = OtherBrand.query.filter_by(name=brand_data['name']).first()
        if not existing:
            brand = OtherBrand(**brand_data)
            db.session.add(brand)
            print(f"  ✅ تم إضافة علامة تجارية: {brand_data['name']}")

def add_product_codes():
    """إضافة أكواد المنتجات"""
    print("🔑 إضافة أكواد المنتجات...")
    
    # جلب المنتجات المضافة
    products = Product.query.all()
    
    code_templates = [
        'GIFT-{:04d}-{:04d}',
        'CARD-{:04d}-{:04d}', 
        'CODE-{:04d}-{:04d}',
        'ESGT-{:04d}-{:04d}'
    ]
    
    for product in products[:3]:  # إضافة أكواد لأول 3 منتجات فقط
        for i in range(5):  # 5 أكواد لكل منتج
            code_data = {
                'product_id': product.id,
                'code': code_templates[i % len(code_templates)].format(product.id, i + 1),
                'is_used': False
            }
            
            code = ProductCode(**code_data)
            db.session.add(code)
        
        db.session.commit()  # حفظ أكواد كل منتج
        print(f"  ✅ تم إضافة 5 أكواد لمنتج: {product.name}")

def add_sample_users():
    """إضافة مستخدمين تجريبيين"""
    print("👥 إضافة مستخدمين تجريبيين...")
    
    from werkzeug.security import generate_password_hash
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@esgift.com',
            'password_hash': generate_password_hash('admin123'),
            'full_name': 'مدير النظام',
            'phone': '+966501234567',
            'is_admin': True,
            'is_verified': True,
            'customer_type': 'premium',
            'kyc_status': 'approved',
            'created_at': datetime.now()
        },
        {
            'username': 'customer1',
            'email': 'customer1@example.com',
            'password_hash': generate_password_hash('customer123'),
            'full_name': 'أحمد محمد',
            'phone': '+966507654321',
            'is_admin': False,
            'is_verified': True,
            'customer_type': 'regular',
            'kyc_status': 'approved',
            'created_at': datetime.now()
        },
        {
            'username': 'vip_customer',
            'email': 'vip@example.com',
            'password_hash': generate_password_hash('vip123'),
            'full_name': 'سارة أحمد',
            'phone': '+966509876543',
            'is_admin': False,
            'is_verified': True,
            'customer_type': 'vip',
            'kyc_status': 'approved',
            'created_at': datetime.now()
        }
    ]
    
    for user_data in users_data:
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User(**user_data)
            db.session.add(user)
            print(f"  ✅ تم إضافة مستخدم: {user_data['username']} ({user_data['email']})")

def add_static_pages():
    """إضافة الصفحات الثابتة"""
    print("📄 إضافة الصفحات الثابتة...")
    
    pages_data = [
        {
            'title': 'سياسة الخصوصية',
            'slug': 'privacy-policy',
            'content': '''
            <h2>سياسة الخصوصية</h2>
            <p>نحن في ES-Gift نحترم خصوصيتك ونلتزم بحماية معلوماتك الشخصية.</p>
            
            <h3>المعلومات التي نجمعها</h3>
            <p>نجمع المعلومات التالية:</p>
            <ul>
                <li>معلومات الحساب (الاسم، البريد الإلكتروني)</li>
                <li>معلومات الدفع</li>
                <li>سجل التصفح والمشتريات</li>
            </ul>
            
            <h3>كيف نستخدم معلوماتك</h3>
            <p>نستخدم معلوماتك لتوفير خدماتنا وتحسين تجربتك.</p>
            ''',
            'meta_description': 'سياسة الخصوصية لمتجر ES-Gift - حماية بياناتك أولويتنا',
            'meta_keywords': 'سياسة الخصوصية, حماية البيانات, ES-Gift',
            'is_active': True,
            'show_in_header': False,
            'show_in_footer': True,
            'display_order': 1
        },
        {
            'title': 'الشروط والأحكام',
            'slug': 'terms-of-service',
            'content': '''
            <h2>الشروط والأحكام</h2>
            <p>مرحباً بك في ES-Gift. باستخدام موقعنا، فإنك توافق على هذه الشروط.</p>
            
            <h3>شروط الاستخدام</h3>
            <ul>
                <li>يجب أن تكون أكبر من 18 عاماً لاستخدام الموقع</li>
                <li>يحظر استخدام الموقع لأغراض غير قانونية</li>
                <li>نحتفظ بالحق في إنهاء حسابك في أي وقت</li>
            </ul>
            
            <h3>سياسة الاسترداد</h3>
            <p>البطاقات الرقمية غير قابلة للاسترداد بعد الشراء.</p>
            ''',
            'meta_description': 'الشروط والأحكام الخاصة بمتجر ES-Gift للبطاقات الرقمية',
            'meta_keywords': 'شروط الاستخدام, أحكام, ES-Gift',
            'is_active': True,
            'show_in_header': False,
            'show_in_footer': True,
            'display_order': 2
        },
        {
            'title': 'من نحن',
            'slug': 'about-us',
            'content': '''
            <h2>من نحن</h2>
            <p>ES-Gift هو متجرك الموثوق للبطاقات الرقمية والهدايا الإلكترونية.</p>
            
            <h3>رؤيتنا</h3>
            <p>أن نكون المنصة الرائدة في المنطقة لبيع البطاقات الرقمية.</p>
            
            <h3>مهمتنا</h3>
            <p>توفير أفضل تجربة شراء للبطاقات الرقمية بأسعار تنافسية وخدمة عملاء ممتازة.</p>
            
            <h3>لماذا نحن؟</h3>
            <ul>
                <li>أسعار تنافسية</li>
                <li>تسليم فوري</li>
                <li>دعم فني 24/7</li>
                <li>ضمان الجودة</li>
            </ul>
            ''',
            'meta_description': 'تعرف على ES-Gift - متجرك الموثوق للبطاقات الرقمية في المنطقة',
            'meta_keywords': 'من نحن, ES-Gift, بطاقات رقمية, متجر إلكتروني',
            'is_active': True,
            'show_in_header': True,
            'show_in_footer': True,
            'display_order': 3
        },
        {
            'title': 'اتصل بنا',
            'slug': 'contact-us',
            'content': '''
            <h2>اتصل بنا</h2>
            <p>نحن هنا لمساعدتك! لا تتردد في التواصل معنا.</p>
            
            <h3>معلومات التواصل</h3>
            <div class="contact-info">
                <p><strong>البريد الإلكتروني:</strong> support@esgift.com</p>
                <p><strong>الهاتف:</strong> +966 11 234 5678</p>
                <p><strong>العنوان:</strong> الرياض، المملكة العربية السعودية</p>
                <p><strong>ساعات العمل:</strong> الأحد - الخميس: 9:00 ص - 6:00 م</p>
            </div>
            
            <h3>نموذج التواصل</h3>
            <form class="contact-form">
                <div class="form-group">
                    <label for="name">الاسم:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="email">البريد الإلكتروني:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="message">الرسالة:</label>
                    <textarea id="message" name="message" rows="5" required></textarea>
                </div>
                <button type="submit">إرسال الرسالة</button>
            </form>
            ''',
            'meta_description': 'تواصل مع فريق دعم ES-Gift - نحن هنا لمساعدتك',
            'meta_keywords': 'اتصل بنا, دعم فني, ES-Gift, خدمة عملاء',
            'is_active': True,
            'show_in_header': True,
            'show_in_footer': True,
            'display_order': 4
        }
    ]
    
    for page_data in pages_data:
        existing = StaticPage.query.filter_by(slug=page_data['slug']).first()
        if not existing:
            page = StaticPage(**page_data)
            db.session.add(page)
            print(f"  ✅ تم إضافة صفحة: {page_data['title']}")

def add_sample_articles():
    """إضافة مقالات تجريبية"""
    print("📰 إضافة المقالات التجريبية...")
    
    articles_data = [
        {
            'title': 'أفضل الألعاب المجانية لعام 2025',
            'content': '''
            <p>مع تطور صناعة الألعاب، أصبحت هناك العديد من الألعاب المجانية الرائعة التي يمكن لعبها دون دفع أي رسوم. في هذا المقال، سنستعرض أفضل الألعاب المجانية المتاحة في عام 2025.</p>
            
            <h3>1. PUBG Mobile</h3>
            <p>لعبة الباتل رويال الأشهر على الهواتف الذكية. تتميز بجرافيك عالي الجودة ونظام لعب مثير يجمع بين الاستراتيجية والمهارة.</p>
            
            <h3>2. Free Fire</h3>
            <p>لعبة أخرى من ألعاب الباتل رويال التي حققت شعبية كبيرة، خاصة في منطقة الشرق الأوسط. تتميز بماتشات سريعة وشخصيات متنوعة.</p>
            
            <h3>3. Fortnite</h3>
            <p>اللعبة التي غيرت عالم الباتل رويال بنظام البناء المبتكر. متاحة على جميع المنصات مع إمكانية اللعب المتقاطع.</p>
            
            <h3>نصائح للاعبين الجدد</h3>
            <ul>
                <li>ابدأ بالتدريب قبل الدخول في المعارك الحقيقية</li>
                <li>تعلم خريطة اللعبة جيداً</li>
                <li>اختر الأسلحة المناسبة لأسلوب لعبك</li>
                <li>العب مع فريق منسق للحصول على أفضل النتائج</li>
            </ul>
            
            <p>هذه الألعاب متاحة مجاناً، لكن يمكنك تحسين تجربة اللعب من خلال شراء بطاقات الشحن المتوفرة في متجرنا!</p>
            ''',
            'author': 'فريق ES-Gift',
            'image_url': 'articles/gaming-2025.jpg',
            'is_published': True,
            'created_at': datetime.now() - timedelta(days=5)
        },
        {
            'title': 'كيفية شحن حسابك في PUBG Mobile بأمان',
            'content': '''
            <p>شحن حساب PUBG Mobile يتطلب الحذر والتعامل مع مصادر موثوقة لضمان أمان حسابك. في هذا الدليل، سنوضح لك الطريقة الصحيحة والآمنة للشحن.</p>
            
            <h3>الطريقة الآمنة للشحن</h3>
            <ol>
                <li><strong>اختر متجراً موثوقاً:</strong> تأكد من أن المتجر الذي تشتري منه معتمد وله تقييمات إيجابية</li>
                <li><strong>استخدم معلومات حسابك الصحيحة:</strong> تأكد من إدخال Player ID الصحيح</li>
                <li><strong>احتفظ بإيصال الشراء:</strong> احفظ كل المعلومات الخاصة بعملية الشراء</li>
                <li><strong>تحقق من وصول UC فوراً:</strong> بعد الشراء، تحقق من حسابك للتأكد من وصول العملات</li>
            </ol>
            
            <h3>أنواع بطاقات PUBG المتاحة</h3>
            <ul>
                <li>بطاقة 60 UC - مثالية للمشتريات الصغيرة</li>
                <li>بطاقة 300 UC - أفضل قيمة للمال</li>
                <li>بطاقة 600 UC - للاعبين النشطين</li>
                <li>بطاقة 1500 UC - للحصول على أفضل العروض</li>
            </ul>
            
            <h3>أخطاء يجب تجنبها</h3>
            <p><strong>لا تشارك معلومات حسابك:</strong> لا تعطِ كلمة مرور حسابك لأي شخص أو موقع.</p>
            <p><strong>تجنب المواقع المشبوهة:</strong> ابتعد عن المواقع التي تعد بـ UC مجاني أو بأسعار منخفضة جداً.</p>
            <p><strong>لا تستخدم برامج الهاك:</strong> استخدام البرامج المحظورة قد يؤدي إلى حظر حسابك نهائياً.</p>
            
            <p>في متجر ES-Gift، نضمن لك شحناً آمناً وفورياً لحسابك في PUBG Mobile بأفضل الأسعار!</p>
            ''',
            'author': 'أحمد الخبير التقني',
            'image_url': 'articles/pubg-guide.jpg',
            'is_published': True,
            'created_at': datetime.now() - timedelta(days=3)
        },
        {
            'title': 'مقارنة بين أشهر منصات الألعاب الرقمية',
            'content': '''
            <p>مع تنوع منصات الألعاب الرقمية، قد يجد اللاعبون صعوبة في اختيار المنصة المناسبة لهم. في هذا المقال، سنقارن بين أشهر المنصات المتاحة حالياً.</p>
            
            <h3>Steam - ملك منصات الكمبيوتر</h3>
            <p><strong>المميزات:</strong></p>
            <ul>
                <li>أكبر مكتبة ألعاب في العالم</li>
                <li>عروض وخصومات مستمرة</li>
                <li>نظام مراجعات موثوق من المجتمع</li>
                <li>دعم للمودات والمحتوى الإضافي</li>
            </ul>
            <p><strong>العيوب:</strong> يتطلب كمبيوتر قوي للألعاب الحديثة</p>
            
            <h3>PlayStation Store - تجربة وحش الألعاب</h3>
            <p><strong>المميزات:</strong></p>
            <ul>
                <li>ألعاب حصرية مميزة</li>
                <li>جودة عالية في الجرافيك والصوت</li>
                <li>خدمة PlayStation Plus ممتازة</li>
                <li>تجربة لعب سلسة ومتطورة</li>
            </ul>
            <p><strong>العيوب:</strong> أسعار الألعاب قد تكون مرتفعة</p>
            
            <h3>Xbox Game Pass - أفضل قيمة مقابل المال</h3>
            <p><strong>المميزات:</strong></p>
            <ul>
                <li>مكتبة ضخمة مقابل اشتراك شهري</li>
                <li>ألعاب جديدة تُضاف باستمرار</li>
                <li>متاح على الكمبيوتر والكونسول</li>
                <li>خدمة Cloud Gaming مبتكرة</li>
            </ul>
            
            <h3>المنصات المحمولة - الألعاب في كل مكان</h3>
            <p>الهواتف الذكية أصبحت منصة ألعاب قوية مع عناوين مثل:</p>
            <ul>
                <li>PUBG Mobile</li>
                <li>Call of Duty Mobile</li>
                <li>Free Fire</li>
                <li>Mobile Legends</li>
            </ul>
            
            <h3>الخلاصة</h3>
            <p>كل منصة لها مميزاتها الخاصة، والاختيار يعتمد على:</p>
            <ul>
                <li>نوع الألعاب التي تفضلها</li>
                <li>الميزانية المتاحة</li>
                <li>الوقت المتاح للعب</li>
                <li>المعدات المتوفرة لديك</li>
            </ul>
            
            <p>مهما كانت منصتك المفضلة، في ES-Gift ستجد بطاقات الشحن المناسبة لجميع المنصات بأفضل الأسعار!</p>
            ''',
            'author': 'سارة محللة الألعاب',
            'image_url': 'articles/gaming-platforms.jpg',
            'is_published': True,
            'created_at': datetime.now() - timedelta(days=7)
        },
        {
            'title': 'نصائح للحصول على أفضل الصفقات في متاجر الألعاب',
            'content': '''
            <p>التسوق الذكي في متاجر الألعاب يمكن أن يوفر عليك الكثير من المال. إليك أهم النصائح للحصول على أفضل الصفقات والعروض.</p>
            
            <h3>أفضل أوقات التسوق</h3>
            <h4>1. مواسم التخفيضات الكبرى</h4>
            <ul>
                <li><strong>الجمعة البيضاء:</strong> خصومات تصل إلى 75%</li>
                <li><strong>تخفيضات الصيف:</strong> عروض ممتازة على الألعاب القديمة</li>
                <li><strong>عروض العودة للمدارس:</strong> خصومات خاصة للطلاب</li>
                <li><strong>عروض نهاية العام:</strong> تصفية المخزون بأسعار مخفضة</li>
            </ul>
            
            <h4>2. العروض الأسبوعية</h4>
            <p>معظم المتاجر تطلق عروضاً أسبوعية يوم الثلاثاء أو الأربعاء. تابع هذه العروض للحصول على صفقات سريعة.</p>
            
            <h3>استراتيجيات التسوق الذكي</h3>
            <h4>قوائم الأمنيات</h4>
            <p>أضف الألعاب التي تريدها إلى قائمة الأمنيات وانتظر تخفيض سعرها. معظم المنصات ترسل تنبيهات عند تخفيض أسعار الألعاب في قائمتك.</p>
            
            <h4>مقارنة الأسعار</h4>
            <p>قارن الأسعار بين المنصات المختلفة:</p>
            <ul>
                <li>Steam vs Epic Games Store</li>
                <li>PlayStation Store vs بائعي المفاتيح المعتمدين</li>
                <li>Xbox Store vs Game Pass</li>
            </ul>
            
            <h4>الإشتراكات الشهرية</h4>
            <p>خدمات مثل Game Pass و PlayStation Plus توفر قيمة ممتازة مقابل المال، خاصة إذا كنت تلعب ألعاباً متنوعة.</p>
            
            <h3>تجنب هذه الأخطاء</h3>
            <p><strong>الشراء الفوري:</strong> لا تشترِ لعبة بمجرد إطلاقها، انتظر بضعة أشهر لتنخفض الأسعار.</p>
            <p><strong>إهمال المراجعات:</strong> اقرأ مراجعات اللاعبين قبل الشراء لتجنب الألعاب المخيبة للآمال.</p>
            <p><strong>شراء المحتوى الإضافي المكلف:</strong> فكر جيداً قبل شراء الـ DLC، هل يستحق السعر فعلاً؟</p>
            
            <h3>بطاقات الشحن - استثمار ذكي</h3>
            <p>شراء بطاقات الشحن عندما تكون بخصم يمكن أن يوفر عليك المال على المدى الطويل:</p>
            <ul>
                <li>اشترِ بطاقات Steam أثناء العروض</li>
                <li>استفد من عروض بطاقات PlayStation</li>
                <li>اشترك في Game Pass عند وجود عروض خاصة</li>
            </ul>
            
            <p>في ES-Gift، نقدم دائماً أفضل الأسعار على بطاقات الشحن مع عروض وخصومات مستمرة!</p>
            ''',
            'author': 'محمد خبير التسوق الإلكتروني',
            'image_url': 'articles/gaming-deals.jpg',
            'is_published': True,
            'created_at': datetime.now() - timedelta(days=1)
        },
        {
            'title': 'مستقبل الألعاب: ما نتوقعه في السنوات القادمة',
            'content': '''
            <p>صناعة الألعاب تتطور بسرعة مذهلة، وكل عام نرى ابتكارات جديدة تغير طريقة لعبنا وتفاعلنا مع الألعاب. دعونا نستكشف ما ينتظرنا في المستقبل القريب.</p>
            
            <h3>الواقع الافتراضي والمعزز</h3>
            <h4>VR Gaming - الواقع الافتراضي</h4>
            <p>تقنية الواقع الافتراضي تتحسن باستمرار مع:</p>
            <ul>
                <li>نظارات أخف وزناً وأكثر راحة</li>
                <li>دقة عرض أعلى وزمن استجابة أقل</li>
                <li>ألعاب أكثر تفاعلية وواقعية</li>
                <li>أسعار أكثر في متناول الجميع</li>
            </ul>
            
            <h4>AR Gaming - الواقع المعزز</h4>
            <p>بعد نجاح Pokemon GO، نرى المزيد من الألعاب التي تدمج العالم الحقيقي مع العالم الافتراضي.</p>
            
            <h3>الذكاء الاصطناعي في الألعاب</h3>
            <p>الذكاء الاصطناعي سيغير الألعاب من خلال:</p>
            <ul>
                <li><strong>NPCs أذكى:</strong> شخصيات غير لاعبة تتفاعل بشكل طبيعي أكثر</li>
                <li><strong>قصص متكيفة:</strong> قصص تتغير حسب أسلوب لعبك</li>
                <li><strong>صعوبة ديناميكية:</strong> اللعبة تتكيف مع مستوى مهارتك</li>
                <li><strong>إنتاج محتوى:</strong> إنشاء مستويات ومهام جديدة تلقائياً</li>
            </ul>
            
            <h3>Cloud Gaming - الألعاب السحابية</h3>
            <p>مستقبل الألعاب قد يكون في السحابة:</p>
            <ul>
                <li>لعب ألعاب عالية الجودة على أي جهاز</li>
                <li>لا حاجة لتحديث الأجهزة باستمرار</li>
                <li>وصول فوري للألعاب دون تحميل</li>
                <li>مكتبات ألعاب ضخمة بإشتراك شهري</li>
            </ul>
            
            <h3>البلوك تشين والـ NFTs في الألعاب</h3>
            <p>تقنية البلوك تشين قد تجلب:</p>
            <ul>
                <li>ملكية حقيقية للعناصر الرقمية</li>
                <li>تداول العناصر بين الألعاب المختلفة</li>
                <li>اقتصاد افتراضي أكثر واقعية</li>
                <li>مكافآت مالية حقيقية للاعبين المهرة</li>
            </ul>
            
            <h3>الألعاب الاجتماعية والـ Metaverse</h3>
            <p>المستقبل يتجه نحو:</p>
            <ul>
                <li>عوالم افتراضية دائمة ومترابطة</li>
                <li>أنشطة اجتماعية أكثر تنوعاً في الألعاب</li>
                <li>مؤتمرات وفعاليات افتراضية داخل الألعاب</li>
                <li>التسوق والعمل في البيئات الافتراضية</li>
            </ul>
            
            <h3>التكنولوجيا الجديدة</h3>
            <h4>معالجات أقوى</h4>
            <p>الجيل الجديد من المعالجات سيمكن من:</p>
            <ul>
                <li>فيزيكس أكثر واقعية</li>
                <li>عوالم أكبر وأكثر تفصيلاً</li>
                <li>ذكاء اصطناعي أكثر تطوراً</li>
                <li>تقديم أفضل للرسوميات</li>
            </ul>
            
            <h4>شاشات أفضل</h4>
            <ul>
                <li>دقة 8K تصبح المعيار</li>
                <li>معدلات تحديث أعلى (240Hz+)</li>
                <li>تقنية HDR محسنة</li>
                <li>شاشات قابلة للطي والالتفاف</li>
            </ul>
            
            <h3>التحديات المستقبلية</h3>
            <p><strong>الأمان والخصوصية:</strong> مع تزايد الاتصال والبيانات الشخصية في الألعاب.</p>
            <p><strong>الإدمان:</strong> الحاجة لتوازن صحي بين الألعاب والحياة الحقيقية.</p>
            <p><strong>التكلفة:</strong> جعل التقنيات الجديدة في متناول جميع اللاعبين.</p>
            
            <h3>الخلاصة</h3>
            <p>مستقبل الألعاب مثير ومليء بالإمكانيات. التقنيات الجديدة ستجعل الألعاب أكثر واقعية وتفاعلية وإثارة من أي وقت مضى.</p>
            
            <p>مهما كان مستقبل الألعاب، ES-Gift ستكون هنا لتوفر لك أفضل بطاقات الشحن والخدمات للاستمتاع بتجربة الألعاب المثالية!</p>
            ''',
            'author': 'د. ليلى الباحثة التقنية',
            'image_url': 'articles/future-gaming.jpg',
            'is_published': True,
            'created_at': datetime.now() - timedelta(days=10)
        },
        {
            'title': 'مسودة: دليل شامل لأفضل إعدادات الألعاب',
            'content': '''
            <p>هذا مقال تحت الإعداد حول أفضل إعدادات الألعاب للحصول على أفضل أداء وجودة رسوميات...</p>
            
            <h3>إعدادات الرسوميات</h3>
            <p>المحتوى قيد الإعداد...</p>
            
            <h3>إعدادات الصوت</h3>
            <p>المحتوى قيد الإعداد...</p>
            ''',
            'author': 'فريق التحرير',
            'image_url': 'articles/gaming-settings.jpg',
            'is_published': False,  # مسودة غير منشورة
            'created_at': datetime.now() - timedelta(hours=2)
        }
    ]
    
    for article_data in articles_data:
        existing = Article.query.filter_by(title=article_data['title']).first()
        if not existing:
            article = Article(**article_data)
            db.session.add(article)
            status = "منشور" if article_data['is_published'] else "مسودة"
            print(f"  ✅ تم إضافة مقال ({status}): {article_data['title']}")
        else:
            print(f"  🔄 المقال موجود مسبقاً: {article_data['title']}")

if __name__ == '__main__':
    print("🎯 مرحباً بك في نظام إضافة البيانات التجريبية لـ ES-Gift")
    print("=" * 60)
    
    confirm = input("هل تريد إضافة البيانات التجريبية؟ (y/n): ")
    if confirm.lower() in ['y', 'yes', 'نعم']:
        init_sample_data()
        print("\n" + "=" * 60)
        print("🎉 تم الانتهاء من إضافة جميع البيانات التجريبية!")
        print("يمكنك الآن تشغيل التطبيق ومعاينة النتائج.")
    else:
        print("تم إلغاء العملية.")
