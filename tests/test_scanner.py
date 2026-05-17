import unittest

from polymarket_arb.config import Settings
from polymarket_arb.models import ArbKind, BinaryMarket, TokenQuote
from polymarket_arb.scanner import ArbitrageScanner


def _market(
    ask_a: float | None,
    ask_b: float | None,
    bid_a: float | None = None,
    bid_b: float | None = None,
    ask_size: float = 100.0,
    bid_size: float = 100.0,
) -> BinaryMarket:
    return BinaryMarket(
        condition_id="0xabc",
        question="Test market?",
        slug="test-market",
        token_a=TokenQuote("t1", "Yes", bid_a, ask_a, bid_size, ask_size),
        token_b=TokenQuote("t2", "No", bid_b, ask_b, bid_size, ask_size),
        min_order_size=5.0,
        neg_risk=False,
    )


class ScannerLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        settings = Settings(
            private_key=None,
            funder_address=None,
            signature_type=0,
            execute_trades=False,
            min_profit_per_share=0.001,
            taker_fee_rate=0.0,
            max_order_usdc=25.0,
            min_order_size=5.0,
            scan_interval_seconds=30.0,
            gamma_page_size=100,
            max_markets_per_scan=500,
            max_concurrent_price_requests=20,
            log_level="INFO",
        )
        self.scanner = ArbitrageScanner(settings, None, None)  # type: ignore[arg-type]

    def test_buy_both_detected(self) -> None:
        market = _market(ask_a=0.45, ask_b=0.50)
        opp = self.scanner._check_buy_both(market)
        self.assertIsNotNone(opp)
        assert opp is not None
        self.assertEqual(opp.kind, ArbKind.BUY_BOTH)
        self.assertAlmostEqual(opp.gross_edge_per_share, 0.05)

    def test_buy_both_rejected_when_sum_at_one(self) -> None:
        market = _market(ask_a=0.52, ask_b=0.48)
        opp = self.scanner._check_buy_both(market)
        self.assertIsNone(opp)

    def test_sell_both_detected(self) -> None:
        market = _market(
            ask_a=0.55,
            ask_b=0.50,
            bid_a=0.54,
            bid_b=0.49,
        )
        opp = self.scanner._check_sell_both(market)
        self.assertIsNotNone(opp)
        assert opp is not None
        self.assertEqual(opp.kind, ArbKind.SELL_BOTH)
        self.assertAlmostEqual(opp.gross_edge_per_share, 0.03)


if __name__ == "__main__":
    unittest.main()
