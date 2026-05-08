# Counterfactual ETF basket simulation — design

**Date:** 2026-05-08  
**Status:** implemented

## Goal

Answer: *"How would my Trading212 ISA have performed since Aug 2022 if, instead of the actual stocks/ETFs I bought, I had spent the same GBP on each buy date in a fixed basket of UCITS ETFs?"*

Output: a Markdown report comparing the actual portfolio against several counterfactual baskets on a chosen cut-off date, with both **final portfolio value** and **money-weighted return (XIRR)**.

## Inputs

- Transaction CSVs in `data/transactions/` — all `.csv` files are loaded automatically regardless of filename.
- Holdings snapshot in `data/holdings/` — the single CSV in this folder is used for actual portfolio valuation. The most-recently-named file (alphabetical sort) wins if multiple exist.
- Historical daily opening prices fetched via `yfinance`, supplemented by real transaction fill prices.

## Counterfactual semantics

| Concern | Decision |
|---|---|
| Buys | Every real Market/Limit/Stop buy → buy the basket with the same GBP `Total`. |
| Sells | Every real Market/Limit/Stop sell → sell the basket for the same GBP `Total`, proportionally across holdings. |
| Sell cap | When basket value < real-sell GBP, sell the entire basket and stop. No negative holdings. |
| FX | Use the CSV's `Total` column (already GBP) as-is. No FX recompute. |
| Price date | Use the opening price on the transaction date; fall forward to next trading day if no price available. |
| Dividends | Ignored. All target ETFs are accumulating (dividends reinvested in price). |
| Interest on cash / corporate actions | Ignored. |
| Final valuation date | Controlled by `END_DATE` in `src/simulate.py` — update when loading a new holdings snapshot. |

## Tickers and scenarios

Both live in `src/scenarios.py` — the single source of truth for all symbol metadata.

**`TICKER_META`** maps each supported ticker to its Yahoo Finance symbol and a GBp divisor:

```python
TICKER_META = {
    "VUAG": {"yahoo": "VUAG.L", "divisor": 1.0},   # GBP
    "V3AB": {"yahoo": "V3AB.L", "divisor": 1.0},   # GBP
    "CNX1": {"yahoo": "CNX1.L", "divisor": 100.0}, # GBp → ÷100
    "SEGM": {"yahoo": "SEGM.L", "divisor": 1.0},   # GBP
    "XMWX": {"yahoo": "XMWX.L", "divisor": 1.0},   # GBP
}
```

**`SCENARIOS`** is a list of `Scenario(name, weights)`. Weights must sum to 1.0 and reference only tickers in `TICKER_META` (validated at import time).

## Price data — two-step load

1. **From real transactions** — for each target ticker, extract `Price / share` from the first transaction of each day and normalize to GBP (GBX rows ÷ 100). These are the most accurate prices since they reflect actual fill prices.
2. **From yfinance** — fetch daily opens for every target ticker over the full transaction date range, inserting only dates not already covered by step 1.

Both steps write to the `prices(ticker, date, open_gbp, source)` table. `source` ∈ `'transaction' | 'yfinance'`.

## Output metrics

Per scenario and for the actual portfolio:

1. **Final portfolio value (£)** at `END_DATE`.
2. **MWR (XIRR)** — annualised money-weighted return. Cash flows: each Deposit = negative (money out of pocket), each Withdrawal = positive, terminal portfolio value = positive.
3. **Net deposited (£)** — sum of all deposits minus withdrawals.

## Architecture

```
trading212-xirr/
├── data/
│   ├── transactions/        ← drop Trading212 export CSVs here
│   ├── holdings/            ← one holdings snapshot CSV
│   └── portfolio.db         ← sqlite cache (gitignored, rebuilt by run.py)
├── src/
│   ├── scenarios.py         ← TICKER_META + SCENARIOS (edit this to change scenarios)
│   ├── db.py                ← sqlite connection + schema init
│   ├── schema.sql           ← transactions + prices table definitions
│   ├── load_transactions.py ← all CSVs → transactions table
│   ├── load_prices.py       ← two-step price loader (transactions then yfinance)
│   ├── simulate.py          ← walk transactions per scenario → SimResult
│   ├── actual.py            ← value holdings CSV in GBP (USD rows via GBPUSD=X)
│   ├── xirr.py              ← XIRR via scipy.optimize.brentq
│   └── report.py            ← Markdown report builder
├── scripts/
│   └── probe_tickers.py     ← one-off: verify ticker ISINs and yfinance availability
├── run.py                   ← entry point: load → prices → simulate → report
├── report.md                ← generated output
└── CLAUDE.md                ← AI assistant context
```

## Out of scope

- Tests (one-shot personal analysis; spot-check by hand).
- Web UI or charts.
- Modelling Trading212 cash interest in the counterfactual.
- Per-buy breakdown (the data is all in sqlite — could be added later).
