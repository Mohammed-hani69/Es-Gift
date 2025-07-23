# -*- coding: utf-8 -*-
"""
إدارة الصور والملفات لنظام ES-Gift
==================================

هذا الملف يحتوي على أدوات لإدارة الصور والملفات في النظام

"""

import os
import shutil
from PIL import Image
import random

def create_default_images():
    """إنشاء صور افتراضية إذا لم تكن موجودة"""
    upload_folder = "static/uploads"
    
    # إنشاء المجلدات المطلوبة
    folders = [
        "categories",
        "subcategories", 
        "gift-cards",
        "main-offers",
        "other-brands"
    ]
    
    for folder in folders:
        folder_path = os.path.join(upload_folder, folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # إنشاء صورة افتراضية إذا لم تكن موجودة
        default_image = os.path.join(folder_path, f"default-{folder.rstrip('s')}.png")
        if not os.path.exists(default_image):
            create_placeholder_image(default_image, f"Default {folder}")

def create_placeholder_image(filepath, text="Placeholder"):
    """إنشاء صورة بديلة بسيطة"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # إنشاء صورة بحجم 300x200
        img = Image.new('RGB', (300, 200), color=(73, 109, 137))
        draw = ImageDraw.Draw(img)
        
        # محاولة استخدام خط افتراضي
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # حساب موقع النص في المنتصف
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (300 - text_width) // 2
        y = (200 - text_height) // 2
        
        # رسم النص
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # حفظ الصورة
        img.save(filepath)
        print(f"✅ تم إنشاء صورة افتراضية: {filepath}")
        
    except ImportError:
        print("⚠️ PIL/Pillow غير مثبت، تم تخطي إنشاء الصور الافتراضية")
    except Exception as e:
        print(f"❌ خطأ في إنشاء الصورة {filepath}: {str(e)}")

def list_available_images():
    """عرض قائمة بالصور المتاحة"""
    upload_folder = "static/uploads"
    
    print("📸 الصور المتاحة في النظام:")
    print("=" * 50)
    
    for root, dirs, files in os.walk(upload_folder):
        if files:
            folder_name = os.path.relpath(root, upload_folder)
            if folder_name == ".":
                folder_name = "المجلد الرئيسي"
            
            print(f"\n📁 {folder_name}:")
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
            images = [f for f in files if f.lower().endswith(image_extensions)]
            
            if images:
                for img in images[:10]:  # عرض أول 10 صور فقط
                    print(f"  🖼️  {img}")
                if len(images) > 10:
                    print(f"  ... و {len(images) - 10} صورة أخرى")
            else:
                print("  📭 لا توجد صور")

def organize_images():
    """تنظيم الصور في مجلدات مناسبة"""
    upload_folder = "static/uploads"
    
    # قائمة بأنواع الملفات وأين يجب وضعها
    file_mappings = {
        'categories': ['category', 'cat', 'قسم'],
        'subcategories': ['subcategory', 'subcat', 'فرعي'],
        'gift-cards': ['gift', 'card', 'هدية', 'بطاقة'],
        'main-offers': ['offer', 'عرض', 'عروض'],
        'products': ['product', 'منتج'],
    }
    
    # جلب جميع الصور من المجلد الرئيسي
    main_folder = upload_folder
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    
    for filename in os.listdir(main_folder):
        if filename.lower().endswith(image_extensions):
            filepath = os.path.join(main_folder, filename)
            
            # تحديد المجلد المناسب بناءً على اسم الملف
            moved = False
            for folder, keywords in file_mappings.items():
                if any(keyword in filename.lower() for keyword in keywords):
                    destination_folder = os.path.join(upload_folder, folder)
                    os.makedirs(destination_folder, exist_ok=True)
                    
                    destination_path = os.path.join(destination_folder, filename)
                    if not os.path.exists(destination_path):
                        shutil.move(filepath, destination_path)
                        print(f"📦 تم نقل {filename} إلى {folder}/")
                        moved = True
                        break
            
            if not moved:
                print(f"🤷 لم يتم تحديد مجلد لـ {filename}")

if __name__ == '__main__':
    print("🎨 أدوات إدارة الصور لـ ES-Gift")
    print("=" * 40)
    
    while True:
        print("\nاختر عملية:")
        print("1. عرض الصور المتاحة")
        print("2. تنظيم الصور")
        print("3. إنشاء صور افتراضية")
        print("4. خروج")
        
        choice = input("\nاختيارك (1-4): ")
        
        if choice == '1':
            list_available_images()
        elif choice == '2':
            organize_images()
        elif choice == '3':
            create_default_images()
        elif choice == '4':
            print("👋 وداعاً!")
            break
        else:
            print("❌ اختيار غير صحيح")
