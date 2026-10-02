"""
관리자 라우트 모듈
- 관리자 로그인 (/admin/login) 및 로그아웃 (/admin/logout)
- 대시보드 (/admin)
- 주문 관리 (/admin/orders, /admin/orders/<id>/status)
- 상품 및 재고 관리 (/admin/products, /admin/products/<id>/stock)
- 회원 관리 (/admin/users, /admin/users/<id>/grade)
"""

import os
import sys
import functools
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

supabase_admin: Client = None
if SUPABASE_URL and (SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY):
    try:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"[ERROR] Admin Supabase 클라이언트 초기화 실패: {e}", file=sys.stderr)

# 관리자 기본 계정 설정 (환경변수 또는 기본값)
DEFAULT_ADMIN_ID = os.getenv('ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_PW = os.getenv('ADMIN_PASSWORD', 'admin1234')


def admin_required(func):
    """관리자 세션 검증 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.login', next=request.path))
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """관리자 전용 로그인 페이지"""
    if session.get('is_admin'):
        return redirect(url_for('admin.dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin_id = os.getenv('ADMIN_USERNAME', DEFAULT_ADMIN_ID)
        admin_pw = os.getenv('ADMIN_PASSWORD', DEFAULT_ADMIN_PW)

        if username == admin_id and password == admin_pw:
            session['is_admin'] = True
            session['admin_user'] = username
            next_url = request.args.get('next') or url_for('admin.dashboard')
            return redirect(next_url)
        else:
            error = "관리자 아이디 또는 비밀번호가 올바르지 않습니다."

    return render_template('admin/login.html', error=error)


@admin_bp.route('/logout')
def logout():
    """관리자 로그아웃"""
    session.pop('is_admin', None)
    session.pop('admin_user', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('', methods=['GET'])
@admin_bp.route('/', methods=['GET'])
@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """관리자 대시보드 메인"""
    db = supabase_admin
    stats = {
        'total_orders': 0,
        'total_sales': 0,
        'total_products': 0,
        'total_users': 0,
        'out_of_stock_count': 0
    }
    recent_orders = []

    if db:
        try:
            # 1. 주문 통계
            orders_res = db.table('orders').select('*').order('created_at', desc=True).execute()
            all_orders = orders_res.data or []
            stats['total_orders'] = len(all_orders)
            stats['total_sales'] = sum(float(o.get('total_amount', 0) or 0) for o in all_orders if o.get('status') in ['PAID', 'SHIPPING', 'DELIVERED'])
            recent_orders = all_orders[:5]

            # 2. 상품 및 재고 통계
            prods_res = db.table('products').select('id').execute()
            stats['total_products'] = len(prods_res.data or [])

            opts_res = db.table('product_options').select('id, stock').execute()
            opts_data = opts_res.data or []
            stats['out_of_stock_count'] = sum(1 for opt in opts_data if int(opt.get('stock', 0) or 0) <= 0)

            # 3. 회원 통계
            profiles_res = db.table('profiles').select('id').execute()
            stats['total_users'] = len(profiles_res.data or [])
        except Exception as e:
            print(f"[ERROR] 대시보드 통계 조회 실패: {e}", file=sys.stderr)

    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


@admin_bp.route('/orders')
@admin_required
def orders():
    """주문 목록 조회"""
    db = supabase_admin
    status_filter = request.args.get('status', '').strip()
    order_list = []

    if db:
        try:
            query = db.table('orders').select('*, profiles(email, full_name)').order('created_at', desc=True)
            if status_filter:
                query = query.eq('status', status_filter.upper())
            res = query.execute()
            raw_orders = res.data or []

            # 주문 상세 아이템도 포함
            for ord_row in raw_orders:
                items_res = db.table('order_items').select('*, products(name), product_options(option_value, color, size)').eq('order_id', ord_row['id']).execute()
                ord_row['order_items'] = items_res.data or []
                order_list.append(ord_row)
        except Exception as e:
            print(f"[ERROR] 주문 목록 조회 실패: {e}", file=sys.stderr)

    return render_template('admin/orders.html', orders=order_list, current_status=status_filter)


@admin_bp.route('/orders/<order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """주문 상태 변경 (PENDING, PAID, SHIPPING, DELIVERED, CANCELLED)"""
    new_status = request.form.get('status', '').strip().upper()
    valid_statuses = ['PENDING', 'PAID', 'SHIPPING', 'DELIVERED', 'CANCELLED']

    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': '유효하지 않은 주문 상태입니다.'}), 400

    db = supabase_admin
    if db:
        try:
            db.table('orders').update({
                'status': new_status,
                'updated_at': 'now()'
            }).eq('id', order_id).execute()
            return jsonify({'success': True, 'message': f'주문 상태가 {new_status}(으)로 변경되었습니다.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'상태 변경 실패: {str(e)}'}), 500

    return jsonify({'success': False, 'message': 'DB 연결 오류'}), 500


@admin_bp.route('/products')
@admin_required
def products():
    """상품 및 재고 관리 목록"""
    db = supabase_admin
    product_list = []

    if db:
        try:
            res = db.table('products').select('*, product_options(*), categories(name)').order('created_at', desc=True).execute()
            product_list = res.data or []
        except Exception as e:
            print(f"[ERROR] 상품 목록 조회 실패: {e}", file=sys.stderr)

    return render_template('admin/products.html', products=product_list)


@admin_bp.route('/options/<option_id>/stock', methods=['POST'])
@admin_required
def update_option_stock(option_id):
    """옵션 재고 수량 변경"""
    raw_stock = request.form.get('stock')
    if raw_stock is None:
        return jsonify({'success': False, 'message': '재고 값이 필요합니다.'}), 400

    try:
        new_stock = int(raw_stock)
        if new_stock < 0:
            return jsonify({'success': False, 'message': '재고는 0 이상이어야 합니다.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '재고는 정수여야 합니다.'}), 400

    db = supabase_admin
    if db:
        try:
            db.table('product_options').update({
                'stock': new_stock
            }).eq('id', option_id).execute()
            return jsonify({'success': True, 'stock': new_stock, 'message': '재고가 수정되었습니다.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'재고 수정 실패: {str(e)}'}), 500

    return jsonify({'success': False, 'message': 'DB 연결 오류'}), 500


@admin_bp.route('/users')
@admin_required
def users():
    """회원 목록 및 등급 관리"""
    db = supabase_admin
    user_list = []

    if db:
        try:
            res = db.table('profiles').select('*').order('created_at', desc=True).execute()
            user_list = res.data or []
        except Exception as e:
            print(f"[ERROR] 회원 목록 조회 실패: {e}", file=sys.stderr)

    return render_template('admin/users.html', users=user_list)


@admin_bp.route('/users/<user_id>/grade', methods=['POST'])
@admin_required
def update_user_grade(user_id):
    """회원 등급 변경 (BRONZE, SILVER, GOLD, VIP)"""
    new_grade = request.form.get('grade', '').strip().upper()
    valid_grades = ['BRONZE', 'SILVER', 'GOLD', 'VIP']

    if new_grade not in valid_grades:
        return jsonify({'success': False, 'message': '유효하지 않은 회원 등급입니다.'}), 400

    db = supabase_admin
    if db:
        try:
            db.table('profiles').update({
                'grade': new_grade,
                'updated_at': 'now()'
            }).eq('id', user_id).execute()
            return jsonify({'success': True, 'grade': new_grade, 'message': f'회원 등급이 {new_grade}로 변경되었습니다.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'등급 변경 실패: {str(e)}'}), 500

    return jsonify({'success': False, 'message': 'DB 연결 오류'}), 500
