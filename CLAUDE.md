# trading212-xirr

Counterfactual ETF basket simulator for a Trading212 ISA. Answers: "what if I had just bought V3AB/VUAG/CNX1/SEGM/XMWX instead of my actual picks?"

## Running

```bash
source .venv/bin/activate   # Python 3.12 via uv
python run.py               # full pipeline: load → prices → simulate → report
```

`run.py` is idempotent — it wipes and repopulates the DB each run.

## Key files

| File | Purpose |
|------|---------|
| `src/scenarios.py` | **Edit this** to add/change basket scenarios |
| `report.md` | Generated output — comparison table |
| `data/portfolio.db` | SQLite cache (gitignored, rebuilt by `run.py`) |
| `data/transactions/*.csv` | Raw Trading212 transaction exports (all CSVs loaded) |
| `data/holdings/*.csv` | Current holdings snapshot — keep exactly one file here |

## Adding a scenario or ticker

**New scenario** — add a `Scenario` to `SCENARIOS` in `src/scenarios.py` and rerun:

```python
Scenario("S6_my_blend", {"VUAG": 0.50, "CNX1": 0.50}),
```

**New ticker** — add it to `TICKER_META` in `src/scenarios.py` first, then use it in a scenario:

```python
TICKER_META["HMWO"] = {"yahoo": "HMWO.L", "divisor": 1.0}
```

Weights must sum to 1.0. Using a ticker not in `TICKER_META` raises an error at import time.

## Architecture

```
Transaction CSVs
    └─ load_transactions.py → transactions table

prices table ←── load_prices.py ←── transactions table (real fills)
                                └─── yfinance (gaps, VUAG.L / V3AB.L / CNX1.L / SEGM.L / XMWX.L)
                                     CNX1 is GBp (÷100); rest GBP

simulate.py  ── walks transactions, mirrors each buy/sell into basket at opening price
xirr.py      ── money-weighted return via scipy brentq
actual.py    ── values holdings CSV in GBP (USD rows converted via GBPUSD=X yfinance)
report.py    ── builds report.md
```

## Conventions

- No tests — spot-check by comparing `report.md` values to Trading212 app.
- `total_gbp` column is used as-is for every buy/sell amount (already in GBP).
- Sells capped at available basket value (no negative holdings).
- Dividends ignored — all 5 target ETFs are accumulating.
- Missing price dates fall forward to next available trading day.

## Updating transaction history

1. Drop new transaction CSVs from Trading212 into `data/transactions/` (any filename, all are loaded).
2. Replace the file in `data/holdings/` with a fresh export (delete the old one, add the new one).
3. Update `END_DATE` in `src/simulate.py` to match the holdings snapshot date.
4. Run `python run.py`.
