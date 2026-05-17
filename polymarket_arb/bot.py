from __future__ import annotations

import logging
import time

from polymarket_arb.clob import ClobService
from polymarket_arb.config import Settings
from polymarket_arb.executor import ArbitrageExecutor
from polymarket_arb.gamma import GammaClient
from polymarket_arb.scanner import ArbitrageScanner

logger = logging.getLogger(__name__)


class ArbitrageBot:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._gamma = GammaClient(settings)
        self._clob = ClobService(settings)
        self._scanner = ArbitrageScanner(settings, self._gamma, self._clob)
        self._executor = ArbitrageExecutor(settings, self._clob)

    def close(self) -> None:
        self._gamma.close()

    def run_once(self, execute: bool | None = None) -> list:
        if not self._clob.health_check():
            raise RuntimeError("CLOB API is not reachable")

        opportunities = self._scanner.scan_once()
        report = ArbitrageScanner.format_report(opportunities)
        print(report)
        logger.info("Scan complete: %d hits", len(opportunities))

        should_execute = (
            execute if execute is not None else self._settings.execute_trades
        )
        if not should_execute or not opportunities:
            return opportunities

        top = opportunities[0]
        logger.info("Executing top opportunity: %s", top.summary())
        try:
            results = self._executor.execute(top)
            logger.info("Execution responses: %s", results)
        except Exception:
            logger.exception("Execution failed")
            raise
        return opportunities

    def run_loop(self, execute: bool | None = None) -> None:
        logger.info(
            "Starting loop (interval=%ss, execute=%s)",
            self._settings.scan_interval_seconds,
            execute if execute is not None else self._settings.execute_trades,
        )
        try:
            while True:
                try:
                    self.run_once(execute=execute)
                except Exception:
                    logger.exception("Scan cycle error")
                time.sleep(self._settings.scan_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            self.close()
