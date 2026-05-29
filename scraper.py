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
        with urllib.request.urlopen(req, timeout=25) as r:
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
    # 실제 HTML 구조 (원본 HTML):
    # <img src="...product/PID_th.jpg?cmsp_timestamp=YYYYMMDD...">
    # <a href="?pid=PID">[KAPITAL]상품명</a>
    img_pat  = re.compile(
        r'https://img09\.shop-pro\.jp/PA01043/640/product/(\d+)_th\.jpg'
        r'\?cmsp_timestamp=(\d{8})\d+'
    )
    name_pat = re.compile(r'href="\?pid=\d+"[^>]*>(?:<img[^>]+>)*\[KAPITAL\]\s*([^<]+)</a>')

    items = []
    for mi in img_pat.finditer(html):
        pid      = mi.group(1)
        date_raw = mi.group(2)
        seg = html[mi.start(): mi.start()+600]
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
    # item ID 높을수록 최신 → date를 ID 기반으로 부여 (필터 통과용 26SS 날짜)
    result = []
    for iid,n,p,ih,ext in static:
        item_num = int(iid)
        # 5317~5366 범위, ID 차이를 날짜로 환산 (5366=26.05.29 기준)
        days_ago = max(0, (5366 - item_num))
        from datetime import date as _date
        item_date = (datetime.now(KST) - timedelta(days=days_ago)).strftime("%Y%m%d")
        result.append({"source":"KEROUAC","color":"#4a9eff","name":n,"price":p,
            "img":f"https://makeshop-multi-images.akamaized.net/kerouac2021/itemimages/{iid}_{ih}.{ext}",
            "link":f"https://kerouac.okinawa/view/item/{iid}?category_page_id=ct45",
            "date":item_date,"date_label":"26SS 신착"})
    return result

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

def scrape_shop_pro(source, color, img_prefix, url, encoding="euc-jp"):
    """shop-pro.jp 기반 사이트 공통 스크래퍼"""
    print(f"[{source}] scraping...")
    raw = fetch_raw(url)
    if not raw: return []
    try: html = raw.decode(encoding)
    except: html = raw.decode("utf-8", errors="replace")

    img_pat   = re.compile(
        r'https://img\d+\.shop-pro\.jp/' + img_prefix +
        r'/product/(\d+)_th\.(jpg|png)\?cmsp_timestamp=(\d{8})\d+'
    )
    name_pat  = re.compile(r'href="\?pid=\d+"[^>]*>(?:<img[^>]+>)*([^<]{4,100})</a>')
    price_pat = re.compile(r'([\d,]+)円')

    items, seen = [], set()
    for mi in img_pat.finditer(html):
        pid, ext, dr = mi.group(1), mi.group(2), mi.group(3)
        if pid in seen: continue
        seen.add(pid)
        seg  = html[mi.start(): mi.start()+600]
        mn   = name_pat.search(seg)
        mp   = price_pat.search(seg)
        name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
        # KAPITAL / kapital 접두어 정리
        name = re.sub(r'^(?:KAPITAL|kapital|\[?kapital\]?)\s*[-/]?\s*', '', name, flags=re.IGNORECASE).strip()
        items.append({
            "source": source, "color": color,
            "name": name,
            "price": f"¥{mp.group(1)}" if mp else "-",
            "img": f"https://img08.shop-pro.jp/{img_prefix}/product/{pid}_th.{ext}",
            "link": f"{url.split('?')[0]}?pid={pid}",
            "date": dr, "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"
        })
    print(f"  → {len(items)} items")
    return items


def scrape_babooshka():
    return scrape_shop_pro(
        "BABOOSHKA", "#38bdf8",
        "PA01038/438",
        "https://bab-web.shop-pro.jp/?mode=cate&cbid=1739088&csid=1&sort=n"
    )

def scrape_aindahing():
    return scrape_shop_pro(
        "AIN.DAH.ING", "#a78bfa",
        "PA01135/633",
        "http://ain-dah-ing.shop-pro.jp/?mode=cate&cbid=1008715&csid=0&sort=n"
    )

