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

def load_date_cache():
    """이전에 기록된 상품 날짜 캐시 로드"""
    try:
        import json
        with open("docs/date_cache.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_date_cache(cache):
    """상품 날짜 캐시 저장"""
    import json
    os.makedirs("docs", exist_ok=True)
    with open("docs/date_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def load_prev_items():
    """이전 실행의 상품 ID 목록 로드"""
    try:
        import json
        with open("docs/prev_items.json", "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_prev_items(item_keys):
    """현재 상품 ID 목록 저장"""
    import json
    os.makedirs("docs", exist_ok=True)
    with open("docs/prev_items.json", "w", encoding="utf-8") as f:
        json.dump(list(item_keys), f, ensure_ascii=False)

def get_item_date(cache, source, item_id, today):
    """캐시에서 날짜 조회, 없으면 오늘 날짜로 신규 등록"""
    key = f"{source}:{item_id}"
    if key not in cache:
        cache[key] = today
    return cache[key]


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

    # 마크다운 변환 후 구조:
    # [![](img?cmsp_timestamp=YYYYMMDD)](link)
    # [[KAPITAL]상품명](link)
    img_pat  = re.compile(
        r'https://img09\.shop-pro\.jp/PA01043/640/product/(\d+)_th\.jpg'
        r'\?cmsp_timestamp=(\d{8})\d+'
    )
    # [[KAPITAL]상품명](링크) 패턴
    name_pat = re.compile(r'href="\?pid=\d+"[^>]*>\[KAPITAL\]([^<]+)</a>')

    items = []
    for mi in img_pat.finditer(html):
        pid      = mi.group(1)
        date_raw = mi.group(2)
        seg = html[mi.start(): mi.start()+600]
        mn = name_pat.search(seg)
        if mn:
            name = unescape(mn.group(1)).strip()
        else:
            name = f"상품 {pid}"
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
    raw = fetch_raw("https://www.net-stc.com/category/14/")
    if not raw:
        print("  재시도...")
        raw = fetch_raw("https://www.net-stc.com/category/14/")
    if not raw: return []
    html = raw.decode("utf-8", errors="replace")

    block_pat = re.compile(
        r'src="(https://www\.net-stc\.com/images/material/(?![\d/])[^"]+\.jpg)"'
        r'.*?href="(https://www\.net-stc\.com/item/([^/]+)/)"[^>]*>\s*([^<]{4,100})'
        r'.*?販売価格:([\d,]+)円',
        re.DOTALL
    )

    items, seen = [], set()
    for m in block_pat.finditer(html):
        code = m.group(3)
        if code in seen: continue
        seen.add(code)
        name = unescape(m.group(4)).strip()
        name = re.sub(r'^KAPITAL\s*\(キャピタル\)\s*', '', name).strip()
        items.append({
            "source":"S.T.C","color":"#34d399",
            "name": name,
            "price": f"¥{m.group(5)}",
            "img": m.group(1),
            "link": m.group(2),
            "date": datetime.now(KST).strftime("%Y%m%d"),
            "date_label": "신착"
        })
    items = items[:10]
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
            mi = re.search(r'src="(/html/upload/save_image/[^"]+)"', seg)
            if not mi: mi = re.search(r'src="(https://se7en\.jp/[^"]+\.(?:jpg|png|webp))"', seg)
            mn = re.search(r'ec-shelfGrid__item-name[^>]*>\s*([^<]{2,80})', seg)
            if not mn: mn = re.search(r'<p[^>]*>\s*([^<]{4,80})\s*</p>', seg)
            img_raw = mi.group(1) if mi else ""
            img = f"https://se7en.jp{img_raw}" if img_raw.startswith("/") else img_raw
            mp = re.search(r'(?:ec-price|price)[^>]*>\D*(\d[\d,]+)\D*<|([\d,]+)円', seg)
            price = f"¥{(mp.group(1) or mp.group(2))}" if mp and (mp.group(1) or mp.group(2)) else "-"
            name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
            items.append({
                "source":"SE7EN","color":"#fb923c",
                "name": name,
                "price": price,
                "img": img, "link": link,
                "date": datetime.now(KST).strftime("%Y%m%d"),
                "date_label": "신착"
            })
            if len(items) >= 10:
                break

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
        price_pat = re.compile(r'(\d[\d,]+)円')
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
            # 가격: 블록 안 + 블록 뒤 200자에서도 검색
            mp = price_pat.search(b)
            if not mp:
                block_end = block.end()
                after = html[block_end: block_end+600]
                mp = price_pat.search(after)
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
            if len(items) >= 10:
                break

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
        f'<div class="sd" style="background:{i["color"]}"></div>'
        f'</div>'
        f'<div class="cb2">'
        f'<span class="st" style="color:{i["color"]}">{i["source"]}</span>'
        f'<p class="cn">{i["name"]}</p>'
        f'<div class="cf"><span class="cp">{i["price"]}</span>'
        f'<span class="db">{i["date_label"]}</span></div>'
        f'</div></a>'
    )

SITE_ORDER = [
    "KAPITAL 공홈","KEROUAC","TAKE FIVE","BLUE NEON",
    "BABOOSHKA","AIN.DAH.ING","S.T.C","SE7EN","SPACE MOO",
]
SITE_COLORS = {
    "KAPITAL 공홈":"#ff6b6b","KEROUAC":"#4a9eff","TAKE FIVE":"#f5c842",
    "BLUE NEON":"#5ecb8f","BABOOSHKA":"#38bdf8","AIN.DAH.ING":"#a78bfa",
    "S.T.C":"#34d399","SE7EN":"#fb923c","SPACE MOO":"#c084fc",
}
SITE_LABELS = {
    "KAPITAL 공홈":"KAPITAL<br>공홈","KEROUAC":"KEROUAC","TAKE FIVE":"TAKE<br>FIVE",
    "BLUE NEON":"BLUE<br>NEON","BABOOSHKA":"BABOOSHKA","AIN.DAH.ING":"AIN.DAH<br>.ING",
    "S.T.C":"S.T.C","SE7EN":"SE7EN","SPACE MOO":"SPACE<br>MOO",
}

CSS = """<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0e0e0e;color:#f0ede8;font-family:sans-serif;font-weight:300;min-height:100vh}
header{border-bottom:1px solid #2a2a2a;padding:14px 16px;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:6px}
.logo{font-size:22px;font-weight:700;letter-spacing:4px;line-height:1}
.logo span{color:#555;font-size:10px;font-weight:300;display:block;letter-spacing:2px;margin-top:2px}
.meta{font-size:10px;color:#555;text-align:right;line-height:1.7}
.filters{padding:7px 16px;display:flex;gap:6px;border-bottom:1px solid #2a2a2a;align-items:center;flex-wrap:wrap}
.fl{font-size:10px;color:#555;margin-right:3px;letter-spacing:1px}
button{background:transparent;border:1px solid #2a2a2a;color:#555;padding:3px 10px;font-size:10px;cursor:pointer;border-radius:2px;font-family:sans-serif;transition:all .15s}
button:hover,button.active{border-color:#f0ede8;color:#f0ede8}
.cbar{padding:5px 16px;font-size:10px;color:#555;border-bottom:1px solid #2a2a2a}
.cbar span{color:#f0ede8}
.grid-wrap{overflow-x:auto;width:100%}
.site-grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);border-left:1px solid #2a2a2a;min-width:0}
.site-col{border-right:1px solid #2a2a2a;min-width:0}
.site-header{padding:0 3px;text-align:center;font-size:8.5px;font-weight:500;letter-spacing:.5px;border-bottom:1px solid #2a2a2a;background:#111;position:sticky;top:0;z-index:5;line-height:1.3;height:40px;min-height:40px;display:flex;align-items:center;justify-content:center}
.cards-wrap{padding:2px}
.card{display:block;text-decoration:none;color:inherit;background:#111;border-radius:2px;overflow:hidden;width:100%;margin-bottom:2px;position:relative}
.card:hover{background:#1a1a1a}
.card.hidden{display:none!important}
.ci{width:100%;aspect-ratio:1/1;overflow:hidden;background:#1a1a1a;position:relative}
.ci img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}
.card:hover .ci img{transform:scale(1.05)}
.nb{position:absolute;top:3px;right:3px;background:rgba(220,38,38,.85);color:#fff;font-size:7px;font-weight:700;padding:1px 4px;border-radius:1px;letter-spacing:.5px;z-index:2}
.sd{position:absolute;top:4px;left:4px;width:5px;height:5px;border-radius:50%}
.cb2{padding:3px 4px 4px}
.cn{font-size:8.5px;line-height:1.4;color:#bbb;margin-bottom:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.cf{display:flex;justify-content:space-between;align-items:center}
.cp{font-size:8.5px;font-weight:500;color:#f0ede8}
.db{font-size:7.5px;color:#555}
.empty{font-size:9px;color:#333;text-align:center;padding:10px 2px}
.notice{padding:12px 16px;font-size:10px;color:#555;line-height:1.8;border-top:1px solid #2a2a2a}
footer{padding:10px 16px;border-top:1px solid #2a2a2a;font-size:10px;color:#555;text-align:center;letter-spacing:1px}
</style>"""

JS = """<script>
var curDays=1;

function getCutoff(days){
  var d=new Date();
  d.setDate(d.getDate()-days);
  return parseInt(d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0'));
}

function applyFilter(){
  var cutoff=getCutoff(curDays);
  var total=0;
  document.querySelectorAll('.card[data-date]').forEach(function(c){
    var show=parseInt(c.dataset.date)>=cutoff;
    c.classList.toggle('hidden',!show);
    if(show)total++;
  });
  document.getElementById('cnt').textContent=total;
}

function filtDays(days){
  curDays=days;
  document.querySelectorAll('.dbtn').forEach(function(b){b.classList.remove('active')});
  document.querySelector('.dbtn[data-days="'+days+'"]').classList.add('active');
  applyFilter();
}

filtDays(1);
</script>"""


def card_html(item):
    oe = "this.style.display='none'"
    color = SITE_COLORS.get(item["source"], "#888")
    is_new = item.get("is_new", False)
    nb = '<span class="nb">NEW</span>' if is_new else ''
    return (
        f'<a class="card" data-date="{item["date"]}" href="{item["link"]}" target="_blank">'
        f'<div class="ci"><img src="{item["img"]}" onerror="{oe}">'
        f'{nb}<div class="sd" style="background:{color}"></div></div>'
        f'<div class="cb2"><p class="cn">{item["name"]}</p>'
        f'<div class="cf"><span class="cp">{item["price"]}</span>'
        f'<span class="db">{item["date_label"]}</span></div>'
        f'</div></a>'
    )


def build_html(items):
    # 사이트별 그룹핑 (최신순 정렬)
    site_map = {s: [] for s in SITE_ORDER}
    for item in items:
        s = item["source"]
        if s in site_map:
            site_map[s].append(item)
    for s in SITE_ORDER:
        site_map[s].sort(key=lambda x: int(x["date"]), reverse=True)

    # 사이트 컬럼 생성
    n = len(SITE_ORDER)
    cols_html = ""
    for s in SITE_ORDER:
        color = SITE_COLORS[s]
        label = SITE_LABELS[s]
        site_items = site_map[s]
        cards = "".join(card_html(i) for i in site_items)
        empty = '<div class="empty">-</div>' if not site_items else ""
        cols_html += (
            f'<div class="site-col">'
            f'<div class="site-header" style="color:{color}">{label}</div>'
            f'<div class="cards-wrap">{cards}{empty}</div>'
            f'</div>'
        )

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
  <div class="meta">업데이트: {NOW}<br>총 {len(items)}개</div>
</header>
<div class="filters">
  <span class="fl">DAYS</span>
  <button class="dbtn active" data-days="1" onclick="filtDays(1)">1일</button>
  <button class="dbtn" data-days="3" onclick="filtDays(3)">3일</button>
  <button class="dbtn" data-days="10" onclick="filtDays(10)">10일</button>
  <button class="dbtn" data-days="30" onclick="filtDays(30)">30일</button>
  <button class="dbtn" data-days="60" onclick="filtDays(60)">60일</button>
</div>
<div class="cbar">총 <span id="cnt">{len(items)}</span>개 표시 중</div>
<div class="grid-wrap">
  <div class="site-grid" style="grid-template-columns:repeat({n},minmax(0,1fr))">
    {cols_html}
  </div>
</div>
<div class="notice">
  ※ Blue Neon·Take Five·Babooshka·AIN.DAH.ING: 이미지 타임스탬프 기준<br>
  ※ Kerouac·S.T.C·SE7EN·KAPITAL 공홈: 최초 등장일 기준 (이후 고정)
</div>
<footer>KAPITAL TRACKER · GitHub Actions 6시간마다 자동 업데이트</footer>
{JS}
</body>
</html>"""


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    today_str = datetime.now(KST).strftime("%Y%m%d")

    # 날짜 캐시 + 이전 상품 목록 로드
    cache = load_date_cache()
    prev_items = load_prev_items()

    all_items = (scrape_blueneon() + scrape_takefive() + scrape_kerouac() + scrape_spacemoo() +
                 scrape_babooshka() + scrape_aindahing() + scrape_stc() +
                 scrape_se7en() + scrape_kapital_home())

    # 날짜 없는 사이트는 캐시에서 날짜 조회 (새 상품이면 오늘 날짜 기록)
    # 모든 상품에 대해 캐시 기반 날짜 고정
    # (한번 기록된 날짜는 절대 바뀌지 않음)
    for item in all_items:
        item_id = item["link"].rstrip("/").split("/")[-1].split("?")[-1]
        key = f"{item['source']}:{item_id}"
        if key not in cache:
            # 신규 상품: 현재 item의 date를 최초 날짜로 기록
            cache[key] = item["date"]
        else:
            # 기존 상품: 캐시의 날짜로 덮어쓰기 (날짜 불변 보장)
            item["date"] = cache[key]

        # date_label 통일
        dr = item["date"]
        if item["source"] in {"S.T.C", "SE7EN", "KAPITAL 공홈", "KEROUAC"}:
            item["date_label"] = f"{dr[2:4]}.{dr[4:6]}.{dr[6:8]} 신착"
        else:
            item["date_label"] = f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"

    # 캐시 저장
    save_date_cache(cache)

    # 상품 키 생성 및 NEW 마킹
    current_keys = set()
    for item in all_items:
        item_id = item["link"].rstrip("/").split("/")[-1].split("?")[-1]
        key = f"{item['source']}:{item_id}"
        current_keys.add(key)
        # 이전에 없던 상품이면 NEW 마킹
        item["is_new"] = (key not in prev_items) and bool(prev_items)

    # 현재 상품 목록 저장 (다음 실행 비교용)
    save_prev_items(current_keys)

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
