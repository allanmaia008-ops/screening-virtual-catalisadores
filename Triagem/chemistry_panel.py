"""Pure helpers used by the chemistry results panel."""

from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in text if not unicodedata.combining(char)).casefold().strip()


def _find_column(frame: pd.DataFrame, terms: tuple[str, ...]) -> str | None:
    normalized_terms = tuple(_normalize(term) for term in terms)
    for column in frame.columns:
        normalized_column = _normalize(column)
        if all(term in normalized_column for term in normalized_terms):
            return str(column)
    return None


def _candidate_row(frame: pd.DataFrame, formula: str) -> pd.Series | None:
    if frame.empty:
        return None
    formula_column = _find_column(frame, ("formula",))
    if formula_column and formula:
        matches = frame[frame[formula_column].astype(str).map(_normalize) == _normalize(formula)]
        if not matches.empty:
            return matches.iloc[0]
    return frame.iloc[0]


def coke_resistance_score(
    primary: pd.DataFrame,
    *alternatives: pd.DataFrame,
) -> float:
    """Return the available coke-resistance score without inventing zero.

    Result exports have existed with Portuguese, English and advanced-validation
    labels. The candidate formula is used to join the same material across those
    tables. A missing metric remains NaN so the UI can show it as unavailable.
    """
    if primary.empty:
        return float("nan")
    primary_row = primary.iloc[0]
    formula_column = _find_column(primary, ("formula",))
    formula = str(primary_row.get(formula_column, "")) if formula_column else ""
    aliases = (
        ("score", "resistencia", "coque"),
        ("coke", "resistance"),
        ("score", "anti", "coque", "avancado"),
        ("advanced", "anti", "coke", "score"),
    )
    for frame in (primary, *alternatives):
        row = _candidate_row(frame, formula)
        if row is None:
            continue
        one_row = pd.DataFrame([row])
        for terms in aliases:
            column = _find_column(one_row, terms)
            if not column:
                continue
            value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
            if pd.isna(value):
                continue
            numeric = float(value)
            if 1.0 < numeric <= 100.0:
                numeric /= 100.0
            if np.isfinite(numeric):
                return float(np.clip(numeric, 0.0, 1.0))
    return float("nan")


def sabatier_columns(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    """Locate the adsorption-energy and activity columns used by Sabatier plots.

    Notebook exports have used both ``volcano`` and the translated ``vulcão``
    in their headers. English result views are accepted as well.
    """
    energy_aliases = (
        ("energia", "adsorcao", "volcano"),
        ("energia", "adsorcao", "vulcao"),
        ("adsorption", "energy", "volcano"),
        ("volcano", "adsorption", "energy"),
    )
    activity_aliases = (
        ("score", "volcano"),
        ("score", "vulcao"),
        ("taxa", "relativa", "volcano"),
        ("taxa", "relativa", "vulcao"),
        ("relative", "rate", "volcano"),
        ("volcano", "score"),
    )
    energy_column = next((_find_column(frame, terms) for terms in energy_aliases if _find_column(frame, terms)), None)
    activity_column = next((_find_column(frame, terms) for terms in activity_aliases if _find_column(frame, terms)), None)
    return energy_column, activity_column


def kinetic_reference_line(
    rate: pd.Series,
    score: pd.Series,
    points: int = 80,
) -> tuple[np.ndarray, np.ndarray, float] | None:
    """Build a linear visual reference only when both axes vary enough."""
    values = pd.DataFrame(
        {
            "rate": pd.to_numeric(rate, errors="coerce"),
            "score": pd.to_numeric(score, errors="coerce"),
        }
    ).replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 3:
        return None
    x = values["rate"].to_numpy(dtype=float)
    y = values["score"].to_numpy(dtype=float)
    x_span = float(np.ptp(x))
    y_span = float(np.ptp(y))
    x_scale = max(float(np.max(np.abs(x))), 1e-12)
    y_scale = max(float(np.max(np.abs(y))), 1e-12)
    if x_span <= max(x_scale * 1e-6, 1e-12) or y_span <= max(y_scale * 1e-6, 1e-9):
        return None
    slope, intercept = np.polyfit(x, y, 1)
    correlation = float(np.corrcoef(x, y)[0, 1])
    if not all(np.isfinite(value) for value in [slope, intercept, correlation]):
        return None
    x_line = np.linspace(float(x.min()), float(x.max()), points)
    y_line = slope * x_line + intercept
    return x_line, y_line, correlation
