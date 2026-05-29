#!/usr/bin/env python3
"""
KAPITAL New Arrivals Scraper
매일 실행되어 각 쇼핑몰의 캐피탈 신상품을 긁어와 docs/index.html을 생성합니다.
"""

import re, urllib.request, urllib.error, os
from datetime import datetime, timezone, timedelta
from html import unescape

JST = timezone(timedelta(hours=9))
NOW = datetime.now(JST).strftime("%Y.%m.%d %H:%M JST")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

def fetch_raw(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()
    except Exception as e:
        print(f"  [WARN] fetch failed: {url} → {e}")
        return b""

# ─── BLUE NEON ────────────────────────────────
def scrape_blueneon():
    print("[Blue Neon] scraping...")
    raw = fetch_raw("https://blueneon.jp/?mode=grp&gid=613974&sort=n")
    if not raw:
        return []
    try:
        html = raw.decode("euc-jp")
    except Exception:
        html = raw.decode("utf-8", errors="replace")

    img_pat   = re.compile(r'src="(https://img\d+\.shop-pro\.jp/PA01239/545/product/\d+_th\.jpg)\?cmsp_timestamp=(\d{8})\d+"')
    link_pat  = re.compile(r'href="(https://blueneon\.jp/\?pid=\d+)"')
    name_pat  = re.compile(r'\[([^\]]{3,80})\]')
    price_pat = re.compile(r'([\d,]+)円')

    items, pos = [], 0
    while True:
        mi = img_pat.search(html, pos)
        if not mi: break
        seg = html[mi.start(): mi.start() + 700]
        ml  = link_pat.search(seg)
        mn  = name_pat.search(seg)
        mp  = price_pat.search(seg)
        if ml and mn:
            dr = mi.group(2)
            name = unescape(mn.group(1)).replace("KAPITAL -","").replace("KAPITAL-","").strip()
            items.append({
                "source":"BLUE NEON","color":"#5ecb8f",
                "name": name,
                "price": f"¥{mp.group(1)}" if mp else "-",
                "img":  mi.group(1),
                "link": ml.group(1),
                "date": dr,
                "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}",
            })
        pos = mi.end()
    print(f"  → {len(items)} items")
    return items

# ─── TAKE FIVE ────────────────────────────────
def scrape_takefive():
    print("[Take Five] scraping...")
    raw = fetch_raw("https://takefive.jp/?mode=grp&gid=1066766&sort=n")
    if not raw:
        return []
    try:
        html = raw.decode("euc-jp")
    except Exception:
        html = raw.decode("utf-8", errors="replace")

    img_pat  = re.compile(r'src="(https://img\d+\.shop-pro\.jp/PA01043/640/product/\d+_th\.jpg)\?cmsp_timestamp=(\d{8})\d+"')
    link_pat = re.compile(r'href="(https://takefive\.jp/\?pid=\d+)"')
    name_pat = re.compile(r'\[([^\]]{3,80})\]')

    items, pos = [], 0
    while True:
        mi = img_pat.search(html, pos)
        if not mi: break
        seg = html[mi.start(): mi.start() + 600]
        ml  = link_pat.search(seg)
        mn  = name_pat.search(seg)
        if ml and mn:
            dr = mi.group(2)
            name = unescape(mn.group(1)).replace("[KAPITAL]","").strip()
            items.append({
                "source":"TAKE FIVE","color":"#f5c842",
                "name": name, "price": "-",
                "img":  mi.group(1),
                "link": ml.group(1),
                "date": dr,
                "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}",
            })
        pos = mi.end()
    print(f"  → {len(items)} items")
    return items

# ─── KEROUAC (static, 날짜 미노출) ───────────
def scrape_kerouac():
    print("[Kerouac] static list...")
    static = [
        ("000000005317","14ozブラック×ブラックデニム 5P ラットフレアパンツ (ヒッピーINSANEリメイク)","¥174,680","zdfvJ4a","png"),
        ("000000005333","ディアレザー プエブロインサボサンダル / キャメル","¥78,980","EAucFSS","jpg"),
        ("000000005334","ディアレザー プエブロインサボサンダル / ブラック","¥78,980","OcsGTUZ","jpg"),
        ("000000005326","シルクレーヨン トグルーマイレpt 長袖開襟シャツ","¥42,680","ohTPnek","jpg"),
        ("000000005325","シルクレーヨン トグルーマイレpt 半袖開襟シャツ","¥37,180","23YUH5E","jpg"),
        ("000000005311","14ozデニム 米米ジョーツ L's","¥30,580","6qwh7Bn","jpg"),
        ("000000005319","シアー天竺×天竺 リンガーT (DENIM MEN LOVE CATS スクラッチpt)","¥19,580","Vu98CF3","jpg"),
    ]
    return [{
        "source":"KEROUAC","color":"#4a9eff",
        "name":n,"price":p,
        "img":f"https://makeshop-multi-images.akamaized.net/kerouac2021/itemimages/{iid}_{ih}.{ext}",
        "link":f"https://kerouac.okinawa/view/item/{iid}?category_page_id=ct45",
        "date":"20260500","date_label":"26SS 신착",
    } for iid,n,p,ih,ext in static]

# ─── SPACE MOO (static, 입고일 기준) ─────────
def scrape_spacemoo():
    print("[Space Moo] static list...")
    static = [
        ("51805","11.5ozデニム サルエルヌーベルパンツ 2026 (EK-1874LP)","¥26,180","ek1874lp_2.jpg","20260518"),
        ("51756","6号帆布 スタンダードTOTE BAG 小 (EK-1399XB)","¥18,480","ek1399xb26_2.jpg","20260423"),
        ("51610","13ozデニム ハイウエストマキシスカート (EK-1422SK)","¥15,180","ek1422sk_2.jpg","20260404"),
        ("51611","レーヨンフリンジストール KAYO HUESO デニムマップ","¥16,280","k2603xm507_2.jpg","20260404"),
        ("51528","fastcolor セルビッチバンダナ 田植え (K2603BA504)","-","k2603ba504_2.jpg","20260326"),
    ]
    return [{
        "source":"SPACE MOO","color":"#c084fc",
        "name":n,"price":p,
        "img":f"https://www.spacemoo.jp/upload/save_image/{img}",
        "link":f"https://www.spacemoo.jp/products/details/{pid}",
        "date":dr,
        "date_label":f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}",
    } for pid,n,p,img,dr in static]