def scrape_stc():
    print("[S.T.C] scraping...")
    # 타임아웃 대응: 2회 시도
    raw = fetch_raw("https://www.net-stc.com/category/14/")
    if not raw:
        print("  재시도...")
        raw = fetch_raw("https://www.net-stc.com/category/14/")
    if not raw: return []
    html = raw.decode("utf-8", errors="replace")

    block_pat = re.compile(
        r'src="(https://www\.net-stc\.com/images/material/(?![\d/])[^"]+\.jpg)"'
        r'.*?href="(https://www\.net-stc\.com/item/([^/]+)/)"[^>]*>\s*([^<]{4,100})',
        re.DOTALL
    )
    price_pat = re.compile(r'([\d,]+)円')

    items, seen = [], set()
    for m in block_pat.finditer(html):
        img  = m.group(1)
        link = m.group(2)
        code = m.group(3)
        name = unescape(m.group(4)).strip()
        if code in seen: continue
        seen.add(code)
        seg = html[m.start(): m.start()+400]
        mp  = price_pat.search(seg)
        name = re.sub(r'^KAPITAL\s*\(キャピタル\)\s*', '', name).strip()
        items.append({
            "source":"S.T.C","color":"#34d399",
            "name": name,
            "price": f"¥{mp.group(1)}" if mp else "-",
            "img": img, "link": link,
            "date": datetime.now(KST).strftime("%Y%m%d"),
            "date_label": "신착"
        })
    print(f"  → {len(items)} items")
    return items


def scrape_se7en():
    print("[SE7EN] scraping with selenium...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        import time

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36")

        driver = webdriver.Chrome(options=opts)
        driver.get("https://se7en.jp/products/list?category_id=32&orderby=3&pageno=1&disp_number=20")

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".item_list, .product_list, .item-list, div[class*='item']"))
            )
        except:
            pass
        time.sleep(3)

        html = driver.page_source
        with open("/tmp/se7en_debug.html", "w", encoding="utf-8") as dbg:
            dbg.write(html)
        driver.quit()

        # 상품 파싱
        # SE7EN 상품 URL 패턴: /products/detail/숫자
        items = []
        seen  = set()

        # 패턴1: 상품 상세 링크 기반
        links = re.findall(r'href="(https://se7en\.jp/products/detail/(\d+))"', html)
        # 디버그: 첫번째 상품 HTML 확인
        if links:
            pid0 = links[0][1]
            idx0 = html.find(f'detail/{pid0}')
            seg0 = html[max(0,idx0-300): idx0+1000]
            print(f"  [SE7EN debug] first item seg: {repr(seg0[:600])}")
        for link, pid in links:
            if pid in seen: continue
            seen.add(pid)
            # 해당 블록에서 이미지+이름 찾기
            idx = html.find(f'detail/{pid}')
            seg = html[max(0,idx-200): idx+800]
            mi = re.search(r'src="(/html/upload/save_image/[^"]+)"|' +
                           r'src="(https://se7en\.jp/[^"]+\.(?:jpg|png|webp))"', seg)
                           r'src="(https://se7en\.jp/[^"]+\.(?:jpg|png|webp))"', seg)
            mn = re.search(r'<p[^>]*>\s*([^<]{4,80})\s*</p>', seg)
            img_raw = (mi.group(1) or mi.group(2)) if mi else ""
            img = f"https://se7en.jp{img_raw}" if img_raw and img_raw.startswith("/") else img_raw
            name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
            items.append({
                "source":"SE7EN","color":"#fb923c",
                "name": name, "price": "-",
                "img": img, "link": link,
                "date": datetime.now(KST).strftime("%Y%m%d"),
                "date_label": "신착"
            })

        print(f"  → {len(items)} items")
        return items

    except Exception as e:
        print(f"  [WARN] SE7EN Selenium 실패: {e}")
        return []


