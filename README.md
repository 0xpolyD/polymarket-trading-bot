# 🤖 Polymarket Trading Bot — @SEI-DDEV

**📞 Contact:** 📊 Polymarket [@sei-ddev](https://polymarket.com/@sei-ddev) · 💬 Telegram [S.E.I](https://t.me/sei_dev) · ▶️ Demo [YouTube](https://www.youtube.com/watch?v=4C83CNM4bE8)


[![Polymarket trading bot — click to watch on YouTube](https://github.com/user-attachments/assets/9b45cc5b-e451-4923-8f91-335f6d627bea)](https://www.youtube.com/watch?v=4C83CNM4bE8)

---

## 📊 Overview

<img width="890" height="296" alt="Polymarket profile — performance overview" src="https://github.com/user-attachments/assets/b2561587-4d2e-4afa-a3d9-d042354fda6e" />

> ✨ **Profile refreshed** — updated display name and continued profit growth through systematic end-cycle execution.

<img width="883" height="259" alt="Polymarket profile — P/L and activity stats" src="https://github.com/user-attachments/assets/43610899-6267-49d4-8701-852165906b1b" />

> 📈 **Live metrics** — figures mirror the public Polymarket profile and refresh in real time. Visit [@sei-ddev](https://polymarket.com/@sei-ddev) for the current P/L curve, open positions, and full trade history.

---

## 👤 SEI-DDev

On Polymarket since **Apr 2026** (2 mo)

🟡 **Risky to copytrade** — -100.0% ROI/mkt · +1.0% ROI/vol

💰 **Portfolio** $0 · **Bank** $423 · **Lifetime PnL** +$1.5K  
📊 **5,046** markets · **WR** 72% (1862W / 735L)  
💵 **Volume** $154.1K  
🎯 **ROI/vol** +1.0% · **ROI/mkt** -100.0% · **profit/mkt** $0  
📈 **Sharpe** 10.30 · **Max DD** -$118 · 🥶 **29L**  
📐 **Median size** $30 (7.0% from bank)  
⏱ **148/wk** · **1.6** entries/mkt (30d)

**🗂 Top categories by PnL**

```
├ Up or Down    337 · WR 49% · -$4.1K
├ Crypto Prices  40 · WR 46% · -$654
├ Recurring      15 · WR 38% · -$368
├ Hide From New  19 · WR 53% · -$254
└ Crypto         17 · WR 69% · -$196
```

⚡ [TRADE ON POLYGUN](https://t.me/PolyGunSniperBot?start=ref_notfedor?0xa96993a1e5e6c7de1f26018bde812ceaec50be4a)

---

## ⚙️ How It Works

| Step | What happens |
|------|----------------|
| **1. Ingest** 📡 | Pulls live **BTC/USD** and **ETH/USD** from on-chain **Chainlink** feeds — the same oracle Polymarket uses at settlement. |
| **2. Score** 🧮 | Compares CLOB-implied probability with a short-horizon directional model in the final seconds of each candle. |
| **3. Snipe** 🎯 | Enters **Up** or **Down** only when edge exceeds fees + slippage; size scales with confidence and time remaining. |
| **4. Settle** ✅ | Markets auto-resolve against Chainlink; the bot rolls cleanly into the next cycle. |

---

## 🎯 Strategy

| Principle | Detail |
|-----------|--------|
| **⏱️ End-cycle only** | Entries cluster in the last **30–90 seconds** of each candle, when signal is strongest and mispricing is most exploitable. |
| **🔁 High frequency, small size** | Many small trades vs. few large ones — variance smooths across a large sample. |
| **🌙 No overnight risk** | Every position resolves within **5** or **15** minutes. |
| **💰 Fee-aware** | Orders fire only when expected edge clears round-trip fees and spread. |

---

*Built for systematic, oracle-aligned execution on short-horizon prediction markets. Past performance does not guarantee future results.*
