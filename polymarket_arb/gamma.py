from __future__ import annotations

import json
import logging
from typing import Any, Iterator

import httpx

from polymarket_arb.config import GAMMA_HOST, Settings

logger = logging.getLogger(__name__)


class GammaClient:
    """Fetches active Polymarket markets from the Gamma API."""

    def __init__(self, settings: Settings, timeout: float = 30.0) -> None:
        self._settings = settings
        self._client = httpx.Client(base_url=GAMMA_HOST, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def iter_active_binary_markets(self) -> Iterator[dict[str, Any]]:
        """Yield raw Gamma market dicts that are binary and order-book enabled."""
        offset = 0
        fetched = 0
        limit = self._settings.gamma_page_size
        cap = self._settings.max_markets_per_scan

        while fetched < cap:
            params = {
                "active": "true",
                "closed": "false",
                "archived": "false",
                "enableOrderBook": "true",
                "limit": min(limit, cap - fetched),
                "offset": offset,
            }
            response = self._client.get("/markets", params=params)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break

            for market in batch:
                if not self._is_scannable_binary(market):
                    continue
                yield market
                fetched += 1
                if fetched >= cap:
                    return

            if len(batch) < params["limit"]:
                break
            offset += len(batch)

    @staticmethod
    def _is_scannable_binary(market: dict[str, Any]) -> bool:
        if not market.get("acceptingOrders"):
            return False
        if market.get("closed") or market.get("archived"):
            return False
        token_ids_raw = market.get("clobTokenIds")
        outcomes_raw = market.get("outcomes")
        if not token_ids_raw or not outcomes_raw:
            return False
        try:
            token_ids = json.loads(token_ids_raw)
            outcomes = json.loads(outcomes_raw)
        except (json.JSONDecodeError, TypeError):
            return False
        return len(token_ids) == 2 and len(outcomes) == 2

    @staticmethod
    def parse_market_row(
        market: dict[str, Any],
    ) -> tuple[str, str, str, str, str, str, str, float, bool]:
        token_ids = json.loads(market["clobTokenIds"])
        outcomes = json.loads(market["outcomes"])
        min_size = float(market.get("orderMinSize") or 5)
        neg_risk = bool(market.get("negRisk", False))
        return (
            market["conditionId"],
            market.get("question", ""),
            market.get("slug", ""),
            outcomes[0],
            outcomes[1],
            token_ids[0],
            token_ids[1],
            min_size,
            neg_risk,
        )
