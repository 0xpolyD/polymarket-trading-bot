# Polymarket Arbitrage Bot (Python)

Scans [Polymarket](https://polymarket.com) binary markets for **complement arbitrage**:

- **Buy both**: best ask(Yes) + best ask(No) &lt; $1 → buy both legs; one side pays $1 at resolution.
- **Sell both**: best bid(Yes) + best bid(No) &gt; $1 → sell both legs if you hold inventory.

Uses the **Gamma API** for market discovery and the **CLOB API** (`py-clob-client`) for live order books and optional execution.

## Quick start

```bash
cd /workspace/polymarket/sample
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Scan only (safe default)

```bash
python main.py --once
```

### Continuous scanning

```bash
python main.py
```

### Live trading

1. Fund a Polygon wallet with USDC and connect it on Polymarket.
2. Export your private key into `.env` as `POLYMARKET_PRIVATE_KEY`.
3. Set `EXECUTE_TRADES=true` or pass `--execute`.

```bash
python main.py --once --execute --min-profit 0.02
```

## Configuration

See `.env.example` for all options. Important fields:

| Variable | Description |
|----------|-------------|
| `POLYMARKET_PRIVATE_KEY` | Wallet key for signing orders |
| `EXECUTE_TRADES` | `false` = scan only |
| `MIN_PROFIT_PER_SHARE` | Minimum net edge per share pair |
| `TAKER_FEE_RATE` | Fee fraction subtracted from gross edge |
| `MAX_ORDER_USDC` | Cap per market-buy leg |
| `SCAN_INTERVAL_SECONDS` | Loop delay |

## Project layout

```
polymarket_arb/
  config.py      # Settings from environment
  gamma.py       # Market discovery
  clob.py        # Order books + trading
  scanner.py     # Arbitrage detection
  executor.py    # FOK market orders
  bot.py         # Main loop
main.py          # CLI
tests/           # Unit tests for edge detection
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Risk disclaimer

Prediction-market arbitrage is competitive; displayed edges may disappear before fills. Fees, partial fills, and inventory requirements (for sell-side arb) can eliminate profit. Use scan-only mode first. This software is for education; not financial advice.
