"""
Supabase 업로드/다운로드 모듈
data/raw/ parquet → Supabase 테이블 적재
Supabase 테이블 → DataFrame (1000행 제한 우회)
"""

import pandas as pd
from supabase import create_client, Client


class SupabaseUploader:

    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    # ── 쓰기 ───────────────────────────────────────────────

    def _upsert(self, table: str, rows: list[dict], conflict_cols: str = None) -> None:
        if not rows:
            print(f"  ⚠️ [{table}] 빈 데이터 — 스킵")
            return
        if conflict_cols:
            self.client.table(table).upsert(rows, on_conflict=conflict_cols).execute()
        else:
            self.client.table(table).insert(rows).execute()
        print(f"  💾 [{table}] {len(rows)}행 적재 완료")

    def _to_rows(self, df: pd.DataFrame) -> list[dict]:
        """DataFrame → dict 리스트 변환 (NaN 제거)"""
        return df.where(pd.notnull(df), None).to_dict(orient="records")

    def upload_search_trend(self, df: pd.DataFrame) -> None:
        """search_trend — period + keyword_group + axis 기준 upsert"""
        df["period"] = pd.to_datetime(df["period"]).dt.strftime("%Y-%m-%d")
        df = df.drop(columns=["collected_at"], errors="ignore")
        self._upsert("search_trend", self._to_rows(df), "period,keyword_group,axis")

    def upload_mention_total(self, df: pd.DataFrame) -> None:
        """mention_total — 매주 스냅샷이라 insert"""
        self._upsert("mention_total", self._to_rows(df))

    def upload_mention_blog(self, df: pd.DataFrame) -> None:
        """mention_blog — insert"""
        self._upsert("mention_blog", self._to_rows(df))

    def upload_mention_news(self, df: pd.DataFrame) -> None:
        """mention_news — insert"""
        self._upsert("mention_news", self._to_rows(df))

    def upload_mention_cafe(self, df: pd.DataFrame) -> None:
        """mention_cafe — insert"""
        self._upsert("mention_cafe", self._to_rows(df))

    def upload_shopping_trend(self, df: pd.DataFrame) -> None:
        """shopping_trend — period + keyword + gender + age 기준 upsert"""
        df["period"] = pd.to_datetime(df["period"]).dt.strftime("%Y-%m-%d")
        df = df.drop(columns=["collected_at"], errors="ignore")
        self._upsert("shopping_trend", self._to_rows(df), "period,keyword,gender,age")

    # ── 읽기 (1000행 제한 우회) ────────────────────────────

    def fetch_all(self, table: str) -> pd.DataFrame:
        """
        Supabase 테이블 전체 읽기
        PostgREST 기본 1000행 제한을 .range()로 우회
        """
        rows = []
        start = 0
        page_size = 1000

        while True:
            response = (
                self.client.table(table)
                .select("*")
                .range(start, start + page_size - 1)
                .execute()
            )
            data = response.data
            rows.extend(data)

            if len(data) < page_size:
                break
            start += page_size

        print(f"  📂 [{table}] 총 {len(rows)}행 로드")
        return pd.DataFrame(rows)


# ── 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv()

    from db.storage import load_latest

    uploader = SupabaseUploader(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
    )

    print("▶ Supabase 업로드 시작")

    print("  search_trend...")
    uploader.upload_search_trend(load_latest("naver_datalab"))

    print("  mention_total...")
    uploader.upload_mention_total(load_latest("mention_total"))

    print("  mention_blog...")
    uploader.upload_mention_blog(load_latest("mention_blog"))

    print("  mention_news...")
    uploader.upload_mention_news(load_latest("mention_news"))

    print("  mention_cafe...")
    uploader.upload_mention_cafe(load_latest("mention_cafe"))

    print("  shopping_trend...")
    uploader.upload_shopping_trend(load_latest("naver_shopping"))

    print("\n✅ 전체 업로드 완료")

    # ── 읽기 테스트 ──────────────────────────────────────────
    print("\n▶ 읽기 테스트")
    for table in ["search_trend", "mention_total", "shopping_trend"]:
        df = uploader.fetch_all(table)
        print(f"  {table}: {len(df)}행")