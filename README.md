# KAPITAL New Arrivals Tracker

매일 07:00 KST에 자동으로 크롤링 → GitHub Pages에 배포됩니다.

## 세팅 방법 (5분)

### 1. GitHub 레포 만들기
1. https://github.com/new 에서 **Public** 레포 생성
2. 이름 예시: `kapital-tracker`

### 2. 파일 업로드
레포에 아래 파일들을 그대로 올리세요:
```
kapital-tracker/
├── scraper.py
├── .github/
│   └── workflows/
│       └── daily.yml
└── docs/
    └── index.html   ← 첫 실행 전엔 비어있어도 OK
```

### 3. GitHub Pages 활성화
레포 → **Settings** → **Pages**  
→ Source: `Deploy from a branch`  
→ Branch: `main` / folder: `/docs`  
→ **Save**

약 1분 후 `https://{유저명}.github.io/kapital-tracker/` 에서 확인 가능

### 4. 수동 실행 (첫 페이지 생성)
레포 → **Actions** → `KAPITAL Tracker - Daily Update` → **Run workflow**

### 5. 폰 알림 설정 (선택)
**방법 A: iOS 단축어**
- 단축어 앱 → 자동화 → 매일 07:05 → URL 열기 (위 GitHub Pages URL)

**방법 B: IFTTT 무료**
1. https://ifttt.com 가입
2. `If This` → Date & Time → Every day at 07:05 AM
3. `Then That` → Notifications → Send a notification
4. 메시지: "KAPITAL 신상 업데이트됨 🛍️"

---

## 자동 실행 시간
| 시간 | 내용 |
|------|------|
| 매일 07:00 KST | GitHub Actions 크롤링 시작 |
| 07:01~02 KST | GitHub Pages 자동 배포 완료 |

## 수동 실행
Actions 탭 → Run workflow 버튼으로 언제든 즉시 실행 가능

## 추가 쇼핑몰 추가하고 싶을 때
`scraper.py` 의 `KEROUAC_ITEMS` 또는 `SPACEMOO_ITEMS` 스타일로 추가하면 됩니다.
