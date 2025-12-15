from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from app.db.models import ProductSnapshot


@dataclass
class TrendMetrics:
    overall_score: float
    demand_score: float
    competition_score: float
    momentum_score: Optional[float]


def _normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_trend_metrics(history: Sequence[ProductSnapshot]) -> TrendMetrics:
    if not history:
        return TrendMetrics(0.0, 0.0, 0.0, None)

    history = sorted(history, key=lambda s: s.captured_at)
    latest = history[-1]

    ranks = [s.rank for s in history if s.rank is not None]
    sales = [s.estimated_sales for s in history if s.estimated_sales is not None]

    demand_raw = 0.0
    if sales:
        demand_raw += sales[-1]
    if latest.review_count:
        demand_raw += latest.review_count

    demand_score = 0.0
    if demand_raw > 0:
        import math
        demand_score = max(0.0, min(1.0, math.log1p(demand_raw) / 10))

    competition_score = 0.0
    if ranks:
        best_rank = min(ranks)
        worst_rank = max(ranks)
        if latest.rank is not None:
            inv_rank = worst_rank - latest.rank
            competition_score = _normalize(inv_rank, 0, worst_rank - best_rank if worst_rank != best_rank else 1)

    momentum_score: Optional[float] = None
    if len(sales) >= 2:
        diff = sales[-1] - sales[0]
        if sales[0] > 0:
            momentum_score = max(-1.0, min(1.0, diff / sales[0]))

    overall = 0.6 * demand_score + 0.3 * (1 - competition_score) + 0.1 * (momentum_score or 0)

    return TrendMetrics(
        overall_score=overall,
        demand_score=demand_score,
        competition_score=competition_score,
        momentum_score=momentum_score,
    )
