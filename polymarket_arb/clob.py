from __future__ import annotations

import logging
from typing import Any

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams, MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

from polymarket_arb.config import CHAIN_ID, CLOB_HOST, Settings
from polymarket_arb.models import BinaryMarket, TokenQuote

logger = logging.getLogger(__name__)


def _price_from_response(payload: Any) -> float | None:
    if payload is None:
        return None
    if isinstance(payload, (int, float)):
        return float(payload)
    if isinstance(payload, dict):
        raw = payload.get("price")
        if raw is None:
            return None
        return float(raw)
    if isinstance(payload, str):
        return float(payload)
    return None


def _top_of_book(levels: list[dict[str, Any]] | None) -> tuple[float | None, float | None]:
    if not levels:
        return None, None
    top = levels[0]
    try:
        return float(top["price"]), float(top["size"])
    except (KeyError, TypeError, ValueError):
        return None, None


class ClobService:
    """Read order books and optionally execute trades via py-clob-client."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._read_client = ClobClient(CLOB_HOST)
        self._trade_client: ClobClient | None = None

    @property
    def read_client(self) -> ClobClient:
        return self._read_client

    def ensure_trading_client(self) -> ClobClient:
        if self._trade_client is not None:
            return self._trade_client
        if not self._settings.private_key:
            raise RuntimeError(
                "POLYMARKET_PRIVATE_KEY is required for trading. "
                "Run in scan-only mode or set the key in .env"
            )

        kwargs: dict[str, Any] = {
            "host": CLOB_HOST,
            "key": self._settings.private_key,
            "chain_id": CHAIN_ID,
            "signature_type": self._settings.signature_type,
        }
        if self._settings.funder_address:
            kwargs["funder"] = self._settings.funder_address

        client = ClobClient(**kwargs)
        creds = client.create_or_derive_api_creds()
        client.set_api_creds(creds)
        self._trade_client = client
        logger.info("CLOB trading client authenticated")
        return client

    def health_check(self) -> bool:
        try:
            return str(self._read_client.get_ok()).upper() == "OK"
        except Exception:
            logger.exception("CLOB health check failed")
            return False

    def get_token_quote(self, token_id: str, outcome: str) -> TokenQuote:
        bid = _price_from_response(self._read_client.get_price(token_id, side="BUY"))
        ask = _price_from_response(self._read_client.get_price(token_id, side="SELL"))
        bid_size: float | None = None
        ask_size: float | None = None
        try:
            book = self._read_client.get_order_book(token_id)
            bids = book.bids if hasattr(book, "bids") else book.get("bids")
            asks = book.asks if hasattr(book, "asks") else book.get("asks")
            bid_size = _top_of_book(bids)[1]
            ask_size = _top_of_book(asks)[1]
        except Exception:
            logger.debug("Order book fetch failed for %s", token_id, exc_info=True)

        return TokenQuote(
            token_id=token_id,
            outcome=outcome,
            best_bid=bid,
            best_ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
        )

    def get_order_books_batch(
        self, token_outcomes: list[tuple[str, str]]
    ) -> list[TokenQuote]:
        if not token_outcomes:
            return []
        params = [BookParams(token_id=tid) for tid, _ in token_outcomes]
        books = self._read_client.get_order_books(params)
        if len(books) != len(token_outcomes):
            raise RuntimeError(
                f"Expected {len(token_outcomes)} books, got {len(books)}"
            )
        quotes: list[TokenQuote] = []
        for (token_id, outcome), book in zip(token_outcomes, books, strict=True):
            bids = book.bids if hasattr(book, "bids") else book.get("bids")
            asks = book.asks if hasattr(book, "asks") else book.get("asks")
            bid_price, bid_size = _top_of_book(bids)
            ask_price, ask_size = _top_of_book(asks)
            quotes.append(
                TokenQuote(
                    token_id=token_id,
                    outcome=outcome,
                    best_bid=bid_price,
                    best_ask=ask_price,
                    bid_size=bid_size,
                    ask_size=ask_size,
                )
            )
        return quotes

    def place_market_buy(self, token_id: str, amount_usdc: float) -> dict[str, Any]:
        client = self.ensure_trading_client()
        order = MarketOrderArgs(token_id=token_id, amount=amount_usdc, side=BUY)
        signed = client.create_market_order(order)
        return client.post_order(signed, OrderType.FOK)

    def place_market_sell(self, token_id: str, shares: float) -> dict[str, Any]:
        client = self.ensure_trading_client()
        order = MarketOrderArgs(token_id=token_id, amount=shares, side=SELL)
        signed = client.create_market_order(order)
        return client.post_order(signed, OrderType.FOK)
