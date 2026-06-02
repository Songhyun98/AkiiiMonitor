-- =============================================
-- 아키클래식 브랜드 헬스 DB 스키마
-- Supabase SQL Editor에서 실행
-- =============================================

-- 1. 검색량 트렌드 (DataLab API)
CREATE TABLE IF NOT EXISTS search_trend (
    id            SERIAL PRIMARY KEY,
    period        DATE        NOT NULL,          -- 주 시작일
    keyword_group TEXT        NOT NULL,          -- 아키클래식 / 컴포트화시장 / 경쟁브랜드
    ratio         FLOAT       NOT NULL,          -- 0~100 상대 검색량
    collected_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (period, keyword_group)               -- 중복 방지
);

-- 2. 소셜 언급량 (네이버 검색 API)
CREATE TABLE IF NOT EXISTS social_mention (
    id           SERIAL PRIMARY KEY,
    keyword      TEXT        NOT NULL,           -- 아키클래식 / 버켄스탁 / 크록스 등
    blog_total   INTEGER     NOT NULL,           -- 블로그 총 문서 수
    news_total   INTEGER     NOT NULL,           -- 뉴스 총 문서 수
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 브랜드 건강도 점수 (분석 결과)
CREATE TABLE IF NOT EXISTS brand_score (
    id             SERIAL PRIMARY KEY,
    week_start     DATE        NOT NULL,         -- 해당 주 시작일
    search_score   FLOAT,                        -- 검색 점수 (0~50)
    mention_score  FLOAT,                        -- 언급 점수 (0~50)
    total_score    FLOAT,                        -- 합계 (0~100)
    diagnosis      TEXT,                         -- 진단 텍스트
    prescription   TEXT,                         -- 처방 텍스트
    calculated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- 분석가용 조회 뷰
-- =============================================

-- 최근 12주 트렌드 비교
CREATE OR REPLACE VIEW v_recent_trend AS
SELECT
    period,
    keyword_group,
    ratio,
    ROUND(
        ratio - LAG(ratio) OVER (
            PARTITION BY keyword_group ORDER BY period
        ), 2
    ) AS ratio_change    -- 전주 대비 변화량
FROM search_trend
ORDER BY period DESC, keyword_group;

-- 브랜드 건강도 이력
CREATE OR REPLACE VIEW v_brand_health_history AS
SELECT
    week_start,
    total_score,
    search_score,
    mention_score,
    diagnosis,
    prescription
FROM brand_score
ORDER BY week_start DESC;
