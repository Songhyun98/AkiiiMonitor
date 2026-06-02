"""
네이버 쇼핑인사이트 수집기
카테고리 내 키워드별 클릭 트렌드 수집
※ 키워드/카테고리 코드는 여자친구랑 확정 후 수정 필요
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional

try:
    from collectors.base import with_retry, raise_for_status, DEFAULT_TIMEOUT
except ImportError:
    from base import with_retry, raise_for_status, DEFAULT_TIMEOUT


class NaverShoppingCollector:

    BASE_URL = "https://openapi.naver.com/v1/datalab/shopping"

    def __init__(self, client_id: str, client_secret: str):
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
            "Content-Type": "application/json",
        }

    def fetch_category_trend(
        self,
        categories: list[dict],
        start_date: str = None,
        end_date: str = None,
        time_unit: str = "month",
    ) -> dict:
        """
        카테고리별 트렌드 수집

        categories 예시:
        [
            {"name": "신발", "param": ["50000167"]},
        ]
        """
        if not end_date:
            end_date = datetime.today().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.today().replace(day=1) - timedelta(days=365)).strftime("%Y-%m-%d")

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": categories,
        }

        def _call():
            response = requests.post(
                f"{self.BASE_URL}/categories",
                headers=self.headers,
                data=json.dumps(body),
                timeout=DEFAULT_TIMEOUT,
            )
            raise_for_status(response, "쇼핑인사이트 카테고리 API")
            return response.json()

        return with_retry(_call, label="쇼핑 카테고리")

    def fetch_keyword_trend(
        self,
        category: str,
        keywords: list[dict],
        start_date: str = None,
        end_date: str = None,
        time_unit: str = "month",
        device: str = "",
        gender: str = "",
        ages: list = [],
    ) -> dict:
        """
        카테고리 내 키워드별 클릭 트렌드 수집

        category: 카테고리 코드 (예: "50000167")
        keywords 예시:
        [
            {"name": "아키클래식", "param": ["아키클래식"]},
            {"name": "버켄스탁", "param": ["버켄스탁"]},
        ]
        """
        if not end_date:
            end_date = datetime.today().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.today().replace(day=1) - timedelta(days=365)).strftime("%Y-%m-%d")

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": category,
            "keyword": keywords,
            "device": device,
            "gender": gender,
            "ages": ages,
        }

        def _call():
            response = requests.post(
                f"{self.BASE_URL}/category/keywords",
                headers=self.headers,
                data=json.dumps(body),
                timeout=DEFAULT_TIMEOUT,
            )
            raise_for_status(response, "쇼핑인사이트 키워드 API")
            return response.json()

        return with_retry(_call, label="쇼핑 키워드")

    def fetch_archi_shopping_trend(self) -> dict:
        """
        아키클래식 쇼핑 트렌드 수집
        ※ category, keywords 확정 후 수정 필요
        """
        # TODO: 여자친구랑 카테고리/키워드 확정 후 수정
        category = "50000167"  # 신발
        keywords = [
            {"name": "아키클래식", "param": ["아키클래식"]},
        ]
        return self.fetch_keyword_trend(category, keywords)

    def parse_to_rows(self, api_response: dict, collected_at: str = None) -> list[dict]:
        """
        API 응답 → DB insert용 행 리스트 변환
        """
        if not collected_at:
            collected_at = datetime.now().isoformat()

        rows = []
        for result in api_response.get("results", []):
            keyword_name = result["title"]
            for data_point in result["data"]:
                rows.append({
                    "period": data_point["period"],
                    "keyword": keyword_name,
                    "ratio": data_point["ratio"],
                    "collected_at": collected_at,
                })
        return rows


# ── 실행 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    import os

    collector = NaverShoppingCollector(
        client_id="여기에_Client_ID",
        client_secret="여기에_Client_Secret",
    )

    print("▶ 쇼핑인사이트 수집 중...")
    raw = collector.fetch_archi_shopping_trend()
    rows = collector.parse_to_rows(raw)

    print(f"✅ {len(rows)}개 데이터 포인트 수집 완료")
    for row in rows[:5]:
        print(row)
