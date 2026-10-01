"""
루트 디렉토리 routes/main.py (호환성 프록시 모듈)
"""

from app.routes.main import main_bp, DUMMY_PRODUCTS, index, product_detail, api_products, mypage, change_password, api_product_options

__all__ = ['main_bp', 'DUMMY_PRODUCTS', 'index', 'product_detail', 'api_products', 'mypage', 'change_password', 'api_product_options']
