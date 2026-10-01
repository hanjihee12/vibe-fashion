"""
메인 라우트 모듈
쇼핑몰 메인 페이지 및 상품 목록을 처리하는 Blueprint입니다.
Supabase DB 연동을 통해 상품 목록을 동적으로 조회합니다.
"""

import os
import sys
import uuid
import traceback
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client
from app.routes.auth import login_required

# 1. python-dotenv로 .env에서 Supabase 설정값 읽기
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabase 클라이언트 초기화 (오류 발생 시에도 앱 시작이 중단되지 않도록 예외 처리)
supabase: Client = None
supabase_admin: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"[ERROR] Supabase 클라이언트 초기화 실패: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
else:
    print("[WARN] .env에 SUPABASE_URL 또는 SUPABASE_ANON_KEY가 설정되지 않았습니다.", file=sys.stderr)

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"[WARN] Supabase 관리자 클라이언트 초기화 실패: {e}", file=sys.stderr)

# 2. Blueprint 인스턴스 생성
main_bp = Blueprint('main', __name__)

# 카테고리별 고화질 더미 상품 데이터 (상의, 하의, 악세사리)
DUMMY_TOP_PRODUCTS = [
    {
        "id": "top-2",
        "name": "클래식 릴렉스드 옥스포드 셔츠",
        "category": "상의",
        "price": "49,000원",
        "price_str": "49,000원",
        "badge": "NEW",
        "badge_color": "primary",
        "thumbnail_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&auto=format&fit=crop&q=80",
        "description": "사계절 내내 단품 또는 레이어드로 편안하게 착용 가능한 프리미엄 코튼 셔츠",
        "rating": 4.8,
        "reviews": 95
    },
    {
        "id": "top-4",
        "name": "시그니처 오버핏 후드 티셔츠",
        "category": "상의",
        "price": "59,000원",
        "price_str": "59,000원",
        "badge": "10% OFF",
        "badge_color": "success",
        "thumbnail_url": "https://images.unsplash.com/photo-1564557287817-3785e38ec1f5?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1564557287817-3785e38ec1f5?w=800&auto=format&fit=crop&q=80",
        "description": "탄탄한 헤비 웨이트 쮸리 원단으로 제작되어 흐트러짐 없는 스트릿 무드 후디",
        "rating": 4.7,
        "reviews": 64
    },
    {
        "id": "top-5",
        "name": "어텀 캐시미어 블렌드 가디건",
        "category": "상의",
        "price": "79,000원",
        "price_str": "79,000원",
        "badge": "FALL NEW",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop&q=80",
        "description": "가을 무드를 완성하는 차분한 카멜 톤과 부드러운 캐시미어 블렌드 루즈핏 가디건",
        "rating": 4.9,
        "reviews": 110
    },
    {
        "id": "top-6",
        "name": "브라운 스웨이드 오버 셔켓",
        "category": "상의",
        "price": "89,000원",
        "price_str": "89,000원",
        "badge": "AUTUMN",
        "badge_color": "danger",
        "thumbnail_url": "https://images.unsplash.com/photo-1516257984-b1b4d707412e?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1516257984-b1b4d707412e?w=800&auto=format&fit=crop&q=80",
        "description": "고급스러운 인조 스웨이드 텍스처로 셔츠와 자켓 겸용으로 연출하는 가을 아우터 셔츠",
        "rating": 4.8,
        "reviews": 73
    },
    {
        "id": "top-7",
        "name": "웜 하프 터틀넥 골지 니트",
        "category": "상의",
        "price": "46,000원",
        "price_str": "46,000원",
        "badge": "SEASON",
        "badge_color": "secondary",
        "thumbnail_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&auto=format&fit=crop&q=80",
        "description": "찬 바람을 막아주는 포근한 하프 터틀넥과 신축성 좋은 립 골지 짜임의 가을 이너 니트",
        "rating": 4.9,
        "reviews": 134
    }
]

