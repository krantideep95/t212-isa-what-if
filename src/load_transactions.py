"""Load all transaction CSVs into the `transactions` table."""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

from src.db import connect, init_schema

REPO_ROOT = Path(__file__).parent.parent

CANONICAL_COLS = [
    "Action", "Time", "ISIN", "Ticker", "Name", "Notes", "ID",
    "No. of shares", "Price / share", "Currency (Price / share)",
    "Exchange rate", "Total", "Currency (Total)",
]


def normalize(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    df = df.reindex(columns=CANONICAL_COLS)
    df = df.rename(columns={
        "Action": "action",
        "Time": "ts",
        "ISIN": "isin",
        "Ticker": "ticker",
        "Name": "name",
        "ID": "raw_id",
        "No. of shares": "shares",
        "Price / share": "price_native",
        "Currency (Price / share)": "ccy_native",
        "Exchange rate": "fx",
        "Total": "total_gbp",
    })
    df["date"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m-%d")
    df["source_file"] = source_file
    return df[[
        "raw_id", "source_file", "action", "ts", "date", "isin", "ticker",
        "name", "shares", "price_native", "ccy_native", "fx", "total_gbp",
    ]]


def load_all() -> int:
    csvs = sorted(glob.glob(str(REPO_ROOT / "data" / "transactions" / "*.csv")))
    if not csvs:
        raise FileNotFoundError("No transaction CSVs found in data/transactions/")

    frames = []
    for path in csvs:
        df = pd.read_csv(path)
        frames.append(normalize(df, source_file=Path(path).name))
    all_tx = pd.concat(frames, ignore_index=True)

    all_tx = all_tx.dropna(subset=["raw_id"])

    with connect() as conn:
        init_schema(conn)
        conn.execute("DELETE FROM transactions")
        all_tx.to_sql("transactions", conn, if_exists="append", index=False)
        n = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    return n


if __name__ == "__main__":
    n = load_all()
    print(f"Loaded {n} transactions")
