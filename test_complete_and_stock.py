import os
from dotenv import load_dotenv
from app import create_app
from supabase import create_client

load_dotenv()
app = create_app()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

users = sb.table('profiles').select('id, email, full_name').limit(2).execute().data
user1 = users[0]
user2 = users[1] if len(users) > 1 else users[0]

opt = sb.table('product_options').select('id, product_id, stock').gt('stock', 2).limit(1).execute().data[0]

results = {}

with app.test_client() as client:
    # 1. user1 세션 로그인
    with client.session_transaction() as sess:
        sess['user_id'] = user1['id']
        sess['email'] = user1['email']
        sess['name'] = user1.get('full_name')

    # 카트 세팅 및 주문 생성
    sb.table('carts').delete().eq('user_id', user1['id']).execute()
    sb.table('carts').insert({
        'user_id': user1['id'],
        'product_id': opt['product_id'],
        'option_id': opt['id'],
        'quantity': 1
    }).execute()

    # 주문 생성 POST /order/create
    res_create = client.post('/order/create', data={
        'recipient_name': '테스트수령인',
        'recipient_phone': '010-1234-5678',
        'shipping_address': '서울특별시 서초구 강남대로 100'
    })
    order_id = res_create.headers.get('Location', '').split('/')[-1]

    # 2. GET /order/complete/<order_id> (본인 접근)
    res_comp = client.get(f'/order/complete/{order_id}')
    html_comp = res_comp.data.decode('utf-8')

    c1_ok = res_comp.status_code == 200
    c1_ord_num = '주문 번호' in html_comp
    c1_addr = '서울특별시 서초구 강남대로 100' in html_comp
    c1_items = '주문 상품 목록' in html_comp
    c1_btn_mypage = '마이페이지로' in html_comp
    c1_btn_shop = '쇼핑 계속하기' in html_comp
    results['1. 본인 주문 완료 페이지 렌더링'] = (
        c1_ok and c1_ord_num and c1_addr and c1_items and c1_btn_mypage and c1_btn_shop,
        f"200ok:{c1_ok}, 주문번호:{c1_ord_num}, 배송지:{c1_addr}, 상품목록:{c1_items}, 마이페이지버튼:{c1_btn_mypage}, 쇼핑계속버튼:{c1_btn_shop}"
    )

    # 3. 다른 사용자(user2)의 접근 차단 검증
    with client.session_transaction() as sess:
        sess['user_id'] = user2['id']
        sess['email'] = user2['email']
        sess['name'] = user2.get('full_name')

    res_block = client.get(f'/order/complete/{order_id}')
    c2_blocked = (res_block.status_code == 403) or (res_block.status_code == 302 and user1['id'] != user2['id'])
    results['2. 타인 order_id 접근 차단'] = (c2_blocked, f"상태코드: {res_block.status_code}")

    # 4. 마이페이지(GET /mypage)에 해당 주문이 뜨는지 확인
    with client.session_transaction() as sess:
        sess['user_id'] = user1['id']
        sess['email'] = user1['email']
        sess['name'] = user1.get('full_name')

    res_mypage = client.get('/mypage')
    html_mypage = res_mypage.data.decode('utf-8')
    order_data = sb.table('orders').select('order_number').eq('id', order_id).execute().data[0]
    c4_mypage_has_order = order_data['order_number'] in html_mypage
    results['3. 마이페이지 주문 내역에 정상 표시'] = (c4_mypage_has_order, f"주문번호({order_data['order_number']}) 마이페이지 노출: {c4_mypage_has_order}")

    # 5. 재고 1개 남았을 때 결제 후 품절(stock=0) 상태 전환 테스트
    # opt의 stock을 1로 설정
    sb.table('product_options').update({'stock': 1}).eq('id', opt['id']).execute()
    sb.table('carts').insert({
        'user_id': user1['id'],
        'product_id': opt['product_id'],
        'option_id': opt['id'],
        'quantity': 1
    }).execute()

    res_last1 = client.post('/order/create', data={
        'recipient_name': '마지막재고구매자',
        'recipient_phone': '010-8888-7777',
        'shipping_address': '부산광역시 해운대구 센텀중앙로 55'
    })
    order_id2 = res_last1.headers.get('Location', '').split('/')[-1]

    # 재고가 0이 되었는지 확인
    stock_after = sb.table('product_options').select('stock').eq('id', opt['id']).execute().data[0]['stock']
    c5_soldout = (stock_after == 0)

    # 장바구니에 다시 담으려 하거나 주문서 접근 시 품절 상태 확인
    sb.table('carts').insert({
        'user_id': user1['id'],
        'product_id': opt['product_id'],
        'option_id': opt['id'],
        'quantity': 1
    }).execute()
    res_cart = client.get('/cart')
    html_cart = res_cart.data.decode('utf-8')
    c5_badge = '품절됨' in html_cart
    c5_disabled = 'disabled>주문하기</button>' in html_cart

    results['4. 1개 남은 상품 결제 후 품절(stock=0) 전환'] = (
        c5_soldout and c5_badge and c5_disabled,
        f"결제후재고: {stock_after}, 품절배지: {c5_badge}, 주문버튼비활성화: {c5_disabled}"
    )

    # 정리
    sb.table('carts').delete().eq('user_id', user1['id']).execute()
    sb.table('orders').delete().eq('id', order_id).execute()
    sb.table('orders').delete().eq('id', order_id2).execute()
    sb.table('product_options').update({'stock': 25}).eq('id', opt['id']).execute()

print("\n================== 주문 완료 및 품절 검증 결과 ==================")
all_pass = True
for name, (passed, detail) in results.items():
    tag = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{tag}] {name} -> {detail}")
print("================================================================")
print("최종 결과:", "모든 검증을 완벽히 통과했습니다!" if all_pass else "일부 검증에 실패했습니다.")