DUMMY_BOTTOM_PRODUCTS = [
    {
        "id": "bot-2",
        "name": "와이드 핏 투턱 세미 슬랙스",
        "category": "하의",
        "price": "59,000원",
        "price_str": "59,000원",
        "badge": "HOT",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=800&auto=format&fit=crop&q=80",
        "description": "유려하게 떨어지는 투턱 주름 디테일로 길고 슬림한 다리 라인을 연출하는 슬랙스",
        "rating": 4.8,
        "reviews": 175
    },
    {
        "id": "bot-3",
        "name": "빈티지 스트레이트 워싱 진",
        "category": "하의",
        "price": "48,000원",
        "price_str": "48,000원",
        "badge": "NEW",
        "badge_color": "primary",
        "thumbnail_url": "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=800&auto=format&fit=crop&q=80",
        "description": "클래식한 레귤러 스트레이트 핏과 은은한 브러쉬 워싱이 매력적인 청바지",
        "rating": 4.7,
        "reviews": 89
    },
    {
        "id": "bot-4",
        "name": "유틸리티 카고 조거 팬츠",
        "category": "하의",
        "price": "45,000원",
        "price_str": "45,000원",
        "badge": "TREND",
        "badge_color": "info text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=800&auto=format&fit=crop&q=80",
        "description": "사이드 입체 카고 포켓과 밑단 밴딩으로 스포티하고 편안한 활동성을 제공",
        "rating": 4.8,
        "reviews": 112
    },
    {
        "id": "bot-5",
        "name": "어텀 딥카키 와이드 코듀로이 팬츠",
        "category": "하의",
        "price": "52,000원",
        "price_str": "52,000원",
        "badge": "FALL NEW",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=800&auto=format&fit=crop&q=80",
        "description": "도톰한 골덴 원단과 깊이 있는 카키 컬러감으로 가을·초겨울 시즌 최적의 무드를 주는 팬츠",
        "rating": 4.9,
        "reviews": 84
    },
    {
        "id": "bot-6",
        "name": "클래식 헤링본 울 테이퍼드 슬랙스",
        "category": "하의",
        "price": "68,000원",
        "price_str": "68,000원",
        "badge": "CLASSIC",
        "badge_color": "secondary",
        "thumbnail_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop&q=80",
        "description": "은은한 헤링본 패턴의 울 혼방 소재로 클래식하고 포멀한 가을 룩북 연출 슬랙스",
        "rating": 4.8,
        "reviews": 59
    },
    {
        "id": "bot-7",
        "name": "다크 브라운 스트레이트 카펜터 팬츠",
        "category": "하의",
        "price": "56,000원",
        "price_str": "56,000원",
        "badge": "AUTUMN",
        "badge_color": "danger",
        "thumbnail_url": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&auto=format&fit=crop&q=80",
        "description": "가을 감성의 딥 브라운 컬러에 해머 루프와 툴 포켓 디테일이 돋보이는 워크웨어 팬츠",
        "rating": 4.9,
        "reviews": 97
    }
]

DUMMY_ACC_PRODUCTS = [
    {
        "id": "acc-1",
        "name": "미니멀 레더 크로스 바디백",
        "category": "악세사리",
        "price": "89,000원",
        "price_str": "89,000원",
        "badge": "BEST",
        "badge_color": "danger",
        "thumbnail_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&auto=format&fit=crop&q=80",
        "description": "모던한 스퀘어 쉐입과 부드러운 천연 소가죽 질감을 살린 데일리 에센셜 백",
        "rating": 4.9,
        "reviews": 154
    },
    {
        "id": "acc-2",
        "name": "실버 레이어드 체인 네크리스",
        "category": "악세사리",
        "price": "25,000원",
        "price_str": "25,000원",
        "badge": "NEW",
        "badge_color": "primary",
        "thumbnail_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&auto=format&fit=crop&q=80",
        "description": "써지컬 스틸 소재로 변색 없이 은은한 포인트를 주는 투웨이 레이어드 목걸이",
        "rating": 4.8,
        "reviews": 92
    },
    {
        "id": "acc-3",
        "name": "클래식 코튼 베이직 볼캡",
        "category": "악세사리",
        "price": "29,000원",
        "price_str": "29,000원",
        "badge": "HOT",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&auto=format&fit=crop&q=80",
        "description": "깊은 깊이감과 안정적인 챙 각도로 얼굴이 작아 보이는 데일리 핏 캡",
        "rating": 4.9,
        "reviews": 230
    },
    {
        "id": "acc-4",
        "name": "레더 빈티지 스퀘어 버클 벨트",
        "category": "악세사리",
        "price": "32,000원",
        "price_str": "32,000원",
        "badge": "MD PICK",
        "badge_color": "secondary",
        "thumbnail_url": "https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=800&auto=format&fit=crop&q=80",
        "description": "빈티지 실버 버클과 은은한 광택감의 가죽으로 슬랙스 및 데님과 완벽 조화",
        "rating": 4.7,
        "reviews": 68
    }
]

DUMMY_PRODUCTS = DUMMY_TOP_PRODUCTS + DUMMY_BOTTOM_PRODUCTS + DUMMY_ACC_PRODUCTS


def classify_category(category_name, product_name=""):
    """
    상품 카테고리명 및 상품명을 분석하여 'top', 'bottom', 'acc', 'other' 중 하나로 분류
    """
    text = f"{category_name} {product_name}".lower()
    if any(k in text for k in ['상의', 'top', '셔츠', '티셔츠', '니트', '스웨터', '후드']):
        return 'top'
    elif any(k in text for k in ['하의', 'bottom', '팬츠', '슬랙스', '데님', '청바지', '바지']):
        return 'bottom'
    elif any(k in text for k in ['악세사리', '액세서리', 'acc', '가방', '모자', '주얼리', '목걸이', '벨트', 'bag', 'cap']):
        return 'acc'
    return 'other'


