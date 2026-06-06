#!/usr/bin/env python3
"""네이버 SMTP 진단 스크립트.
환경변수 NAVER_USER, NAVER_PASS를 읽어 단계별로 무슨 일이 일어나는지 출력한다.
비밀번호 자체는 절대 출력하지 않고, 길이/공백 유무 등 안전한 정보만 마스킹해서 보여준다."""
import os
import smtplib
import ssl
import sys

def mask(s):
    """값은 숨기고 안전한 메타정보만."""
    if s is None:
        return "(없음/None)"
    if s == "":
        return "(빈 문자열)"
    has_lead = s != s.lstrip()
    has_trail = s != s.rstrip()
    has_space_inside = " " in s.strip()
    return (f"길이={len(s)}자 / 앞공백={'있음' if has_lead else '없음'} / "
            f"뒤공백={'있음' if has_trail else '없음'} / 중간공백={'있음' if has_space_inside else '없음'} / "
            f"첫글자='{s[0]}' / 끝글자='{s[-1]}'")

print("=" * 60)
print("네이버 SMTP 진단 시작")
print("=" * 60)

user = os.environ.get("NAVER_USER")
pw   = os.environ.get("NAVER_PASS")

print(f"\n[1] 환경변수 확인")
print(f"  NAVER_USER: {mask(user)}")
print(f"  NAVER_PASS: {mask(pw)}")

if not user or not pw:
    print("\n  ✗ 환경변수가 비어 있음! Secret 이름(NAVER_USER/NAVER_PASS) 또는 전달 확인 필요.")
    sys.exit(0)  # 워크플로우는 계속

# username 후보 두 가지 모두 시도: 아이디만 / 전체주소
user_id_only = user.split("@")[0]
user_full    = user if "@" in user else user + "@naver.com"

candidates = [
    ("전체주소", user_full),
    ("아이디만", user_id_only),
]

for label, login_user in candidates:
    print(f"\n[2] 로그인 시도 — username='{login_user}' ({label})")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.naver.com", 465, context=ctx, timeout=20) as server:
            # debuglevel은 비밀번호가 base64로 로그에 찍힐 수 있어 끔
            print("  → 연결 성공, 로그인 시도...")
            server.login(login_user, pw)
            print(f"  ✓✓✓ 로그인 성공! username='{login_user}' ({label}) 이게 정답입니다.")
            server.quit()
            print("\n" + "=" * 60)
            print(f"결론: username 으로 '{login_user}' 를 쓰면 됩니다.")
            print("=" * 60)
            sys.exit(0)
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ✗ 인증 실패 (535 계열): {e.smtp_code} / {e.smtp_error}")
    except Exception as e:
        print(f"  ✗ 기타 오류: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("두 방식(전체주소/아이디만) 모두 인증 실패.")
print("→ 비밀번호(앱 비밀번호)가 이 계정과 안 맞거나, 해당 계정 SMTP 사용 설정 문제.")
print("=" * 60)
