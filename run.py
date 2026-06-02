"""
아키클래식 브랜드 헬스 파이프라인
GitHub Actions cron으로 매주 월요일 실행

실행: python -m archi_health.run
"""

import os
from collectors.naver_datalab import NaverDataLabCollector
from collectors.naver_search import NaverSearchCollector
from db.supabase_client import SupabaseDB
from analysis.brand_health import BrandHealthAnalyzer


def run():
    print("=" * 50)
    print("🏃 아키클래식 브랜드 헬스 파이프라인 시작")
    print("=" * 50)

    # ── 환경변수 로드 ──────────────────────────────────────────
    naver_id     = os.environ["NAVER_CLIENT_ID"]
    naver_secret = os.environ["NAVER_CLIENT_SECRET"]
    supa_url     = os.environ["SUPABASE_URL"]
    supa_key     = os.environ["SUPABASE_KEY"]

    # ── 클라이언트 초기화 ──────────────────────────────────────
    datalab   = NaverDataLabCollector(naver_id, naver_secret)
    search    = NaverSearchCollector(naver_id, naver_secret)
    db        = SupabaseDB(supa_url, supa_key)
    analyzer  = BrandHealthAnalyzer()

    # ── 1단계: 데이터 수집 ─────────────────────────────────────
    print("\n📡 1단계: 데이터 수집")

    print("  ▶ 검색량 트렌드 수집 중...")
    raw_trend    = datalab.fetch_archi_vs_market()
    trend_rows   = datalab.parse_to_rows(raw_trend)
    print(f"  ✅ {len(trend_rows)}개 검색량 포인트 수집")

    print("  ▶ 소셜 언급량 수집 중...")
    mention_rows = search.fetch_all_brand_mentions()

    # ── 2단계: DB 저장 ─────────────────────────────────────────
    print("\n💾 2단계: DB 저장")
    db.upsert_search_trend(trend_rows)
    db.insert_social_mention(mention_rows)

    # ── 3단계: 분석 ────────────────────────────────────────────
    print("\n🔬 3단계: 브랜드 건강도 분석")
    score_result = analyzer.analyze(trend_rows, mention_rows)
    db.insert_brand_score(score_result)

    # ── 4단계: 결과 출력 ───────────────────────────────────────
    print("\n📊 분석 결과")
    print(f"  검색 점수:  {score_result['search_score']} / 50")
    print(f"  언급 점수:  {score_result['mention_score']} / 50")
    print(f"  총합 점수:  {score_result['total_score']} / 100")
    print(f"\n  진단: {score_result['diagnosis']}")
    print(f"  처방: {score_result['prescription']}")

    print("\n✅ 파이프라인 완료")
    return score_result


if __name__ == "__main__":
    run()
