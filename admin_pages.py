# قائمة صفحات لوحة التحكم المتاحة
# هذا الملف يحتوي على تعريف جميع الصفحات المتاحة في لوحة التحكم
# يستخدم في نظام إدارة الأدوار والصلاحيات

ADMIN_PAGES = {
    # الصفحة الرئيسية
    'admin.dashboard': {
        'name': 'لوحة التحكم الرئيسية',
        'description': 'عرض الإحصائيات العامة والملخصات',
        'category': 'main',
        'required': True  # صفحة مطلوبة لجميع الموظفين
    },
    
    # إدارة المستخدمين
    'admin.users': {
        'name': 'إدارة المستخدمين',
        'description': 'عرض وإدارة حسابات المستخدمين',
        'category': 'users'
    },
    'admin.kyc_requests': {
        'name': 'طلبات التحقق من الهوية',
        'description': 'مراجعة والموافقة على طلبات KYC',
        'category': 'users'
    },
    
    # إدارة المنتجات
    'admin.products': {
        'name': 'إدارة المنتجات',
        'description': 'إضافة وتعديل وحذف المنتجات',
        'category': 'products'
    },
    'admin.categories': {
        'name': 'إدارة الفئات',
        'description': 'إدارة فئات وأقسام المنتجات',
        'category': 'products'
    },
    
    # إدارة الطلبات
    'admin.orders': {
        'name': 'إدارة الطلبات',
        'description': 'عرض ومتابعة طلبات العملاء',
        'category': 'orders'
    },
    'admin.invoices': {
        'name': 'إدارة الفواتير',
        'description': 'عرض وإدارة الفواتير الإلكترونية',
        'category': 'orders'
    },
    'admin.transactions': {
        'name': 'إدارة المعاملات',
        'description': 'متابعة المعاملات المالية',
        'category': 'orders'
    },
    
    # الإدارة المالية
    'admin.financial': {
        'name': 'الإدارة المالية',
        'description': 'التقارير والإحصائيات المالية',
        'category': 'financial'
    },
    'admin.currency': {
        'name': 'إدارة العملات',
        'description': 'إعدادات أسعار الصرف',
        'category': 'financial'
    },
    'admin.wallet': {
        'name': 'إدارة المحافظ',
        'description': 'متابعة أرصدة المحافظ',
        'category': 'financial'
    },
    
    # إدارة الموظفين والأدوار
    'admin.employees': {
        'name': 'إدارة الموظفين',
        'description': 'إضافة وإدارة حسابات الموظفين',
        'category': 'hr'
    },
    'admin.roles': {
        'name': 'إدارة الأدوار',
        'description': 'إنشاء وتعديل أدوار الموظفين',
        'category': 'hr'
    },
    
    # إدارة المحتوى
    'admin.content': {
        'name': 'إدارة المحتوى',
        'description': 'إدارة الصفحات والمقالات',
        'category': 'content'
    },
    'admin.notifications': {
        'name': 'إدارة التنبيهات',
        'description': 'إرسال وإدارة التنبيهات',
        'category': 'content'
    },
    
    # الإعدادات والنظام
    'admin.settings': {
        'name': 'إعدادات النظام',
        'description': 'إعدادات عامة للنظام',
        'category': 'system'
    },
    'admin.logs': {
        'name': 'سجلات النظام',
        'description': 'عرض سجلات النشاطات',
        'category': 'system'
    },
    'admin.backup': {
        'name': 'النسخ الاحتياطية',
        'description': 'إدارة النسخ الاحتياطية',
        'category': 'system'
    },
    
    # التقارير والإحصائيات
    'admin.reports': {
        'name': 'التقارير',
        'description': 'تقارير مفصلة وإحصائيات',
        'category': 'reports'
    },
    'admin.analytics': {
        'name': 'التحليلات',
        'description': 'تحليل البيانات والسلوكيات',
        'category': 'reports'
    }
}

# تجميع الصفحات حسب الفئات
PAGE_CATEGORIES = {
    'main': 'الصفحة الرئيسية',
    'users': 'إدارة المستخدمين',
    'products': 'إدارة المنتجات',
    'orders': 'إدارة الطلبات',
    'financial': 'الإدارة المالية',
    'hr': 'الموارد البشرية',
    'content': 'إدارة المحتوى',
    'system': 'إعدادات النظام',
    'reports': 'التقارير والإحصائيات'
}

def get_pages_for_js():
    """جلب الصفحات بصيغة مناسبة للـ JavaScript"""
    result = {}
    for category, name in PAGE_CATEGORIES.items():
        result[category] = {
            'name': name,
            'pages': {}
        }
        
        # جلب الصفحات للفئة
        for page_id, page_info in ADMIN_PAGES.items():
            if page_info.get('category') == category:
                result[category]['pages'][page_id] = {
                    'name': page_info['name'],
                    'description': page_info['description'],
                    'required': page_info.get('required', False)
                }
    
    return result

def get_pages_by_category(category=None):
    """جلب الصفحات حسب الفئة"""
    if category:
        return {k: v for k, v in ADMIN_PAGES.items() if v.get('category') == category}
    return ADMIN_PAGES

def get_required_pages():
    """جلب الصفحات المطلوبة لجميع الموظفين"""
    return {k: v for k, v in ADMIN_PAGES.items() if v.get('required', False)}

def get_allowed_pages_for_employee(employee):
    """
    جلب الصفحات المسموحة لموظف معين
    """
    if not employee or not employee.role:
        return {}
    
    # الأدوار الإدارية لها وصول كامل
    if employee.role.is_admin:
        return ADMIN_PAGES
    
    # جلب الصفحات المسموحة من الدور
    allowed_pages = {}
    if employee.role.allowed_pages:
        try:
            import json
            allowed_page_routes = json.loads(employee.role.allowed_pages)
            for route in allowed_page_routes:
                if route in ADMIN_PAGES:
                    allowed_pages[route] = ADMIN_PAGES[route]
        except (json.JSONDecodeError, TypeError):
            pass
    
    return allowed_pages

def get_sidebar_menu_for_employee(employee):
    """
    إنشاء قائمة الشريط الجانبي المخصصة للموظف
    """
    if not employee:
        return {}
        
    allowed_pages = get_allowed_pages_for_employee(employee)
    
    # تجميع الصفحات حسب الفئات
    menu_categories = {}
    for page_route, page_info in allowed_pages.items():
        category = page_info.get('category', 'other')
        if category not in menu_categories:
            menu_categories[category] = {
                'name': PAGE_CATEGORIES.get(category, 'أخرى'),
                'pages': []
            }
        menu_categories[category]['pages'].append({
            'route': page_route,
            'name': page_info['name'],
            'description': page_info['description']
        })
    
    return menu_categories

def is_valid_page(page_route):
    """التحقق من صحة مسار الصفحة"""
    return page_route in ADMIN_PAGES

def get_page_info(page_route):
    """جلب معلومات صفحة محددة"""
    return ADMIN_PAGES.get(page_route, {})