def scrape_kapital_home():
    print("[Kapital Home] scraping with selenium...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36")

        driver = webdriver.Chrome(options=opts)

        # 신착순 URL
        url = "https://www.kapital-webshop.jp/item_list.html?sort=3&dispno=40"
        driver.get(url)
        time.sleep(4)

        # 상품 목록 대기
        try:
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li"))
            )
        except:
            pass
        time.sleep(3)

        html = driver.page_source
        # 디버그용 저장
        with open("/tmp/kapital_debug.html", "w", encoding="utf-8") as dbg:
            dbg.write(html)
        driver.quit()

        # 상품 파싱 - 캐피탈 공홈 구조:
        # <li class="...item..."> 블록 안에
        # <a href="/item/코드.html"><img src="...코드_M.jpg"></a>
        # <p class="...name...">상품명</p>
        # <p class="...price...">가격円</p>
        price_pat = re.compile(r'([\d,]+)円')
        block_pat = re.compile(r'<li[^>]*class="item_list_box"[^>]*>(.*?)</li>', re.DOTALL)

        # 실제 HTML 구조 확인용 출력 (첫 2000자)
        print(f"  [debug] html length: {len(html)}")
        # li 태그 샘플
        li_sample = re.findall(r'<li[^>]*class="[^"]*item[^"]*"[^>]*>', html)[:3]
        print(f"  [debug] li.item samples: {li_sample}")
        # 첫 번째 블록 내용 출력
        first_block = block_pat.search(html)
        if first_block:
            print(f"  [debug] first block (500chars): {repr(first_block.group(1)[:500])}")
        # 링크 샘플
        link_sample = re.findall(r'href="(https://www\.kapital-webshop\.jp/item/[^"]+)"', html)[:3]
        print(f"  [debug] item links: {link_sample}")

        items = []
        seen  = set()
        for block in block_pat.finditer(html):
            b  = block.group(1)
            ml = re.search(r'href="(https://www\.kapital-webshop\.jp/item/([^"]+)\.html)"', b)
            mi = re.search(r'data-original="(/client_info/KAPITAL/itemimage/[^"]+\.jpg)"', b)
            if not mi: mi = re.search(r'src="(/client_info/KAPITAL/[^"]+\.jpg)"', b)

            mn = re.search(r'alt="([^"]{4,80})"', b)
            if not mn: mn = re.search(r'class="[^"]*name[^"]*"[^>]*>\s*([^<]{4,80})', b)
            if not mn: mn = re.search(r'<p[^>]*>\s*([^<]{10,80})\s*</p>', b)
            mp = price_pat.search(b)
            if not ml: continue
            item_code = ml.group(2)
            if item_code in seen: continue
            seen.add(item_code)
            name  = unescape(mn.group(1)).strip() if mn else item_code
            img_raw = mi.group(1) if mi else ""
            img = f"https://www.kapital-webshop.jp{img_raw}" if img_raw else ""
            price = f"¥{mp.group(1)}" if mp else "-"
            items.append({
                "source":"KAPITAL 공홈","color":"#ff6b6b",
                "name": name, "price": price,
                "img": img, "link": ml.group(1),
                "date": datetime.now(KST).strftime("%Y%m%d"),
                "date_label": "신착"
            })

        print(f"  → {len(items)} items")
        return items

    except Exception as e:
        print(f"  [WARN] Selenium 실패: {e}")
        return []


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

var curSrc='ALL', curDays=3;

function getDateInt(daysAgo){
  var d=new Date();
  d.setDate(d.getDate()-daysAgo);
  var y=d.getFullYear();
  var m=String(d.getMonth()+1).padStart(2,'0');
  var day=String(d.getDate()).padStart(2,'0');
  return parseInt(y+m+day);
}

function applyFilter(){
  var cutoff=getDateInt(curDays);
  var n=0;
  cs.forEach(function(c){
    var srcOk=curSrc==='ALL'||c.dataset.source===curSrc;
    var dateOk=parseInt(c.dataset.date)>=cutoff;
    var show=srcOk&&dateOk;
    c.classList.toggle('hidden',!show);
    if(show)n++;
  });
  document.getElementById('cnt').textContent=n;
}

function filt(src){
  curSrc=src;
  document.querySelectorAll('button[data-source]').forEach(function(b){b.classList.remove('active')});
  document.querySelector('button[data-source="'+src+'"]').classList.add('active');
  applyFilter();
}