# ─── HTML 생성 ────────────────────────────────
NO_IMG = "<div class=\\'no-img\\'>NO IMAGE</div>"

def card_html(i):
    oe = f"this.parentNode.innerHTML='<div class=no-img>NO IMAGE</div>'"
    return f"""<a class="card" data-source="{i['source']}" data-date="{i['date']}" href="{i['link']}" target="_blank">
  <div class="card-img"><img src="{i['img']}" alt="" onerror="{oe}"><div class="source-dot" style="background:{i['color']}"></div></div>
  <div class="card-body">
    <span class="source-tag" style="color:{i['color']}">{i['source']}</span>
    <p class="card-name">{i['name']}</p>
    <div class="card-footer"><span class="card-price">{i['price']}</span><span class="date-badge">{i['date_label']}</span></div>
  </div>
</a>"""

def build_html(items):
    cards = "\n".join(card_html(i) for i in items)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KAPITAL 신상품 트래커</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0e0e0e;--sur:#1a1a1a;--bd:#2a2a2a;--txt:#f0ede8;--mu:#888}}
body{{background:var(--bg);color:var(--txt);font-family:'Noto Sans KR',sans-serif;font-weight:300}}
header{{border-bottom:1px solid var(--bd);padding:22px 28px;display:flex;justify-content:space-between;align-items:flex-end}}
.logo{{font-family:'Bebas Neue',cursive;font-size:36px;letter-spacing:4px;line-height:1}}
.logo span{{color:var(--mu);font-size:12px;font-family:'Noto Sans KR',sans-serif;display:block;letter-spacing:2px;margin-top:3px}}
.meta{{text-align:right;font-size:11px;color:var(--mu);line-height:1.8}}
.legend{{display:flex;gap:16px;padding:10px 28px;border-bottom:1px solid var(--bd);flex-wrap:wrap}}
.ld{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--mu)}}
.dot{{width:7px;height:7px;border-radius:50%}}
.filters{{padding:10px 28px;display:flex;gap:7px;border-bottom:1px solid var(--bd);flex-wrap:wrap;align-items:center}}
.fl{{font-size:11px;color:var(--mu);letter-spacing:1px;margin-right:3px}}
.fb{{background:transparent;border:1px solid var(--bd);color:var(--mu);padding:4px 11px;font-size:11px;font-family:'Noto Sans KR',sans-serif;cursor:pointer;letter-spacing:1px;transition:all .15s;border-radius:2px}}
.fb:hover,.fb.active{{border-color:var(--txt);color:var(--txt)}}
.cb{{padding:7px 28px;font-size:12px;color:var(--mu);border-bottom:1px solid var(--bd)}}
.cb span{{color:var(--txt);font-weight:500}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:1px;background:var(--bd)}}
.card{{background:var(--bg);transition:background .15s;position:relative;display:block;text-decoration:none;color:inherit}}
.card:hover{{background:var(--sur)}}
.ci{{width:100%;aspect-ratio:1;overflow:hidden;position:relative;background:var(--sur)}}
.ci img{{width:100%;height:100%;object-fit:cover;transition:transform .4s;display:block}}
.card:hover .ci img{{transform:scale(1.04)}}
.no-img{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#333;font-size:10px;letter-spacing:2px}}
.sd{{position:absolute;top:9px;left:9px;width:7px;height:7px;border-radius:50%}}
.cb2{{padding:10px 12px 12px;border-top:1px solid var(--bd)}}
.st{{font-size:9px;letter-spacing:2px;margin-bottom:4px;font-weight:500;display:block}}
.cn{{font-size:11px;line-height:1.5;color:var(--txt);margin-bottom:7px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-weight:300}}
.cf{{display:flex;justify-content:space-between;align-items:center}}
.cp{{font-size:12px;font-weight:500}}
.db{{font-size:9px;color:var(--mu);border:1px solid var(--bd);padding:2px 5px;border-radius:2px;white-space:nowrap}}
.notice{{padding:14px 28px;font-size:11px;color:var(--mu);line-height:1.8;border-top:1px solid var(--bd)}}
footer{{padding:14px 28px;border-top:1px solid var(--bd);font-size:11px;color:var(--mu);text-align:center;letter-spacing:1px}}
.hidden{{display:none!important}}
</style>
</head>
<body>
<header>
  <div class="logo">KAPITAL <span>NEW ARRIVALS TRACKER</span></div>
  <div class="meta">업데이트: {NOW}<br>총 {len(items)}개 · 등록일 최신순</div>
</header>
<div class="legend">
  <div class="ld"><div class="dot" style="background:#5ecb8f"></div>BLUE NEON</div>
  <div class="ld"><div class="dot" style="background:#4a9eff"></div>KEROUAC</div>
  <div class="ld"><div class="dot" style="background:#f5c842"></div>TAKE FIVE</div>
  <div class="ld"><div class="dot" style="background:#c084fc"></div>SPACE MOO</div>
</div>
<div class="filters">
  <span class="fl">FILTER</span>
  <button class="fb active" data-source="ALL" onclick="filt('ALL')">ALL</button>
  <button class="fb" data-source="BLUE NEON" onclick="filt('BLUE NEON')">BLUE NEON</button>
  <button class="fb" data-source="KEROUAC" onclick="filt('KEROUAC')">KEROUAC</button>
  <button class="fb" data-source="TAKE FIVE" onclick="filt('TAKE FIVE')">TAKE FIVE</button>
  <button class="fb" data-source="SPACE MOO" onclick="filt('SPACE MOO')">SPACE MOO</button>
</div>
<div class="cb">총 <span id="cnt">{len(items)}</span>개 표시 중</div>
<div class="grid" id="grid">{cards}</div>
<div class="notice">
  ※ Blue Neon·Take Five: 이미지 타임스탬프(등록/수정일) | Kerouac: 날짜 미노출 → 26SS 신착 표기 | Space Moo: 입고일 기준<br>
  ※ 캐피탈 공홈·SE7EN: robots 차단으로 수집 불가 | 카드 클릭 → 상품 페이지
</div>
<footer>KAPITAL TRACKER · GitHub Actions 매일 07:00 KST 자동 업데이트</footer>
<script>
const cs=Array.from(document.querySelectorAll('.card[data-source]'));
cs.sort((a,b)=>parseInt(b.dataset.date)-parseInt(a.dataset.date));
cs.forEach(c=>document.getElementById('grid').appendChild(c));
function filt(src){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  document.querySelector(`.fb[data-source="${{src}}"]`).classList.add('active');
  let n=0;
  cs.forEach(c=>{{const s=src==='ALL'||c.dataset.source===src;c.classList.toggle('hidden',!s);if(s)n++;}});
  document.getElementById('cnt').textContent=n;
}}
</script>
</body>
</html>"""

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    all_items = scrape_blueneon() + scrape_takefive() + scrape_kerouac() + scrape_spacemoo()
    html = build_html(all_items)
    with open("docs/index.html","w",encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ docs/index.html 생성 완료 ({len(all_items)}개 상품)")
