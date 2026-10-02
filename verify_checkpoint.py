from app import create_app
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
app = create_app()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

user = sb.table('profiles').select('id, email').limit(1).execute().data[0]
uid = user['id']
email = user['email']

options = sb.table('product_options').select('id, product_id, stock, additional_price, option_value').execute().data
in_stock = [o for o in options if (o.get('stock') or 0) >= 5]
sold_out = [o for o in options if (o.get('stock') or 0) == 0]

opt1 = in_stock[0]
opt_zero = sold_out[0]

# 카트 비우기
sb.table('carts').delete().eq('user_id', uid).execute()

results = {}

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = uid
        sess['email'] = email
        sess['name'] = '테스터'

    # [1] 담기 테스트: POST /cart/add -> 200 & '담겼습니다'
    r1 = client.post('/cart/add', json={
        'product_id': opt1['product_id'],
        'option_id': opt1['id'],
        'quantity': 1
    })
    data1 = r1.get_json()
    cp1_ok = (r1.status_code == 200) and ('담겼습니다' in data1.get('message', ''))
    results['1. 담기 테스트'] = (cp1_ok, data1.get('message'))

    # [2] 중복 담기 테스트: 동일 옵션 1회 더 담기 -> 행 1개, 수량 2
    r2 = client.post('/cart/add', json={
        'product_id': opt1['product_id'],
        'option_id': opt1['id'],
        'quantity': 1
    })
    rows = sb.table('carts').select('*').eq('user_id', uid).execute().data
    cp2_ok = len(rows) == 1 and rows[0]['quantity'] == 2
    results['2. 중복 담기 테스트'] = (cp2_ok, f"행 개수: {len(rows)}, 수량: {rows[0]['quantity']}")

    # [3] 수량 변경 및 삭제 테스트
    cart_id = rows[0]['id']
    # 3-1. 재고 초과 에러
    r3_err = client.patch(f'/cart/{cart_id}', json={'quantity': opt1['stock'] + 10})
    ok_err = (r3_err.status_code == 400) and ('재고가 부족합니다' in r3_err.get_json().get('message', ''))
    # 3-2. 수량 변경 성공
    r3_patch = client.patch(f'/cart/{cart_id}', json={'quantity': 3})
    ok_patch = (r3_patch.status_code == 200) and (r3_patch.get_json().get('quantity') == 3)
    # 3-3. 삭제
    r3_del = client.delete(f'/cart/{cart_id}')
    rem = sb.table('carts').select('*').eq('id', cart_id).execute().data
    ok_del = (r3_del.status_code == 200) and len(rem) == 0
    results['3. 수량 변경/삭제 테스트'] = (ok_err and ok_patch and ok_del, f"재고초과방어: {ok_err}, 수량3변경: {ok_patch}, 삭제: {ok_del}")

    # [4] 품절 아이템 테스트
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': opt_zero['product_id'],
        'option_id': opt_zero['id'],
        'quantity': 1
    }).execute()
    r4 = client.get('/cart')
    html4 = r4.data.decode('utf-8')
    b1 = '품절됨' in html4
    b2 = 'disabled>주문하기</button>' in html4
    b3 = '품절된 상품이 있어 주문할 수 없습니다' in html4
    results['4. 품절 아이템 테스트'] = (b1 and b2 and b3, f"품절배지: {b1}, 주문버튼비활성화: {b2}, 안내문구: {b3}")
    sb.table('carts').delete().eq('user_id', uid).execute()

    # [5] 배송비 테스트 (50,000원 기준)
    # 5-1. 1개 (약 19,900원 -> 배송비 3,000원)
    sb.table('carts').insert({
        'user_id': uid,
        'product_id': opt1['product_id'],
        'option_id': opt1['id'],
        'quantity': 1
    }).execute()
    h5_1 = client.get('/cart').data.decode('utf-8')
    under_ok = '3,000원' in h5_1

    # 5-2. 3개 (약 59,700원 -> 배송비 무료)
    sb.table('carts').update({'quantity': 3}).eq('user_id', uid).execute()
    h5_2 = client.get('/cart').data.decode('utf-8')
    over_ok = '무료' in h5_2
    results['5. 배송비 테스트'] = (under_ok and over_ok, f"5만원미만(3,000원): {under_ok}, 5만원이상(무료): {over_ok}")

# 정리
sb.table('carts').delete().eq('user_id', uid).execute()

print("\n================== 체크포인트 5종 검증 결과 ==================")
all_pass = True
for name, (passed, detail) in results.items():
    tag = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"[{tag}] {name} -> {detail}")
print("==============================================================")
print("최종 결과:", "모두 정상 동작합니다!" if all_pass else "일부 실패가 있습니다.")
