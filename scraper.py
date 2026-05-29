#!/usr/bin/env python3
import re, urllib.request, os
from datetime import datetime, timezone, timedelta
from html import unescape

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST).strftime("%Y.%m.%d %H:%M KST")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

def fetch_raw(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()
    except Exception as e:
        print(f"  [WARN] {url} → {e}")
        return b""

def scrape_blueneon():
    print("[Blue Neon] scraping...")
    raw = fetch_raw("https://blueneon.jp/?mode=grp&gid=613974&sort=n")
    if not raw: return []
    try: html = raw.decode("euc-jp")
    except: html = raw.decode("utf-8", errors="replace")

    # 실제 마크다운 변환 후 구조:
    # [![](img?cmsp_timestamp=YYYYMMDD)](link)
    # [KAPITAL - 상품명](link)
    # 가격円
    img_pat   = re.compile(r'https://img\d+\.shop-pro\.jp/PA01239/545/product/(\d+)_th\.jpg\?cmsp_timestamp=(\d{8})\d+')
    name_pat  = re.compile(r'\[KAPITAL\s*-\s*([^\]]+)\]\(https://blueneon')
    price_pat = re.compile(r'([\d,]+)円')

    items = []
    for mi in img_pat.finditer(html):
        pid, dr = mi.group(1), mi.group(2)
        seg = html[mi.start(): mi.start()+400]
        mn = name_pat.search(seg)
        mp = price_pat.search(seg)
        name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
        items.append({
            "source":"BLUE NEON","color":"#5ecb8f",
            "name": name,
            "price": f"¥{mp.group(1)}" if mp else "-",
            "img": f"https://img15.shop-pro.jp/PA01239/545/product/{pid}_th.jpg",
            "link": f"https://blueneon.jp/?pid={pid}",
            "date": dr, "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"
        })
    print(f"  → {len(items)} items")
    return items

def scrape_takefive():
    print("[Take Five] scraping...")
    raw = fetch_raw("https://takefive.jp/?mode=grp&gid=1066766&sort=n")
    if not raw: return []
    try: html = raw.decode("euc-jp")
    except: html = raw.decode("utf-8", errors="replace")

    # 실제 HTML 구조:
    # [![](img_url?cmsp_timestamp=YYYYMMDD...)](link_url)
    # [[KAPITAL]상품명](link_url)
    # 이미지 URL과 링크가 별도 줄에 있음

    # 이미지 URL + timestamp
    # 실제 HTML 구조:
    # [![](img?cmsp_timestamp=YYYYMMDD)](link)
    # [![](icon)][KAPITAL]상품명](link)
    img_pat  = re.compile(
        r'https://img09\.shop-pro\.jp/PA01043/640/product/(\d+)_th\.jpg'
        r'\?cmsp_timestamp=(\d{8})\d+'
    )
    name_pat = re.compile(r'\[(?:!\[.*?\]\(.*?\))?\[KAPITAL\]\s*([^\[\]]+)\]\(https://takefive')

    items = []
    for mi in img_pat.finditer(html):
        pid      = mi.group(1)
        date_raw = mi.group(2)
        seg = html[mi.start(): mi.start()+500]
        mn = name_pat.search(seg)
        name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
        dr = date_raw
        items.append({
            "source":"TAKE FIVE","color":"#f5c842",
            "name": name, "price": "-",
            "img": f"https://img09.shop-pro.jp/PA01043/640/product/{pid}_th.jpg",
            "link": f"https://takefive.jp/?pid={pid}",
            "date": dr, "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"
        })

    print(f"  → {len(items)} items")
    return items

def scrape_kerouac():
    static = [
        ("000000005317","14ozブラック×ブラックデニム 5P ラットフレアパンツ (ヒッピーINSANEリメイク)","¥174,680","zdfvJ4a","png"),
        ("000000005333","ディアレザー プエブロインサボサンダル / キャメル","¥78,980","EAucFSS","jpg"),
        ("000000005334","ディアレザー プエブロインサボサンダル / ブラック","¥78,980","OcsGTUZ","jpg"),
        ("000000005326","シルクレーヨン トグルーマイレpt 長袖開襟シャツ","¥42,680","ohTPnek","jpg"),
        ("000000005325","シルクレーヨン トグルーマイレpt 半袖開襟シャツ","¥37,180","23YUH5E","jpg"),
        ("000000005311","14ozデニム 米米ジョーツ L's","¥30,580","6qwh7Bn","jpg"),
        ("000000005319","シアー天竺×天竺 リンガーT (DENIM MEN LOVE CATS スクラッチpt)","¥19,580","Vu98CF3","jpg"),
    ]
    return [{"source":"KEROUAC","color":"#4a9eff","name":n,"price":p,
        "img":f"https://makeshop-multi-images.akamaized.net/kerouac2021/itemimages/{iid}_{ih}.{ext}",
        "link":f"https://kerouac.okinawa/view/item/{iid}?category_page_id=ct45",
        "date":"20260500","date_label":"26SS 신착"} for iid,n,p,ih,ext in static]

def scrape_spacemoo():
    static = [
        ("51805","11.5ozデニム サルエルヌーベルパンツ 2026 (EK-1874LP)","¥26,180","ek1874lp_2.jpg","20260518"),
        ("51756","6号帆布 スタンダードTOTE BAG 小 (EK-1399XB)","¥18,480","ek1399xb26_2.jpg","20260423"),
        ("51610","13ozデニム ハイウエストマキシスカート (EK-1422SK)","¥15,180","ek1422sk_2.jpg","20260404"),
        ("51611","レーヨンフリンジストール KAYO HUESO デニムマップ","¥16,280","k2603xm507_2.jpg","20260404"),
        ("51528","fastcolor セルビッチバンダナ 田植え (K2603BA504)","-","k2603ba504_2.jpg","20260326"),
    ]
    return [{"source":"SPACE MOO","color":"#c084fc","name":n,"price":p,
        "img":f"https://www.spacemoo.jp/upload/save_image/{img}",
        "link":f"https://www.spacemoo.jp/products/details/{pid}",
        "date":dr,"date_label":f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"} for pid,n,p,img,dr in static]

def card_html(i):
    oe = "this.style.display='none'"
    return (
        f'<a class="card" data-source="{i["source"]}" data-date="{i["date"]}" '
        f'href="{i["link"]}" target="_blank">'
        f'<div class="ci"><img src="{i["img"]}" onerror="{oe}">'
        f'<div class="sd" style="background:{i["color"]}"></div></div>'
        f'<div class="cb2">'
        f'<span class="st" style="color:{i["color"]}">{i["source"]}</span>'
        f'<p class="cn">{i["name"]}</p>'
        f'<div class="cf"><span class="cp">{i["price"]}</span>'
        f'<span class="db">{i["date_label"]}</span></div>'
        f'</div></a>'
    )

CSS = """<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0e0e0e;color:#f0ede8;font-family:sans-serif;font-weight:300;min-height:100vh}
header{border-bottom:1px solid #2a2a2a;padding:20px 24px;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:8px}
.logo{font-size:26px;font-weight:700;letter-spacing:4px;line-height:1}
.logo span{color:#888;font-size:11px;font-weight:300;display:block;letter-spacing:2px;margin-top:3px}
.meta{text-align:right;font-size:11px;color:#888;line-height:1.8}
.legend{display:flex;gap:14px;padding:10px 24px;border-bottom:1px solid #2a2a2a;flex-wrap:wrap}
.ld{display:flex;align-items:center;gap:5px;font-size:11px;color:#888}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.filters{padding:10px 24px;display:flex;gap:7px;border-bottom:1px solid #2a2a2a;flex-wrap:wrap;align-items:center}
.fl{font-size:11px;color:#888;letter-spacing:1px;margin-right:3px}
button{background:transparent;border:1px solid #2a2a2a;color:#888;padding:4px 11px;font-size:11px;cursor:pointer;letter-spacing:1px;transition:all .15s;border-radius:2px;font-family:sans-serif}
button:hover,button.active{border-color:#f0ede8;color:#f0ede8}
.cbar{padding:7px 24px;font-size:12px;color:#888;border-bottom:1px solid #2a2a2a}
.cbar span{color:#f0ede8;font-weight:500}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1px;background:#2a2a2a}
.card{background:#0e0e0e;transition:background .15s;display:block;text-decoration:none;color:inherit}
.card:hover{background:#1a1a1a}
.ci{width:100%;aspect-ratio:1/1;overflow:hidden;position:relative;background:#1a1a1a;display:block}
.ci img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s}
.card:hover .ci img{transform:scale(1.04)}
.sd{position:absolute;top:8px;left:8px;width:7px;height:7px;border-radius:50%}
.cb2{padding:10px 12px 12px;border-top:1px solid #2a2a2a}
.st{font-size:9px;letter-spacing:2px;margin-bottom:4px;font-weight:500;display:block}
.cn{font-size:11px;line-height:1.5;color:#f0ede8;margin-bottom:7px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-weight:300}
.cf{display:flex;justify-content:space-between;align-items:center}
.cp{font-size:12px;font-weight:500;color:#f0ede8}
.db{font-size:9px;color:#888;border:1px solid #2a2a2a;padding:2px 5px;border-radius:2px;white-space:nowrap}
.notice{padding:14px 24px;font-size:11px;color:#888;line-height:1.8;border-top:1px solid #2a2a2a}
footer{padding:14px 24px;border-top:1px solid #2a2a2a;font-size:11px;color:#888;text-align:center;letter-spacing:1px}
.hidden{display:none!important}
</style>"""

JS = """<script>
var cs=Array.from(document.querySelectorAll('.card[data-source]'));
cs.sort(function(a,b){return parseInt(b.dataset.date)-parseInt(a.dataset.date)});
var g=document.getElementById('grid');
cs.forEach(function(c){g.appendChild(c)});
function filt(src){
  document.querySelectorAll('button[data-source]').forEach(function(b){b.classList.remove('active')});
  document.querySelector('button[data-source="'+src+'"]').classList.add('active');
  var n=0;
  cs.forEach(function(c){var s=src==='ALL'||c.dataset.source===src;c.classList.toggle('hidden',!s);if(s)n++});
  document.getElementById('cnt').textContent=n;
}
</script>"""

def build_html(items):
    cards = "\n".join(card_html(i) for i in items)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KAPITAL 신상품 트래커</title>
{CSS}
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
  <button class="active" data-source="ALL" onclick="filt('ALL')">ALL</button>
  <button data-source="BLUE NEON" onclick="filt('BLUE NEON')">BLUE NEON</button>
  <button data-source="KEROUAC" onclick="filt('KEROUAC')">KEROUAC</button>
  <button data-source="TAKE FIVE" onclick="filt('TAKE FIVE')">TAKE FIVE</button>
  <button data-source="SPACE MOO" onclick="filt('SPACE MOO')">SPACE MOO</button>
</div>
<div class="cbar">총 <span id="cnt">{len(items)}</span>개 표시 중</div>
<div class="grid" id="grid">{cards}</div>
<div class="notice">
  ※ Blue Neon·Take Five: 이미지 타임스탬프 기준 | Kerouac: 날짜 미노출 → 26SS 신착 | Space Moo: 입고일 기준<br>
  ※ 캐피탈 공홈·SE7EN: robots 차단으로 수집 불가
</div>
<footer>KAPITAL TRACKER · GitHub Actions 매일 07:00 KST 자동 업데이트</footer>
{JS}
</body>
</html>"""

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    all_items = scrape_blueneon() + scrape_takefive() + scrape_kerouac() + scrape_spacemoo()

    # 2달 이내 필터 + 최신순 정렬
    from datetime import date
    today = datetime.now(KST)
    cutoff = (today.replace(day=1) - timedelta(days=1)).replace(day=1)  # 2달 전 1일
    cutoff_int = int(cutoff.strftime("%Y%m00"))

    items = [i for i in all_items if int(i["date"]) >= cutoff_int]
    items.sort(key=lambda x: int(x["date"]), reverse=True)

    print(f"  필터 후: {len(items)}개 (기준일: {cutoff.strftime('%Y.%m')} 이후)")
    with open("docs/index.html","w",encoding="utf-8") as f:
        f.write(build_html(items))
    print(f"\n✅ 완료 ({len(items)}개)")
