-- =============================================
-- 아키클래식 브랜드 헬스 DB 스키마
-- Supabase SQL Editor에서 실행
-- =============================================

-- 1. 검색어 트렌드 (네이버 DataLab)
CREATE TABLE IF NOT EXISTS search_trend (
    id             SERIAL PRIMARY KEY,
    period         DATE        NOT NULL,
    keyword_group  TEXT        NOT NULL,
    axis           TEXT        NOT NULL,  -- direct / mass / market
    ratio          FLOAT       NOT NULL,
    UNIQUE (period, keyword_group, axis)
);

-- 2. 언급량 스냅샷
CREATE TABLE IF NOT EXISTS mention_total (
    id           SERIAL PRIMARY KEY,
    collected_at TIMESTAMPTZ NOT NULL,
    keyword      TEXT        NOT NULL,
    blog_total   INTEGER     NOT NULL,
    news_total   INTEGER     NOT NULL,
    cafe_total   INTEGER     NOT NULL
);

-- 3. 블로그 개별 문서
CREATE TABLE IF NOT EXISTS mention_blog (
    id           SERIAL PRIMARY KEY,
    keyword      TEXT        NOT NULL,
    title        TEXT,
    description  TEXT,
    bloggername  TEXT,
    postdate     TEXT,
    link         TEXT,
    collected_at TIMESTAMPTZ NOT NULL
);

-- 4. 뉴스 개별 문서
CREATE TABLE IF NOT EXISTS mention_news (
    id            SERIAL PRIMARY KEY,
    keyword       TEXT        NOT NULL,
    title         TEXT,
    description   TEXT,
    originallink  TEXT,
    pub_date      TEXT,
    link          TEXT,
    collected_at  TIMESTAMPTZ NOT NULL
);

-- 5. 카페 개별 문서
CREATE TABLE IF NOT EXISTS mention_cafe (
    id           SERIAL PRIMARY KEY,
    keyword      TEXT        NOT NULL,
    title        TEXT,
    description  TEXT,
    cafename     TEXT,
    cafeurl      TEXT,
    link         TEXT,
    collected_at TIMESTAMPTZ NOT NULL
);

-- 6. 쇼핑인사이트
CREATE TABLE IF NOT EXISTS shopping_trend (
    id       SERIAL PRIMARY KEY,
    period   DATE        NOT NULL,
    keyword  TEXT        NOT NULL,
    gender   TEXT        NOT NULL,  -- m / f / all
    age      TEXT        NOT NULL,  -- 10s / 20s / ... / 60s+ / all
    ratio    FLOAT       NOT NULL,
    UNIQUE (period, keyword, gender, age)
);