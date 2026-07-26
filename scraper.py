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


def extract_item_code(source, link, name="", item=None):
    """사이트별 품번 추출"""
    import re as _re
    if source == "KAPITAL 공홈":
        m = _re.search(r'/item/([A-Z][A-Z0-9\-]+)\.html', link)
        return m.group(1) if m else None
    elif source == "S.T.C":
        m = _re.search(r'/item/([A-Z][A-Z0-9\-]+)/', link)
        return m.group(1) if m else None
    elif source == "SPACE MOO":
        m = _re.search(r'\(([A-Z]{2}-\d{4}[A-Z]{0,3})\)', name)
        return m.group(1) if m else None
    elif source == "KEROUAC":
        # item_code 필드에 미리 저장된 품번 사용, 없으면 link의 item_id로 폴백
        if hasattr(item, "get"):
            code = item.get("item_code")
            if code:
                return code
        m = _re.search(r'/view/item/(\d+)', link)
        return m.group(1) if m else None
    return None


def scrape_shop_pro_v2(source, color, img_prefix, base_url, cat_name=None):
    """shop-pro.jp 공통 스크래퍼 v2 - 원본 HTML 기준"""
    print(f"[{source}] scraping...")
    raw = fetch_raw(base_url)
    if not raw: return []
    try: html = raw.decode("euc-jp")
    except: html = raw.decode("utf-8", errors="replace")

    img_pat   = re.compile(
        r'https://img\d+\.shop-pro\.jp/' + img_prefix +
        r'/product/(\d+)_th\.(jpg|png)\?cmsp_timestamp=(\d{8})\d+'
    )
    name_pat  = re.compile(r'href="\?pid=\d+"[^>]*>(?:KAPITAL\s*[-/]\s*|\[KAPITAL\]\s*)?([^<]{4,100})</a>')
    price_pat = re.compile(r'([\d,]+)円')
    sold_pat  = re.compile(r'SOLD\s*OUT|完売|sold[-_]out', re.IGNORECASE)

    items, seen = [], set()
    for mi in img_pat.finditer(html):
        pid, ext, dr = mi.group(1), mi.group(2), mi.group(3)
        if pid in seen: continue
        seen.add(pid)
        seg = html[mi.start(): mi.start()+600]
        mn  = name_pat.search(seg)
        mp  = price_pat.search(seg)
        sold = bool(sold_pat.search(seg))
        name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
        items.append({
            "source": source, "color": color,
            "name": name,
            "price": f"¥{mp.group(1)}" if mp else "-",
            "img": f"https://img15.shop-pro.jp/{img_prefix}/product/{pid}_th.{ext}",
            "link": f"{base_url.split('?')[0]}?pid={pid}",
            "date": dr, "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}",
            "sold_out": sold,
        })
    print(f"  → {len(items)} items (품절 {sum(1 for i in items if i['sold_out'])}개)")
    return items




def scrape_blueneon():
    return scrape_shop_pro_v2(
        "BLUE NEON", "#5ecb8f", "PA01239/545",
        "https://blueneon.jp/?mode=grp&gid=613974&sort=n"
    )

def scrape_takefive():
    print("[Take Five] scraping...")
    # 가격 캐시 로드
    import json as _j
    try:
        with open("docs/tf_price_cache.json","r",encoding="utf-8") as _f:
            tf_price_cache = _j.load(_f)
    except:
        tf_price_cache = {}
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
            "name": name, "price": tf_price_cache.get(pid, "-"),
            "img": f"https://img09.shop-pro.jp/PA01043/640/product/{pid}_th.jpg",
            "link": f"https://takefive.jp/?pid={pid}",
            "date": dr, "date_label": f"{dr[:4]}.{dr[4:6]}.{dr[6:8]}"
        })

    # 가격 없는 상품 개별 fetch (최대 5개만, 나머지는 다음 실행에)
    missing = [i for i in items if i["price"] == "-"][:5]
    for item in missing:
        pid = item["link"].split("pid=")[-1]
        raw2 = fetch_raw(item["link"])
        if raw2:
            try: page = raw2.decode("euc-jp")
            except: page = raw2.decode("utf-8", errors="replace")
            mp = re.search(r'販売価格[^\d]*(\d[\d,]+)円', page)
            if not mp: mp = re.search(r'(\d[\d,]+)円', page)
            if mp:
                item["price"] = f"¥{mp.group(1)}"
                tf_price_cache[pid] = item["price"]
    # 캐시 저장
    import json as _j2
    import os as _os
    _os.makedirs("docs", exist_ok=True)
    with open("docs/tf_price_cache.json","w",encoding="utf-8") as _f:
        _j2.dump(tf_price_cache, _f, ensure_ascii=False)
    print(f"  → {len(items)} items")
    return items


