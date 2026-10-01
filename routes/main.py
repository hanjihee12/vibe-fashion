"""
루트 디렉토리 routes/main.py (호환성 프록시 모듈)
"""

from app.routes.main import main_bp, DUMMY_PRODUCTS, index, product_detail, api_products, mypage, change_password, api_product_options, add_to_cart, update_cart_quantity, get_cart_items, view_cart

__all__ = ['main_bp', 'DUMMY_PRODUCTS', 'index', 'product_detail', 'api_products', 'mypage', 'change_password', 'api_product_options', 'add_to_cart', 'update_cart_quantity', 'get_cart_items', 'view_cart']
