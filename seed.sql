-- ==============================================================================
-- VIBE-FASHION 쇼핑몰 초기 데이터 시드 (Seed Data)
-- Supabase SQL Editor에서 바로 실행 가능
-- ==============================================================================

-- 1. 카테고리 7개 등록
INSERT INTO public.categories (name, slug, display_order)
VALUES 
    ('상의', 'top', 1),
    ('하의', 'bottom', 2),
    ('아우터', 'outer', 3),
    ('원피스/세트', 'dress', 4),
    ('액세서리', 'acc', 5),
    ('가방', 'bag', 6),
    ('신발', 'shoes', 7)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name,
    display_order = EXCLUDED.display_order;


-- 2. 샘플 상품 4개 등록 (고유 UUID 변수 또는 서브쿼리 활용)
-- 상품 1: 베이직 크롭 티셔츠 (상의, 정상가 29,900원 / 할인가 19,900원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    (SELECT id FROM public.categories WHERE slug = 'top'),
    '베이직 크롭 티셔츠',
    '트렌디하고 슬림한 핏의 데일리 코튼 크롭 티셔츠입니다. 다양한 하의와 매치하기 좋습니다.',
    19900,
    29900,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- 상품 2: 와이드 데님 팬츠 (하의, 39,900원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '22222222-2222-4222-8222-222222222222',
    (SELECT id FROM public.categories WHERE slug = 'bottom'),
    '와이드 데님 팬츠',
    '편안한 착용감과 내추럴한 와이드 실루엣이 돋보이는 사계절용 데님 팬츠입니다.',
    39900,
    39900,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- 상품 3: 오버핏 코튼 자켓 (아우터, 59,900원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '33333333-3333-4333-8333-333333333333',
    (SELECT id FROM public.categories WHERE slug = 'outer'),
    '오버핏 코튼 자켓',
    '탄탄한 코튼 소재로 제작되어 캐주얼하면서도 모던한 무드를 연출할 수 있는 오버핏 자켓입니다.',
    59900,
    59900,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- 상품 4: 플로럴 미디 원피스 (원피스, 45,900원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '44444444-4444-4444-8444-444444444444',
    (SELECT id FROM public.categories WHERE slug = 'dress'),
    '플로럴 미디 원피스',
    '화사한 플로럴 패턴과 살랑이는 실루엣으로 로맨틱한 분위기를 주는 미디 기장의 원피스입니다.',
    45900,
    45900,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- 상품 5: 미니멀 레더 크로스 바디백 (액세서리, 89,000원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '55555555-5555-5555-8555-555555555555',
    (SELECT id FROM public.categories WHERE slug = 'acc'),
    '미니멀 레더 크로스 바디백',
    '모던한 스퀘어 쉐입과 부드러운 천연 소가죽 질감을 살린 데일리 에센셜 백입니다.',
    89000,
    119000,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;

-- 상품 6: 실버 레이어드 체인 네크리스 (액세서리, 25,000원)
INSERT INTO public.products (id, category_id, name, description, price, original_price, is_active, is_featured)
VALUES (
    '66666666-6666-6666-8666-666666666666',
    (SELECT id FROM public.categories WHERE slug = 'acc'),
    '실버 레이어드 체인 네크리스',
    '써지컬 스틸 소재로 변색 없이 은은한 포인트를 주는 투웨이 레이어드 목걸이입니다.',
    25000,
    25000,
    true,
    true
)
ON CONFLICT (id) DO UPDATE
SET category_id = EXCLUDED.category_id,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    original_price = EXCLUDED.original_price,
    is_active = EXCLUDED.is_active,
    is_featured = EXCLUDED.is_featured;


-- 3. 첫 번째 상품(베이직 크롭 티셔츠) 옵션 9개 등록 (블랙/화이트/베이지 × S/M/L)
DELETE FROM public.product_options WHERE product_id = '11111111-1111-4111-8111-111111111111';

INSERT INTO public.product_options (product_id, option_name, option_value, additional_price, stock)
VALUES
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '블랙 / S', 0, 50),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '블랙 / M', 0, 80),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '블랙 / L', 0, 40),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '화이트 / S', 0, 60),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '화이트 / M', 0, 100),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '화이트 / L', 0, 50),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '베이지 / S', 0, 30),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '베이지 / M', 0, 70),
    ('11111111-1111-4111-8111-111111111111', '색상/사이즈', '베이지 / L', 0, 30);


-- 4. 상품별 대표 이미지 (패션 아이템에 부합하는 고화질 의류 이미지)
DELETE FROM public.product_images WHERE product_id IN (
    '11111111-1111-4111-8111-111111111111',
    '22222222-2222-4222-8222-222222222222',
    '33333333-3333-4333-8333-333333333333',
    '44444444-4444-4444-8444-444444444444',
    '55555555-5555-5555-8555-555555555555',
    '66666666-6666-6666-8666-666666666666'
);

INSERT INTO public.product_images (product_id, image_url, is_thumbnail, display_order)
VALUES
    -- 베이직 크롭 티셔츠 (상의)
    ('11111111-1111-4111-8111-111111111111', 'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80', true, 1),
    -- 와이드 데님 팬츠 (하의)
    ('22222222-2222-4222-8222-222222222222', 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&auto=format&fit=crop&q=80', true, 1),
    -- 오버핏 코튼 자켓 (아우터)
    ('33333333-3333-4333-8333-333333333333', 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&auto=format&fit=crop&q=80', true, 1),
    -- 플로럴 미디 원피스 (원피스)
    ('44444444-4444-4444-8444-444444444444', 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop&q=80', true, 1),
    -- 미니멀 레더 크로스 바디백 (액세서리)
    ('55555555-5555-5555-8555-555555555555', 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&auto=format&fit=crop&q=80', true, 1),
    -- 실버 레이어드 체인 네크리스 (액세서리)
    ('66666666-6666-6666-8666-666666666666', 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&auto=format&fit=crop&q=80', true, 1);