def scrape_kerouac():
    print("[Kerouac] scraping...")
    # KEROUAC는 기본 헤더로 403 → 완전한 브라우저 헤더로 재시도
    kero_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8,ko;q=0.7",
        "Accept-Encoding": "identity",
        "Referer": "https://kerouac.okinawa/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    raw = b""
    try:
        req = urllib.request.Request("https://kerouac.okinawa/view/category/ct45", headers=kero_headers)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
    except Exception as e:
        print(f"  [WARN] 직접요청 실패: {e}")
        # 폴백: jina 프록시 경유
        try:
            preq = urllib.request.Request(
                "https://r.jina.ai/https://kerouac.okinawa/view/category/ct45",
                headers={"User-Agent": kero_headers["User-Agent"], "Accept": "application/json"})
            with urllib.request.urlopen(preq, timeout=30) as r:
                import json as _j
                jd = _j.loads(r.read().decode("utf-8", "ignore"))
                raw = jd.get("data", {}).get("content", "").encode("utf-8")
            if raw:
                print("  (jina 프록시 경유 성공)")
        except Exception as e2:
            print(f"  [WARN] 프록시도 실패: {e2}")
            return []
    if not raw: return []
    html = raw.decode("utf-8", errors="replace")

    item_pat = re.compile(
        r'href="/view/item/(\d+)\?category_page_id=ct45"[^>]*>.*?'
        r'<img\s+src="(https://makeshop-multi-images\.akamaized\.net/kerouac2021/itemimages/[^"]+)".*?'
        r'<p class="itemName">(.*?)</p>.*?'
        r'<p class="itemPrice">([\d,]+)円',
        re.DOTALL
    )

    items = []
    seen = set()
    for m in item_pat.finditer(html):
        item_id = m.group(1)
        if item_id in seen: continue
        seen.add(item_id)
        img  = m.group(2)
        name = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        # "KAPITAL(キャピタル) / 상품명 / 26SS" 형태에서 상품명만 추출
        name_clean = re.sub(r'KAPITAL\(キャピタル\)\s*/\s*', '', name)
        name_clean = re.sub(r'\s*/\s*26SS.*$', '', name_clean).strip()
        price = f"¥{m.group(4)}"
        link  = f"https://kerouac.okinawa/view/item/{item_id}?category_page_id=ct45"
        items.append({
            "source":"KEROUAC","color":"#4a9eff",
            "name": name_clean if name_clean else name,
            "price": price,
            "img": img,
            "link": link,
            "date": datetime.now(KST).strftime("%Y%m%d"),
            "date_label": "신착"
        })

    print(f"  → {len(items)} items")
    # 품번 캐시 로드
    import json as _jk, os as _osk
    try:
        with open("docs/kerouac_code_cache.json","r",encoding="utf-8") as _f:
            code_cache = _jk.load(_f)
    except:
        code_cache = {}

    # 품번 없는 상품 최대 5개 개별 페이지 fetch
    missing = [it for it in items if it["link"].split("/item/")[1].split("?")[0] not in code_cache][:5]
    for it in missing:
        pid = it["link"].split("/item/")[1].split("?")[0]
        raw2 = fetch_raw(it["link"])
        if raw2:
            page = raw2.decode("utf-8", errors="replace")
            m = re.search(r'品番[\s：:]+([A-Z][A-Z0-9\-]+)', page)
            code_cache[pid] = m.group(1) if m else ""
        else:
            code_cache[pid] = ""

    # 캐시에서 품번 적용
    for it in items:
        pid = it["link"].split("/item/")[1].split("?")[0]
        if code_cache.get(pid):
            it["item_code"] = code_cache[pid]

    # 캐시 저장
    _osk.makedirs("docs", exist_ok=True)
    with open("docs/kerouac_code_cache.json","w",encoding="utf-8") as _f:
        _jk.dump(code_cache, _f, ensure_ascii=False)

    return items


def scrape_spacemoo():
    print("[SPACE MOO] scraping...")
    # 카테고리 84 = KAPITAL, sort=2 = 신착순. 한 페이지에 전체(약 40개) 표시.
    url = "https://www.spacemoo.jp/products/category/84?sort=2"
    raw = fetch_raw(url)
    if not raw:
        print("  [WARN] 응답 없음 → 0 items")
        return []
    html = raw.decode("utf-8", errors="replace")
    today = datetime.now(KST).strftime("%Y%m%d")

    # 상품 블록(<dl>...</dl>) 단위로 분리 후 각각 파싱
    items = []
    seen = set()
    # 각 상품 dl 블록 추출
    for block in re.split(r'<!--▼商品-->', html)[1:]:
        block = block.split('<!--▲商品-->')[0]
        pid_m = re.search(r'/products/details/(\d+)', block)
        if not pid_m:
            continue
        pid = pid_m.group(1)
        if pid in seen:
            continue
        seen.add(pid)
        img_m = re.search(r'<img src="(/upload/save_image/[^"]+)"', block)
        name_m = re.search(r'<dd class="name"><a [^>]*>(.*?)</a>', block, re.DOTALL)
        price_m = re.search(r'id="price02_default_\d+">\s*¥\s*([\d,]+)', block)
        if not name_m:
            continue
        sold = "SOLD OUT" in block
        items.append({
            "source": "SPACE MOO", "color": "#c084fc",
            "name": name_m.group(1).strip(),
            "price": f"¥{price_m.group(1)}" if price_m else "-",
            "img": f"https://www.spacemoo.jp{img_m.group(1)}" if img_m else "",
            "link": f"https://www.spacemoo.jp/products/details/{pid}",
            "date": today,
            "date_label": "신착",
            "sold_out": sold,
        })
    sold_cnt = sum(1 for it in items if it.get("sold_out"))
    print(f"  → {len(items)} items (품절 {sold_cnt}개)")
    return items

