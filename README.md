# 아키클래식 브랜드 헬스 모니터링

> 공개 데이터(검색량·소셜 언급량)로 아키클래식의 컴포트화 시장 건강도를 자동 진단하는 파이프라인

---

## 구조

```
네이버 DataLab API (검색량)  ─┐
네이버 검색 API   (언급량)  ─┤→ Supabase DB → 건강도 분석 → 리포트
                              └─ GitHub Actions (매주 월요일 자동 실행)
```

## 파일 구조

```
archi_health/
├── collectors/
│   ├── naver_datalab.py   # 검색량 트렌드 수집 (엔지니어)
│   └── naver_search.py    # 블로그/뉴스 언급량 수집 (엔지니어)
├── db/
│   ├── supabase_client.py # DB 저장/조회 (엔지니어)
│   └── schema.sql         # 테이블 생성 SQL (같이 논의)
├── analysis/
│   └── brand_health.py    # 건강도 점수 산출 (분석가)
├── run.py                 # 전체 파이프라인 실행
└── .github/workflows/
    └── weekly_pipeline.yml  # 자동 실행 스케줄러
```

## 역할 분담

| 파일 | 담당 |
|---|---|
| collectors/ | 엔지니어 |
| db/supabase_client.py | 엔지니어 |
| db/schema.sql | 같이 설계 |
| analysis/brand_health.py | 분석가 |
| run.py | 같이 |

---

## 시작하기

### 1. 네이버 API 키 발급
1. https://developers.naver.com 접속
2. 애플리케이션 등록
3. **DataLab(검색어트렌드)** + **검색(블로그, 뉴스)** 권한 체크
4. Client ID / Client Secret 복사

### 2. Supabase 프로젝트 생성
1. https://supabase.com 에서 새 프로젝트 생성
2. SQL Editor에서 `db/schema.sql` 실행
3. Settings → API에서 URL / anon key 복사

### 3. GitHub Secrets 등록
```
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
SUPABASE_URL
SUPABASE_KEY
```

### 4. 로컬 테스트
```bash
pip install -r requirements.txt

export NAVER_CLIENT_ID=...
export NAVER_CLIENT_SECRET=...
export SUPABASE_URL=...
export SUPABASE_KEY=...

python run.py
```

### 5. 자동화 활성화
- GitHub에 push하면 매주 월요일 오전 10시(KST) 자동 실행
- Actions 탭에서 수동 실행도 가능

---

## 분석가가 데이터 보는 법

### Supabase 대시보드
- Table Editor에서 직접 조회
- SQL Editor로 커스텀 쿼리

### Python (Jupyter)
```python
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 최근 트렌드
df = pd.DataFrame(
    client.table("search_trend").select("*").order("period", desc=True).limit(50).execute().data
)

# 건강도 이력
scores = pd.DataFrame(
    client.table("brand_score").select("*").execute().data
)
```
