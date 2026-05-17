from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ArbKind(str, Enum):
    BUY_BOTH = "buy_both"  # ask_yes + ask_no < 1
    SELL_BOTH = "sell_both"  # bid_yes + bid_no > 1


@dataclass(frozen=True)
class TokenQuote:
    token_id: str
    outcome: str
    best_bid: float | None
    best_ask: float | None
    bid_size: float | None
    ask_size: float | None


@dataclass(frozen=True)
class BinaryMarket:
    condition_id: str
    question: str
    slug: str
    token_a: TokenQuote
    token_b: TokenQuote
    min_order_size: float
    neg_risk: bool

    @property
    def token_ids(self) -> tuple[str, str]:
        return (self.token_a.token_id, self.token_b.token_id)


@dataclass(frozen=True)
class ArbitrageOpportunity:
    market: BinaryMarket
    kind: ArbKind
    gross_edge_per_share: float
    net_edge_per_share: float
    max_executable_shares: float
    total_cost_per_share: float
    details: dict[str, Any]

    def summary(self) -> str:
        legs = f"{self.market.token_a.outcome} / {self.market.token_b.outcome}"
        return (
            f"[{self.kind.value}] {self.net_edge_per_share:.4f} net/share "
            f"(gross {self.gross_edge_per_share:.4f}) | "
            f"max {self.max_executable_shares:.2f} shares | {legs} | "
            f"{self.market.question[:72]}"
        )