def scrape_babooshka():
    return scrape_shop_pro_v2(
        "BABOOSHKA", "#38bdf8", "PA01038/438",
        "https://bab-web.shop-pro.jp/?mode=cate&cbid=1739088&csid=1&sort=n"
    )

def scrape_aindahing():
    return scrape_shop_pro_v2(
        "AIN.DAH.ING", "#a78bfa", "PA01135/633",
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
    # 제한 없음
    print(f"  → {len(items)} items")
    return items


def scrape_chromehearts():
    """Chrome Hearts: 상품이 아니라 '카테고리 출현'을 추적한다.
    평소엔 없던 카테고리가 신상품과 함께 새로 생기므로,
    현재 카테고리 목록을 캐시와 비교해 새로 생긴 카테고리만 NEW로 반환한다."""
    print("[Chrome Hearts] scraping categories...")
    import json as _jc, os as _osc

    BASE = "https://www.chromehearts.com"
    today = datetime.now(KST).strftime("%Y%m%d")
    now_ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")  # 감지 시각(시:분)

    # 메인 페이지에서 메뉴(카테고리 목록) 긁기
    raw = fetch_raw(BASE + "/")
    if not raw:
        print("  [WARN] 메인 페이지 응답 없음 (차단 가능성) → 0 items")
        return []
    html = raw.decode("utf-8", errors="replace")

    # 카테고리 링크: class="b-dropdown-menu_item" 이고 href가 실제 경로(/...)
    cat_pat = re.compile(
        r'<a\s+href="(/[^"]+)"\s+id="([^"]+)"\s+class="b-dropdown-menu_item[^"]*"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    current = {}
    for m in cat_pat.finditer(html):
        href = m.group(1).strip()
        label = re.sub(r'<[^>]+>', '', m.group(3)).strip().replace('&amp;', '&')
        if href.startswith("/") and href not in current:
            current[href] = label
    print(f"  현재 카테고리 {len(current)}개: {', '.join(current.keys())}")

    # 카테고리 캐시 로드
    _osc.makedirs("docs", exist_ok=True)
    try:
        with open("docs/ch_categories.json", "r", encoding="utf-8") as _f:
            known = _jc.load(_f)
    except Exception:
        known = {}

    # 첫 실행(캐시 비어있음)이면 기준만 저장하고 NEW 없음 처리 → 메일 폭탄 방지
    first_run = not known

    items = []
    for href, label in current.items():
        if href not in known:
            known[href] = {"label": label, "first_seen": today, "seen_at": now_ts}
            if not first_run:
                # 진짜 새로 생긴 카테고리 → NEW (메인 로직 거치지 않게 직접 마킹)
                items.append({
                    "source": "CHROME HEARTS", "color": "#e2c97e",
                    "name": f"새 카테고리: {label}",
                    "price": "-",
                    "img": "",
                    "link": BASE + href,
                    "date": today,
                    "date_label": f"신규 카테고리 {now_ts.split(' ',1)[1][:5]}",
                    "is_new": True,
                    "_ch_category": True,
                })

    # 캐시 저장 (사라진 카테고리도 유지 → 다시 생겨도 중복 알림 안 함)
    with open("docs/ch_categories.json", "w", encoding="utf-8") as _f:
        _jc.dump(known, _f, ensure_ascii=False, indent=2)

    # ── 카테고리 안의 개별 신상품 감지 (메뉴는 안 변해도 상품만 추가되는 경우) ──
    # 각 카테고리 페이지를 긁어 상품 링크를 모으고, 처음 보는 상품을 NEW로.
    try:
        with open("docs/ch_products.json", "r", encoding="utf-8") as _f:
            seen_products = _jc.load(_f)
    except Exception:
        seen_products = {}
    products_first_run = not seen_products

    prod_pat = re.compile(r'href="(/[^"]*?\.html)"', re.I)
    img_pat = re.compile(r'<img[^>]+src="(https://[^"]+?)"', re.I)
    now_products = {}
    for href in list(current.keys()):
        praw = fetch_raw(BASE + href)
        if not praw:
            continue
        phtml = praw.decode("utf-8", errors="replace")
        for pm in prod_pat.finditer(phtml):
            plink = pm.group(1)
            # 상품 상세 페이지만 (general/magazine 등 제외)
            if any(x in plink for x in ["/general", "/magazine", "/store", "/customer", "/about", "/contact", "/faq"]):
                continue
            if plink not in now_products:
                # 근처에서 이미지/이름 추출 시도
                seg = phtml[pm.start():pm.start()+800]
                im = img_pat.search(seg)
                img = im.group(1) if im else ""
                nm = re.search(r'alt="([^"]{3,80})"', seg)
                pname = nm.group(1).strip() if nm else plink.split("/")[-1].replace(".html","").replace("-"," ")
                now_products[plink] = {"img": img, "name": pname, "cat": href}

    for plink, info in now_products.items():
        if plink not in seen_products:
            seen_products[plink] = {"date": today, "seen_at": now_ts}
            if not products_first_run:
                items.append({
                    "source": "CHROME HEARTS", "color": "#e2c97e",
                    "name": info["name"],
                    "price": "-",
                    "img": info.get("img", ""),
                    "link": BASE + plink,
                    "date": today,
                    "date_label": f"신상품 {now_ts.split(' ',1)[1][:5]}",
                    "is_new": True,
                    "_ch_category": True,
                })

    with open("docs/ch_products.json", "w", encoding="utf-8") as _f:
        _jc.dump(seen_products, _f, ensure_ascii=False, indent=2)

    if first_run:
        print(f"  첫 실행 → 카테고리 {len(current)}개 기준 저장, NEW 0개")
    elif products_first_run:
        print(f"  → 새 카테고리 {len([i for i in items])}개 / 상품 기준 첫 저장 {len(now_products)}개")
    else:
        print(f"  → NEW {len(items)}개 (새 카테고리+신상품)")
    return items


def scrape_selenium_sites():
    """SE7EN + KAPITAL 공홈을 하나의 Selenium 드라이버로 처리"""
    import time
    results = {"SE7EN": [], "KAPITAL 공홈": []}

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36")

        driver = webdriver.Chrome(options=opts)

        # ── SE7EN ──────────────────────────────────
        print("[SE7EN] scraping with selenium...")
        try:
            driver.get("https://se7en.jp/products/list?category_id=32&orderby=3&pageno=1&disp_number=20")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ec-shelfGrid__item"))
                )
            except: pass
            time.sleep(2)

            html = driver.page_source

            # SE7EN 파싱
            items_se7 = []
            seen_se7 = set()
            links = re.findall(r'href="(https://se7en\.jp/products/detail/(\d+))"', html)
            for link, pid in links:
                if pid in seen_se7: continue
                seen_se7.add(pid)
                idx = html.find(f'detail/{pid}')
                seg = html[max(0, idx-200): idx+800]
                mi = re.search(r'src="(/html/upload/save_image/[^"]+)"', seg)
                if not mi: mi = re.search(r'src="(https://se7en\.jp/[^"]+\.(?:jpg|png|webp))"', seg)
                img_raw = (mi.group(1) if mi else "")
                img = f"https://se7en.jp{img_raw}" if img_raw.startswith("/") else img_raw
                mn = re.search(r'ec-shelfGrid__item-name[^>]*>\s*([^<]{2,80})', seg)
                mp = re.search(r'([\d,]+)円', seg)
                price = f"¥{mp.group(1)}" if mp else "-"
                name = unescape(mn.group(1)).strip() if mn else f"상품 {pid}"
                sold = bool(re.search(r'完売|Sold\s*[Oo]ut|sold-out', seg, re.IGNORECASE))
                items_se7.append({
                    "source":"SE7EN","color":"#fb923c",
                    "name": name, "price": price,
                    "img": img, "link": link,
                    "date": datetime.now(KST).strftime("%Y%m%d"),
                    "date_label": "신착",
                    "sold_out": sold,
                })
                if len(items_se7) >= 30: break

            results["SE7EN"] = items_se7
            print(f"  → {len(items_se7)} items")

        except Exception as e:
            print(f"  [WARN] SE7EN 실패: {e}")

        # ── KAPITAL 공홈 ───────────────────────────
        print("[Kapital Home] scraping with selenium...")
        try:
            driver.get("https://www.kapital-webshop.jp/item_list.html?sort=3&dispno=60")
            try:
                WebDriverWait(driver, 12).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li"))
                )
            except: pass
            time.sleep(2)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
            except: pass

            html = driver.page_source

            price_pat = re.compile(r'(\d[\d,]+)円')
            block_pat = re.compile(r'<li[^>]*class="item_list_box"[^>]*>(.*?)</li>', re.DOTALL)
            blocks = list(block_pat.finditer(html))



            items_kap = []
            seen_kap = set()
            for block in blocks:
                b = block.group(1)
                mi_code = re.search(r'/client_info/KAPITAL/itemimage/([A-Z][A-Z0-9]+)/', b)
                if not mi_code: continue
                item_code = mi_code.group(1)
                if item_code in seen_kap: continue
                seen_kap.add(item_code)
                link = f"https://www.kapital-webshop.jp/item/{item_code}.html"
                mi = re.search(r'data-original="(/client_info/KAPITAL/itemimage/[^"]+\.jpg)"', b)
                if not mi: mi = re.search(r'src="(/client_info/KAPITAL/[^"]+\.jpg)"', b)
                img_raw = mi.group(1) if mi else ""
                img = f"https://www.kapital-webshop.jp{img_raw}" if img_raw else ""
                mn = re.search(r'alt="([^"]{4,80})"', b)
                name = unescape(mn.group(1)).strip() if mn else item_code
                mp = price_pat.search(b)
                if not mp:
                    after = html[block.end(): block.end()+1000]
                    mp = price_pat.search(after)
                if not mp:
                    idx_code = html.find(item_code)
                    if idx_code > 0:
                        surrounding = html[idx_code: idx_code+2000]
                        mp = price_pat.search(surrounding)
                price = f"¥{mp.group(1)}" if mp else "-"
                sold = False
                items_kap.append({
                    "source":"KAPITAL 공홈","color":"#ff6b6b",
                    "name": name, "price": price,
                    "img": img, "link": link,
                    "date": datetime.now(KST).strftime("%Y%m%d"),
                    "date_label": "신착",
                    "sold_out": sold,
                })
            results["KAPITAL 공홈"] = items_kap
            print(f"  → {len(items_kap)} items")

        except Exception as e:
            print(f"  [WARN] Kapital Home 실패: {e}")

        driver.quit()

    except Exception as e:
        print(f"  [WARN] Selenium 초기화 실패: {e}")

    return results["SE7EN"], results["KAPITAL 공홈"]


