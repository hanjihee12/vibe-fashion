# app/routes/auth.py

import os
import time
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    current_app,
)
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from supabase import create_client

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)

# =====================================================
# Supabase
# =====================================================

SITE_URL = os.getenv(
    "SITE_URL",
    "http://localhost:5000"
)

supabase = create_client(
    os.getenv("SUPABASE_URL", "https://placeholder.supabase.co"),
    os.getenv("SUPABASE_ANON_KEY", "placeholder-key")
)

# =====================================================
# 이메일 발송 & 인증 링크 유틸리티
# =====================================================

def get_serializer():
    secret_key = current_app.config.get("SECRET_KEY", "vibe-fashion-default-secret-key")
    return URLSafeTimedSerializer(secret_key)


def get_smtp_accounts():
    """
    SMTP 계정 목록을 파싱합니다.
    단일 계정(SMTP_USER / SMTP_PASSWORD) 또는
    쉼표(,) 및 세미콜론(;)으로 구분된 멀티 계정(GMAIL_ACCOUNTS / SMTP_USERS / SMTP_PASSWORDS)을 지원하여
    여러 Gmail 계정을 라운드로빈 방식으로 자동 분산 발송(한도 계정 수 × 500통 확장)합니다.
    """
    accounts = []

    # 1. GMAIL_ACCOUNTS 포맷 지원 (예: "user1@gmail.com:pass1,user2@gmail.com:pass2")
    multi_raw = os.getenv("GMAIL_ACCOUNTS", "").strip()
    if multi_raw:
        for entry in multi_raw.split(","):
            entry = entry.strip()
            if ":" in entry:
                u, p = entry.split(":", 1)
                accounts.append({
                    "user": u.strip(),
                    "password": p.strip(),
                    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "from": u.strip()
                })

    # 2. SMTP_USERS 및 SMTP_PASSWORDS 리스트 포맷 지원
    users_raw = os.getenv("SMTP_USERS", "").strip()
    passwords_raw = os.getenv("SMTP_PASSWORDS", "").strip()
    if users_raw and passwords_raw:
        users = [u.strip() for u in users_raw.split(",") if u.strip()]
        passwords = [p.strip() for p in passwords_raw.split(",") if p.strip()]
        for u, p in zip(users, passwords):
            accounts.append({
                "user": u,
                "password": p,
                "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "from": u
            })

    # 3. 기본 단일 계정 지원
    single_user = os.getenv("SMTP_USER", "").strip()
    single_pass = os.getenv("SMTP_PASSWORD", "").strip()
    if single_user and single_pass:
        # 중복 추가 방지
        if not any(acc["user"] == single_user for acc in accounts):
            accounts.append({
                "user": single_user,
                "password": single_pass,
                "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "from": os.getenv("SMTP_FROM", single_user)
            })

    return accounts


_account_index = 0