def get_categorized_products():
    """
    Supabase 및 더미 데이터를 기반으로 상의, 하의, 악세사리별로 분류된 상품 딕셔너리 반환
    """
    products = []

    if supabase:
        try:
            response = (
                supabase.table('products')
                .select('*, product_images(image_url, is_thumbnail, display_order), categories(name, slug)')
                .eq('is_active', True)
                .execute()
            )
            raw_data = response.data or []

            for item in raw_data:
                raw_price = item.get('price', 0)
                try:
                    formatted_price = f"{int(raw_price):,}원"
                except (ValueError, TypeError):
                    formatted_price = f"{raw_price}원"

                images = item.get('product_images') or []
                thumbnail_url = ''
                for img in sorted(images, key=lambda x: x.get('display_order', 0)):
                    if img.get('is_thumbnail'):
                        thumbnail_url = img.get('image_url')
                        break
                if not thumbnail_url and images:
                    thumbnail_url = images[0].get('image_url')
                if not thumbnail_url:
                    thumbnail_url = f"https://picsum.photos/seed/{item.get('id', 'item')}/600/800"

                category_name = 'FASHION'
                if item.get('categories') and isinstance(item['categories'], dict):
                    category_name = item['categories'].get('name', 'FASHION')

                products.append({
                    'id': str(item.get('id')),
                    'name': item.get('name'),
                    'price': formatted_price,
                    'price_str': formatted_price,
                    'thumbnail_url': thumbnail_url,
                    'image': thumbnail_url,
                    'description': item.get('description', ''),
                    'category': category_name,
                    'badge': 'NEW',
                    'badge_color': 'coral',
                    'is_active': item.get('is_active', True),
                    'is_featured': item.get('is_featured', True)
                })
        except Exception as e:
            print(f"[ERROR] Supabase 상품 조회 실패: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    # 카테고리별 분류
    top_list = [p for p in products if classify_category(p.get('category', ''), p.get('name', '')) == 'top']
    bottom_list = [p for p in products if classify_category(p.get('category', ''), p.get('name', '')) == 'bottom']
    acc_list = [p for p in products if classify_category(p.get('category', ''), p.get('name', '')) == 'acc']

    # Supabase 데이터와 가을 신상품 더미 데이터를 병합하여 항상 풍성하게 노출
    def merge_products(db_list, dummy_list):
        existing_names = {p['name'] for p in db_list}
        merged = list(db_list)
        for item in dummy_list:
            if item['name'] not in existing_names:
                merged.append(item)
        return merged

    final_top = merge_products(top_list, DUMMY_TOP_PRODUCTS)
    final_bottom = merge_products(bottom_list, DUMMY_BOTTOM_PRODUCTS)
    final_acc = merge_products(acc_list, DUMMY_ACC_PRODUCTS)
    all_products = final_top + final_bottom + final_acc

    return {
        'all': all_products,
        'top': final_top,
        'bottom': final_bottom,
        'acc': final_acc
    }


def get_featured_products():
    """
    기존 호환성 유지용 함수
    """
    categorized = get_categorized_products()
    return categorized['all'][:8] if categorized['all'] else DUMMY_PRODUCTS


@main_bp.route('/')
def index():
    """
    메인 페이지 라우트
    상의, 하의, 악세사리별로 분류된 상품 목록을 index.html 템플릿에 전달합니다.
    """
    data = get_categorized_products()
    return render_template(
        'index.html',
        mall_name="VIBE-FASHION",
        products=data['all'],
        top_products=data['top'],
        bottom_products=data['bottom'],
        acc_products=data['acc']
    )


@main_bp.route('/products/<product_id>')
@main_bp.route('/product/<product_id>')
def product_detail(product_id):
    """
    상품 상세 정보 라우트 (GET /products/<product_id>)
    - Supabase에서 product_id로 상품 정보 조회
    - 상품 이미지(목록 및 대표이미지), 이름, 가격(할인가/정가), 설명 표시
    - product_options 테이블에서 해당 상품의 색상(color) 목록을 DISTINCT로 조회
    """
    product = None
    colors = []

    if supabase and is_valid_uuid(product_id):
        try:
            # 1. 상품 기본 정보 및 이미지, 카테고리 조회
            res = (
                supabase.table('products')
                .select('*, product_images(*), categories(name)')
                .eq('id', product_id)
                .execute()
            )
            if res.data:
                item = res.data[0]
                raw_price = item.get('price', 0)
                raw_orig_price = item.get('original_price') or raw_price

                try:
                    price_val = int(raw_price)
                    price_str = f"{price_val:,}원"
                except (ValueError, TypeError):
                    price_val = 0
                    price_str = f"{raw_price}원"

                try:
                    orig_price_val = int(raw_orig_price)
                    orig_price_str = f"{orig_price_val:,}원"
                except (ValueError, TypeError):
                    orig_price_val = 0
                    orig_price_str = f"{raw_orig_price}원"

                # 할인율 계산
                discount_rate = 0
                if orig_price_val > price_val and orig_price_val > 0:
                    discount_rate = int(round((orig_price_val - price_val) / orig_price_val * 100))

                # 이미지 목록 정렬
                raw_images = item.get('product_images') or []
                sorted_images = sorted(raw_images, key=lambda x: x.get('display_order', 0))
                image_urls = [img.get('image_url') for img in sorted_images if img.get('image_url')]

                thumbnail_url = ''
                for img in sorted_images:
                    if img.get('is_thumbnail'):
                        thumbnail_url = img.get('image_url')
                        break
                if not thumbnail_url and image_urls:
                    thumbnail_url = image_urls[0]
                if not thumbnail_url:
                    thumbnail_url = f"https://picsum.photos/seed/{product_id}/800/1000"
                    image_urls = [thumbnail_url]

                category_name = item.get('categories', {}).get('name') if isinstance(item.get('categories'), dict) else '패션'

                product = {
                    'id': str(item.get('id')),
                    'name': item.get('name'),
                    'price': price_val,
                    'price_str': price_str,
                    'original_price': orig_price_val,
                    'original_price_str': orig_price_str,
                    'discount_rate': discount_rate,
                    'thumbnail_url': thumbnail_url,
                    'images': image_urls,
                    'description': item.get('description', ''),
                    'category': category_name,
                    'is_active': item.get('is_active', True)
                }

                # 2. product_options 테이블에서 해당 상품의 색상(color) 목록을 DISTINCT로 조회
                opt_res = (
                    supabase.table('product_options')
                    .select('color')
                    .eq('product_id', product_id)
                    .not_.is_('color', 'null')
                    .execute()
                )
                if opt_res.data:
                    seen = set()
                    for row in opt_res.data:
                        c = row.get('color')
                        if c and c not in seen:
                            seen.add(c)
                            colors.append(c)
        except Exception as e:
            print(f"[ERROR] 상품 상세 조회 실패 ({product_id}): {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    if not product:
        # 더미 데이터 fallback
        dummy = next((p for p in DUMMY_PRODUCTS if str(p.get("id")) == str(product_id)), None)
        if dummy:
            raw_p = dummy.get('price_str', dummy.get('price', '0원'))
            num_p = 49000
            try:
                num_p = int(''.join(filter(str.isdigit, str(raw_p))))
            except Exception:
                pass
            product = {
                'id': str(dummy.get('id')),
                'name': dummy.get('name'),
                'price': num_p,
                'price_str': f"{num_p:,}원",
                'original_price': int(num_p * 1.2),
                'original_price_str': f"{int(num_p * 1.2):,}원",
                'discount_rate': 20,
                'thumbnail_url': dummy.get('thumbnail_url') or dummy.get('image'),
                'images': [dummy.get('thumbnail_url') or dummy.get('image')],
                'description': dummy.get('description', ''),
                'category': dummy.get('category', '패션'),
                'is_active': True
            }
            colors = ["Black", "White", "Gray"]

    if not product:
        return render_template('404.html', message="상품을 찾을 수 없습니다."), 404

    return render_template(
        'detail.html',
        product=product,
        colors=colors,
        mall_name="VIBE-FASHION"
    )


@main_bp.route('/api/products/<product_id>/options')
def api_product_options(product_id):
    """
    선택한 색상에 해당하는 사이즈 목록 및 재고/추가금 조회 API
    Query Param: color (예: ?color=Black)
    """
    color = request.args.get('color', '').strip()
    if not color:
        return jsonify({
            'status': 'error',
            'message': '색상(color) 파라미터가 필요합니다.',
            'options': []
        }), 400

    options = []
    if supabase and is_valid_uuid(product_id):
        try:
            res = (
                supabase.table('product_options')
                .select('id, size, stock, additional_price')
                .eq('product_id', product_id)
                .eq('color', color)
                .not_.is_('size', 'null')
                .execute()
            )
            raw_data = res.data or []

            # 사이즈 순서 정렬 (S, M, L, XL 등 표준 정렬)
            size_order = {'XS': 1, 'S': 2, 'M': 3, 'L': 4, 'XL': 5, 'XXL': 6, 'FREE': 7}
            sorted_data = sorted(
                raw_data,
                key=lambda x: size_order.get(str(x.get('size')).upper(), 99)
            )

            for opt in sorted_data:
                stock_val = int(opt.get('stock', 0) or 0)
                add_price = int(opt.get('additional_price', 0) or 0)
                options.append({
                    'id': str(opt.get('id')),
                    'size': opt.get('size'),
                    'stock': stock_val,
                    'is_soldout': (stock_val <= 0),
                    'additional_price': add_price,
                    'additional_price_str': f"+{add_price:,}원" if add_price > 0 else ""
                })
        except Exception as e:
            print(f"[ERROR] 옵션 조회 API 오류 ({product_id}, {color}): {e}", file=sys.stderr)
            return jsonify({'status': 'error', 'message': str(e), 'options': []}), 500

    if not options:
        # 더미 데이터 fallback
        for s, stk, add_p in [('S', 0, 0), ('M', 25, 0), ('L', 10, 2000)]:
            options.append({
                'id': f"dummy-{color}-{s}",
                'size': s,
                'stock': stk,
                'is_soldout': (stk <= 0),
                'additional_price': add_p,
                'additional_price_str': f"+{add_p:,}원" if add_p > 0 else ""
            })

    return jsonify({
        'status': 'success',
        'product_id': product_id,
        'color': color,
        'options': options
    })


@main_bp.route('/api/products')
def api_products():
    """
    상품 목록 JSON API
    프론트엔드 비동기 요청 시 Supabase 상품 목록을 반환합니다.
    """
    products = get_featured_products()
    return jsonify({
        "status": "success",
        "count": len(products),
        "data": products
    })


def is_valid_uuid(val):
    """문자열이 유효한 UUID 형식인지 확인"""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@main_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    장바구니 담기 라우트 (POST /cart/add)
    - 요청 body: product_option_id, quantity
    - 로그인 안 했으면 /auth/login 으로 리다이렉트
    - 담기 전에 product_options.stock을 조회해서 요청 수량보다 적으면
      "재고가 부족합니다(현재 N개)" 에러 반환, DB에 아무 것도 쓰지 않음
    - carts 테이블에 upsert (같은 옵션이면 수량 누적)
    - 누적 후 수량이 재고를 초과하게 되는 경우도 동일하게 에러 처리
    - 성공 시 JSON: {"success": true, "message": "장바구니에 담겼습니다"}
    """
    # 1. 로그인 여부 확인 (비로그인 시 401 JSON 응답)
    user_id = session.get("user_id")
    user_email = session.get("email")
    if not user_id:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    # 2. 요청 파라미터 파싱
    data = request.get_json(silent=True) or request.form or {}
    product_option_id = str(data.get("product_option_id") or data.get("option_id") or "").strip()
    raw_quantity = data.get("quantity", 1)

    try:
        quantity = int(raw_quantity)
    except (ValueError, TypeError):
        quantity = 1

    if not product_option_id:
        return jsonify({"success": False, "message": "상품 옵션 ID가 필요합니다."}), 400

    if quantity <= 0:
        return jsonify({"success": False, "message": "수량은 1개 이상이어야 합니다."}), 400

    db = supabase_admin or supabase
    if not db:
        return jsonify({"success": False, "message": "데이터베이스 연결에 실패했습니다."}), 500

    # 3. product_options 조회 및 재고 확인
    opt_res = db.table('product_options').select('*').eq('id', product_option_id).execute()
    if not opt_res.data:
        return jsonify({"success": False, "message": "선택한 상품 옵션을 찾을 수 없습니다."}), 404

    option_row = opt_res.data[0]
    product_id = option_row.get('product_id')
    stock = int(option_row.get('stock', 0) or 0)

    # 요청 수량이 재고보다 많은 경우 즉시 에러 반환 (DB에 아무것도 쓰지 않음)
    if quantity > stock:
        return jsonify({
            "success": False,
            "message": f"재고가 부족합니다(현재 {stock}개)"
        }), 400

    # 4. 사용자 UUID 확인 (carts 테이블 user_id 외래키용)
    user_uuid = None
    if is_valid_uuid(user_id):
        user_uuid = str(user_id)
    elif user_email:
        prof_res = db.table('profiles').select('id').eq('email', user_email).execute()
        if prof_res.data:
            user_uuid = str(prof_res.data[0]['id'])

    if not user_uuid and user_email and supabase_admin:
        try:
            auth_users = supabase_admin.auth.admin.list_users()
            for u in auth_users:
                if (u.email or "").lower() == user_email.lower():
                    user_uuid = str(u.id)
                    break
        except Exception:
            pass

    if not user_uuid:
        prof_any = db.table('profiles').select('id').limit(1).execute()
        if prof_any.data:
            user_uuid = str(prof_any.data[0]['id'])

    if not user_uuid:
        return jsonify({"success": False, "message": "사용자 프로필 정보를 확인할 수 없습니다."}), 400

    # 5. carts 테이블 기존 수량 확인 (같은 옵션이면 수량 누적 upsert)
    cart_query = db.table('carts').select('*').eq('user_id', user_uuid).eq('option_id', product_option_id).execute()
    existing_cart = cart_query.data[0] if cart_query.data else None

    if existing_cart:
        current_cart_qty = int(existing_cart.get('quantity', 0) or 0)
        new_total_qty = current_cart_qty + quantity

        # 누적 후 수량이 재고를 초과하게 되는 경우 에러 처리
        if new_total_qty > stock:
            return jsonify({
                "success": False,
                "message": f"재고가 부족합니다(현재 {stock}개)"
            }), 400

        # 수량 갱신
        db.table('carts').update({
            'quantity': new_total_qty,
            'updated_at': 'now()'
        }).eq('id', existing_cart['id']).execute()
    else:
        # 신규 삽입
        db.table('carts').insert({
            'user_id': user_uuid,
            'product_id': product_id,
            'option_id': product_option_id,
            'quantity': quantity
        }).execute()

    response = jsonify({
        "success": True,
        "message": "장바구니에 담겼습니다"
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


@main_bp.route('/cart/<cart_id>', methods=['PATCH'])
def update_cart_quantity(cart_id):
    """
    장바구니 수량 변경 라우트 (PATCH /cart/<cart_id>)
    - 요청 body: quantity (변경할 새 수량)
    - 본인 소유의 장바구니 아이템인지 확인 (다른 사용자의 cart_id 접근 차단)
    - quantity가 1 미만이면 에러
    - 변경하려는 quantity가 해당 옵션의 stock을 초과하면
      "재고가 부족합니다(현재 N개)" 에러, 변경하지 않음
    - 성공 시 UPDATE 후 새 소계(subtotal) 반환
    """
    # 1. 로그인 여부 확인
    user_id = session.get("user_id")
    user_email = session.get("email")
    if not user_id:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    # 2. cart_id 유효성 확인
    if not is_valid_uuid(cart_id):
        return jsonify({"success": False, "message": "유효하지 않은 장바구니 ID입니다."}), 400

    # 3. 요청 파라미터 파싱
    data = request.get_json(silent=True) or request.form or {}
    raw_quantity = data.get("quantity")

    if raw_quantity is None:
        return jsonify({"success": False, "message": "새 수량(quantity)이 필요합니다."}), 400

    try:
        quantity = int(raw_quantity)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "수량은 정수여야 합니다."}), 400

    if quantity < 1:
        return jsonify({"success": False, "message": "수량은 1개 이상이어야 합니다."}), 400

    db = supabase_admin or supabase
    if not db:
        return jsonify({"success": False, "message": "데이터베이스 연결에 실패했습니다."}), 500

    # 4. cart_id로 장바구니 아이템 조회
    cart_res = db.table('carts').select('*').eq('id', cart_id).execute()
    if not cart_res.data:
        return jsonify({"success": False, "message": "해당 장바구니 항목을 찾을 수 없습니다."}), 404

    cart_item = cart_res.data[0]
    cart_user_id = cart_item.get('user_id')
    option_id = cart_item.get('option_id')

    # 5. 권한 확인 (본인 소유의 장바구니 아이템인지 확인)
    user_uuid = None
    if is_valid_uuid(user_id):
        user_uuid = str(user_id)
    elif user_email:
        prof_res = db.table('profiles').select('id').eq('email', user_email).execute()
        if prof_res.data:
            user_uuid = str(prof_res.data[0]['id'])

    if not user_uuid:
        prof_any = db.table('profiles').select('id').limit(1).execute()
        if prof_any.data:
            user_uuid = str(prof_any.data[0]['id'])

    if str(cart_user_id) != str(user_uuid):
        return jsonify({"success": False, "message": "다른 사용자의 장바구니에 접근할 수 없습니다."}), 403

    # 6. 옵션의 재고 확인
    opt_res = db.table('product_options').select('*').eq('id', option_id).execute()
    if not opt_res.data:
        return jsonify({"success": False, "message": "해당 상품 옵션을 찾을 수 없습니다."}), 404

    option_row = opt_res.data[0]
    stock = int(option_row.get('stock', 0) or 0)
    additional_price = int(option_row.get('additional_price', 0) or 0)

    # 7. 변경하려는 quantity가 해당 옵션의 stock을 초과하는지 확인
    if quantity > stock:
        return jsonify({
            "success": False,
            "message": f"재고가 부족합니다(현재 {stock}개)"
        }), 400

    # 8. quantity 업데이트
    db.table('carts').update({
        'quantity': quantity,
        'updated_at': 'now()'
    }).eq('id', cart_id).execute()

    # 9. 소계 계산 (product의 price + option의 additional_price) × quantity
    prod_res = db.table('products').select('price').eq('id', cart_item.get('product_id')).execute()
    if not prod_res.data:
        return jsonify({"success": False, "message": "상품 정보를 찾을 수 없습니다."}), 404

    base_price = int(prod_res.data[0].get('price', 0) or 0)
    unit_price = base_price + additional_price
    subtotal = unit_price * quantity

    return jsonify({
        "success": True,
        "message": "수량이 변경되었습니다",
        "quantity": quantity,
        "unit_price": unit_price,
        "subtotal": subtotal
    })


@main_bp.route('/cart/<cart_id>', methods=['DELETE'])
def delete_cart_item(cart_id):
    """
    장바구니 아이템 삭제 라우트 (DELETE /cart/<cart_id>)
    - 로그인 여부 확인
    - 본인 소유의 장바구니 아이템인지 확인
    - 성공 시 아이템 삭제 후 {"success": true} 반환
    """
    # 1. 로그인 여부 확인
    user_id = session.get("user_id")
    user_email = session.get("email")
    if not user_id:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    # 2. cart_id 유효성 확인
    if not is_valid_uuid(cart_id):
        return jsonify({"success": False, "message": "유효하지 않은 장바구니 ID입니다."}), 400

    db = supabase_admin or supabase
    if not db:
        return jsonify({"success": False, "message": "데이터베이스 연결에 실패했습니다."}), 500

    # 3. cart_id로 장바구니 아이템 조회
    cart_res = db.table('carts').select('*').eq('id', cart_id).execute()
    if not cart_res.data:
        return jsonify({"success": False, "message": "해당 장바구니 항목을 찾을 수 없습니다."}), 404

    cart_item = cart_res.data[0]
    cart_user_id = cart_item.get('user_id')

    # 4. 권한 확인 (본인 소유의 장바구니 아이템인지 확인)
    user_uuid = None
    if is_valid_uuid(user_id):
        user_uuid = str(user_id)
    elif user_email:
        prof_res = db.table('profiles').select('id').eq('email', user_email).execute()
        if prof_res.data:
            user_uuid = str(prof_res.data[0]['id'])

    if not user_uuid:
        prof_any = db.table('profiles').select('id').limit(1).execute()
        if prof_any.data:
            user_uuid = str(prof_any.data[0]['id'])

    if str(cart_user_id) != str(user_uuid):
        return jsonify({"success": False, "message": "다른 사용자의 장바구니에 접근할 수 없습니다."}), 403

    # 5. 장바구니 아이템 삭제
    try:
        db.table('carts').delete().eq('id', cart_id).execute()
    except Exception as e:
        print(f"[ERROR] 장바구니 삭제 오류: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": "장바구니 삭제 중 오류가 발생했습니다."}), 500

    return jsonify({
        "success": True,
        "message": "장바구니에서 제거되었습니다."
    })


@main_bp.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    """
    마이페이지 라우트 (로그인 필수)
    - 탭1: 내 정보 (이름, 이메일, 기본 배송지 표시 및 수정 폼)
    - 탭2: 주문 내역 (안내 문구)
    - 탭3: 환불 내역 (안내 문구)
    """
    user_id = session.get("user_id")
    user_email = session.get("email")

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if full_name:
            session["name"] = full_name
        if phone:
            session["phone"] = phone

        if supabase and (user_id or user_email):
            try:
                update_data = {
                    "full_name": full_name,
                    "phone": phone,
                    "address": address
                }
                # id가 유효한 UUID인 경우 id로 업데이트
                if is_valid_uuid(user_id):
                    supabase.table('profiles').update(update_data).eq('id', user_id).execute()
                elif user_email:
                    # 소셜 로그인 계정 등 UUID가 아닌 경우 email로 업데이트
                    supabase.table('profiles').update(update_data).eq('email', user_email).execute()
            except Exception as e:
                print(f"[WARN] profiles 업데이트 오류: {e}", file=sys.stderr)

        return redirect(url_for('main.mypage', updated='true'))

    profile = None
    if supabase and (user_id or user_email):
        try:
            # 1. user_id가 UUID인 경우 id로 조회 시도
            if is_valid_uuid(user_id):
                res = supabase.table('profiles').select('*').eq('id', user_id).execute()
                if res.data:
                    profile = res.data[0]
            # 2. email로 조회 시도
            if not profile and user_email:
                res = supabase.table('profiles').select('*').eq('email', user_email).execute()
                if res.data:
                    profile = res.data[0]
        except Exception as e:
            print(f"[WARN] profiles 조회 오류: {e}", file=sys.stderr)

    if not profile:
        profile = {
            "id": user_id,
            "email": user_email or "",
            "full_name": session.get("name") or "고객",
            "phone": session.get("phone") or "",
            "address": "",
            "grade": "BRONZE"
        }

    # 소셜 로그인 사용자 여부 판별 (kakao_, ms_ 등 또는 이메일 로그인 여부)
    # user_id가 kakao_ 로 시작하거나, email이 @vibe-fashion.com 가상 도메인인 경우 소셜
    # 또는 supabase auth 사용자 정보를 조회해 provider 확인
    is_social_user = False
    if str(user_id or "").startswith("kakao_") or str(user_id or "").startswith("ms_") or "@vibe-fashion.com" in str(user_email or ""):
        is_social_user = True
    elif supabase_admin and is_valid_uuid(user_id):
        try:
            auth_user = supabase_admin.auth.admin.get_user_by_id(str(user_id))
            if auth_user and auth_user.user:
                provider = (auth_user.user.app_metadata or {}).get("provider", "email")
                if provider != "email":
                    is_social_user = True
        except Exception:
            pass

    updated = request.args.get('updated') == 'true'
    pwd_success = request.args.get('pwd_success')
    pwd_error = request.args.get('pwd_error')

    return render_template(
        'mypage.html',
        mall_name="VIBE-FASHION",
        profile=profile,
        updated=updated,
        is_social_user=is_social_user,
        pwd_success=pwd_success,
        pwd_error=pwd_error
    )


@main_bp.route('/mypage/change-password', methods=['POST'])
@login_required
def change_password():
    """
    비밀번호 변경 처리 라우트 (POST)
    - 기존 비밀번호 검증 (Supabase sign_in_with_password 방식 확인)
    - 새 비밀번호 검증 (최소 4자리 이상)
    - 새 비밀번호와 기존 비밀번호 동일 여부 체크
    - Supabase update_user_by_id()를 통한 안전한 비밀번호 변경
    """
    user_id = session.get("user_id")
    user_email = session.get("email")

    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not current_password:
        return redirect(url_for('main.mypage', pwd_error="현재 비밀번호를 입력해주세요."))

    if not new_password:
        return redirect(url_for('main.mypage', pwd_error="새 비밀번호를 입력해주세요."))

    # Day 4 이메일 가입 검증 조건: 4자리 이상
    if len(new_password) < 4:
        return redirect(url_for('main.mypage', pwd_error="새 비밀번호를 4자리 이상 입력해주세요."))

    if new_password != confirm_password:
        return redirect(url_for('main.mypage', pwd_error="새 비밀번호와 확인용 비밀번호가 일치하지 않습니다."))

    if new_password == current_password:
        return redirect(url_for('main.mypage', pwd_error="새로운 비밀번호가 현재 비밀번호와 동일합니다."))

    if not user_email:
        return redirect(url_for('main.mypage', pwd_error="사용자 이메일 정보를 확인할 수 없습니다."))

    # 1. 기존 비밀번호 검증 (Supabase 재인증 시도)
    auth_verified = False
    auth_uid = None
    if supabase:
        try:
            auth_res = supabase.auth.sign_in_with_password({
                "email": user_email,
                "password": current_password
            })
            if auth_res and auth_res.user:
                auth_verified = True
                auth_uid = auth_res.user.id
        except Exception:
            auth_verified = False

    if not auth_verified:
        return redirect(url_for('main.mypage', pwd_error="현재 비밀번호가 일치하지 않습니다."))

    # 2. Supabase update_user_by_id() 사용해 비밀번호 변경
    target_uid = auth_uid or (str(user_id) if is_valid_uuid(user_id) else None)
    if not target_uid:
        return redirect(url_for('main.mypage', pwd_error="비밀번호를 변경할 대상 계정 ID를 찾을 수 없습니다."))

    try:
        admin_client = supabase_admin or supabase
        if hasattr(admin_client.auth, 'admin') and hasattr(admin_client.auth.admin, 'update_user_by_id'):
            admin_client.auth.admin.update_user_by_id(
                target_uid,
                {"password": new_password}
            )
        else:
            # fallback: 일반 auth.update_user
            supabase.auth.update_user({"password": new_password})

        return redirect(url_for('main.mypage', pwd_success="비밀번호가 변경되었습니다."))
    except Exception as e:
        print(f"[ERROR] 비밀번호 변경 오류: {e}", file=sys.stderr)
        return redirect(url_for('main.mypage', pwd_error=f"비밀번호 변경 처리 중 오류가 발생했습니다: {str(e)}"))


@main_bp.route('/api/cart', methods=['GET'])
def get_cart_items():
    """
    장바구니 아이템 목록 API (GET /api/cart)
    - 로그인한 사용자의 모든 장바구니 아이템 반환
    - 응답: [
        {
            "id": "cart-id",
            "product_id": "product-id",
            "option_id": "option-id",
            "product_name": "상품명",
            "color": "색상",
            "size": "사이즈",
            "base_price": 19900,
            "additional_price": 0,
            "unit_price": 19900,
            "quantity": 2,
            "subtotal": 39800,
            "stock": 25,
            "image": "url"
        },
        ...
      ]
    """
    # 1. 로그인 여부 확인
    user_id = session.get("user_id")
    user_email = session.get("email")
    
    if not user_id:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    db = supabase_admin or supabase
    if not db:
        return jsonify({"success": False, "message": "데이터베이스 연결에 실패했습니다."}), 500

    # 2. 사용자 UUID 확인
    user_uuid = None
    if is_valid_uuid(user_id):
        user_uuid = str(user_id)
    elif user_email:
        prof_res = db.table('profiles').select('id').eq('email', user_email).execute()
        if prof_res.data:
            user_uuid = str(prof_res.data[0]['id'])

    if not user_uuid:
        prof_any = db.table('profiles').select('id').limit(1).execute()
        if prof_any.data:
            user_uuid = str(prof_any.data[0]['id'])

    if not user_uuid:
        return jsonify({"success": False, "message": "사용자 프로필 정보를 확인할 수 없습니다."}), 400

    # 3. carts 조회 (user_id로 필터링)
    try:
        carts_res = db.table('carts').select('*').eq('user_id', user_uuid).order('created_at', desc=False).execute()
        carts_data = carts_res.data or []
    except Exception as e:
        print(f"[ERROR] 장바구니 조회 오류: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": "장바구니 조회 중 오류가 발생했습니다."}), 500

    cart_items = []
    for cart in carts_data:
        cart_id = cart.get('id')
        product_id = cart.get('product_id')
        option_id = cart.get('option_id')
        quantity = int(cart.get('quantity', 1) or 1)

        # 4. 상품 정보 조회
        try:
            prod_res = db.table('products').select('*').eq('id', product_id).execute()
            if not prod_res.data:
                continue
            product = prod_res.data[0]
            product_name = product.get('name', '상품명')
            base_price = int(product.get('price', 0) or 0)
        except Exception as e:
            print(f"[WARN] 상품 조회 오류 ({product_id}): {e}", file=sys.stderr)
            continue

        # 5. 옵션 정보 조회 (color, size, stock, additional_price)
        try:
            opt_res = db.table('product_options').select('*').eq('id', option_id).execute()
            if not opt_res.data:
                continue
            option = opt_res.data[0]
            color = option.get('color', 'N/A')
            size = option.get('size', 'N/A')
            stock = int(option.get('stock', 0) or 0)
            additional_price = int(option.get('additional_price', 0) or 0)
        except Exception as e:
            print(f"[WARN] 옵션 조회 오류 ({option_id}): {e}", file=sys.stderr)
            continue

        # 6. 상품 이미지 조회
        image_url = ""
        try:
            img_res = db.table('product_images').select('image_url').eq('product_id', product_id).limit(1).execute()
            if img_res.data:
                image_url = img_res.data[0].get('image_url', '')
        except Exception as e:
            print(f"[WARN] 이미지 조회 오류 ({product_id}): {e}", file=sys.stderr)

        # 7. 소계 계산
        unit_price = base_price + additional_price
        subtotal = unit_price * quantity

        cart_items.append({
            "id": cart_id,
            "product_id": product_id,
            "option_id": option_id,
            "product_name": product_name,
            "color": color,
            "size": size,
            "base_price": base_price,
            "additional_price": additional_price,
            "unit_price": unit_price,
            "quantity": quantity,
            "subtotal": subtotal,
            "stock": stock,
            "image": image_url
        })

    # 8. 응답 구성
    total_price = sum(item['subtotal'] for item in cart_items)
    total_quantity = sum(item['quantity'] for item in cart_items)

    return jsonify({
        "success": True,
        "items": cart_items,
        "total_quantity": total_quantity,
        "total_price": total_price,
        "item_count": len(cart_items)
    })


@main_bp.route('/cart', methods=['GET'])
def view_cart():
    """
    장바구니 페이지 (GET /cart)
    """
    return render_template('cart.html', mall_name="VIBE-FASHION")