def scrape_reddit_drops():
    """r/ChromeHeart에서 'online drop' 관련 글 감시.
    레딧이 서버 IP를 차단하므로 rss2json 서비스를 경유해 JSON으로 받아온다.
    (rss2json 서버가 레딧을 대신 읽어줌 → GitHub 서버 차단 우회)"""
    import json as _j, html as htmlmod, urllib.parse
    print("[Reddit CH Drops] scraping via rss2json...")
    queries = ["online drop", "drop online"]  # r/ChromeHeart 내 검색 (restrict_sr=1)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    all_raw = []
    seen_guid = set()
    for q in queries:
        rss = ("https://www.reddit.com/r/ChromeHeart/search.rss?q="
               + urllib.parse.quote(q) + "&restrict_sr=1&sort=new")
        api = "https://api.rss2json.com/v1/api.json?rss_url=" + urllib.parse.quote(rss, safe="")
        got = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(api, headers={"User-Agent": ua})
                with urllib.request.urlopen(req, timeout=25) as r:
                    got = _j.loads(r.read().decode("utf-8", "ignore"))
                if got.get("status") == "ok" and got.get("items") is not None:
                    break
                got = None
            except Exception:
                got = None
        if not got:
            continue
        for it in got.get("items", []):
            g = it.get("guid", it.get("link", ""))
            if g in seen_guid:
                continue
            seen_guid.add(g)
            all_raw.append(it)
    if not all_raw:
        print("  [WARN] rss2json 실패")
        return []

    today = datetime.now(KST).strftime("%Y%m%d")
    items = []
    for it in all_raw:
        title = htmlmod.unescape(it.get("title", "").strip())
        tl = title.lower()
        # 느슨한 필터: 제목에 online과 drop 둘 다
        if not ("online" in tl and "drop" in tl):
            continue
        permalink = it.get("link", "")
        pid = it.get("guid", permalink)
        content = it.get("content", "") + " " + it.get("description", "")
        img = it.get("thumbnail", "") or ""
        if not img:
            mi = re.search(r'<img[^>]+src="([^"]+)"', content)
            if mi:
                img = htmlmod.unescape(mi.group(1))
        ch_link = ""
        mch = re.search(r'https?://(?:www\.)?chromehearts\.com/[^\s\)\]"<]+', content)
        if mch:
            ch_link = mch.group(0)
        items.append({
            "source": "CH DROP", "color": "#ffffff",
            "name": title,
            "price": "",
            "img": img,
            "link": ch_link or permalink,
            "reddit_url": permalink,
            "ch_link": ch_link,
            "date": today,
            "date_label": "🔥 DROP",
            "_reddit_id": pid,
        })
    print(f"  → {len(items)}건 (online drop 관련)")
    return items


