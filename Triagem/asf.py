"""Ideal ASF distribution, conditional on hydrocarbon formation.

alpha is an input, not a prediction from catalyst or operating conditions.
Carbon fractions n*(1-alpha)^2*alpha**(n-1) are not exact paraffin mass fractions.
"""
import math
from numbers import Integral, Real


def validate_alpha(alpha):
    if isinstance(alpha, bool) or not isinstance(alpha, Real) or not math.isfinite(alpha) or not 0 <= alpha < 1:
        raise ValueError("alpha must be finite and satisfy 0 <= alpha < 1")
    return float(alpha)


def _integer(n):
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("Carbon number must be a positive integer")


def tail_fraction(alpha, start, basis="carbon"):
    """Exact infinite tail, including start; no finite-grid renormalization."""
    a = validate_alpha(alpha)
    _integer(start)
    if basis not in {"carbon", "molar", "paraffin_mass"}:
        raise ValueError("Unknown fraction basis")
    molar = a ** (start - 1)
    carbon = molar * (1 + (start - 1) * (1 - a))
    if basis == "molar":
        return molar
    if basis == "carbon":
        return carbon
    # CnH(2n+2): M(n) = (MC+2MH)*n + 2MH.
    unit, ends = 12.011 + 2 * 1.008, 2 * 1.008
    return (unit * carbon + ends * (1-a) * molar) / (unit + ends * (1-a))


def band_fraction(alpha, start, end=None, basis="carbon"):
    _integer(start)
    if end is not None:
        _integer(end)
        if end < start:
            raise ValueError("end must be >= start")
    return max(0.0, tail_fraction(alpha, start, basis) - (tail_fraction(alpha, end+1, basis) if end is not None else 0.0))


def distribution(alpha, max_carbon=60, basis="carbon"):
    """Return finite plotting rows and an explicit remainder through infinity."""
    a = validate_alpha(alpha)
    _integer(max_carbon)
    if max_carbon > 10000:
        raise ValueError("max_carbon must not exceed 10000")
    rows = [{"carbon_number": n, "fraction": band_fraction(a, n, n, basis)} for n in range(1, max_carbon+1)]
    groups = {name: band_fraction(a, low, high, basis) for name, low, high in
              [("CH4", 1, 1), ("C2-C4", 2, 4), ("C5-C11", 5, 11), ("C12+", 12, None)]}
    return {"alpha": a, "basis": basis, "model": "ideal_ASF_user_supplied_alpha",
            "rows": rows, "tail_start": max_carbon+1,
            "tail_fraction": tail_fraction(a, max_carbon+1, basis),
            "exclusive_groups": groups, "C5plus_subtotal": tail_fraction(a, 5, basis),
            "closure_error": abs(math.fsum(groups.values())-1.0)}


def aviation_screen(alpha, jet_min=8, jet_max=16, basis="carbon"):
    """Configurable carbon-number cut, not aviation-fuel qualification."""
    _integer(jet_min)
    _integer(jet_max)
    if jet_min < 2 or jet_max < jet_min:
        raise ValueError("Require 2 <= jet_min <= jet_max")
    return {"alpha": validate_alpha(alpha), "basis": basis,
            "cut_definition": f"C{jet_min}-C{jet_max} (screening convention)",
            "lighter_fraction": band_fraction(alpha, 1, jet_min-1, basis),
            "direct_cut_fraction": band_fraction(alpha, jet_min, jet_max, basis),
            "heavy_feed_fraction": tail_fraction(alpha, jet_max+1, basis),
            "upgraded_jet_yield": None, "fuel_qualification": "not_assessed"}
