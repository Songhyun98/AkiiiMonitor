# AkiiiMonitor — 아키클래식 브랜드 헬스 모니터링

> 공개 데이터(검색량·소셜 언급량·쇼핑 클릭)로 아키클래식의 컴포트화 시장 건강도를 자동 진단하는 데이터 파이프라인

---

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| **목적** | 아키클래식 브랜드의 시장 건강도를 공개 데이터로 주간 자동 진단 |
| **데이터 소스** | 네이버 DataLab, 네이버 검색 API, 네이버 쇼핑인사이트 |
| **수집 주기** | 매주 일요일 23:59 (KST) 자동 실행 |
| **저장소** | Supabase PostgreSQL |
| **역할** | 엔지니어(수집·적재) + 분석가(분석·시각화) |

---

## 아키텍처

```
[네이버 DataLab]     ──┐
[네이버 검색 API]    ──┤──→ collectors/ ──→ data/raw/ (parquet) ──→ Supabase DB
[네이버 쇼핑인사이트] ──┘

GitHub Actions (매주 일요일 23:59 KST)
└── db/storage.py (수집 → parquet 저장)
└── db/upload.py  (parquet → Supabase 적재)
```

---

## 폴더 구조

```
AkiiiMonitor/
├── collectors/
│   ├── base.py            # 공통 retry/timeout 유틸리티
│   ├── naver_datalab.py   # 검색어 트렌드 수집 (axis별)
│   ├── naver_search.py    # 블로그/뉴스/카페 언급량 수집
│   └── naver_shopping.py  # 쇼핑인사이트 수집 (성별×연령)
├── db/
│   ├── storage.py         # parquet 저장/로드
│   ├── upload.py          # Supabase 적재
│   ├── reader.py          # Supabase 읽기 (분석가용)
│   ├── schema.sql         # 테이블 생성 SQL
│   └── index.sql          # 인덱스 생성 SQL
├── .github/
│   └── workflows/
│       └── weekly_pipeline.yml  # GitHub Actions 자동화
├── data/
│   └── raw/               # 수집된 parquet 파일 (로컬 백업)
├── .env                   # API 키 (git 제외)
└── requirements.txt
```

---

## 데이터 소스 및 수집 전략

### 1. 네이버 DataLab (검색어 트렌드)
- **측정 대상**: 네이버 검색창 입력 횟수 (상대값 0~100)
- **기준**: 요청 내 전체 그룹 중 최고값 = 100
- **axis 설계**: 비교 목적에 따라 3개 요청으로 분리

| axis | 비교 대상 | 목적 |
|---|---|---|
| `direct` | 포즈간츠, 23.65 | 동급 브랜드 직접 비교 |
| `mass` | 스케쳐스, 휠라 | 대중 브랜드 대비 규모 |
| `market` | 컴포트수요지수, 여행시그널, 발건강시그널 | 시장 수요 트렌드 |

### 2. 네이버 검색 API (언급량)
- **측정 대상**: 블로그/뉴스/카페 총 문서 수 + 개별 문서
- **수집량**: 키워드당 최대 1000건 × 3개 소스
- **키워드**: `"아키클래식"`, `"포즈간츠"`, `"23.65"` (정확히 일치 검색)

### 3. 네이버 쇼핑인사이트
- **측정 대상**: 네이버쇼핑 클릭 트렌드 (상대값 0~100)
- **세분화**: 키워드 × 성별(m/f/all) × 연령(10s~60s+/all)
- **목적**: 키워드별 성별/연령 수요 분포 파악

---

## DB 스키마

### ERD

```
search_trend                    shopping_trend
─────────────────────           ──────────────────────────
period        DATE              period    DATE
keyword_group TEXT              keyword   TEXT
axis          TEXT              gender    TEXT
ratio         FLOAT             age       TEXT
                                ratio     FLOAT

mention_total                   mention_blog
─────────────────────           ──────────────────────────
collected_at  TIMESTAMPTZ       keyword      TEXT
collected_date DATE             title        TEXT
keyword       TEXT              description  TEXT
blog_total    INTEGER           bloggername  TEXT
news_total    INTEGER           postdate     TEXT
cafe_total    INTEGER           link         TEXT
                                collected_at TIMESTAMPTZ

mention_news                    mention_cafe
─────────────────────           ──────────────────────────
keyword       TEXT              keyword      TEXT
title         TEXT              title        TEXT
description   TEXT              description  TEXT
originallink  TEXT              cafename     TEXT
pub_date      TEXT              cafeurl      TEXT
link          TEXT              link         TEXT
collected_at  TIMESTAMPTZ       collected_at TIMESTAMPTZ
```

### 테이블별 적재 전략

| 테이블 | 전략 | 기준 키 | 이유 |
|---|---|---|---|
| `search_trend` | upsert | period + keyword_group + axis | 같은 주 데이터 덮어쓰기 |
| `shopping_trend` | upsert | period + keyword + gender + age | 같은 주 데이터 덮어쓰기 |
| `mention_total` | upsert | collected_date + keyword | 같은 날 중복 방지 |
| `mention_blog` | upsert | keyword + link | 같은 글 중복 방지 |
| `mention_news` | upsert | keyword + link | 같은 기사 중복 방지 |
| `mention_cafe` | upsert | keyword + link | 같은 글 중복 방지 |

### 인덱스 설계

카디널리티(값의 종류)가 높은 `period` 컬럼에만 인덱스를 설정했습니다. `keyword`, `axis`, `gender` 등 값의 종류가 적은 컬럼은 인덱스 효과가 없어 제외했습니다.

```sql
CREATE INDEX ON search_trend(period);
CREATE INDEX ON shopping_trend(period);
CREATE INDEX ON mention_total(collected_date);
CREATE INDEX ON mention_blog(postdate);
CREATE INDEX ON mention_news(pub_date);
```

---

## 시작하기

### 1. 환경 설정

```bash
pip install -r requirements.txt
```

`.env` 파일 생성:
```
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

### 2. Supabase 테이블 생성

Supabase SQL Editor에서 순서대로 실행:
```
db/schema.sql
db/index.sql
```

### 3. 수동 실행

```bash
python db/storage.py   # 수집 → parquet 저장
python db/upload.py    # parquet → Supabase 적재
```

### 4. 자동화

GitHub Secrets에 환경변수 4개 등록 후 push하면 매주 일요일 23:59(KST) 자동 실행.

---

## 분석가용 데이터 접근

```python
from db.reader import SupabaseReader
from dotenv import load_dotenv
import os

load_dotenv()
reader = SupabaseReader(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY"),
)

# 전체 읽기
df = reader.fetch_all("search_trend")

# 필터링
df_direct = reader.fetch_filtered("search_trend", {"axis": "direct"})
```

---

## 설계 결정 기록

| 결정 | 이유 |
|---|---|
| parquet 로컬 저장 후 Supabase 적재 | raw 백업 보존 + DB 부하 분리 |
| axis별 DataLab 요청 분리 | 비교 목적이 다르면 같은 스케일로 비교 불가 |
| 쇼핑인사이트 키워드별 단독 요청 | API param 1개 제한 + 세그먼트별 독립 100 기준 |
| mention 계열 개별 문서 수집 | 감성 분석 등 텍스트 분석 확장 가능성 |
| collected_at 제거 (search/shopping) | period가 기준 시점 역할 → 중복 컬럼 제거 |
| 인덱스를 period에만 설정 | keyword/axis 등 카디널리티 낮은 컬럼은 효과 없음 |