function filtDays(days){
  curDays=days;
  document.querySelectorAll('.dbtn').forEach(function(b){b.classList.remove('active')});
  document.querySelector('.dbtn[data-days="'+days+'"]').classList.add('active');
  applyFilter();
}

// 초기 3일 필터 적용
filtDays(3);
</script>"""

def build_html(items):
    cards = "\n".join(card_html(i) for i in items)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KAPITAL NEW ARRIVALS TRACKER</title>
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
  <div class="ld"><div class="dot" style="background:#38bdf8"></div>BABOOSHKA</div>
  <div class="ld"><div class="dot" style="background:#a78bfa"></div>AIN.DAH.ING</div>
  <div class="ld"><div class="dot" style="background:#34d399"></div>S.T.C</div>
  <div class="ld"><div class="dot" style="background:#fb923c"></div>SE7EN</div>
  <div class="ld"><div class="dot" style="background:#ff6b6b"></div>KAPITAL 공홈</div>
</div>
<div class="filters">
  <span class="fl">SHOP</span>
  <button class="active" data-source="ALL" onclick="filt('ALL')">ALL</button>
  <button data-source="BLUE NEON" onclick="filt('BLUE NEON')">BLUE NEON</button>
  <button data-source="KEROUAC" onclick="filt('KEROUAC')">KEROUAC</button>
  <button data-source="TAKE FIVE" onclick="filt('TAKE FIVE')">TAKE FIVE</button>
  <button data-source="SPACE MOO" onclick="filt('SPACE MOO')">SPACE MOO</button>
  <button data-source="BABOOSHKA" onclick="filt('BABOOSHKA')">BABOOSHKA</button>
  <button data-source="AIN.DAH.ING" onclick="filt('AIN.DAH.ING')">AIN.DAH.ING</button>
  <button data-source="S.T.C" onclick="filt('S.T.C')">S.T.C</button>
  <button data-source="SE7EN" onclick="filt('SE7EN')">SE7EN</button>
  <button data-source="KAPITAL 공홈" onclick="filt('KAPITAL 공홈')">KAPITAL 공홈</button>
</div>
<div class="filters">
  <span class="fl">DAYS</span>
  <button class="dbtn active" data-days="3" onclick="filtDays(3)">3일</button>
  <button class="dbtn" data-days="10" onclick="filtDays(10)">10일</button>
  <button class="dbtn" data-days="30" onclick="filtDays(30)">30일</button>
  <button class="dbtn" data-days="60" onclick="filtDays(60)">60일</button>
</div>
<div class="cbar">총 <span id="cnt">{len(items)}</span>개 표시 중</div>
<div class="grid" id="grid">{cards}</div>
<div class="notice">
  ※ Blue Neon·Take Five: 이미지 타임스탬프 기준 | Kerouac: 날짜 미노출 → 26SS 신착 | Space Moo: 입고일 기준<br>
  ※ 캐피탈 공홈·SE7EN: robots 차단으로 수집 불가
</div>
<footer>KAPITAL TRACKER · GitHub Actions 6시간마다 자동 업데이트</footer>
{JS}
</body>
</html>"""

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    all_items = (scrape_blueneon() + scrape_takefive() + scrape_kerouac() + scrape_spacemoo() +
                 scrape_babooshka() + scrape_aindahing() + scrape_stc() +
                 scrape_se7en() + scrape_kapital_home())

    # 60일 이내 필터 + 최신순 정렬
    today = datetime.now(KST)
    cutoff = today - timedelta(days=60)
    cutoff_int = int(cutoff.strftime("%Y%m%d"))

    items = [i for i in all_items if int(i["date"]) >= cutoff_int]
    items.sort(key=lambda x: int(x["date"]), reverse=True)

    print(f"  필터 후: {len(items)}개 (기준일: {cutoff.strftime('%Y.%m.%d')} 이후)")
    with open("docs/index.html","w",encoding="utf-8") as f:
        f.write(build_html(items))
    print(f"\n✅ 완료 ({len(items)}개)")
