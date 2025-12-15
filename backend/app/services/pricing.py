from dataclasses import dataclass
from typing import Iterable


@dataclass
class PriceBand:
    recommended_min: float
    recommended_max: float
    currency: str
    rationale: str


def recommend_price(current_price: float, peer_prices: Iterable[float], currency: str = "USD") -> PriceBand:
    peers = [p for p in peer_prices if p > 0]
    if not peers:
        return PriceBand(
            recommended_min=current_price * 0.9,
            recommended_max=current_price * 1.1,
            currency=currency,
            rationale="No peer data; +/-10% around current price.",
        )

    peers.sort()
    n = len(peers)
    median = peers[n // 2] if n % 2 == 1 else 0.5 * (peers[n // 2 - 1] + peers[n // 2])
    low = median * 0.85
    high = median * 1.15
    rationale = f"Based on median price of {median:.2f} across {n} similar listings."
    return PriceBand(recommended_min=low, recommended_max=high, currency=currency, rationale=rationale)
