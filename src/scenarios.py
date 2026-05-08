"""Counterfactual basket scenarios. Edit weights here and rerun `python run.py`."""

from dataclasses import dataclass

# Single source of truth for tradeable tickers.
# Add a new entry here before referencing a ticker in any Scenario.
# divisor: 100.0 for tickers quoted in GBp (pence), 1.0 for GBP.
TICKER_META: dict[str, dict] = {
    "VUAG": {"yahoo": "VUAG.L", "divisor": 1.0},
    "V3AB": {"yahoo": "V3AB.L", "divisor": 1.0},
    "CNX1": {"yahoo": "CNX1.L", "divisor": 100.0},
    "SEGM": {"yahoo": "SEGM.L", "divisor": 1.0},
    "XMWX": {"yahoo": "XMWX.L", "divisor": 1.0},
}


@dataclass(frozen=True)
class Scenario:
    name: str
    weights: dict[str, float]  # ticker -> weight; must sum to 1.0

    def __post_init__(self) -> None:
        unknown = set(self.weights) - set(TICKER_META)
        if unknown:
            raise ValueError(f"Scenario {self.name!r} uses unknown tickers: {unknown}. Add them to TICKER_META first.")
        s = sum(self.weights.values())
        if abs(s - 1.0) > 1e-6:
            raise ValueError(f"Scenario {self.name!r} weights sum to {s}, not 1.0")


SCENARIOS: list[Scenario] = [
    Scenario("S1_v3ab_only", {"V3AB": 1.0}),
    Scenario("S2_vuag_only", {"VUAG": 1.0}),
    Scenario(
        "S3_blend_40_20_20_20",
        {"VUAG": 0.40, "CNX1": 0.20, "SEGM": 0.20, "XMWX": 0.20},
    ),
    Scenario(
        "S4_blend_all_caps_and_all",
        {"V3AB": 0.40, "SEGM": 0.2, "CNX1": 0.15, "VUAG": 0.10, "XMWX": 0.15},
    ),
    Scenario(
        "S5_blend_all_caps_CNX1_heavy",
        {"V3AB": 0.40, "SEGM": 0.15, "CNX1": 0.2, "VUAG": 0.15, "XMWX": 0.1},
    ),
]