def send_signup_email(to_email, user_name, verify_url):
    """
    회원가입 인증 링크가 담긴 이메일을 발송합니다.
    등록된 Gmail 계정들을 라운드로빈 및 장애 복구(Failover) 방식으로 순환 발송하여
    Gmail 1개당 500통 한도를 N개(N x 500통)로 자동 확장합니다.
    """
    global _account_index
    subject = f"[VIBE-FASHION] {user_name}님, 회원가입 인증 링크입니다."
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #212529; background-color: #f8f9fa; padding: 20px; }}
            .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef; }}
            .header {{ background: #111827; padding: 32px 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 2px; font-weight: 800; }}
            .header p {{ margin: 8px 0 0; font-size: 13px; color: #9ca3af; }}
            .content {{ padding: 36px 32px; }}
            .welcome {{ font-size: 18px; font-weight: 700; margin-bottom: 16px; }}
            .btn-box {{ text-align: center; margin: 32px 0; }}
            .btn {{ display: inline-block; background: #111827; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 50px; font-weight: 700; font-size: 15px; letter-spacing: 0.5px; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #e9ecef; }}
            .link-text {{ word-break: break-all; font-size: 12px; color: #0d6efd; background: #f1f5f9; padding: 12px; border-radius: 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>VIBE-FASHION</h1>
                <p>트렌디한 감성의 프리미엄 패션 셀렉트샵</p>
            </div>
            <div class="content">
                <div class="welcome">안녕하세요, {user_name}님! 🎉</div>
                <p>VIBE-FASHION에 회원가입을 신청해 주셔서 대단히 감사드립니다.</p>
                <p>아래 <strong>[회원가입 완료하기]</strong> 버튼을 누르시면 이메일 인증이 완료되며 정상적으로 가입이 완료됩니다.</p>
                
                <div class="btn-box">
                    <a href="{verify_url}" class="btn" target="_blank">회원가입 완료하기</a>
                </div>

                <p style="font-size: 13px; color: #6c757d;">
                    * 본 링크는 발송 후 24시간 동안 유효합니다.<br>
                    * 본인이 요청하지 않은 경우 이 메일을 무시하셔도 됩니다.
                </p>

                <div class="link-text">
                    버튼 클릭이 되지 않을 경우 아래 링크를 복사하여 브라우저 주소창에 붙여넣어 주세요:<br>
                    <a href="{verify_url}" style="color: #0d6efd;">{verify_url}</a>
                </div>
            </div>
            <div class="footer">
                © 2026 VIBE-FASHION. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    # 콘솔 로그 출력 (개발 및 확인용)
    print("\n" + "=" * 70, file=sys.stdout)
    print(" [VIBE-FASHION] 가입 인증 메일이 발송되었습니다.", file=sys.stdout)
    print(f" 수신자: {to_email} ({user_name} 님)", file=sys.stdout)
    print(f" 가입 완료 링크: {verify_url}", file=sys.stdout)
    print("=" * 70 + "\n", file=sys.stdout)

    accounts = get_smtp_accounts()
    if not accounts:
        return True

    # 등록된 Gmail 계정 목록 순환 (Round-Robin) 및 장애 시 자동 전환 (Failover)
    total_accounts = len(accounts)
    start_index = _account_index % total_accounts

    for attempt in range(total_accounts):
        current_idx = (start_index + attempt) % total_accounts
        acc = accounts[current_idx]
        smtp_user = acc["user"]
        smtp_password = acc["password"]
        smtp_host = acc.get("host", "smtp.gmail.com")
        smtp_port = acc.get("port", 587)
        smtp_from = acc.get("from", smtp_user)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"VIBE-FASHION <{smtp_from}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [to_email], msg.as_string())
            server.quit()
            
            # 발송 성공 시 다음 계정으로 인덱스 이동 (계정 간 균등 분산으로 한도 극대화)
            _account_index = (current_idx + 1) % total_accounts
            print(f"[SUCCESS] 이메일 발송 성공 (사용 계정: {smtp_user}): {to_email}", file=sys.stdout)
            return True
        except Exception as e:
            print(f"[WARN] Gmail 계정 ({smtp_user}) 발송 실패/한도초과, 다음 계정 시도: {e}", file=sys.stderr)

    return False


# =====================================================
# 이메일 가입 링크 발송 API (AJAX 비동기 요청)
# =====================================================

@auth_bp.route("/send-signup-link", methods=["POST"])
def send_signup_link():
    """
    회원가입 폼에서 입력받은 이메일로 가입 인증 링크를 전송합니다.
    """
    data = request.get_json(silent=True) or request.form

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "message": "올바른 이메일 주소를 입력해주세요."}), 400

    if not password or len(password) < 4:
        return jsonify({"success": False, "message": "비밀번호를 4자리 이상 입력해주세요."}), 400

    if not name:
        return jsonify({"success": False, "message": "이름(성함)을 입력해주세요."}), 400

    if not phone:
        return jsonify({"success": False, "message": "전화번호를 입력해주세요."}), 400

    # 안전한 서명 토큰 생성 (유효기간 검증 가능)
    serializer = get_serializer()
    token_payload = {
        "email": email,
        "password": password,
        "name": name,
        "phone": phone,
        "ts": time.time(),
    }
    token = serializer.dumps(token_payload, salt="email-signup")

    site_url = os.getenv("SITE_URL")
    if not site_url:
        site_url = request.host_url.rstrip("/")

    verify_url = f"{site_url}/auth/verify-signup?token={token}"

    # 1. Supabase Auth 회원가입 및 Supabase Custom SMTP 메일 발송 트리거
    try:
        if supabase:
            supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": f"{site_url}/auth/confirm",
                    "data": {
                        "name": name,
                        "phone": phone
                    }
                }
            })
            print(f"[SUCCESS] Supabase Auth sign_up 호출 완료 (Custom SMTP 연동): {email}", file=sys.stdout)
    except Exception as e:
        print(f"[WARN] Supabase Auth sign_up 오류 또는 기존 계정: {e}", file=sys.stderr)

    # 2. 백엔드 자체 SMTP 발송 (설정되어 있을 경우 백업 발송 및 콘솔 출력)
    send_signup_email(email, name, verify_url)

    return jsonify({
        "success": True,
        "message": f"'{email}' 주소로 가입 인증 링크가 발송되었습니다. 메일함을 확인해주세요.",
        "email": email,
        "verify_url": verify_url,
    })


# =====================================================
# 이메일 가입 링크 검증 & 가입 완료
# =====================================================

@auth_bp.route("/verify-signup")
def verify_signup():
    """
    메일로 온 가입 링크를 클릭했을 때 호출되어 가입을 완료하고 자동 로그인합니다.
    """
    token = request.args.get("token")
    if not token:
        return render_template(
            "auth/verify_error.html",
            error_title="잘못된 접근",
            error_message="가입 인증 토큰이 누락되었습니다."
        ), 400

    serializer = get_serializer()
    try:
        # 24시간(86400초) 유효
        data = serializer.loads(token, salt="email-signup", max_age=86400)
    except SignatureExpired:
        return render_template(
            "auth/verify_error.html",
            error_title="인증 링크 만료",
            error_message="가입 인증 링크가 만료되었습니다 (유효시간 24시간). 다시 가입을 신청해주세요."
        ), 400
    except BadSignature:
        return render_template(
            "auth/verify_error.html",
            error_title="유효하지 않은 링크",
            error_message="변조되었거나 올바르지 않은 가입 인증 링크입니다."
        ), 400

    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    phone = data.get("phone")

    # Supabase Auth 및 DB 연동 시도 (선택적)
    try:
        if supabase:
            supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name,
                        "phone": phone
                    }
                }
            })
    except Exception as e:
        print(f"[INFO] Supabase auth 연동 패스 또는 기존 유저: {e}", file=sys.stderr)

    # Flask 세션에 로그인 상태 등록
    session["user_id"] = email
    session["email"] = email
    session["name"] = name
    session["phone"] = phone

    user_info = {
        "id": email,
        "email": email,
        "name": name,
        "phone": phone,
    }

    return render_template(
        "auth/verify_success.html",
        user=user_info,
        mall_name="VIBE-FASHION"
    )


