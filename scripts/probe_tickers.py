"""One-shot probe to confirm ticker → ISIN mapping and yfinance availability."""

import sqlite3
import yfinance as yf
from src.db import connect

TARGET_TICKERS = ["VUAG", "V3AB", "CNX1", "SEGM", "XMWX"]


def isins_from_db(conn: sqlite3.Connection) -> dict[str, list[tuple]]:
    out: dict[str, list[tuple]] = {}
    for t in TARGET_TICKERS:
        rows = conn.execute(
            "SELECT DISTINCT isin, name FROM transactions WHERE ticker = ?",
            (t,),
        ).fetchall()
        out[t] = [(r["isin"], r["name"]) for r in rows]
    return out


def yf_probe(ticker: str) -> str:
    t = yf.Ticker(f"{ticker}.L")
    hist = t.history(period="5d", auto_adjust=False)
    if hist.empty:
        return "EMPTY"
    return f"{len(hist)} rows; last open={hist['Open'].iloc[-1]:.4f} ccy={t.info.get('currency','?')}"


if __name__ == "__main__":
    with connect() as conn:
        mapping = isins_from_db(conn)
    for t, isins in mapping.items():
        print(f"{t}: {isins}")
    print()
    for t in TARGET_TICKERS:
        print(f"{t}.L → {yf_probe(t)}")
