from __future__ import annotations

import logging
import time
from typing import Iterable

from polymarket_arb.clob import ClobService
from polymarket_arb.config import Settings
from polymarket_arb.gamma import GammaClient
from polymarket_arb.models import ArbKind, ArbitrageOpportunity, BinaryMarket, TokenQuote

logger = logging.getLogger(__name__)


class ArbitrageScanner:
    """Scans Polymarket binary markets for complement mispricing."""

    def __init__(
        self,
        settings: Settings,
        gamma: GammaClient,
        clob: ClobService,
    ) -> None:
        self._settings = settings
        self._gamma = gamma
        self._clob = clob

    def scan_once(self) -> list[ArbitrageOpportunity]:
        markets = list(self._gamma.iter_active_binary_markets())
        logger.info("Gamma returned %d scannable binary markets", len(markets))
        if not markets:
            return []

        payloads: list[tuple[str, str, str, str, str, str, str, float, bool]] = []
        for row in markets:
            (
                condition_id,
                question,
                slug,
                outcome_a,
                outcome_b,
                token_a,
                token_b,
                min_size,
                neg_risk,
            ) = GammaClient.parse_market_row(row)
            payloads.append(
                (
                    condition_id,
                    question,
                    slug,
                    outcome_a,
                    outcome_b,
                    token_a,
                    token_b,
                    min_size,
                    neg_risk,
                )
            )

        quote_map = self._fetch_quotes_batched(payloads)
        opportunities: list[ArbitrageOpportunity] = []
        for payload in payloads:
            token_a = payload[5]
            token_b = payload[6]
            quotes = quote_map.get(token_a), quote_map.get(token_b)
            if quotes[0] is None or quotes[1] is None:
                continue
            market = BinaryMarket(
                condition_id=payload[0],
                question=payload[1],
                slug=payload[2],
                token_a=quotes[0],
                token_b=quotes[1],
                min_order_size=payload[7],
                neg_risk=payload[8],
            )
            opp = self._check_buy_both(market)
            if opp is None:
                opp = self._check_sell_both(market)
            if opp is not None:
                opportunities.append(opp)

        opportunities.sort(key=lambda o: o.net_edge_per_share, reverse=True)
        return opportunities

    def _fetch_quotes_batched(
        self,
        payloads: list[tuple[str, str, str, str, str, str, str, float, bool]],
    ) -> dict[str, TokenQuote]:
        chunk_size = max(2, self._settings.max_concurrent_price_requests * 2)
        token_outcomes: list[tuple[str, str]] = []
        for payload in payloads:
            token_outcomes.append((payload[5], payload[3]))
            token_outcomes.append((payload[6], payload[4]))

        quote_map: dict[str, TokenQuote] = {}
        for start in range(0, len(token_outcomes), chunk_size):
            chunk = token_outcomes[start : start + chunk_size]
            for attempt in range(3):
                try:
                    quotes = self._clob.get_order_books_batch(chunk)
                    quote_map.update({q.token_id: q for q in quotes})
                    break
                except Exception:
                    if attempt == 2:
                        logger.exception(
                            "Order book batch failed (%d tokens)", len(chunk)
                        )
                    else:
                        time.sleep(0.5 * (attempt + 1))
        return quote_map

    def _check_buy_both(self, market: BinaryMarket) -> ArbitrageOpportunity | None:
        a, b = market.token_a, market.token_b
        if a.best_ask is None or b.best_ask is None:
            return None

        total_cost = a.best_ask + b.best_ask
        gross_edge = 1.0 - total_cost
        if gross_edge <= 0:
            return None

        net_edge = self._apply_fees(gross_edge, total_cost, ArbKind.BUY_BOTH)
        if net_edge < self._settings.min_profit_per_share:
            return None

        max_shares = self._max_executable_shares(a, b, use_asks=True)
        if max_shares < market.min_order_size:
            return None

        return ArbitrageOpportunity(
            market=market,
            kind=ArbKind.BUY_BOTH,
            gross_edge_per_share=gross_edge,
            net_edge_per_share=net_edge,
            max_executable_shares=max_shares,
            total_cost_per_share=total_cost,
            details={
                "ask_a": a.best_ask,
                "ask_b": b.best_ask,
                "slug": market.slug,
            },
        )

    def _check_sell_both(self, market: BinaryMarket) -> ArbitrageOpportunity | None:
        a, b = market.token_a, market.token_b
        if a.best_bid is None or b.best_bid is None:
            return None

        total_proceeds = a.best_bid + b.best_bid
        gross_edge = total_proceeds - 1.0
        if gross_edge <= 0:
            return None

        net_edge = self._apply_fees(gross_edge, total_proceeds, ArbKind.SELL_BOTH)
        if net_edge < self._settings.min_profit_per_share:
            return None

        max_shares = self._max_executable_shares(a, b, use_asks=False)
        if max_shares < market.min_order_size:
            return None

        return ArbitrageOpportunity(
            market=market,
            kind=ArbKind.SELL_BOTH,
            gross_edge_per_share=gross_edge,
            net_edge_per_share=net_edge,
            max_executable_shares=max_shares,
            total_cost_per_share=total_proceeds,
            details={
                "bid_a": a.best_bid,
                "bid_b": b.best_bid,
                "slug": market.slug,
            },
        )

    def _apply_fees(self, gross_edge: float, notional: float, kind: ArbKind) -> float:
        fee = notional * self._settings.taker_fee_rate
        if kind == ArbKind.BUY_BOTH:
            fee += notional * self._settings.taker_fee_rate
        else:
            fee += notional * self._settings.taker_fee_rate
        return gross_edge - fee

    @staticmethod
    def _max_executable_shares(
        a: TokenQuote, b: TokenQuote, *, use_asks: bool
    ) -> float:
        if use_asks:
            sizes = [s for s in (a.ask_size, b.ask_size) if s is not None]
        else:
            sizes = [s for s in (a.bid_size, b.bid_size) if s is not None]
        if not sizes:
            return float("inf")
        return min(sizes)

    @staticmethod
    def format_report(opportunities: Iterable[ArbitrageOpportunity]) -> str:
        items = list(opportunities)
        if not items:
            return "No arbitrage opportunities above threshold."
        lines = [f"Found {len(items)} opportunity(ies):", ""]
        for idx, opp in enumerate(items, start=1):
            lines.append(f"{idx}. {opp.summary()}")
            lines.append(f"   https://polymarket.com/event/{opp.market.slug}")
        return "\n".join(lines)
