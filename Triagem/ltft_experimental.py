"""Auditable UFRN LTFT evidence; measurements stay separate from models."""
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

MELLO_2017_REFERENCE = {
    "reference_id": "UFRN-PPGQ-MELLO-2017",
    "title": "Estudo de catalisadores para a produção de combustíveis alternativos: reação de Fischer-Tropsch e síntese de metanol via hidrogenação de CO2",
    "source_url": "https://repositorio.ufrn.br/jspui/handle/123456789/24934",
    "laboratory": "LABPEMOL/UFRN",
    "catalyst_family": "20 wt% Co–0.5 wt% Ru/MOx@Al2O3",
    "temperature_C": 220.0,
    "pressure_bar": 20.0,
    "H2_CO": 2.0,
    "feed_mol_pct": {"CO": 30.0, "H2": 60.0, "Ar": 10.0},
    "initial_GHSV_L_syngas_gcat_h": 6.9,
    "catalyst_mass_g_approx": 1.5,
    "bed_volume_cm3": 6.4,
    "reduction_temperature_C": 400.0,
    "reduction_time_h": 10.0,
    "target_CO_conversion_pct": 40.0,
    "target_CO_conversion_tolerance_pct_points": 5.0,
    "carbon_balance_pct": 100.0,
    "carbon_balance_tolerance_pct_points": 2.0,
    "observation_window_h": "8–16; estabilidade acompanhada até 95 h",
}

MELLO_2017_SELECTIVITY = (
    ("CoRu/AO", 0.6, 14.7, 12.8, 42.0, 30.5, None),
    ("CoRu/YOx@AO", 0.7, 10.1, 25.6, 48.4, 15.9, None),
    ("CoRu/TiOx@AO", 0.5, 14.6, 11.2, 33.7, 40.5, 0.23),
    ("CoRu/TaOx@AO", 0.4, 15.5, 11.5, 32.2, 40.8, None),
    ("CoRu/WOx@AO", 0.8, 19.6, 19.3, 41.4, 19.7, None),
)

BEZERRA_2010_REFERENCE = {
    "reference_id": "UFRN-PPGEQ-BEZERRA-2010",
    "title": "Implementação de um modelo computacional para estudo do processo Fischer-Tropsch em reator de leito de lama",
    "source_url": "https://repositorio.ufrn.br/jspui/handle/123456789/15798",
    "evidence_role": "proveniência de equações; sem estimação de parâmetros",
    "cobalt_rate_equation": "R_FT = k * P_H2^0.7 * P_CO^-0.2",
    "cobalt_k": None,
    "cobalt_wgs_assumption_in_model": "R_WGS = 0",
    "applicability_status": "não_calibrado_para_o_sistema_atual",
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


def mello_selectivity_table():
    """Return carbon selectivity values transcribed from thesis Table S1."""
    columns = ["Catalisador", "CO2_pct", "C1_pct", "C2_C4_pct", "C5_C12_pct", "C13plus_pct", "CTY_mol_CO_gCo_h"]
    table = pd.DataFrame(MELLO_2017_SELECTIVITY, columns=columns)
    # Hydrocarbon fractions are reported on a CO2-free carbon basis and must close to 100%.
    table["fechamento_HC_pct"] = table[["C1_pct", "C2_C4_pct", "C5_C12_pct", "C13plus_pct"]].sum(axis=1)
    return table


def thesis_evidence_readiness():
    """Explain what the theses unlock and what still blocks kinetic calibration."""
    missing = [
        "série multitemperatura de velocidades",
        "parâmetros cinéticos ajustados com unidades",
        "incerteza/covariância dos parâmetros",
        "validação externa do modelo para catalisadores sem Ru",
    ]
    return {
        "experimental_anchor_ready": True,
        "kinetic_calibration_ready": False,
        "missing_fields": missing,
        "reason": "Mello fornece desempenho em uma condição controlada; Bezerra não estimou k para Co.",
    }
