#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes for static pages management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from models import db, StaticPage

# إنشاء Blueprint للصفحات الثابتة
static_pages_bp = Blueprint('static_pages', __name__, url_prefix='/admin/static-pages')

@static_pages_bp.route('/')
@login_required
def static_pages():
    """إدارة الصفحات الثابتة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    pages = StaticPage.query.order_by(StaticPage.display_order, StaticPage.title).all()
    return render_template('admin/static_pages.html', pages=pages)

@static_pages_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_static_page():
    """إضافة صفحة ثابتة جديدة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            meta_description = request.form.get('meta_description')
            meta_keywords = request.form.get('meta_keywords')
            show_in_footer = 'show_in_footer' in request.form
            show_in_header = 'show_in_header' in request.form
            display_order = request.form.get('display_order', 0)
            
            # التحقق من البيانات المطلوبة
            if not title or not slug or not content:
                flash('العنوان والرابط والمحتوى مطلوبة', 'error')
                return render_template('admin/add_static_page.html')
            
            # التحقق من عدم تكرار الـ slug
            existing_page = StaticPage.query.filter_by(slug=slug).first()
            if existing_page:
                flash('الرابط المختصر مستخدم بالفعل', 'error')
                return render_template('admin/add_static_page.html')
            
            # إنشاء الصفحة الجديدة
            page = StaticPage(
                title=title,
                slug=slug,
                content=content,
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                show_in_footer=show_in_footer,
                show_in_header=show_in_header,
                display_order=int(display_order),
                created_by=current_user.id
            )
            
            db.session.add(page)
            db.session.commit()
            
            flash('تم إضافة الصفحة بنجاح', 'success')
            return redirect(url_for('static_pages.static_pages'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    return render_template('admin/add_static_page.html')

@static_pages_bp.route('/edit/<int:page_id>', methods=['GET', 'POST'])
@login_required
def edit_static_page(page_id):
    """تعديل صفحة ثابتة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    page = StaticPage.query.get_or_404(page_id)
    
    if request.method == 'POST':
        try:
            page.title = request.form.get('title')
            page.slug = request.form.get('slug')
            page.content = request.form.get('content')
            page.meta_description = request.form.get('meta_description')
            page.meta_keywords = request.form.get('meta_keywords')
            page.show_in_footer = 'show_in_footer' in request.form
            page.show_in_header = 'show_in_header' in request.form
            page.display_order = int(request.form.get('display_order', 0))
            page.updated_at = datetime.utcnow()
            
            # التحقق من البيانات المطلوبة
            if not page.title or not page.slug or not page.content:
                flash('العنوان والرابط والمحتوى مطلوبة', 'error')
                return render_template('admin/edit_static_page.html', page=page)
            
            # التحقق من عدم تكرار الـ slug (عدا الصفحة الحالية)
            existing_page = StaticPage.query.filter(
                StaticPage.slug == page.slug,
                StaticPage.id != page.id
            ).first()
            if existing_page:
                flash('الرابط المختصر مستخدم بالفعل', 'error')
                return render_template('admin/edit_static_page.html', page=page)
            
            db.session.commit()
            flash('تم تحديث الصفحة بنجاح', 'success')
            return redirect(url_for('static_pages.static_pages'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    return render_template('admin/edit_static_page.html', page=page)

@static_pages_bp.route('/delete/<int:page_id>', methods=['POST'])
@login_required
def delete_static_page(page_id):
    """حذف صفحة ثابتة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        page = StaticPage.query.get_or_404(page_id)
        db.session.delete(page)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف الصفحة بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@static_pages_bp.route('/toggle-status/<int:page_id>', methods=['POST'])
@login_required
def toggle_static_page_status(page_id):
    """تفعيل/إلغاء تفعيل صفحة ثابتة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        page = StaticPage.query.get_or_404(page_id)
        page.is_active = not page.is_active
        page.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'مفعلة' if page.is_active else 'معطلة'
        return jsonify({'success': True, 'message': f'الصفحة الآن {status}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@static_pages_bp.route('/init-default', methods=['POST'])
@login_required
def init_default_static_pages():
    """إنشاء الصفحات الافتراضية"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        # صفحة سياسة الخصوصية
        if not StaticPage.query.filter_by(slug='privacy-policy').first():
            privacy_policy = StaticPage(
                title='سياسة الخصوصية',
                slug='privacy-policy',
                content='''<h2>سياسة الخصوصية - Es-Gift</h2>
<p>نحن في Es-Gift نلتزم بحماية خصوصيتك وبياناتك الشخصية.</p>

<h3>المعلومات التي نجمعها:</h3>
<ul>
<li>معلومات الحساب: البريد الإلكتروني وكلمة المرور</li>
<li>معلومات الملف الشخصي: الاسم وتاريخ الميلاد</li>
<li>معلومات الطلبات والمعاملات</li>
</ul>

<h3>كيف نستخدم المعلومات:</h3>
<ul>
<li>تقديم خدماتنا وتحسينها</li>
<li>معالجة طلباتك وإتمام عمليات الشراء</li>
<li>التواصل معك بشأن حسابك أو طلباتك</li>
<li>الامتثال للمتطلبات القانونية</li>
</ul>

<h3>حماية البيانات:</h3>
<p>نستخدم أحدث تقنيات الأمان لحماية بياناتك الشخصية.</p>

<h3>التواصل معنا:</h3>
<p>إذا كان لديك أي استفسارات حول سياسة الخصوصية، يرجى التواصل معنا.</p>''',
                meta_description='سياسة الخصوصية لمتجر Es-Gift للألعاب الرقمية',
                meta_keywords='سياسة الخصوصية, حماية البيانات, Es-Gift',
                show_in_footer=True,
                display_order=1,
                created_by=current_user.id
            )
            db.session.add(privacy_policy)
        
        # صفحة اتصل بنا
        if not StaticPage.query.filter_by(slug='contact-us').first():
            contact_us = StaticPage(
                title='اتصل بنا',
                slug='contact-us',
                content='''<h2>اتصل بنا - Es-Gift</h2>
<p>نحن هنا لمساعدتك! تواصل معنا بأي من الطرق التالية:</p>

<div class="contact-info">
<h3>معلومات التواصل:</h3>
<ul>
<li><strong>البريد الإلكتروني:</strong> support@es-gift.com</li>
<li><strong>الهاتف:</strong> +966 XX XXX XXXX</li>
<li><strong>ساعات العمل:</strong> 24/7 دعم فني</li>
</ul>

<h3>الدعم الفني:</h3>
<p>للحصول على دعم فوري، يمكنك استخدام نظام الدردشة المباشر في أسفل الصفحة.</p>

<h3>عنوان المكتب:</h3>
<p>المملكة العربية السعودية<br>
الرياض - حي النخيل<br>
مجمع الأعمال الرقمية</p>

<h3>وسائل التواصل الاجتماعي:</h3>
<p>تابعنا على منصات التواصل الاجتماعي للحصول على أحدث العروض والأخبار.</p>
</div>''',
                meta_description='تواصل مع فريق دعم Es-Gift',
                meta_keywords='اتصل بنا, دعم فني, Es-Gift, خدمة العملاء',
                show_in_footer=True,
                display_order=2,
                created_by=current_user.id
            )
            db.session.add(contact_us)
        
        # صفحة من نحن
        if not StaticPage.query.filter_by(slug='about-us').first():
            about_us = StaticPage(
                title='من نحن',
                slug='about-us',
                content='''<h2>من نحن - Es-Gift</h2>
<p>Es-Gift هو متجرك الموثوق للألعاب الرقمية وبطاقات الهدايا في المنطقة العربية.</p>

<h3>رؤيتنا:</h3>
<p>أن نكون المنصة الرائدة لتوفير الألعاب الرقمية وبطاقات الهدايا بأفضل الأسعار وأعلى جودة خدمة.</p>

<h3>مهمتنا:</h3>
<p>نوفر لعملائنا تجربة تسوق استثنائية مع ضمان الجودة والأمان في جميع المعاملات.</p>

<h3>ما يميزنا:</h3>
<ul>
<li>توصيل فوري للمنتجات الرقمية</li>
<li>أسعار تنافسية ومناسبة لجميع الفئات</li>
<li>دعم فني متاح 24/7</li>
<li>منتجات أصلية ومضمونة</li>
<li>واجهة سهلة الاستخدام</li>
</ul>

<h3>منتجاتنا:</h3>
<ul>
<li>بطاقات PlayStation وXbox</li>
<li>بطاقات Steam وEpic Games</li>
<li>بطاقات هدايا للمتاجر الإلكترونية</li>
<li>عملات الألعاب المختلفة</li>
<li>اشتراكات الألعاب والخدمات</li>
</ul>

<h3>التزامنا:</h3>
<p>نلتزم بتقديم أفضل خدمة ممكنة لعملائنا وضمان رضاهم التام.</p>''',
                meta_description='تعرف على Es-Gift - متجر الألعاب الرقمية الموثوق',
                meta_keywords='من نحن, Es-Gift, متجر ألعاب, بطاقات هدايا',
                show_in_footer=True,
                display_order=3,
                created_by=current_user.id
            )
            db.session.add(about_us)
        
        # صفحة الشروط والأحكام
        if not StaticPage.query.filter_by(slug='terms-of-service').first():
            terms = StaticPage(
                title='الشروط والأحكام',
                slug='terms-of-service',
                content='''<h2>الشروط والأحكام - Es-Gift</h2>
<p>مرحباً بك في Es-Gift. باستخدام موقعنا وخدماتنا، فإنك توافق على الشروط والأحكام التالية:</p>

<h3>1. قبول الشروط:</h3>
<p>باستخدام موقع Es-Gift، فإنك توافق على جميع الشروط والأحكام المذكورة هنا.</p>

<h3>2. الخدمات المقدمة:</h3>
<p>نوفر منصة لبيع المنتجات الرقمية وبطاقات الهدايا.</p>

<h3>3. حساب المستخدم:</h3>
<ul>
<li>يجب تقديم معلومات صحيحة عند التسجيل</li>
<li>المستخدم مسؤول عن حماية بيانات حسابه</li>
<li>يحظر مشاركة بيانات الحساب مع الآخرين</li>
</ul>

<h3>4. المدفوعات:</h3>
<ul>
<li>جميع الأسعار معروضة بالعملة المحددة</li>
<li>المدفوعات تتم عبر بوابات دفع آمنة</li>
<li>لا يمكن استرداد المنتجات الرقمية بعد التسليم</li>
</ul>

<h3>5. استخدام الموقع:</h3>
<ul>
<li>يحظر استخدام الموقع لأغراض غير قانونية</li>
<li>يحظر محاولة اختراق أو إلحاق الضرر بالموقع</li>
<li>نحتفظ بالحق في إيقاف أي حساب يخالف الشروط</li>
</ul>

<h3>6. التواصل:</h3>
<p>لأي استفسارات حول الشروط والأحكام، يرجى التواصل معنا.</p>''',
                meta_description='الشروط والأحكام لاستخدام موقع Es-Gift',
                meta_keywords='شروط الاستخدام, أحكام, Es-Gift',
                show_in_footer=True,
                display_order=4,
                created_by=current_user.id
            )
            db.session.add(terms)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم إنشاء الصفحات الافتراضية بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
