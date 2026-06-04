#!/usr/bin/env python3
"""new_items.json을 읽어 메일 본문(email_body.html)을 생성한다.
NEW 상품이 1개 이상이면 GITHUB_OUTPUT에 send=true 를 기록한다."""
import json, os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST).strftime("%Y.%m.%d %H:%M KST")
SITE_URL = "https://wg052026.github.io/kapital-tracker/"

try:
    with open("docs/new_items.json", "r", encoding="utf-8") as f:
        items = json.load(f)
except Exception:
    items = []

# GitHub Actions 출력: NEW 유무
out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a") as f:
        f.write(f"send={'true' if items else 'false'}\n")
        f.write(f"count={len(items)}\n")

if not items:
    print("NEW 없음 → 메일 발송 안 함")
    raise SystemExit(0)

# 사이트별 그룹핑
by_site = {}
for it in items:
    by_site.setdefault(it["source"], []).append(it)

rows = []
for source, group in by_site.items():
    rows.append(
        f'<tr><td colspan="2" style="padding:14px 12px 6px;font-size:13px;'
        f'font-weight:700;color:#111;border-bottom:2px solid #111;">'
        f'{source} ({len(group)})</td></tr>'
    )
    for it in group:
        img = it.get("img", "")
        img_cell = (
            f'<img src="{img}" width="64" height="64" '
            f'style="object-fit:cover;border-radius:4px;display:block;">'
            if img else ""
        )
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
    <div style="font-size:18px;font-weight:700;letter-spacing:2px;">KAPITAL NEW ARRIVALS</div>
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
