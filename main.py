#!/usr/bin/env python3
"""Polymarket binary complement arbitrage bot — CLI entrypoint."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace

from polymarket_arb.bot import ArbitrageBot
from polymarket_arb.config import Settings


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Polymarket binary markets for complement arbitrage "
            "(buy both outcomes below $1 or sell both above $1)."
        )
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scan and exit (default: continuous loop)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Place orders on the best opportunity (requires private key)",
    )
    parser.add_argument(
        "--min-profit",
        type=float,
        default=None,
        help="Override MIN_PROFIT_PER_SHARE from environment",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()

    if args.min_profit is not None:
        settings = replace(settings, min_profit_per_share=args.min_profit)

    _configure_logging(settings.log_level)

    if args.execute and not settings.can_trade:
        logging.error(
            "--execute requires POLYMARKET_PRIVATE_KEY in .env"
        )
        return 1

    bot = ArbitrageBot(settings)
    try:
        if args.once:
            bot.run_once(execute=args.execute)
        else:
            bot.run_loop(execute=args.execute)
    finally:
        bot.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
