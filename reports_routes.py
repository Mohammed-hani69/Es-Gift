from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from reports_service import ReportsService
from employee_utils import requires_page_access

# إنشاء Blueprint للتقارير
reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')

@reports_bp.route('/')
@login_required
@requires_page_access('admin.reports')
def reports_dashboard():
    """صفحة التقارير الرئيسية"""
    try:
        return render_template('admin/reports/dashboard.html')
    except Exception as e:
        flash(f'خطأ في تحميل لوحة التقارير: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@reports_bp.route('/main')
@login_required
@requires_page_access('admin.reports')
def main_reports():
    """صفحة التقارير الأساسية"""
    try:
        # استخدام ReportsService للحصول على البيانات المطلوبة
        basic_stats = ReportsService.get_basic_stats()
        
        return render_template('admin/reports.html', **basic_stats)
    except Exception as e:
        flash(f'خطأ في تحميل التقارير الأساسية: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/resellers')
@login_required
@requires_page_access('admin.reports')
def resellers_reports():
    """صفحة تقارير الموزعين"""
    try:
        # الحصول على المعاملات
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # الحصول على إحصائيات الموزعين
        stats = ReportsService.get_reseller_stats(period, start_date, end_date)
        
        return render_template('admin/reports/resellers.html', 
                             stats=stats, 
                             selected_period=period,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل تقارير الموزعين: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/resellers/advanced')
@login_required
@requires_page_access('admin.reports')
def resellers_advanced_reports():
    """صفحة تقارير الموزعين المتقدمة"""
    try:
        # الحصول على المعاملات
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # الحصول على إحصائيات الموزعين
        stats = ReportsService.get_reseller_stats(period, start_date, end_date)
        
        return render_template('admin/reports/resellers_advanced.html', 
                             stats=stats, 
                             selected_period=period,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل تقارير الموزعين المتقدمة: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))


@reports_bp.route('/customers')
@login_required
@requires_page_access('admin.reports')
def customers_reports():
    """صفحة تقارير العملاء (العاديين والموثقين)"""
    try:
        # الحصول على المعاملات
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # الحصول على إحصائيات العملاء
        stats = ReportsService.get_regular_kyc_stats(period, start_date, end_date)
        
        return render_template('admin/reports/customers.html', 
                             stats=stats, 
                             selected_period=period,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل تقارير العملاء: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/customers/advanced')
@login_required
@requires_page_access('admin.reports')
def customers_advanced_reports():
    """صفحة تقارير العملاء المتقدمة"""
    try:
        # الحصول على المعاملات
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # الحصول على إحصائيات العملاء
        stats = ReportsService.get_regular_kyc_stats(period, start_date, end_date)
        
        return render_template('admin/reports/customers_advanced.html', 
                             stats=stats, 
                             selected_period=period,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل تقارير العملاء المتقدمة: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/comparison')
@login_required
@requires_page_access('admin.reports')
def comparison_reports():
    """صفحة المقارنة بين أنواع المستخدمين"""
    try:
        # الحصول على المعاملات
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # الحصول على بيانات المقارنة
        comparison_data = ReportsService.get_comparison_stats(period, start_date, end_date)
        
        return render_template('admin/reports/comparison.html', 
                             comparison_data=comparison_data, 
                             selected_period=period,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل تقارير المقارنة: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/api/resellers-data')
@login_required
@requires_page_access('admin.reports')
def api_resellers_data():
    """API للحصول على بيانات الموزعين (AJAX)"""
    try:
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        stats = ReportsService.get_reseller_stats(period, start_date, end_date)
        
        # تحويل البيانات لصيغة JSON مناسبة للرسوم البيانية
        chart_data = {
            'monthly_sales': [
                {
                    'month': f"{int(sale.year)}-{int(sale.month):02d}",
                    'revenue': float(sale.revenue),
                    'orders': int(sale.orders)
                } for sale in stats['monthly_sales']
            ],
            'top_products': [
                {
                    'name': product.name,
                    'sold': int(product.total_sold),
                    'revenue': float(product.total_revenue)
                } for product in stats['top_products']
            ],
            'top_resellers': [
                {
                    'name': reseller.full_name or reseller.email,
                    'orders': int(reseller.total_orders),
                    'revenue': float(reseller.total_spent)
                } for reseller in stats['top_resellers']
            ]
        }
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'stats': {
                'total_revenue': stats['total_revenue'],
                'total_profit': stats['total_profit'],
                'profit_margin': stats['profit_margin'],
                'total_orders': stats['total_orders'],
                'active_resellers': stats['active_resellers']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@reports_bp.route('/api/customers-data')
@login_required
@requires_page_access('admin.reports')
def api_customers_data():
    """API للحصول على بيانات العملاء (AJAX)"""
    try:
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        stats = ReportsService.get_regular_kyc_stats(period, start_date, end_date)
        
        # تحويل البيانات لصيغة JSON
        chart_data = {
            'regular_monthly_sales': [
                {
                    'month': f"{int(sale.year)}-{int(sale.month):02d}",
                    'revenue': float(sale.revenue),
                    'orders': int(sale.orders)
                } for sale in stats['regular']['monthly_sales']
            ],
            'kyc_monthly_sales': [
                {
                    'month': f"{int(sale.year)}-{int(sale.month):02d}",
                    'revenue': float(sale.revenue),
                    'orders': int(sale.orders)
                } for sale in stats['kyc']['monthly_sales']
            ],
            'regular_top_products': [
                {
                    'name': product.name,
                    'sold': int(product.total_sold),
                    'revenue': float(product.total_revenue)
                } for product in stats['regular']['top_products']
            ],
            'kyc_top_products': [
                {
                    'name': product.name,
                    'sold': int(product.total_sold),
                    'revenue': float(product.total_revenue)
                } for product in stats['kyc']['top_products']
            ]
        }
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'stats': {
                'regular': stats['regular'],
                'kyc': stats['kyc']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@reports_bp.route('/api/comparison-data')
@login_required
@requires_page_access('admin.reports')
def api_comparison_data():
    """API للحصول على بيانات المقارنة (AJAX)"""
    try:
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        comparison_data = ReportsService.get_comparison_stats(period, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': comparison_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@reports_bp.route('/export/resellers')
@login_required
@requires_page_access('admin.reports')
def export_resellers_report():
    """تصدير تقرير الموزعين"""
    try:
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'excel')  # excel, pdf, csv
        
        stats = ReportsService.get_reseller_stats(period, start_date, end_date)
        
        # هنا يمكن إضافة منطق التصدير
        # للتبسيط، سنعيد JSON الآن
        if format_type == 'json':
            return jsonify(stats)
        
        flash('ميزة التصدير قيد التطوير', 'info')
        return redirect(url_for('reports.resellers_reports'))
        
    except Exception as e:
        flash(f'خطأ في تصدير التقرير: {str(e)}', 'error')
        return redirect(url_for('reports.resellers_reports'))
