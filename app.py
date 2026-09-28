"""
루트 디렉토리 app.py (호환성 및 진입점 모듈)
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print(" [VIBE-FASHION] 패션 쇼핑몰 서버를 시작합니다.")
    print(" 로컬 주소: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
