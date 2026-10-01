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

# 테스트용 cart item 생성
cart1 = sb.table('carts').insert({
    'user_id': test_uid,
    'product_id': '11111111-1111-4111-8111-111111111111',
    'option_id': opt_stock25,
    'quantity': 2
}).execute()
cart1_id = cart1.data[0]['id']

opt_white = 'd566d240-9cde-4c1b-b220-7a7def6419d8'
cart2 = sb.table('carts').insert({
    'user_id': test_uid,
    'product_id': '11111111-1111-4111-8111-111111111111',
    'option_id': opt_white,
    'quantity': 1
}).execute()
cart2_id = cart2.data[0]['id']

print('✓ 테스트용 장바구니 데이터 생성 완료')
print(f'  Cart 1 ID: {cart1_id}')
print(f'  Cart 2 ID: {cart2_id}')

with app.test_client() as client:
    # 로그인 세션 설정
    with client.session_transaction() as sess:
        sess['user_id'] = test_uid
        sess['email'] = 'rkdspd12@naver.com'
        sess['name'] = '한지희'

    # 1. 비로그인 DELETE 요청 -> 401
    client_unauth = app.test_client()
    r1 = client_unauth.delete(f'/cart/{cart1_id}')
    print(f'\n1. 비로그인 DELETE: {r1.status_code} (예상: 401)')
    assert r1.status_code == 401
    print('   -> PASS!')

    # 2. 유효하지 않은 cart_id (UUID 아님) -> 400
    r2 = client.delete('/cart/invalid-id')
    print(f'2. 유효하지 않은 UUID: {r2.status_code} (예상: 400)')
    assert r2.status_code == 400
    print('   -> PASS!')

    # 3. 존재하지 않는 cart_id -> 404
    r3 = client.delete('/cart/00000000-0000-0000-0000-000000000000')
    print(f'3. 존재하지 않는 cart: {r3.status_code} (예상: 404)')
    assert r3.status_code == 404
    print('   -> PASS!')

    # 4. 다른 사용자의 cart_id 삭제 시도 -> 403
    # 먼저 다른 사용자의 cart item 생성
    other_uid = '2a55f3c7-45d5-4c2b-ad43-57eed78cd93f'
    other_cart = sb.table('carts').insert({
        'user_id': other_uid,
        'product_id': '11111111-1111-4111-8111-111111111111',
        'option_id': opt_stock25,
        'quantity': 3
    }).execute()
    other_cart_id = other_cart.data[0]['id']

    r4 = client.delete(f'/cart/{other_cart_id}')
    print(f'4. 다른 사용자의 cart 삭제: {r4.status_code} (예상: 403)')
    data = r4.get_json()
    assert r4.status_code == 403
    assert '다른 사용자' in data.get('message', '')
    print('   -> PASS!')

    # cleanup other user cart
    sb.table('carts').delete().eq('id', other_cart_id).execute()

    # 5. 정상 DELETE (cart1) -> 200
    r5 = client.delete(f'/cart/{cart1_id}')
    print(f'5. 정상 DELETE: {r5.status_code} (예상: 200)')
    data = r5.get_json()
    assert r5.status_code == 200
    assert data['success'] is True
    print('   -> PASS!')

    # 6. DB에서 삭제 확인
    cart_check = sb.table('carts').select('*').eq('id', cart1_id).execute()
    assert len(cart_check.data) == 0, 'DB에서 아이템이 삭제되지 않음'
    print(f'6. DB 삭제 확인: OK')
    print('   -> PASS!')

    # 7. 두 번째 아이템은 여전히 존재
    cart_check2 = sb.table('carts').select('*').eq('id', cart2_id).execute()
    assert len(cart_check2.data) == 1, '다른 아이템이 삭제됨'
    print(f'7. 다른 아이템 유지: OK')
    print('   -> PASS!')

    # 8. cart2도 정상 DELETE
    r8 = client.delete(f'/cart/{cart2_id}')
    assert r8.status_code == 200
    cart_check3 = sb.table('carts').select('*').eq('user_id', test_uid).execute()
    assert len(cart_check3.data) == 0, '모든 아이템이 삭제되지 않음'
    print(f'8. 모든 아이템 삭제: OK')
    print('   -> PASS!')

print('\n✅ 모든 DELETE 테스트 통과 (8/8)!')

# cleanup
sb.table('carts').delete().eq('user_id', test_uid).execute()