SITE_ORDER = [
    "KAPITAL 공홈","KEROUAC","TAKE FIVE","BLUE NEON",
    "BABOOSHKA","AIN.DAH.ING","S.T.C","SE7EN","SPACE MOO","CHROME HEARTS","CH DROP",
]
SITE_COLORS = {
    "CH DROP":"#ffffff",
    "KAPITAL 공홈":"#ff6b6b","KEROUAC":"#4a9eff","TAKE FIVE":"#f5c842",
    "BLUE NEON":"#5ecb8f","BABOOSHKA":"#38bdf8","AIN.DAH.ING":"#a78bfa",
    "S.T.C":"#34d399","SE7EN":"#fb923c","SPACE MOO":"#c084fc",
    "CHROME HEARTS":"#e2c97e",
}
SITE_LABELS = {
    "CH DROP":"CH<br>DROP🔥",
    "KAPITAL 공홈":"KAPITAL<br>공홈","KEROUAC":"KEROUAC","TAKE FIVE":"TAKE<br>FIVE",
    "BLUE NEON":"BLUE<br>NEON","BABOOSHKA":"BABOOSHKA","AIN.DAH.ING":"AIN.DAH<br>.ING",
    "S.T.C":"S.T.C","SE7EN":"SE7EN","SPACE MOO":"SPACE<br>MOO",
    "CHROME HEARTS":"CHROME<br>HEARTS",
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
.site-grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);border-left:1px solid #2a2a2a;min-width:0;align-items:start}
.site-col{border-right:1px solid #2a2a2a;min-width:0}
.site-header{padding:0 3px;text-align:center;font-size:8.5px;font-weight:500;letter-spacing:.5px;border-bottom:1px solid #2a2a2a;background:#111;position:sticky;top:0;z-index:5;line-height:1.3;height:44px;min-height:44px;max-height:44px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.cards-wrap{padding:2px}
.card{display:block;text-decoration:none;color:inherit;background:#111;border-radius:2px;overflow:hidden;width:100%;margin-bottom:2px;position:relative}
.card:hover{background:#1a1a1a}
.card.hidden{display:none!important}
.sold{position:relative}
.sold .ci{opacity:.45}
.sold-badge{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.7);color:#ff4444;font-size:8px;font-weight:700;padding:2px 6px;border-radius:2px;letter-spacing:1px;white-space:nowrap;z-index:3}
.ci{width:100%;aspect-ratio:1/1;overflow:hidden;background:#1a1a1a;position:relative}
.ci img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}
.card:hover .ci img{transform:scale(1.05)}
.nb{position:absolute;top:3px;right:3px;background:rgba(220,38,38,.85);color:#fff;font-size:7px;font-weight:700;padding:1px 4px;border-radius:1px;letter-spacing:.5px;z-index:2}
.sd{position:absolute;top:4px;left:4px;width:5px;height:5px;border-radius:50%}
.cb2{padding:4px 5px 4px;height:62px;min-height:62px;max-height:62px;display:flex;flex-direction:column;overflow:hidden}
.cn{font-size:8px;line-height:1.35;color:#bbb;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;flex:1;word-break:break-all;margin:0}
.cf{display:flex;justify-content:space-between;align-items:center;flex-shrink:0;padding-top:2px}
.cp{font-size:8.5px;font-weight:500;color:#f0ede8}
.db{font-size:7.5px;color:#555}
.kb{display:block;font-size:8px;color:#e2c97e;padding:2px 4px;border-top:1px solid #222;text-decoration:none;letter-spacing:.3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb:hover{background:#1a1a1a;color:#f5d87a}
.empty{font-size:9px;color:#333;text-align:center;padding:10px 2px}
.notice{padding:12px 16px;font-size:10px;color:#555;line-height:1.8;border-top:1px solid #2a2a2a}
footer{padding:10px 16px;border-top:1px solid #2a2a2a;font-size:10px;color:#555;text-align:center;letter-spacing:1px}
</style>"""

JS = """<script>
var total=document.querySelectorAll('.card[data-date]').length;
document.getElementById('cnt').textContent=total;
</script>"""


def card_html(item):
    import urllib.parse as _up
    oe = "this.style.display='none'"
    color = SITE_COLORS.get(item["source"], "#888")
    is_new  = item.get("is_new", False)
    is_sold = item.get("sold_out", False)
    nb   = '<span class="nb">NEW</span>' if is_new else ''
    sold = '<span class="sold-badge">SOLD OUT</span>' if is_sold else ''
    sold_cls = ' sold' if is_sold else ''

    # CH DROP(레딧 발매글) 전용 카드: 가격 없음, 공홈+레딧 링크
    if item["source"] == "CH DROP":
        ch_link = item.get("ch_link", "")
        reddit_url = item.get("reddit_url", item["link"])
        btns = f'<a class="kb" href="{reddit_url}" target="_blank" onclick="event.stopPropagation()">레딧 원문</a>'
        if ch_link:
            btns = (f'<a class="kb" href="{ch_link}" target="_blank" onclick="event.stopPropagation()" style="color:#fff">공홈 보기</a>'
                    + btns)
        main_link = ch_link or reddit_url
        return (
            f'<a class="card{sold_cls}" data-date="{item["date"]}" href="{main_link}" target="_blank">'
            f'<div class="ci"><img src="{item["img"]}" onerror="{oe}">'
            f'{nb}'
            f'<div class="sd" style="background:{color}"></div></div>'
            f'<div class="cb2"><p class="cn">{item["name"]}</p>'
            f'<div class="cf"><span class="db">{item.get("date_label","🔥 DROP")}</span></div>'
            + btns
            + f'</div></a>'
        )

    # 품번 추출 + 크림 버튼
    code = extract_item_code(item["source"], item["link"], item["name"], item=item)
    if code:
        kream_url = f"https://kream.co.kr/search?tab=products&keyword={_up.quote(code)}"
        kream_btn = f'<a class="kb" href="{kream_url}" target="_blank" onclick="event.stopPropagation()">{code}</a>'
    else:
        kream_btn = ''
    return (
        f'<a class="card{sold_cls}" data-date="{item["date"]}" href="{item["link"]}" target="_blank">'
        f'<div class="ci"><img src="{item["img"]}" onerror="{oe}">'
        f'{nb}{sold}'
        f'<div class="sd" style="background:{color}"></div></div>'
        f'<div class="cb2"><p class="cn">{item["name"]}</p>'
        f'<div class="cf"><span class="cp">{item["price"]}</span>'
        f'<span class="db">{item["date_label"]}</span></div>'
        + kream_btn
        + f'</div></a>'
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
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5,user-scalable=yes">
<title>KAPITAL NEW ARRIVALS TRACKER</title>
{CSS}
</head>
<body>
<header>
  <div class="logo">KAPITAL <span>NEW ARRIVALS TRACKER</span></div>
  <div class="meta">업데이트: {NOW}<br>총 {len(items)}개</div>
</header>
<div class="cbar">총 <span id="cnt">{len(items)}</span>개 표시 중 (최근 120일)</div>
<div class="grid-wrap">
  <div class="site-grid">
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
    # KEROUAC 깨진 공용 키 정리: 과거 모든 상품이 'category_page_id=ct45' 한 키를
    # 공유해 옛 날짜를 잘못 표시하던 버그. 제거하면 상품별 키로 오늘 날짜 재기록됨.
    if "KEROUAC:category_page_id=ct45" in cache:
        del cache["KEROUAC:category_page_id=ct45"]
        print("  [정리] 깨진 KEROUAC 캐시 키 제거")
    prev_items = load_prev_items()

    se7en_items, kapital_items = scrape_selenium_sites()
    all_items = (scrape_blueneon() + scrape_takefive() + scrape_kerouac() + scrape_spacemoo() +
                 scrape_babooshka() + scrape_aindahing() + scrape_stc() +
                 se7en_items + kapital_items + scrape_chromehearts())

    # ── 레딧 CH 드롭 감시 (rss2json 경유) ──
    import json as _json
    reddit_drops = scrape_reddit_drops()
    try:
        with open("docs/reddit_seen.json", "r", encoding="utf-8") as f:
            reddit_seen = set(_json.load(f))
    except Exception:
        reddit_seen = set()
    reddit_first_build = (len(reddit_seen) == 0)
    for rd in reddit_drops:
        rid = rd.get("_reddit_id", "")
        # 처음 보는 글이면 NEW (단, 최초 구축 회차는 기준만 잡고 알림 안 함)
        rd["is_new"] = (rid not in reddit_seen) and (not reddit_first_build)
        rd["_ch_category"] = True  # date_cache 로직에서 제외시키기 위한 플래그 재사용
        reddit_seen.add(rid)
    # 레딧 본 글 목록 저장 (최근 200개만 유지)
    try:
        with open("docs/reddit_seen.json", "w", encoding="utf-8") as f:
            _json.dump(list(reddit_seen)[-200:], f, ensure_ascii=False)
    except Exception as e:
        print(f"  [WARN] reddit_seen 저장 실패: {e}")
    all_items = all_items + reddit_drops

    # 날짜 없는 사이트는 캐시에서 날짜 조회 (새 상품이면 오늘 날짜 기록)
    # 모든 상품에 대해 캐시 기반 날짜 고정
    # (한번 기록된 날짜는 절대 바뀌지 않음)
    def _item_key(item):
        """상품별 고유 키. KEROUAC는 link 끝이 ?category_page_id=ct45로 모두 같아
        item 번호(?앞)를 써야 충돌하지 않는다. 나머지는 기존 방식 유지."""
        link = item["link"]
        if item["source"] == "KEROUAC":
            mm = re.search(r'/view/item/(\d+)', link)
            iid = mm.group(1) if mm else link
        else:
            iid = link.rstrip("/").split("/")[-1].split("?")[-1].replace(".html","").replace(".htm","")
        return f"{item['source']}:{iid}"

    for item in all_items:
        if item.get("_ch_category"):
            continue  # 카테고리 item은 date_cache 대상 아님
        key = _item_key(item)
        if key not in cache:
            # 신규 상품: 현재 item의 date를 최초 날짜로 기록 + 첫 등장 표시
            cache[key] = item["date"]
            item["_first_seen"] = True   # date_cache에 처음 기록 = 진짜 신규
        else:
            # 기존 상품: 캐시의 날짜로 덮어쓰기 (날짜 불변 보장)
            item["date"] = cache[key]
            item["_first_seen"] = False

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
    new_items = []
    # KEROUAC 키 방식이 바뀐 첫 회차 감지: prev_items에 새 방식 KEROUAC 키(KEROUAC:숫자)가
    # 하나도 없으면, 이번엔 KEROUAC를 NEW에서 제외하고 기준만 갱신(메일 폭탄 방지).
    kero_new_scheme_in_prev = any(
        k.startswith("KEROUAC:") and k.split(":",1)[1].isdigit() for k in prev_items
    )

    # 사이트별 prev 키 보유 여부 미리 계산.
    # 어떤 사이트가 이번엔 상품이 있는데 prev_items엔 그 사이트 키가 "하나도" 없으면,
    # 직전 회차에 그 사이트 크롤링이 실패(0개)했을 가능성 → 통짜 NEW 오발송 방지를 위해
    # 이번 회차는 그 사이트 NEW를 건너뛰고 기준만 갱신한다.
    from collections import Counter as _Counter
    prev_site_has = set()
    for k in prev_items:
        src = k.split(":", 1)[0]
        prev_site_has.add(src)
    this_site_count = _Counter(it["source"] for it in all_items if not it.get("_ch_category"))
    # prev에 이 사이트 키가 전혀 없고, 이번엔 여러 개 잡힌 사이트 = 복구 회차로 간주
    recovering_sites = set()
    for src, cnt in this_site_count.items():
        if cnt >= 3 and src not in prev_site_has and bool(prev_items):
            recovering_sites.add(src)
    if recovering_sites:
        print(f"  [복구감지] prev에 없던 사이트 {recovering_sites} → 이번 회차 NEW 제외, 기준만 갱신")

    for item in all_items:
        # 레딧 CH 드롭은 별도 캐시(reddit_seen)로 관리 → prev_items 키에서 제외
        if item.get("source") == "CH DROP":
            if item.get("is_new"):
                new_items.append({
                    "source": "CH DROP",
                    "name": item["name"],
                    "price": "",
                    "link": item.get("ch_link") or item.get("reddit_url", ""),
                    "img": item.get("img", ""),
                    "reddit_url": item.get("reddit_url", ""),
                    "ch_link": item.get("ch_link", ""),
                })
            continue
        key = _item_key(item)
        current_keys.add(key)
        # Chrome Hearts 카테고리 item은 자체 판정(is_new)을 그대로 사용
        if item.get("_ch_category"):
            pass  # is_new 이미 함수에서 결정됨
        elif item["source"] in recovering_sites:
            # 직전 크롤링 실패로 prev에 키가 없던 사이트 → 통짜 NEW 방지
            item["is_new"] = False
        else:
            # date_cache에 처음 기록된 상품만 NEW.
            # (prev_items 방식과 달리 페이지 경계가 흔들려도 가짜 NEW 안 생김.
            #  date_cache는 한번 본 상품을 영구 기록하므로 들락날락에 영향 안 받음)
            # 단, cache가 비어있던 최초 구축 회차는 전부 first_seen이 되므로 prev_items로 보호.
            item["is_new"] = bool(item.get("_first_seen")) and bool(prev_items)
        if item["is_new"]:
            new_items.append({
                "source": item["source"],
                "name": item["name"],
                "price": item.get("price", "-"),
                "link": item["link"],
                "img": item.get("img", ""),
            })

    # NEW 상품 목록 저장 (메일 발송용). 항상 덮어쓰기 → 없으면 빈 배열
    import json as _jn
    with open("docs/new_items.json", "w", encoding="utf-8") as _f:
        _jn.dump(new_items, _f, ensure_ascii=False, indent=2)
    print(f"  NEW 상품: {len(new_items)}개")

    # 크롤링 실패 보호: 이번에 0개인 사이트는 prev의 키를 그대로 살려서 저장.
    # (셀레니움 등 일시적 실패로 한 사이트가 0개가 돼도 기준선이 사라지지 않게 → 다음 회차 통짜 NEW 방지)
    this_sites = set(this_site_count.keys())
    for k in prev_items:
        src = k.split(":", 1)[0]
        if src not in this_sites and src != "CHROME HEARTS":
            current_keys.add(k)  # 이번에 안 잡힌 사이트의 이전 키 보존

    # 현재 상품 목록 저장 (다음 실행 비교용)
    save_prev_items(current_keys)

    # 최신순 정렬 (날짜 필터 없음 - 각 사이트 1페이지 전체)
    items = sorted(all_items, key=lambda x: int(x["date"]), reverse=True)
    # 사이트별 그룹핑 후 정렬
    from collections import defaultdict
    site_groups = defaultdict(list)
    for i in items:
        site_groups[i["source"]].append(i)
    items = []
    for src in site_groups:
        site_groups[src].sort(key=lambda x: int(x["date"]), reverse=True)
        items.extend(site_groups[src])
    items.sort(key=lambda x: int(x["date"]), reverse=True)

    print(f"  완료: {len(items)}개 (각 사이트 1페이지)")
    with open("docs/index.html","w",encoding="utf-8") as f:
        f.write(build_html(items))
    print(f"\n✅ 완료 ({len(items)}개)")
