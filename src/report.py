"""Build the final Markdown comparison report."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.actual import actual_value_gbp, total_deposited_gbp
from src.db import connect
from src.scenarios import SCENARIOS
from src.simulate import simulate, END_DATE
from src.xirr import xirr

REPORT_PATH = Path(__file__).parent.parent / "report.md"


def cashflow_history(conn) -> list[tuple]:
    """All Deposit/Withdrawal cashflows. Sign convention:
       deposit = -amount (out of pocket), withdrawal = +amount."""
    rows = conn.execute(
        "SELECT date, action, total_gbp FROM transactions "
        "WHERE action IN ('Deposit', 'Withdrawal') ORDER BY date"
    ).fetchall()
    out = []
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        amt = float(r["total_gbp"])
        out.append((d, -amt if r["action"] == "Deposit" else +amt))
    return out


def _weights_str(weights: dict[str, float]) -> str:
    return ", ".join(f"{t} {int(w*100)}%" for t, w in weights.items())


def build_report() -> str:
    lines: list[str] = []
    lines.append(f"# Counterfactual ETF basket comparison (as of {END_DATE})\n")
    lines.append("| Scenario | Allocation | Final value (£) | MWR (XIRR) | Net deposited (£) |")
    lines.append("|---|---|---:|---:|---:|")

    with connect() as conn:
        cfs = cashflow_history(conn)
        net_dep = total_deposited_gbp(conn)
        end = datetime.strptime(END_DATE, "%Y-%m-%d").date()

        # Actual portfolio row.
        actual_val = actual_value_gbp()
        actual_xirr = xirr(cfs + [(end, +actual_val)])
        lines.append(
            f"| **Actual portfolio** | (real picks) | {actual_val:,.2f} | {actual_xirr*100:.2f}% | {net_dep:,.2f} |"
        )

        # Counterfactual scenario rows.
        for s in SCENARIOS:
            r = simulate(conn, s)
            r_xirr = xirr(cfs + [(end, +r.final_value_gbp)])
            lines.append(
                f"| {s.name} | {_weights_str(s.weights)} | {r.final_value_gbp:,.2f} | {r_xirr*100:.2f}% | {net_dep:,.2f} |"
            )

    lines.append("")
    lines.append("**Notes:**")
    lines.append("- Counterfactual sells capped at available basket value when basket < real-sell GBP.")
    lines.append("- Real dividends ignored (target ETFs are accumulating).")
    lines.append("- Buy-date price uses next available trading day's open if missing.")
    lines.append("- See `src/scenarios.py` to edit weights and rerun.")
    return "\n".join(lines)


if __name__ == "__main__":
    md = build_report()
    REPORT_PATH.write_text(md)
    print(md)
    print(f"\nWrote {REPORT_PATH}")
