"""Money-weighted return (XIRR)."""

from __future__ import annotations

from datetime import date

from scipy.optimize import brentq


def xirr(cashflows: list[tuple[date, float]]) -> float:
    """Cashflows: list of (date, amount). Negative = money in, positive = money out / final value."""
    if not cashflows:
        raise ValueError("No cashflows")
    cashflows = sorted(cashflows, key=lambda x: x[0])
    t0 = cashflows[0][0]

    def npv(rate: float) -> float:
        s = 0.0
        for d, cf in cashflows:
            years = (d - t0).days / 365.0
            s += cf / (1.0 + rate) ** years
        return s

    try:
        return brentq(npv, -0.99, 10.0, xtol=1e-7)
    except ValueError as e:
        raise ValueError(f"XIRR did not converge: {e}") from e
