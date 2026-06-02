"""
구글 트렌드 수집기
pytrends 라이브러리로 한국 검색 트렌드 수집
키워드간 직접 비교 가능 (최고값=100 기준)
"""

from pytrends.request import TrendReq
from datetime import datetime
import pandas as pd

try:
    from collectors.base import with_retry, RetryableError, DEFAULT_RETRIES
except ImportError:
    from base import with_retry, RetryableError, DEFAULT_RETRIES

# pytrends 예외 메시지에서 재시도 여부를 판단하는 키워드
_RETRYABLE_KEYWORDS = ("429", "500", "502", "503", "504", "too many requests", "rate limit")


class GoogleTrendsCollector:

    def __init__(self):
        self.pytrends = TrendReq(hl="ko", tz=540)  # 한국어, KST

    def fetch_trend(
        self,
        keywords: list[str],
        timeframe: str = "today 12-m",  # 최근 1년
        geo: str = "KR",
    ) -> pd.DataFrame:
        """
        키워드 검색 트렌드 수집

        keywords: 최대 5개 (구글 트렌드 제한)
        timeframe: "today 12-m" / "today 3-m" / "2025-01-01 2026-01-01"
        """
        def _call():
            try:
                self.pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)
                return self.pytrends.interest_over_time()
            except Exception as e:
                # pytrends는 HTTP 오류를 자체 예외로 감싸므로 메시지로 재시도 여부 판단
                if any(kw in str(e).lower() for kw in _RETRYABLE_KEYWORDS):
                    raise RetryableError(str(e)) from e
                raise

        df = with_retry(_call, label="구글 트렌드")

        if df.empty:
            print("  ⚠️ 데이터 없음")
            return df

        # isPartial=True (진행 중인 주) 제거
        df = df[df["isPartial"] == False].drop(columns=["isPartial"])
        df.index.name = "period"
        df = df.reset_index()
        df["period"] = df["period"].astype(str)

        return df

    def fetch_archi_vs_competitors(self) -> pd.DataFrame:
        """아키클래식 vs 경쟁브랜드 비교 트렌드"""
        keywords = [
            "아키클래식",
            "버켄스탁",
            "크록스",
            "컴포트화",
        ]
        print(f"  ▶ 구글 트렌드 수집 중: {keywords}")
        df = self.fetch_trend(keywords)
        print(f"  ✅ {len(df)}주 데이터 수집 완료")
        return df

    def parse_to_rows(self, df: pd.DataFrame, collected_at: str = None) -> list[dict]:
        """
        DataFrame → DB insert용 행 리스트 변환

        반환 예시:
        [
            {"period": "2025-06-01", "keyword": "아키클래식", "ratio": 3, "collected_at": "..."},
            ...
        ]
        """
        if df.empty:
            return []

        if not collected_at:
            collected_at = datetime.now().isoformat()

        rows = []
        keyword_cols = [c for c in df.columns if c != "period"]
        for _, row in df.iterrows():
            for kw in keyword_cols:
                rows.append({
                    "period": row["period"],
                    "keyword": kw,
                    "ratio": int(row[kw]),
                    "collected_at": collected_at,
                })
        return rows


# ── 실행 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    import json

    collector = GoogleTrendsCollector()

    print("▶ 구글 트렌드 수집 시작")
    df = collector.fetch_archi_vs_competitors()

    print("\n[ DataFrame ]")
    print(df.to_string())

    print("\n[ DB 저장용 rows (앞 5개) ]")
    rows = collector.parse_to_rows(df)
    for row in rows[:5]:
        print(row)

    print(f"\n총 {len(rows)}개 row")
