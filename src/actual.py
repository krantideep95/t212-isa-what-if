"""Compute the actual portfolio's GBP value on 2026-05-06."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

def _holdings_csv() -> Path:
    candidates = sorted((Path(__file__).parent.parent / "data" / "holdings").glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("No holdings CSV found in data/holdings/")
    return candidates[-1]  # most recent by filename sort
END_DATE = "2026-05-06"


def _gbpusd_rate() -> float:
    """GBP→USD rate on END_DATE (how many USD per 1 GBP)."""
    fx = yf.Ticker("GBPUSD=X").history(start="2026-05-05", end="2026-05-09", auto_adjust=False)
    if fx.empty:
        raise RuntimeError("Could not fetch GBPUSD rate")
    return float(fx["Open"].iloc[0])


def actual_value_gbp() -> float:
    df = pd.read_csv(_holdings_csv())
    df = df.dropna(subset=["Quantity", "Price"])
    rate = _gbpusd_rate()
    total = 0.0
    for _, row in df.iterrows():
        ccy = str(row["Currency"]).upper()
        price = float(row["Price"])
        qty = float(row["Quantity"])
        if ccy == "GBP":
            per_share_gbp = price
        elif ccy == "GBX":
            per_share_gbp = price / 100.0
        elif ccy == "USD":
            per_share_gbp = price / rate
        else:
            raise ValueError(f"Unsupported currency: {ccy}")
        total += qty * per_share_gbp
    return total


def total_deposited_gbp(conn) -> float:
    """Net deposits (deposits - withdrawals) in GBP."""
    rows = conn.execute(
        "SELECT action, SUM(total_gbp) AS s FROM transactions "
        "WHERE action IN ('Deposit', 'Withdrawal') "
        "GROUP BY action"
    ).fetchall()
    deposits = 0.0
    withdrawals = 0.0
    for r in rows:
        if r["action"] == "Deposit":
            deposits = float(r["s"] or 0.0)
        elif r["action"] == "Withdrawal":
            withdrawals = float(r["s"] or 0.0)
    return deposits - withdrawals


if __name__ == "__main__":
    from src.db import connect
    print(f"Actual portfolio value on {END_DATE}: £{actual_value_gbp():,.2f}")
    with connect() as conn:
        print(f"Net deposited: £{total_deposited_gbp(conn):,.2f}")