# =====================================================
# 메시지
# =====================================================

ERROR_MESSAGES = {
    "login_required": "로그인이 필요합니다.",
    "email_not_confirmed": "이메일 인증 후 로그인해주세요.",
    "invalid_credentials": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "already_registered": "이미 가입된 이메일입니다.",
    "signup_failed": "회원가입 중 오류가 발생했습니다.",
    "invalid_token": "유효하지 않은 인증 링크입니다.",
    "reset_failed": "비밀번호 변경에 실패했습니다.",
    "password_too_short": "비밀번호는 8자 이상 입력해주세요.",
}

SUCCESS_MESSAGES = {
    "password_reset_sent": "비밀번호 재설정 메일을 발송했습니다.",
    "password_updated": "비밀번호가 성공적으로 변경되었습니다.",
}


def get_error_message():
    code = request.args.get("error")
    return ERROR_MESSAGES.get(code)


def get_success_message():
    code = request.args.get("success")
    return SUCCESS_MESSAGES.get(code)


# =====================================================
# 로그인 필요 데코레이터
# =====================================================

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):
            return redirect(
                url_for(
                    "auth.login",
                    error="login_required",
                    next=request.url
                )
            )

        return func(*args, **kwargs)

    return wrapper


# =====================================================
# 로그인
# =====================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user_id"):
        return redirect("/mypage")

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        next_url = request.args.get("next")

        try:

            result = supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            user = result.user

            if not user:
                return redirect(
                    url_for(
                        "auth.login",
                        error="invalid_credentials"
                    )
                )

            if not getattr(
                user,
                "email_confirmed_at",
                None
            ):
                return redirect(
                    url_for(
                        "auth.login",
                        error="email_not_confirmed"
                    )
                )

            session["user_id"] = user.id
            session["email"] = user.email

            if result.session:
                session["access_token"] = (
                    result.session.access_token
                )

                session["refresh_token"] = (
                    result.session.refresh_token
                )

            if next_url:
                return redirect(next_url)

            return redirect("/mypage")

        except Exception:
            return redirect(
                url_for(
                    "auth.login",
                    error="invalid_credentials"
                )
            )

    return render_template(
        "auth/login.html",
        error=get_error_message(),
        success=get_success_message(),
    )


