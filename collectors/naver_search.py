"""
네이버 검색 API - 블로그/뉴스 언급량 수집기
소셜 언급량 = 블로그 + 뉴스 검색 결과 수
"""

import requests
from datetime import datetime
from typing import Optional

try:
    from collectors.base import with_retry, raise_for_status, DEFAULT_TIMEOUT
except ImportError:
    from base import with_retry, raise_for_status, DEFAULT_TIMEOUT


class NaverSearchCollector:
    """네이버 블로그/뉴스 검색 API로 브랜드 언급량 측정"""

    BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"
    NEWS_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, client_id: str, client_secret: str):
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

    def _search(self, url: str, query: str, display: int = 1) -> dict:
        params = {
            "query": query,
            "display": display,
            "sort": "date",  # 최신순
        }

        def _call():
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=DEFAULT_TIMEOUT,
            )
            raise_for_status(response, "검색 API")
            return response.json()

        return with_retry(_call, label=f"검색({query})")

    def fetch_mention_count(self, keyword: str) -> dict:
        """
        키워드의 블로그/뉴스 총 언급 수 반환

        반환 예시:
        {
            "keyword": "아키클래식",
            "blog_total": 15230,
            "news_total": 312,
            "collected_at": "2025-06-01T10:00:00"
        }
        """
        blog_data = self._search(self.BLOG_URL, keyword)
        news_data = self._search(self.NEWS_URL, keyword)

        return {
            "keyword": keyword,
            "blog_total": blog_data.get("total", 0),
            "news_total": news_data.get("total", 0),
            "collected_at": datetime.now().isoformat(),
        }

    def fetch_all_brand_mentions(self) -> list[dict]:
        """아키클래식 + 경쟁 브랜드 언급량 일괄 수집"""
        keywords = [
            "아키클래식",
            "버켄스탁",
            "크록스",
            "컴포트화",
        ]
        results = []
        for kw in keywords:
            try:
                data = self.fetch_mention_count(kw)
                results.append(data)
                print(f"  ✅ '{kw}' 수집 완료: 블로그 {data['blog_total']:,}건, 뉴스 {data['news_total']:,}건")
            except Exception as e:
                # 재시도 후에도 실패한 키워드는 건너뛰고 나머지 수집 계속
                print(f"  ❌ '{kw}' 수집 실패 (재시도 소진): {e}")
        return results


# ── 실행 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    import os

    collector = NaverSearchCollector(
        client_id=os.getenv("NAVER_CLIENT_ID", "YOUR_CLIENT_ID"),
        client_secret=os.getenv("NAVER_CLIENT_SECRET", "YOUR_CLIENT_SECRET"),
    )

    print("▶ 브랜드 언급량 수집 중...")
    results = collector.fetch_all_brand_mentions()
    print(f"\n총 {len(results)}개 키워드 수집 완료")
