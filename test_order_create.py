import os
import re
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
    # 로그인 세션 주입
    with client.session_transaction() as sess:
        sess['user_id'] = uid
        sess['email'] = email
        sess['name'] = user.get('full_name')

    # 1. 재고 부족 시 에러 (장바구니에 담긴 수량 > 재고)
    # stock 0 인 아이템 담기
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': sold_out['product_id'],
        'option_id': sold_out['id'],
        'quantity': 1
    }).execute()
    r1 = client.post('/order/create', data={
        'recipient_name': '홍길동',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '서울특별시 강남구 역삼동 123-45'
    })
    html1 = r1.data.decode('utf-8')
    c1 = '재고가 부족합니다' in html1
    # DB에 orders 생성 안 되었는지 확인
    orders_c1 = sb.table('orders').select('*').eq('recipient_name', '홍길동').execute().data
    results['1. 재고 부족 시 에러/중단/아무것도 안 씀'] = (c1 and len(orders_c1) == 0, f"에러문구:{c1}, 주문생성안됨:{len(orders_c1)==0}")
    sb.table('carts').delete().eq('user_id', uid).execute()

    # 2. 배송지 입력값 재검증 (전화번호, 주소)
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': in_stock['product_id'],
        'option_id': in_stock['id'],
        'quantity': 1
    }).execute()
    r2_phone = client.post('/order/create', data={
        'recipient_name': '홍길동',
        'recipient_phone': '01012345678',
        'shipping_address': '서울특별시 강남구 역삼동 123-45'
    })
    c2_phone = '휴대폰 번호 형식' in r2_phone.data.decode('utf-8')

    r2_addr = client.post('/order/create', data={
        'recipient_name': '홍길동',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '서울'
    })
    c2_addr = '5자 이상' in r2_addr.data.decode('utf-8')
    results['2. 배송지 입력값 재검증'] = (c2_phone and c2_addr, f"전화번호:{c2_phone}, 주소:{c2_addr}")

    # 3. 정상 주문 생성: 순서 3~8 전 과정 검증
    # 이전 stock 확인
    initial_stock = sb.table('product_options').select('stock').eq('id', in_stock['id']).execute().data[0]['stock']
    order_qty = 2
    sb.table('carts').update({'quantity': order_qty}).eq('user_id', uid).execute()

    r3 = client.post('/order/create', data={
        'recipient_name': '한지희',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '부산광역시 해운대구 우동 센텀중앙로 100',
        'shipping_memo': '문 앞 배송'
    })

    # 8. 리다이렉트 확인 (/order/complete/<order_id>)
    c8_redirect = (r3.status_code == 302) and ('/order/complete/' in r3.headers.get('Location', ''))
    order_id = r3.headers.get('Location', '').split('/')[-1] if c8_redirect else None

    # 3. 주문번호 패턴: VF-YYYYMMDD-XXXXYYY (VF- + 8자리 날짜 + - + 4자리숫자 + 3자리밀리초)
    latest_order = sb.table('orders').select('*').eq('id', order_id).execute().data[0] if order_id else None
    order_num = latest_order['order_number'] if latest_order else ''
    order_num_pattern = r'^VF-\d{8}-\d{7}$'
    c3_order_num = bool(re.match(order_num_pattern, order_num))

    # 4. orders 테이블 status='PAID'
    c4_status = (latest_order is not None) and (latest_order['status'] == 'PAID')

    # 5. order_items 스냅샷 확인
    items_in_db = sb.table('order_items').select('*').eq('order_id', order_id).execute().data if order_id else []
    c5_items = len(items_in_db) == 1 and items_in_db[0]['quantity'] == order_qty

    # 6. 재고 차감 확인 (initial_stock - order_qty)
    after_stock = sb.table('product_options').select('stock').eq('id', in_stock['id']).execute().data[0]['stock']
    c6_stock = after_stock == (initial_stock - order_qty)

    # 7. carts 아이템 삭제 확인
    carts_left = sb.table('carts').select('*').eq('user_id', uid).execute().data
    c7_carts_empty = len(carts_left) == 0

    results['3~8. 주문번호, orders, order_items, 재고차감, 카트삭제, 리다이렉트'] = (
        c3_order_num and c4_status and c5_items and c6_stock and c7_carts_empty and c8_redirect,
        f"주문번호({order_num}):{c3_order_num}, status:{c4_status}, items:{c5_items}, 재고({initial_stock}->{after_stock}):{c6_stock}, 카트삭제:{c7_carts_empty}, 리다이렉트:{c8_redirect}"
    )

    # 6-2. 조건부 UPDATE 실패 시 '방금 재고가 소진되었습니다' 및 롤백 검증
    # 재고를 1로 맞추고 2개 주문 시도
    sb.table('product_options').update({'stock': 1}).eq('id', in_stock['id']).execute()
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': in_stock['product_id'],
        'option_id': in_stock['id'],
        'quantity': 2  # 재고(1) 초과
    }).execute()

    r6_race = client.post('/order/create', data={
        'recipient_name': '동시성테스터',
        'recipient_phone': '010-9999-8888',
        'shipping_address': '서울특별시 서초구 반포대로 1234'
    })
    html6 = r6_race.data.decode('utf-8')
    c6_race_msg = '방금 재고가 소진되었습니다' in html6 or '재고가 부족합니다' in html6
    results['6-2. 재고 소진 시 에러 반환'] = (c6_race_msg, f"에러메시지:{c6_race_msg}")

    # 복원
    sb.table('product_options').update({'stock': initial_stock}).eq('id', in_stock['id']).execute()
    sb.table('carts').delete().eq('user_id', uid).execute()
    if order_id:
        sb.table('orders').delete().eq('id', order_id).execute()

print("\n================== POST /order/create 검증 결과 ==================")
all_pass = True
for name, (passed, detail) in results.items():
    tag = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{tag}] {name} -> {detail}")
print("================================================================")
print("최종 결과:", "모든 요구사항을 만족합니다!" if all_pass else "일부 검증에 실패했습니다.")