# =====================================================
# 회원가입
# =====================================================

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():

    if session.get("user_id"):
        return redirect("/mypage")

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if len(password) < 8:
            return redirect(
                url_for(
                    "auth.signup",
                    error="password_too_short"
                )
            )

        try:

            supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "email_redirect_to": (
                            f"{SITE_URL}/auth/confirm"
                        ),
                        "data": {
                            "name": name
                        }
                    }
                }
            )

            return redirect(
                url_for(
                    "auth.signup_complete"
                )
            )

        except Exception as e:

            if "already" in str(e).lower():
                return redirect(
                    url_for(
                        "auth.signup",
                        error="already_registered"
                    )
                )

            return redirect(
                url_for(
                    "auth.signup",
                    error="signup_failed"
                )
            )

    return render_template(
        "auth/signup.html",
        error=get_error_message(),
    )


# =====================================================
# 회원가입 완료
# =====================================================

@auth_bp.route("/signup-complete")
def signup_complete():

    return render_template(
        "auth/signup_complete.html",
        message="인증 메일을 보냈습니다. 이메일을 확인해주세요."
    )


# =====================================================
# 이메일 인증
# =====================================================

@auth_bp.route("/confirm")
def confirm():

    token_hash = request.args.get(
        "token_hash"
    )

    verify_type = request.args.get(
        "type",
        "signup"
    )

    if not token_hash:
        return redirect(
            url_for(
                "auth.login",
                error="invalid_token"
            )
        )

    try:

        result = supabase.auth.verify_otp(
            {
                "token_hash": token_hash,
                "type": verify_type,
            }
        )

        user = result.user

        if not user:
            return redirect(
                url_for(
                    "auth.login",
                    error="invalid_token"
                )
            )

        session["user_id"] = user.id
        session["email"] = user.email

        if result.session:
            session["access_token"] = (
                result.session.access_token
            )
            session["refresh_token"] = (
                result.session.refresh_token
            )

        if verify_type == "recovery":
            return redirect(
                url_for("auth.reset_password")
            )

        # 사용자 메타데이터 추출 및 세션 동기화
        user_meta = getattr(user, "user_metadata", {}) or {}
        user_name = user_meta.get("name") or (user.email.split("@")[0] if user.email else "고객")
        user_phone = user_meta.get("phone", "")

        session["name"] = user_name
        session["phone"] = user_phone

        user_info = {
            "id": user.email or user.id,
            "email": user.email or "",
            "name": user_name,
            "phone": user_phone,
        }

        return render_template(
            "auth/verify_success.html",
            user=user_info,
            mall_name="VIBE-FASHION"
        )

    except Exception as e:
        print(f"[ERROR] 이메일 인증(confirm) 오류: {e}", file=sys.stderr)
        return render_template(
            "auth/verify_error.html",
            error_title="이메일 인증 오류",
            error_message="유효하지 않거나 이미 만료된 인증 링크입니다. 다시 가입을 시도해주세요."
        ), 400


# =====================================================
# 로그아웃
# =====================================================

@auth_bp.route("/logout")
def logout():

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    session.clear()

    return redirect("/")


# =====================================================
# 비밀번호 재설정 이메일 요청
# =====================================================

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        try:

            supabase.auth.reset_password_for_email(
                email,
                {
                    "redirect_to": (
                        f"{SITE_URL}/auth/confirm?type=recovery"
                    )
                }
            )

            return redirect(
                url_for(
                    "auth.login",
                    success="password_reset_sent"
                )
            )

        except Exception:
            return redirect(
                url_for(
                    "auth.login",
                    success="password_reset_sent"
                )
            )

    return render_template(
        "auth/forgot_password.html",
        error=get_error_message(),
        success=get_success_message(),
    )


# =====================================================
# 비밀번호 변경
# =====================================================

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if not session.get("user_id"):
        return redirect(
            url_for(
                "auth.login",
                error="invalid_token"
            )
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        if len(password) < 8:
            return redirect(
                url_for(
                    "auth.reset_password",
                    error="password_too_short"
                )
            )

        try:

            access_token = session.get("access_token")
            refresh_token = session.get("refresh_token")

            if access_token and refresh_token:
                supabase.auth.set_session(
                    access_token,
                    refresh_token
                )

            supabase.auth.update_user(
                {
                    "password": password
                }
            )

            return redirect(
                url_for(
                    "auth.login",
                    success="password_updated"
                )
            )

        except Exception:
            return redirect(
                url_for(
                    "auth.reset_password",
                    error="reset_failed"
                )
            )

    return render_template(
        "auth/reset_password.html",
        error=get_error_message(),
        success=get_success_message(),
    )
