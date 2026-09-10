"""Experimental LTFT anchor from PI.012; no kinetic extrapolation."""
import math

import pandas as pd


# Stores only values explicitly reported in the complete PI.012 conference paper.
PI012_REFERENCE = {
    "reference_id": "CBCAT-2023-PI.012",
    "title": "Desenvolvimento de catalisador a base de Cobalto para produção de Combustível Sustentável de Aviação pela rota Fischer-Tropsch",
    "source_url": "https://submissao.22cbcat.sbcat.org/index.php/2023-cbcat/article/view/11",
    "catalyst": "20% Co/γ-Al2O3",
    "temperature_C": 220.0,
    "pressure_bar": 20.0,
    "H2_CO": 2.0,
    "GHSV_h-1": 500.0,
    "reported_operation_h": 192.0,
    "water_g_h": 0.3,
    "light_C8_C16_g_h": 0.3,
    "heavy_liquids_g_h": 0.2,
    "deactivation_observed": False,
}

# Enumerates the fields absent from PI.012 that prevent intrinsic-rate calibration.
KINETIC_REQUIRED_FIELDS = (
    "CO_conversion_pct",
    "H2_conversion_pct",
    "absolute_feed_flow_mol_h",
    "catalyst_mass_g",
    "bed_volume_mL",
    "gas_product_distribution",
    "liquid_carbon_number_distribution",
    "carbon_balance_pct",
    "rate_equation",
    "fitted_parameters_with_units",
    "parameter_uncertainty",
)


def observed_totals(hours, reference=PI012_REFERENCE):
    """Integrate reported average production rates only inside the observed run."""
    hours = float(hours)
    # Reject non-finite, negative, or extrapolated durations instead of inventing kinetics.
    if not math.isfinite(hours) or not 0 <= hours <= reference["reported_operation_h"]:
        raise ValueError("Use duração entre 0 e 192 h, limitada ao período experimental reportado.")
    rows = [
        ("Água", reference["water_g_h"]),
        ("Hidrocarbonetos leves C8-C16", reference["light_C8_C16_g_h"]),
        ("Hidrocarbonetos líquidos pesados", reference["heavy_liquids_g_h"]),
    ]
    # Multiplication by time is an integration of the reported mean, not a rate-law fit.
    return pd.DataFrame(
        {"Fração": [name for name, _ in rows],
         "Produção média reportada (g/h)": [rate for _, rate in rows],
         "Massa no período (g)": [rate * hours for _, rate in rows]}
    )


def kinetic_readiness(reference=PI012_REFERENCE):
    """Return an auditable gate explaining why conversion/rates remain unavailable."""
    missing = [field for field in KINETIC_REQUIRED_FIELDS if reference.get(field) is None]
    return {
        "ready": not missing,
        "missing_fields": missing,
        "CO_conversion_pct": reference.get("CO_conversion_pct"),
        "physical_productivity": None,
        "WGS_extent": None,
        "status": "bloqueado_por_dados_incompletos" if missing else "pronto_para_calibracao",
    }

