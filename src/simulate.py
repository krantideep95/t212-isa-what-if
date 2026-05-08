"""Walk transactions chronologically and simulate counterfactual basket scenarios."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from src.db import connect
from src.scenarios import Scenario

BUY_ACTIONS = ("Market buy", "Limit buy", "Stop buy")
SELL_ACTIONS = ("Market sell", "Limit sell", "Stop sell")
END_DATE = "2026-05-06"


@dataclass
class SimResult:
    scenario: str
    holdings: dict[str, float] = field(default_factory=dict)  # ticker -> shares
    final_value_gbp: float = 0.0
    n_buys_mirrored: int = 0
    n_sells_mirrored: int = 0
    n_sells_capped: int = 0  # sells where basket value < real-sell GBP


def price_on_or_after(conn: sqlite3.Connection, ticker: str, date: str) -> tuple[str, float] | None:
    """Return (date, open_gbp) for the first available trading day on or after `date`."""
    row = conn.execute(
        "SELECT date, open_gbp FROM prices "
        "WHERE ticker = ? AND date >= ? "
        "ORDER BY date ASC LIMIT 1",
        (ticker, date),
    ).fetchone()
    if row is None:
        return None
    return row["date"], row["open_gbp"]


def simulate(conn: sqlite3.Connection, scenario: Scenario) -> SimResult:
    res = SimResult(scenario=scenario.name)
    holdings = {t: 0.0 for t in scenario.weights}

    txs = conn.execute(
        "SELECT date, action, total_gbp FROM transactions "
        "WHERE action IN ({}) "
        "ORDER BY ts ASC".format(",".join("?" * (len(BUY_ACTIONS) + len(SELL_ACTIONS)))),
        (*BUY_ACTIONS, *SELL_ACTIONS),
    ).fetchall()

    for tx in txs:
        date, action, total_gbp = tx["date"], tx["action"], float(tx["total_gbp"] or 0.0)
        if total_gbp <= 0:
            continue

        if action in BUY_ACTIONS:
            for ticker, weight in scenario.weights.items():
                p = price_on_or_after(conn, ticker, date)
                if p is None:
                    print(f"WARN: no price for {ticker} on/after {date} (buy)")
                    continue
                _, price = p
                holdings[ticker] += (total_gbp * weight) / price
            res.n_buys_mirrored += 1

        elif action in SELL_ACTIONS:
            current_prices: dict[str, float] = {}
            basket_value = 0.0
            for ticker in scenario.weights:
                p = price_on_or_after(conn, ticker, date)
                if p is None:
                    continue
                _, price = p
                current_prices[ticker] = price
                basket_value += holdings[ticker] * price

            if basket_value <= total_gbp:
                holdings = {t: 0.0 for t in scenario.weights}
                res.n_sells_capped += 1
            else:
                fraction = total_gbp / basket_value
                for ticker in scenario.weights:
                    holdings[ticker] *= (1.0 - fraction)
            res.n_sells_mirrored += 1

    # Final valuation at END_DATE.
    final_value = 0.0
    for ticker, shares in holdings.items():
        p = price_on_or_after(conn, ticker, END_DATE)
        if p is None:
            print(f"WARN: no end-date price for {ticker}")
            continue
        _, price = p
        final_value += shares * price
    res.holdings = holdings
    res.final_value_gbp = final_value
    return res


if __name__ == "__main__":
    from src.scenarios import SCENARIOS
    with connect() as conn:
        for s in SCENARIOS:
            r = simulate(conn, s)
            print(f"{r.scenario}: £{r.final_value_gbp:,.2f}  "
                  f"(buys={r.n_buys_mirrored}, sells={r.n_sells_mirrored}, "
                  f"capped={r.n_sells_capped})")
