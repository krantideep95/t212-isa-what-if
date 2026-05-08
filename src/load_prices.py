"""Two-step price loader.

Step 1: from `transactions` table, for each (ticker, date) where the user
        has a real buy or sell of one of the target ETFs, record
        `Price / share` (normalized to GBP) into `prices`.

Step 2: fill in remaining dates via yfinance.
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import yfinance as yf

from src.db import connect, init_schema
from src.scenarios import TICKER_META

BUY_SELL_ACTIONS = (
    "Market buy", "Limit buy", "Stop buy",
    "Market sell", "Limit sell", "Stop sell",
)


def load_from_transactions(conn: sqlite3.Connection) -> int:
    """Insert prices derived from real transactions for target tickers.
    Uses the FIRST transaction of the day per (ticker, date)."""
    placeholders = ",".join("?" * len(TICKER_META))
    rows = conn.execute(
        f"""
        SELECT ticker, date, price_native, ccy_native, ts
        FROM transactions
        WHERE ticker IN ({placeholders})
          AND action IN ({",".join("?" * len(BUY_SELL_ACTIONS))})
          AND price_native IS NOT NULL
        ORDER BY ticker, date, ts ASC
        """,
        (*TICKER_META.keys(), *BUY_SELL_ACTIONS),
    ).fetchall()

    seen: set[tuple[str, str]] = set()
    inserted = 0
    for r in rows:
        key = (r["ticker"], r["date"])
        if key in seen:
            continue
        seen.add(key)
        ccy = (r["ccy_native"] or "").upper()
        price = float(r["price_native"])
        if ccy in ("GBX", "GBP"):
            open_gbp = price / 100.0 if ccy == "GBX" else price
        else:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO prices(ticker, date, open_gbp, source) "
            "VALUES (?, ?, ?, 'transaction')",
            (r["ticker"], r["date"], open_gbp),
        )
        inserted += 1
    conn.commit()
    return inserted


def all_relevant_dates(conn: sqlite3.Connection) -> list[str]:
    """All distinct transaction dates we may need to value the basket on."""
    rows = conn.execute(
        "SELECT DISTINCT date FROM transactions ORDER BY date"
    ).fetchall()
    return [r["date"] for r in rows]


def fill_from_yfinance(conn: sqlite3.Connection) -> int:
    dates = all_relevant_dates(conn)
    if not dates:
        return 0
    start = min(dates)
    end_dt = pd.Timestamp(max(dates)) + pd.Timedelta(days=2)
    end = end_dt.strftime("%Y-%m-%d")

    inserted = 0
    for ticker, meta in TICKER_META.items():
        yahoo_sym, divisor = meta["yahoo"], meta["divisor"]
        hist = yf.download(
            yahoo_sym, start=start, end=end,
            auto_adjust=False, progress=False,
        )
        if hist.empty:
            print(f"WARN: yfinance returned no data for {yahoo_sym}")
            continue
        opens = hist["Open"].squeeze().dropna()
        for ts, val in opens.items():
            d = ts.strftime("%Y-%m-%d")
            existing = conn.execute(
                "SELECT 1 FROM prices WHERE ticker = ? AND date = ?",
                (ticker, d),
            ).fetchone()
            if existing:
                continue
            open_gbp = float(val) / divisor
            conn.execute(
                "INSERT INTO prices(ticker, date, open_gbp, source) "
                "VALUES (?, ?, ?, 'yfinance')",
                (ticker, d, open_gbp),
            )
            inserted += 1
    conn.commit()
    return inserted


if __name__ == "__main__":
    with connect() as conn:
        init_schema(conn)
        n1 = load_from_transactions(conn)
        print(f"Step 1: inserted {n1} price rows from transactions")
        n2 = fill_from_yfinance(conn)
        print(f"Step 2: inserted {n2} price rows from yfinance")
