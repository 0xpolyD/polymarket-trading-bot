from __future__ import annotations

import logging
import math

from polymarket_arb.clob import ClobService
from polymarket_arb.config import Settings
from polymarket_arb.models import ArbKind, ArbitrageOpportunity

logger = logging.getLogger(__name__)


class ArbitrageExecutor:
    """Executes complement arbitrage when enabled in settings."""

    def __init__(self, settings: Settings, clob: ClobService) -> None:
        self._settings = settings
        self._clob = clob

    def execute(self, opportunity: ArbitrageOpportunity) -> list[dict]:
        if not self._settings.execute_trades:
            logger.warning("EXECUTE_TRADES=false; skipping execution")
            return []
        if not self._settings.can_trade:
            raise RuntimeError("Cannot execute without POLYMARKET_PRIVATE_KEY")

        if opportunity.kind == ArbKind.BUY_BOTH:
            return self._execute_buy_both(opportunity)
        return self._execute_sell_both(opportunity)

    def _execute_buy_both(self, opportunity: ArbitrageOpportunity) -> list[dict]:
        market = opportunity.market
        shares = min(
            opportunity.max_executable_shares,
            self._shares_from_usdc_cap(market),
        )
        shares = max(shares, market.min_order_size)
        shares = math.floor(shares * 100) / 100

        results: list[dict] = []
        for quote in (market.token_a, market.token_b):
            if quote.best_ask is None:
                raise RuntimeError(f"Missing ask for {quote.outcome}")
            usdc = shares * quote.best_ask
            usdc = min(usdc, self._settings.max_order_usdc)
            logger.info(
                "BUY %s @ ~%.4f for $%.2f (%s)",
                quote.outcome,
                quote.best_ask,
                usdc,
                market.question[:50],
            )
            results.append(self._clob.place_market_buy(quote.token_id, usdc))
        return results

    def _execute_sell_both(self, opportunity: ArbitrageOpportunity) -> list[dict]:
        market = opportunity.market
        shares = min(
            opportunity.max_executable_shares,
            self._shares_from_usdc_cap(market),
        )
        shares = max(shares, market.min_order_size)
        shares = math.floor(shares * 100) / 100

        results: list[dict] = []
        for quote in (market.token_a, market.token_b):
            logger.info(
                "SELL %.2f shares %s (%s)",
                shares,
                quote.outcome,
                market.question[:50],
            )
            results.append(self._clob.place_market_sell(quote.token_id, shares))
        return results

    def _shares_from_usdc_cap(self, market) -> float:
        quotes = (market.token_a, market.token_b)
        costs = []
        for q in quotes:
            if q.best_ask is None and q.best_bid is None:
                continue
            ref = q.best_ask if q.best_ask is not None else q.best_bid
            if ref and ref > 0:
                costs.append(self._settings.max_order_usdc / ref)
        if not costs:
            return market.min_order_size
        return min(costs)
