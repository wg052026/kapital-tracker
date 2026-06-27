#!/usr/bin/env python3
"""new_items.json을 읽어 메일 본문(email_body.html)을 생성한다.
NEW 상품이 1개 이상이면 GITHUB_OUTPUT에 send=true 를 기록한다."""
import json, os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST).strftime("%Y.%m.%d %H:%M KST")
SITE_URL = "https://wg052026.github.io/kapital-tracker/"

# 메일 알림을 받을 사이트만 지정 (여기 목록만 발송됨)
ALERT_SITES = {"KAPITAL 공홈", "KEROUAC", "TAKE FIVE", "CHROME HEARTS", "CH DROP"}

try:
    with open("docs/new_items.json", "r", encoding="utf-8") as f:
        items = json.load(f)
except Exception:
    items = []

# 지정한 사이트의 신상품만 남김
items = [it for it in items if it["source"] in ALERT_SITES]

# 테스트 모드: TEST_EMAIL=1 이면 가짜 상품을 넣어 무조건 메일 발송 (작동 확인용)
if os.environ.get("TEST_EMAIL") == "1":
    items = [{
        "source": "CHROME HEARTS",
        "name": "[테스트] 새 카테고리: Test Drop",
        "price": "-",
        "link": SITE_URL,
        "img": "",
    }] + items
    print("테스트 모드: 가짜 상품으로 메일 강제 발송")

# GitHub Actions 출력: NEW 유무
has_ch = any(it.get("source") in ("CHROME HEARTS", "CH DROP") for it in items)
out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a") as f:
        f.write(f"send={'true' if items else 'false'}\n")
        f.write(f"count={len(items)}\n")
        f.write(f"has_ch={'true' if has_ch else 'false'}\n")

if not items:
    print("NEW 없음 → 메일 발송 안 함")
    raise SystemExit(0)

# 사이트별 그룹핑
by_site = {}
for it in items:
    by_site.setdefault(it["source"], []).append(it)

# 표시 이름 (CH DROP은 친근한 라벨로)
SITE_DISPLAY = {"CH DROP": "🔥 크롬하츠 발매 (레딧)"}

rows = []
for source, group in by_site.items():
    disp = SITE_DISPLAY.get(source, source)
    rows.append(
        f'<tr><td colspan="2" style="padding:14px 12px 6px;font-size:13px;'
        f'font-weight:700;color:#111;border-bottom:2px solid #111;">'
        f'{disp} ({len(group)})</td></tr>'
    )
    for it in group:
        img = it.get("img", "")
        img_cell = (
            f'<img src="{img}" width="64" height="64" '
            f'style="object-fit:cover;border-radius:4px;display:block;">'
            if img else ""
        )
        if source == "CH DROP":
            # CH DROP: 가격 대신 공홈/레딧 링크 표시
            ch_link = it.get("ch_link", "")
            reddit_url = it.get("reddit_url", it.get("link", ""))
            sub = ""
            if ch_link:
                sub += f'<a href="{ch_link}" style="color:#111;text-decoration:underline;">공홈 보기</a> · '
            sub += f'<a href="{reddit_url}" style="color:#666;text-decoration:underline;">레딧 원문</a>'
            rows.append(
                f'<tr>'
                f'<td style="padding:8px 12px;width:64px;vertical-align:top;">{img_cell}</td>'
                f'<td style="padding:8px 12px;vertical-align:top;font-size:13px;line-height:1.5;">'
                f'<a href="{it["link"]}" style="color:#1a5fb4;text-decoration:none;font-weight:600;">'
                f'{it["name"]}</a><br>'
                f'<span style="color:#666;font-size:12px;">{sub}</span>'
                f'</td></tr>'
            )
        else:
            rows.append(
                f'<tr>'
                f'<td style="padding:8px 12px;width:64px;vertical-align:top;">{img_cell}</td>'
                f'<td style="padding:8px 12px;vertical-align:top;font-size:13px;line-height:1.5;">'
                f'<a href="{it["link"]}" style="color:#1a5fb4;text-decoration:none;font-weight:600;">'
                f'{it["name"]}</a><br>'
                f'<span style="color:#666;">{it.get("price","-")}</span>'
                f'</td></tr>'
            )

body = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:16px;background:#f4f3f1;font-family:sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e0ddd8;">
  <div style="padding:16px 20px;background:#111;color:#fff;">
    <div style="font-size:18px;font-weight:700;letter-spacing:2px;">{'🔥 CHROME HEARTS DROP' if has_ch else 'KAPITAL NEW ARRIVALS'}</div>
    <div style="font-size:11px;color:#aaa;margin-top:4px;">신상품 {len(items)}개 · {NOW}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;">
    {''.join(rows)}
  </table>
  <div style="padding:16px 20px;text-align:center;border-top:1px solid #e0ddd8;">
    <a href="{SITE_URL}" style="display:inline-block;padding:10px 24px;background:#111;color:#fff;
       text-decoration:none;border-radius:4px;font-size:13px;font-weight:600;">전체 트래커 보기</a>
  </div>
</div>
</body></html>"""

with open("email_body.html", "w", encoding="utf-8") as f:
    f.write(body)

print(f"NEW {len(items)}개 → email_body.html 생성")
