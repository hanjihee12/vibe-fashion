"""
VIBE-FASHION 웹 애플리케이션 팩토리 모듈
이 모듈은 Flask 앱 인스턴스를 생성하고 설정하는 create_app 함수를 제공합니다.
초보자도 이해하기 쉽도록 단계별로 구성되어 있습니다.
"""

import os
from datetime import timedelta
from flask import Flask, abort
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()


def create_app(test_config=None):
    """
    Flask 앱 팩토리 함수
    
    앱 팩토리 패턴을 사용하면:
    1. 여러 인스턴스를 서로 다른 설정으로 생성할 수 있습니다 (테스트, 개발, 프로덕션).
    2. 순환 참조(circular import) 문제를 예방할 수 있습니다.
    """
    # 1. 기본 디렉토리 경로 설정 (현재 파일 기준)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    # 2. Flask 애플리케이션 인스턴스 생성
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # 3. 기본 설정값 구성
    admin_prefix = os.getenv('ADMIN_PATH_PREFIX', '/mgt-sec-9a72df81c3e4').strip()
    if not admin_prefix.startswith('/'):
        admin_prefix = '/' + admin_prefix

    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'vibe-fashion-default-secret-key'),
        APP_NAME='VIBE-FASHION',
        DEBUG=os.getenv('FLASK_DEBUG', '1') == '1',
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_HTTPONLY=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        ADMIN_PATH_PREFIX=admin_prefix,
    )

    # 리버스 프록시(Azure App Service 등) 환경에서 올바른 scheme(https) 및 host를 인식하도록 설정
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # 테스트 설정이 전달된 경우 덮어씌웁니다.
    if test_config:
        app.config.from_mapping(test_config)

    # 4. 라우트(Blueprint) 등록
    # routes 폴더의 main_bp(메인 블루프린트), auth_bp, admin_bp를 앱에 등록합니다.
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    current_admin_prefix = app.config.get('ADMIN_PATH_PREFIX', admin_prefix)
    app.register_blueprint(admin_bp, url_prefix=current_admin_prefix)

    # 보안 방어: 기존의 흔한 '/admin' 경로로 접속을 시도하는 외부인/스캐너는 404 차단
    if current_admin_prefix != '/admin':
        @app.route('/admin')
        @app.route('/admin/<path:subpath>')
        def block_default_admin(subpath=None):
            abort(404)

    return app
