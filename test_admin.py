import os
from dotenv import load_dotenv
from app import create_app
from supabase import create_client

load_dotenv()
app = create_app()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

results = {}

with app.test_client() as client:
    # 1. 미인증 상태로 /admin 접근 시 /admin/login 리다이렉트
    r1 = client.get('/admin')
    c1_redir = r1.status_code == 302 and '/admin/login' in (r1.headers.get('Location') or '')
    results['1. 비로그인 접근 차단 및 리다이렉트'] = (c1_redir, f"상태코드:{r1.status_code}, 이동위치:{r1.headers.get('Location')}")

    # 2. 관리자 로그인 실패 (잘못된 계정)
    r2_fail = client.post('/admin/login', data={'username': 'admin', 'password': 'wrongpassword'})
    c2_fail = '올바르지 않습니다' in r2_fail.data.decode('utf-8')
    results['2. 잘못된 비밀번호 로그인 실패'] = (c2_fail, "에러 메시지 정상 표시")

    # 3. 관리자 로그인 성공
    r3_login = client.post('/admin/login', data={'username': 'admin', 'password': 'admin1234'}, follow_redirects=False)
    c3_login = r3_login.status_code == 302 and '/admin' in (r3_login.headers.get('Location') or '')
    results['3. 관리자 로그인 성공 및 대시보드 리다이렉트'] = (c3_login, f"상태코드:{r3_login.status_code}")

    # 세션에 관리자 주입 후 대시보드 조회
    with client.session_transaction() as sess:
        sess['is_admin'] = True
        sess['admin_user'] = 'admin'

    # 4. 대시보드 정상 렌더링
    r4_dash = client.get('/admin/dashboard')
    html4 = r4_dash.data.decode('utf-8')
    c4 = r4_dash.status_code == 200 and 'ADMIN CENTER' in html4 and '총 누적 결제액' in html4
    results['4. 대시보드 통계 정상 렌더링'] = (c4, f"상태코드:{r4_dash.status_code}")

    # 5. 주문 관리 페이지 조회
    r5_orders = client.get('/admin/orders')
    html5 = r5_orders.data.decode('utf-8')
    c5 = r5_orders.status_code == 200 and '주문 관리' in html5
    results['5. 주문 관리 페이지 정상 렌더링'] = (c5, f"상태코드:{r5_orders.status_code}")

    # 6. 상품 및 재고 관리 페이지 조회
    r6_prods = client.get('/admin/products')
    html6 = r6_prods.data.decode('utf-8')
    c6 = r6_prods.status_code == 200 and '상품 및 옵션 재고 관리' in html6
    results['6. 상품/재고 관리 페이지 정상 렌더링'] = (c6, f"상태코드:{r6_prods.status_code}")

    # 7. 재고 수량 수정 API (POST /admin/options/<id>/stock)
    opt = sb.table('product_options').select('id, stock').limit(1).execute().data[0]
    orig_stock = opt['stock']
    test_new_stock = orig_stock + 5
    r7_stock = client.post(f'/admin/options/{opt["id"]}/stock', data={'stock': test_new_stock})
    data7 = r7_stock.get_json()
    c7 = r7_stock.status_code == 200 and data7.get('success') is True
    # DB 반영 확인
    db_stock = sb.table('product_options').select('stock').eq('id', opt['id']).execute().data[0]['stock']
    c7_db = (db_stock == test_new_stock)
    # 원복
    sb.table('product_options').update({'stock': orig_stock}).eq('id', opt['id']).execute()
    results['7. 관리자 재고 수정 API 및 DB 반영'] = (c7 and c7_db, f"API성공:{c7}, DB수정확인:{c7_db}")

    # 8. 회원 관리 페이지 조회
    r8_users = client.get('/admin/users')
    html8 = r8_users.data.decode('utf-8')
    c8 = r8_users.status_code == 200 and '회원 관리' in html8
    results['8. 회원 관리 페이지 정상 렌더링'] = (c8, f"상태코드:{r8_users.status_code}")

    # 9. 회원 등급 수정 API (POST /admin/users/<id>/grade)
    user = sb.table('profiles').select('id, grade').limit(1).execute().data[0]
    orig_grade = user.get('grade') or 'BRONZE'
    new_grade = 'GOLD' if orig_grade != 'GOLD' else 'SILVER'
    r9_grade = client.post(f'/admin/users/{user["id"]}/grade', data={'grade': new_grade})
    data9 = r9_grade.get_json()
    c9 = r9_grade.status_code == 200 and data9.get('success') is True
    # DB 반영 확인
    db_grade = sb.table('profiles').select('grade').eq('id', user['id']).execute().data[0]['grade']
    c9_db = (db_grade == new_grade)
    # 원복
    sb.table('profiles').update({'grade': orig_grade}).eq('id', user['id']).execute()
    results['9. 회원 등급 수정 API 및 DB 반영'] = (c9 and c9_db, f"API성공:{c9}, DB수정확인:{c9_db}")

    # 10. 관리자 로그아웃
    r10_logout = client.get('/admin/logout')
    c10 = r10_logout.status_code == 302 and '/admin/login' in (r10_logout.headers.get('Location') or '')
    with client.session_transaction() as sess:
        c10_sess = not sess.get('is_admin')
    results['10. 관리자 로그아웃 및 세션 제거'] = (c10 and c10_sess, f"로그아웃이동:{c10}, 세션제거:{c10_sess}")

print("\n================== 관리자(Admin) 전체 기능 검증 결과 ==================")
all_pass = True
for name, (passed, detail) in results.items():
    tag = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{tag}] {name} -> {detail}")
print("====================================================================")
print("최종 결과:", "모든 관리자 기능이 정상 작동합니다!" if all_pass else "일부 검증에 실패했습니다.")
