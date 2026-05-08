"""End-to-end: load → prices → simulate → report."""

from src.db import connect, init_schema
from src.load_transactions import load_all as load_tx
from src.load_prices import load_from_transactions, fill_from_yfinance
from src.report import build_report, REPORT_PATH


def main() -> None:
    with connect() as conn:
        init_schema(conn)

    n_tx = load_tx()
    print(f"Transactions loaded: {n_tx}")

    with connect() as conn:
        n1 = load_from_transactions(conn)
        print(f"Prices from transactions: {n1}")
        n2 = fill_from_yfinance(conn)
        print(f"Prices from yfinance:     {n2}")

    md = build_report()
    REPORT_PATH.write_text(md)
    print()
    print(md)
    print(f"\nWrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
