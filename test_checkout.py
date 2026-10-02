import os
from dotenv import load_dotenv
from app import create_app
from supabase import create_client

load_dotenv()
app = create_app()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

user = sb.table('profiles').select('id, email, full_name, phone, address').limit(1).execute().data[0]
uid = user['id']
email = user['email']

options = sb.table('product_options').select('id, product_id, stock').execute().data
in_stock = [o for o in options if (o.get('stock') or 0) >= 5][0]
sold_out = [o for o in options if (o.get('stock') or 0) == 0][0]

sb.table('carts').delete().eq('user_id', uid).execute()

results = {}

with app.test_client() as client:
    # 1. 비로그인 접근 시 리다이렉트
    r1 = client.get('/order/checkout')
    results['1. 비로그인 접근'] = (r1.status_code in [302, 301] and '/auth/login' in (r1.headers.get('Location') or ''), r1.status_code)

    # 로그인 세션 주입
    with client.session_transaction() as sess:
        sess['user_id'] = uid
        sess['email'] = email
        sess['name'] = user.get('full_name')

    # 2. 장바구니 비어있을 때 /cart 리다이렉트
    r2 = client.get('/order/checkout')
    results['2. 빈 장바구니 리다이렉트'] = (r2.status_code in [302, 301] and '/cart' in (r2.headers.get('Location') or ''), r2.headers.get('Location'))

    # 3. 품절 아이템 포함 시 /cart 리다이렉트 및 메시지 전달
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': sold_out['product_id'],
        'option_id': sold_out['id'],
        'quantity': 1
    }).execute()
    r3 = client.get('/order/checkout')
    loc = r3.headers.get('Location') or ''
    results['3. 품절 아이템 리다이렉트'] = (r3.status_code in [302, 301] and '/cart' in loc and 'msg=' in loc, loc)
    sb.table('carts').delete().eq('user_id', uid).execute()

    # 4. 정상 장바구니 아이템 담기 후 GET /order/checkout
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': in_stock['product_id'],
        'option_id': in_stock['id'],
        'quantity': 2
    }).execute()
    r4 = client.get('/order/checkout')
    html4 = r4.data.decode('utf-8')
    c1 = r4.status_code == 200
    c2 = '주문서 작성' in html4
    c3 = '기본 배송지 불러오기' in html4
    c4 = 'pattern="^010-\\d{4}-\\d{4}$"' in html4
    c5 = 'minlength="5"' in html4
    c6 = '결제하기' in html4
    results['4. 주문서 페이지 정상 렌더링'] = (c1 and c2 and c3 and c4 and c5 and c6, f"200ok:{c1}, form:{c2}, loadBtn:{c3}, phoneRegex:{c4}, addrMinLen:{c5}, btn:{c6}")

    # 5. POST 주문 처리 - 유효성 실패 케이스 (전화번호 형식 오류)
    r5_fail = client.post('/order/checkout', data={
        'recipient_name': '홍길동',
        'recipient_phone': '01012345678',  # 하이픈 없음
        'shipping_address': '서울특별시 강남구 테헤란로 123'
    })
    results['5. 전화번호 형식 검증 실패'] = ('휴대폰 번호 형식' in r5_fail.data.decode('utf-8'), '검증 메시지 노출 확인')

    # 6. POST 주문 처리 - 유효성 실패 케이스 (주소 5자 미만)
    r6_fail = client.post('/order/checkout', data={
        'recipient_name': '홍길동',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '서울'  # 2자
    })
    results['6. 배송 주소 최소 길이 검증 실패'] = ('5자 이상' in r6_fail.data.decode('utf-8'), '검증 메시지 노출 확인')

    # 7. POST 주문 처리 - 정상 결제 완료
    r7 = client.post('/order/checkout', data={
        'recipient_name': '홍길동',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '서울특별시 강남구 역삼동 123-45',
        'shipping_memo': '문 앞 배송'
    }, follow_redirects=True)
    html7 = r7.data.decode('utf-8')
    order_ok = r7.status_code == 200 and '주문이 성공적으로 완료되었습니다' in html7 and 'VF-' in html7

    # DB 장바구니가 비워졌는지 확인
    rem_cart = sb.table('carts').select('*').eq('user_id', uid).execute().data
    cart_cleared = len(rem_cart) == 0

    # orders 행 조회
    latest_order = sb.table('orders').select('*').eq('user_id', uid).order('created_at', desc=True).limit(1).execute().data
    order_created = len(latest_order) > 0 and latest_order[0]['recipient_name'] == '홍길동'

    results['7. 정상 주문 완료 및 장바구니 비우기'] = (order_ok and cart_cleared and order_created, f"완료화면:{order_ok}, 카트비움:{cart_cleared}, DB주문생성:{order_created}")

    # 정리: 생성된 order 및 items 삭제
    if order_created:
        sb.table('orders').delete().eq('id', latest_order[0]['id']).execute()

sb.table('carts').delete().eq('user_id', uid).execute()

print("\n================== 주문서(Checkout) 검증 결과 ==================")
all_pass = True
for name, (passed, detail) in results.items():
    tag = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{tag}] {name} -> {detail}")
print("==============================================================")
print("최종 결과:", "모든 검증을 통과했습니다!" if all_pass else "일부 검증에 실패했습니다.")
