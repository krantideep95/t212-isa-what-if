# trading212-xirr

Answers: *"What if, instead of the stocks I actually bought, I had put the same money into a basket of passive UCITS ETFs?"*

Takes your Trading212 ISA transaction history, mirrors every buy and sell into configurable ETF baskets, and produces a comparison table of final portfolio value and money-weighted return (XIRR).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (recommended) **or** Python 3.11+
- Your Trading212 transaction history CSVs (see [Exporting data](#exporting-data))

## Setup

```bash
# clone / download the repo, then:
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e .
```

## Add your data

```
data/
├── transactions/   ← drop all Trading212 transaction CSVs here
└── holdings/       ← drop your latest holdings CSV here (keep exactly one)
```

Both directories are already tracked in git so they exist after cloning.

## Run

```bash
python run.py
```

Prints the comparison table and writes `report.md`. Takes ~30 seconds on first run (fetches price history from Yahoo Finance; cached in `data/portfolio.db` on subsequent runs).

## Customise scenarios

Edit `src/scenarios.py`. Each scenario is a named basket with weights that must sum to 1.0.

**Add a scenario:**
```python
Scenario("S6_nasdaq_heavy", {"CNX1": 0.60, "VUAG": 0.40}),
```

**Add a new ticker** — register it in `TICKER_META` first, then use it in a scenario:
```python
TICKER_META["HMWO"] = {"yahoo": "HMWO.L", "divisor": 1.0}
```

`divisor` is `100.0` if Yahoo Finance quotes the ticker in pence (GBp), `1.0` if in pounds (GBP). CNX1 is the only pence-quoted ticker in the current set.

Rerun `python run.py` after any change.

## Exporting data from Trading212

**Transaction history:**
1. Trading212 → Menu → History → Export CSV.
2. Choose a date range (up to 1 year per export). Export as many ranges as needed.
3. Drop all exported files into `data/transactions/` — every `.csv` in that folder is loaded automatically.

**Holdings snapshot:**
1. Trading212 → Menu → Documents → Confirmation of Holdings. Ask Claude to convert .pdf to .csv.
2. Replace the existing file in `data/holdings/` with the new export.
3. Update `END_DATE` in `src/simulate.py` to match the snapshot date.

## Output

`report.md` contains a table like:

| Scenario | Allocation | Final value (£) | MWR (XIRR) | Net deposited (£) |
|---|---|---:|---:|---:|
| **Actual portfolio** | (real picks) | X,XXX.XX | XX.XX% | X,XXX.XX |
| S1_v3ab_only | V3AB 100% | X,XXX.XX | XX.XX% | X,XXX.XX |
| S2_vuag_only | VUAG 100% | X,XXX.XX | XX.XX% | X,XXX.XX |
| … | … | … | … | … |

- **Final value** — GBP value of the counterfactual holdings on the snapshot date.
- **MWR (XIRR)** — annualised money-weighted return across all deposits, withdrawals, and the terminal value.
- Sells are mirrored proportionally into the basket; dividends are ignored (all target ETFs are accumulating).
