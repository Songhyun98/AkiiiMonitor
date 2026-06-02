"""
네이버 DataLab API - 검색어 트렌드 수집기
아키클래식 vs 컴포트화 시장 키워드 검색량 수집
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional

try:
    from collectors.base import with_retry, raise_for_status, DEFAULT_TIMEOUT
except ImportError:
    from base import with_retry, raise_for_status, DEFAULT_TIMEOUT


class NaverDataLabCollector:
    """네이버 DataLab 통합 검색어 트렌드 API"""

    BASE_URL = "https://openapi.naver.com/v1/datalab/search"

    def __init__(self, client_id: str, client_secret: str):
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
            "Content-Type": "application/json",
        }

    def fetch_trend(
        self,
        keyword_groups: list[dict],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_unit: str = "week",  # date / week / month
    ) -> dict:
        """
        검색어 트렌드 조회

        keyword_groups 예시:
        [
            {"groupName": "아키클래식", "keywords": ["아키클래식", "ARCHIES"]},
            {"groupName": "컴포트화", "keywords": ["컴포트화", "편한신발", "족저근막"]},
        ]
        """
        if not end_date:
            end_date = datetime.today().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }

        def _call():
            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                data=json.dumps(body),
                timeout=DEFAULT_TIMEOUT,
            )
            raise_for_status(response, "DataLab API")
            return response.json()

        return with_retry(_call, label="네이버 DataLab")

    def fetch_archi_vs_market(self) -> dict:
        """아키클래식 vs 컴포트화 시장 비교 트렌드"""
        keyword_groups = [
            {
                "groupName": "아키클래식",
                "keywords": ["아키클래식", "ARCHIES", "아키스"],
            },
            {
                "groupName": "컴포트화시장",
                "keywords": ["컴포트화", "편한신발", "족저근막염신발", "기능성슬리퍼"],
            },
            {
                "groupName": "경쟁브랜드",
                "keywords": ["버켄스탁", "크록스", "우르바노"],
            },
        ]
        return self.fetch_trend(keyword_groups)

    def parse_to_rows(self, api_response: dict, collected_at: Optional[str] = None) -> list[dict]:
        """
        API 응답 → DB insert용 행 리스트 변환

        반환 예시:
        [
            {"period": "2025-01-01", "keyword_group": "아키클래식", "ratio": 45.23, "collected_at": "..."},
            ...
        ]
        """
        if not collected_at:
            collected_at = datetime.now().isoformat()

        rows = []
        for result in api_response.get("results", []):
            group_name = result["title"]
            for data_point in result["data"]:
                rows.append({
                    "period": data_point["period"],
                    "keyword_group": group_name,
                    "ratio": data_point["ratio"],  # 0~100 상대 검색량
                    "collected_at": collected_at,
                })
        return rows


# ── 실행 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    import os

    collector = NaverDataLabCollector(
        client_id=os.getenv("NAVER_CLIENT_ID", "YOUR_CLIENT_ID"),
        client_secret=os.getenv("NAVER_CLIENT_SECRET", "YOUR_CLIENT_SECRET"),
    )

    print("▶ 아키클래식 vs 컴포트화 시장 검색 트렌드 수집 중...")
    raw = collector.fetch_archi_vs_market()
    rows = collector.parse_to_rows(raw)

    print(f"✅ {len(rows)}개 데이터 포인트 수집 완료")
    for row in rows[:5]:
        print(row)
