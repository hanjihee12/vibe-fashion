"""
메인 라우트 모듈
쇼핑몰 메인 페이지 및 상품 목록을 처리하는 Blueprint입니다.
Supabase DB 연동을 통해 상품 목록을 동적으로 조회합니다.
"""

import os
import sys
import traceback
from flask import Blueprint, render_template, request, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. python-dotenv로 .env에서 Supabase 설정값 읽기
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# Supabase 클라이언트 초기화 (오류 발생 시에도 앱 시작이 중단되지 않도록 예외 처리)
supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"[ERROR] Supabase 클라이언트 초기화 실패: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
else:
    print("[WARN] .env에 SUPABASE_URL 또는 SUPABASE_ANON_KEY가 설정되지 않았습니다.", file=sys.stderr)

# 2. Blueprint 인스턴스 생성
main_bp = Blueprint('main', __name__)

# 카테고리별 고화질 더미 상품 데이터 (상의, 하의, 악세사리)
DUMMY_TOP_PRODUCTS = [
    {
        "id": "top-1",
        "name": "베이직 코튼 크롭 티셔츠",
        "category": "상의",
        "price": "19,900원",
        "price_str": "19,900원",
        "badge": "BEST",
        "badge_color": "danger",
        "thumbnail_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80",
        "description": "트렌디한 실루엣과 부드러운 코튼 100% 원단으로 완성한 데일리 크롭 티셔츠",
        "rating": 4.9,
        "reviews": 142
    },
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
        "id": "top-3",
        "name": "미니멀 라운드넥 니트 스웨터",
        "category": "상의",
        "price": "54,000원",
        "price_str": "54,000원",
        "badge": "HOT",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop&q=80",
        "description": "부드럽고 촘촘한 조직감으로 포근한 실루엣을 연출해주는 데일리 니트",
        "rating": 4.9,
        "reviews": 88
    },
    {
        "id": "top-4",
        "name": "시그니처 오버핏 후드 티셔츠",
        "category": "상의",
        "price": "59,000원",
        "price_str": "59,000원",
        "badge": "10% OFF",
        "badge_color": "success",
        "thumbnail_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80",
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
        "id": "bot-1",
        "name": "내추럴 와이드 핏 데님 팬츠",
        "category": "하의",
        "price": "39,900원",
        "price_str": "39,900원",
        "badge": "BEST",
        "badge_color": "danger",
        "thumbnail_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&auto=format&fit=crop&q=80",
        "image": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&auto=format&fit=crop&q=80",
        "description": "자연스러운 워싱감과 트렌디한 와이드 핏으로 감각적인 룩을 완성하는 데님",
        "rating": 4.9,
        "reviews": 210
    },
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

    # 각 카테고리가 비어있거나 부족할 경우 고화질 더미 상품으로 보강
    final_top = top_list if top_list else DUMMY_TOP_PRODUCTS
    final_bottom = bottom_list if bottom_list else DUMMY_BOTTOM_PRODUCTS
    final_acc = acc_list if acc_list else DUMMY_ACC_PRODUCTS
    all_products = (products if products else DUMMY_PRODUCTS)

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


@main_bp.route('/product/<product_id>')
def product_detail(product_id):
    """
    상품 상세 정보 라우트 (단일 상품 확인)
    """
    product = None
    if supabase:
        try:
            res = (
                supabase.table('products')
                .select('*, product_images(*), categories(name)')
                .eq('id', product_id)
                .execute()
            )
            if res.data:
                item = res.data[0]
                raw_price = item.get('price', 0)
                try:
                    price_str = f"{int(raw_price):,}원"
                except (ValueError, TypeError):
                    price_str = f"{raw_price}원"

                images = item.get('product_images') or []
                thumbnail_url = images[0].get('image_url') if images else f"https://picsum.photos/seed/{product_id}/600/800"
                category_name = item.get('categories', {}).get('name') if isinstance(item.get('categories'), dict) else 'ITEM'

                product = {
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'price': price_str,
                    'price_str': price_str,
                    'thumbnail_url': thumbnail_url,
                    'image': thumbnail_url,
                    'description': item.get('description', ''),
                    'category': category_name
                }
        except Exception as e:
            print(f"[ERROR] 상품 상세 조회 실패 ({product_id}): {e}", file=sys.stderr)

    if not product:
        # 더미 데이터 fallback
        product = next((p for p in DUMMY_PRODUCTS if str(p.get("id")) == str(product_id)), None)

    if not product:
        return render_template('404.html', message="상품을 찾을 수 없습니다."), 404
    return render_template('detail.html', product=product, mall_name="VIBE-FASHION")


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
