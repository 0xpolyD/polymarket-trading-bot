from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

CLOB_HOST = "https://clob.polymarket.com"
GAMMA_HOST = "https://gamma-api.polymarket.com"
CHAIN_ID = 137


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    private_key: str | None
    funder_address: str | None
    signature_type: int
    execute_trades: bool
    min_profit_per_share: float
    taker_fee_rate: float
    max_order_usdc: float
    min_order_size: float
    scan_interval_seconds: float
    gamma_page_size: int
    max_markets_per_scan: int
    max_concurrent_price_requests: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            private_key=os.getenv("POLYMARKET_PRIVATE_KEY") or None,
            funder_address=os.getenv("POLYMARKET_FUNDER_ADDRESS") or None,
            signature_type=_env_int("POLYMARKET_SIGNATURE_TYPE", 0),
            execute_trades=_env_bool("EXECUTE_TRADES", False),
            min_profit_per_share=_env_float("MIN_PROFIT_PER_SHARE", 0.01),
            taker_fee_rate=_env_float("TAKER_FEE_RATE", 0.0),
            max_order_usdc=_env_float("MAX_ORDER_USDC", 25.0),
            min_order_size=_env_float("MIN_ORDER_SIZE", 5.0),
            scan_interval_seconds=_env_float("SCAN_INTERVAL_SECONDS", 30.0),
            gamma_page_size=_env_int("GAMMA_PAGE_SIZE", 100),
            max_markets_per_scan=_env_int("MAX_MARKETS_PER_SCAN", 500),
            max_concurrent_price_requests=_env_int("MAX_CONCURRENT_PRICE_REQUESTS", 20),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    @property
    def can_trade(self) -> bool:
        return bool(self.private_key)
