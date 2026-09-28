"""
VIBE-FASHION 애플리케이션 진입점 (Entry Point)
이 파일은 개발 서버 실행 및 WSGI(Gunicorn) 구동의 진입점으로 사용됩니다.
"""

from app import create_app

# 앱 팩토리 함수를 호출하여 Flask 애플리케이션 객체를 생성합니다.
app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print(" [VIBE-FASHION] 패션 쇼핑몰 서버를 시작합니다.")
    print(" 로컬 주소: http://127.0.0.1:5000")
    print("=" * 60)
    # 개발 서버 실행
    app.run(host='127.0.0.1', port=5000, debug=True)
