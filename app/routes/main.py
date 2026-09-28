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

# 기존 호환성 유지용 더미 상품 데이터
DUMMY_PRODUCTS = [
    {
        "id": 1,
        "name": "오버핏 울 미니멀 블레이저",
        "category": "OUTER",
        "price": "129,000원",
        "price_str": "129,000원",
        "badge": "BEST",
        "badge_color": "danger",
        "thumbnail_url": "https://picsum.photos/id/1025/600/700",
        "image": "https://picsum.photos/id/1025/600/700",
        "description": "트렌디한 실루엣과 고급스러운 울 블렌드 소재로 완성한 시그니처 오버핏 블레이저",
        "rating": 4.9,
        "reviews": 128
    },
    {
        "id": 2,
        "name": "클래식 릴렉스드 옥스포드 셔츠",
        "category": "TOP",
        "price": "49,000원",
        "price_str": "49,000원",
        "badge": "NEW",
        "badge_color": "primary",
        "thumbnail_url": "https://picsum.photos/id/1062/600/700",
        "image": "https://picsum.photos/id/1062/600/700",
        "description": "사계절 내내 단품 또는 레이어드로 편안하게 착용 가능한 프리미엄 코튼 셔츠",
        "rating": 4.8,
        "reviews": 95
    },
    {
        "id": 3,
        "name": "와이드 핏 투턱 세미 슬랙스",
        "category": "BOTTOM",
        "price": "59,000원",
        "price_str": "59,000원",
        "badge": "HOT",
        "badge_color": "warning text-dark",
        "thumbnail_url": "https://picsum.photos/id/1059/600/700",
        "image": "https://picsum.photos/id/1059/600/700",
        "description": "유려하게 떨어지는 투턱 주름 디테일로 길고 슬림한 다리 라인을 연출하는 슬랙스",
        "rating": 4.9,
        "reviews": 210
    },
    {
        "id": 4,
        "name": "미니멀 레더 크로스 바디백",
        "category": "ACC",
        "price": "89,000원",
        "price_str": "89,000원",
        "badge": "20% OFF",
        "badge_color": "success",
        "thumbnail_url": "https://picsum.photos/id/1069/600/700",
        "image": "https://picsum.photos/id/1069/600/700",
        "description": "모던한 스퀘어 쉐입과 부드러운 천연 가죽 질감을 살린 데일리 에센셜 백",
        "rating": 4.7,
        "reviews": 74
    }
]


def get_featured_products():
    """
    Supabase products 테이블에서 데이터 조회 함수:
    - 조건: is_active=true AND is_featured=true, 최대 4개
    - 가격 포맷: {:,}원 형태 (예: 19,900원)
    - 이미지: product_images 테이블의 대표 썸네일(is_thumbnail) 연동
    - 에러 처리: 연결 실패 또는 데이터 부재 시 DUMMY_PRODUCTS로 fallback
    """
    if not supabase:
        print("[WARN] Supabase 클라이언트가 초기화되지 않았습니다. 기본 더미 상품 데이터를 반환합니다.", file=sys.stderr)
        return DUMMY_PRODUCTS

    try:
        response = (
            supabase.table('products')
            .select('*, product_images(image_url, is_thumbnail, display_order), categories(name)')
            .eq('is_active', True)
            .eq('is_featured', True)
            .limit(4)
            .execute()
        )

        raw_data = response.data or []
        products = []

        for item in raw_data:
            # 1. 가격 {:,} 형식 포맷팅 (예: 19,900원)
            raw_price = item.get('price', 0)
            try:
                formatted_price = f"{int(raw_price):,}원"
            except (ValueError, TypeError):
                formatted_price = f"{raw_price}원"

            # 2. thumbnail_url 추출 (is_thumbnail=True 우선, 없으면 첫 번째 이미지)
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

            # 3. 카테고리명 추출
            category_name = 'FASHION'
            if item.get('categories') and isinstance(item['categories'], dict):
                category_name = item['categories'].get('name', 'FASHION')

            products.append({
                'id': item.get('id'),
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

        return products if products else DUMMY_PRODUCTS

    except Exception as e:
        # Supabase 연결/조회 실패 시 앱이 종료되지 않도록 예외 처리 및 DUMMY_PRODUCTS 반환
        print(f"[ERROR] Supabase products 테이블 조회 실패: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return DUMMY_PRODUCTS


@main_bp.route('/')
def index():
    """
    메인 페이지 라우트
    Supabase products 테이블에서 추천 상품을 조회하여 index.html 템플릿에 전달합니다.
    """
    products = get_featured_products()
    return render_template(
        'index.html',
        mall_name="VIBE-FASHION",
        products=products
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
