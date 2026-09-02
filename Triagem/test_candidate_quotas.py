from __future__ import annotations

import ast
import contextlib
import io
import re
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd


NOTEBOOK = Path(__file__).with_name("notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb")


def code_cell_containing(notebook, marker: str) -> str:
    for cell in notebook.cells:
        if cell.cell_type == "code" and marker in cell.source:
            return cell.source
    raise AssertionError(f"Célula não encontrada: {marker}")


def run_generation(source: str, metals: list[str], promoter: str) -> pd.DataFrame:
    namespace = {
        "np": np,
        "pd": pd,
        "reacao": "reforma",
        "metais_usuario": metals,
        "promotor_usuario": promoter,
    }
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, "<candidate-generation>", "exec"), namespace)
    candidates = namespace["candidatos_df"]
    assert len(candidates) == 1000
    complete = int(candidates["candidato_configuracao_completa"].sum())
    assert complete >= 300, (metals, complete)
    assert candidates.loc[candidates["candidato_configuracao_completa"], "formula"].map(
        lambda value: set(metals + [promoter]).issubset(set(re.findall(r"[A-Z][a-z]?", value)))
    ).all()
    complete_candidates = candidates.loc[candidates["candidato_configuracao_completa"]].copy()
    fractions = complete_candidates["formula"].map(
        lambda formula: {
            element: float(value or 1.0)
            for element, value in re.findall(r"([A-Z][a-z]?)([0-9]+(?:\.[0-9]+)?)?", formula)
        }
    )
    for metal in metals:
        values = fractions.map(lambda composition: composition[metal])
        assert values.nunique() >= 20, (metal, values.nunique())
        assert values.max() - values.min() >= 0.40, (metal, values.min(), values.max())
    promoter_values = fractions.map(lambda composition: composition[promoter])
    assert promoter_values.min() <= 0.05
    assert promoter_values.max() >= 0.30
    return candidates


def extract_function(source: str, name: str) -> str:
    tree = ast.parse(source)
    node = next(
        item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    return ast.get_source_segment(source, node)


def test_selector(source: str) -> None:
    function_source = extract_function(source, "selecionar_com_representacao_multimetal")
    namespace = {
        "np": np,
        "pd": pd,
        "metais_usuario": ["Ni", "Co", "Fe"],
        "promotor_usuario": "Mg",
    }
    exec(compile(function_source, "<quota-selector>", "exec"), namespace)
    selector = namespace["selecionar_com_representacao_multimetal"]
    frame = pd.DataFrame(
        {
            "formula": [f"incomplete-{i}" for i in range(70)] + [f"complete-{i}" for i in range(30)],
            "score": np.linspace(1.0, 0.0, 100),
            "candidato_configuracao_completa": [False] * 70 + [True] * 30,
            "candidato_com_todos_metais_ativos": [False] * 70 + [True] * 30,
            "candidato_com_promotor": [False] * 70 + [True] * 30,
        }
    )
    selected_100 = selector(frame, 100, "score", fracao_minima_configuracao_completa=0.30)
    selected_10 = selector(frame, 10, "score", fracao_minima_configuracao_completa=0.30)
    assert int(selected_100["candidato_configuracao_completa"].sum()) == 30
    assert int(selected_10["candidato_configuracao_completa"].sum()) >= 3


def test_local_property_matching(source: str) -> None:
    function_source = extract_function(source, "buscar_propriedade_local")
    namespace = {
        "pd": pd,
        "base_local": pd.DataFrame(
            {
                "formula": ["Mg14CoNi", "Ni0.50Co0.50"],
                "material_id": ["mp-analogo", "local-exato"],
                "origem": ["MP", "local"],
                "score_multicriterio_v2": [0.9, 0.8],
                "energy_above_hull": [0.42, 0.01],
            }
        ),
        "elementos_formula": lambda formula: set(re.findall(r"[A-Z][a-z]?", str(formula))),
    }
    exec(compile(function_source, "<local-property-matching>", "exec"), namespace)
    match = namespace["buscar_propriedade_local"]
    exact = match("Ni0.50Co0.50")
    analogous = match("Ni0.25Co0.25Fe0.25Mg0.25")
    assert exact["tipo_correspondencia_local"] == "exata"
    assert exact["energy_above_hull"] == 0.01
    assert analogous["tipo_correspondencia_local"] == "analoga"
    assert analogous["formula_analoga"] == "Mg14CoNi"
    assert "energy_above_hull" not in analogous


def main() -> None:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    generation = code_cell_containing(notebook, "N_CANDIDATOS_GERADOS_FUNIL = 1000")
    selector_cell = code_cell_containing(notebook, "def selecionar_com_representacao_multimetal(")
    property_cell = code_cell_containing(notebook, "def buscar_propriedade_local(formula):")
    two_metals = run_generation(generation, ["Ni", "Co"], "Mg")
    three_metals = run_generation(generation, ["Ni", "Co", "Fe"], "Mg")
    test_selector(selector_cell)
    test_local_property_matching(property_cell)
    print(
        {
            "two_metals_complete": int(two_metals["candidato_configuracao_completa"].sum()),
            "three_metals_complete": int(three_metals["candidato_configuracao_completa"].sum()),
            "two_metals_total": len(two_metals),
            "three_metals_total": len(three_metals),
            "selector_quota": "ok",
            "analog_property_isolation": "ok",
        }
    )


if __name__ == "__main__":
    main()
