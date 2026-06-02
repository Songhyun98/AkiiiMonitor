"""
브랜드 건강도 분석 모듈
수집된 데이터로 아키클래식의 시장 건강도 점수 산출
"""

import pandas as pd
from datetime import datetime


class BrandHealthAnalyzer:
    """
    브랜드 건강도 = 검색량 트렌드 점수 + 언급량 점수
    각 50점 만점 → 총 100점
    """

    def analyze(
        self,
        trend_rows: list[dict],
        mention_rows: list[dict],
    ) -> dict:
        """
        수집 데이터 → 건강도 점수 + 진단 + 처방 반환
        """
        search_score, search_detail = self._score_search_trend(trend_rows)
        mention_score, mention_detail = self._score_mention(mention_rows)
        total_score = round(search_score + mention_score, 1)

        diagnosis, prescription = self._diagnose(total_score, search_detail, mention_detail)

        return {
            "week_start": datetime.now().strftime("%Y-%m-%d"),
            "search_score": search_score,
            "mention_score": mention_score,
            "total_score": total_score,
            "search_detail": search_detail,
            "mention_detail": mention_detail,
            "diagnosis": diagnosis,
            "prescription": prescription,
            "calculated_at": datetime.now().isoformat(),
        }

    def _score_search_trend(self, rows: list[dict]) -> tuple[float, dict]:
        """
        검색량 점수 (50점 만점)
        - 아키클래식 최근 4주 평균 ratio
        - 전분기 대비 증감률
        - 시장 대비 점유율
        """
        if not rows:
            return 0.0, {}

        df = pd.DataFrame(rows)
        df["period"] = pd.to_datetime(df["period"])
        df = df.sort_values("period")

        archi = df[df["keyword_group"] == "아키클래식"]
        market = df[df["keyword_group"] == "컴포트화시장"]

        if archi.empty:
            return 0.0, {"error": "아키클래식 데이터 없음"}

        # 최근 4주 평균
        recent_avg = archi.tail(4)["ratio"].mean()

        # 전분기 대비 증감률
        if len(archi) >= 8:
            prev_avg = archi.iloc[-8:-4]["ratio"].mean()
            growth_rate = (recent_avg - prev_avg) / prev_avg * 100 if prev_avg else 0
        else:
            growth_rate = 0

        # 시장 점유율 (아키 / 시장 비율)
        market_avg = market.tail(4)["ratio"].mean() if not market.empty else 100
        market_share = (recent_avg / market_avg * 100) if market_avg else 0

        # 점수 계산 (각 요소별 배점)
        trend_score = min(recent_avg * 0.3, 20)          # 최대 20점
        growth_score = min(max(growth_rate * 0.2, -10), 15)  # -10 ~ 15점
        share_score = min(market_share * 0.15, 15)        # 최대 15점

        total = round(trend_score + growth_score + share_score, 1)
        total = max(0, min(50, total))  # 0~50 범위 보정

        detail = {
            "recent_avg_ratio": round(recent_avg, 2),
            "growth_rate_pct": round(growth_rate, 1),
            "market_share_pct": round(market_share, 1),
            "score": total,
        }
        return total, detail

    def _score_mention(self, rows: list[dict]) -> tuple[float, dict]:
        """
        언급량 점수 (50점 만점)
        - 블로그 언급량 절대값
        - 경쟁사 대비 비율
        """
        if not rows:
            return 0.0, {}

        df = pd.DataFrame(rows)
        archi_row = df[df["keyword"] == "아키클래식"]

        if archi_row.empty:
            return 0.0, {"error": "아키클래식 언급 데이터 없음"}

        archi_blog = int(archi_row["blog_total"].values[0])
        archi_news = int(archi_row["news_total"].values[0])

        # 경쟁사 대비 블로그 점유율
        total_blog = df["blog_total"].sum()
        blog_share = (archi_blog / total_blog * 100) if total_blog else 0

        # 점수 계산
        blog_score = min(blog_share * 0.4, 30)   # 최대 30점
        news_score = min(archi_news / 100, 20)    # 최대 20점

        total = round(blog_score + news_score, 1)
        total = max(0, min(50, total))

        detail = {
            "blog_total": archi_blog,
            "news_total": archi_news,
            "blog_share_pct": round(blog_share, 1),
            "score": total,
        }
        return total, detail

    def _diagnose(self, total_score: float, search: dict, mention: dict) -> tuple[str, str]:
        """점수 기반 진단 + 처방 텍스트 생성"""

        growth = search.get("growth_rate_pct", 0)
        share = search.get("market_share_pct", 0)
        blog_share = mention.get("blog_share_pct", 0)

        # 진단
        if total_score >= 75:
            diagnosis = f"✅ 브랜드 건강 우수 (점수 {total_score}). 검색 관심과 소셜 존재감 모두 양호."
        elif total_score >= 55:
            if growth > 0:
                diagnosis = f"📈 성장 중 (점수 {total_score}). 검색량 전분기 대비 +{growth:.1f}%, 상승 모멘텀 확인됨."
            else:
                diagnosis = f"⚠️ 관심 둔화 (점수 {total_score}). 검색량 전분기 대비 {growth:.1f}%, 개입 필요."
        else:
            diagnosis = f"🚨 브랜드 관심 저조 (점수 {total_score}). 검색량·언급량 모두 낮음. 즉각 대응 필요."

        # 처방
        prescriptions = []
        if growth < -10:
            prescriptions.append("검색량 급감: 시즌 마케팅 또는 프로모션 집행 검토")
        if share < 20:
            prescriptions.append(f"시장 내 점유율 {share:.1f}%로 낮음: 핵심 키워드 SEO 강화")
        if blog_share < 15:
            prescriptions.append("블로그 언급 부족: 체험단/리뷰어 마케팅 확대")
        if not prescriptions:
            prescriptions.append("현 수준 유지: 정기 콘텐츠 발행으로 검색 점유율 수성")

        prescription = " | ".join(prescriptions)
        return diagnosis, prescription
