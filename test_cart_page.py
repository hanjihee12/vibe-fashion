from app import create_app
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

test_uid = 'bd8b770e-fa16-44ce-afab-2978e3be95bf'
opt_stock25 = 'aabb1a4b-ad76-4d3e-93ab-f44453002cd1'

# cleanup
sb.table('carts').delete().eq('user_id', test_uid).execute()

# 테스트용 cart item 2개 생성
sb.table('carts').insert({
    'user_id': test_uid,
    'product_id': '11111111-1111-4111-8111-111111111111',
    'option_id': opt_stock25,
    'quantity': 2
}).execute()

opt_white = 'd566d240-9cde-4c1b-b220-7a7def6419d8'  # White M, stock=1
sb.table('carts').insert({
    'user_id': test_uid,
    'product_id': '11111111-1111-4111-8111-111111111111',
    'option_id': opt_white,
    'quantity': 1
}).execute()

print('✓ 테스트용 장바구니 데이터 생성 완료')

with app.test_client() as client:
    # 1. 비로그인 상태에서 /api/cart 조회
    r1 = client.get('/api/cart')
    print(f'1. 비로그인 /api/cart: {r1.status_code} (예상: 401)')
    assert r1.status_code == 401, 'FAIL: 비로그인이어야 401'

    # 2. 로그인 세션 설정
    with client.session_transaction() as sess:
        sess['user_id'] = test_uid
        sess['email'] = 'rkdspd12@naver.com'
        sess['name'] = '한지희'

    # 3. 로그인 후 /api/cart 조회
    r2 = client.get('/api/cart')
    print(f'2. 로그인 후 /api/cart: {r2.status_code} (예상: 200)')
    assert r2.status_code == 200, f'FAIL: 상태 코드는 {r2.status_code}'
    
    data = r2.get_json()
    print(f'   - success: {data["success"]}')
    print(f'   - item_count: {data["item_count"]} (예상: 2)')
    print(f'   - total_quantity: {data["total_quantity"]} (예상: 3)')
    print(f'   - total_price: {data["total_price"]:,}원')
    
    assert data['success'] is True
    assert data['item_count'] == 2
    assert data['total_quantity'] == 3
    
    # 각 아이템 정보 확인
    for i, item in enumerate(data['items'], 1):
        print(f'   - Item {i}: {item["product_name"]} ({item["color"]}/{item["size"]}) x {item["quantity"]}개 = {item["subtotal"]:,}원')
    
    # 4. GET /cart 페이지 요청
    r3 = client.get('/cart')
    print(f'3. GET /cart 페이지: {r3.status_code} (예상: 200)')
    assert r3.status_code == 200, 'FAIL: 페이지 로드 실패'
    assert 'cart.html' in r3.data.decode() or '주문 요약' in r3.data.decode(), 'FAIL: cart 페이지가 아님'

print('\n✅ 모든 엔드포인트 테스트 통과!')

# cleanup
sb.table('carts').delete().eq('user_id', test_uid).execute()
