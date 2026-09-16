import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from scientific_pdf_report import _figuras, _selecionar_colunas, gerar_relatorio_cientifico_pdf


class ScientificPdfReportTests(unittest.TestCase):
    def test_semantic_column_selection_does_not_depend_on_csv_order(self):
        frame = pd.DataFrame([{
            "observação": "x",
            "classe_indice_interno_nao_calibrado": "alta",
            "score final": 0.91,
            "fórmula": "NiFe",
        }])
        selected = _selecionar_colunas(frame, [
            ("Fórmula", ("formula",)),
            ("Score final", ("score", "final")),
            ("Classe interna", ("classe", "indice", "interno")),
        ])
        self.assertEqual(list(selected.columns), ["Fórmula", "Score final", "Classe interna"])
        self.assertEqual(selected.iloc[0].tolist(), ["NiFe", 0.91, "alta"])

    def test_all_available_figures_are_collected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            names = []
            for index in range(5):
                path = folder / f"figura_{index}.png"
                path.touch()
                names.append(str(path))
            found = _figuras(pd.DataFrame({"arquivo png": names}), folder)
            self.assertEqual(len(found), 5)

    def test_pdf_separates_internal_class_from_experimental_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            prefix = folder / "execucao"
            ranking = pd.DataFrame([{
                "fórmula": "NiFe", "score final": 0.91,
                "classe_indice_interno_nao_calibrado": "alta",
                "probabilidade Monte Carlo de ficar no top 5": 0.8,
                "validacao_experimental": "Não disponível nesta execução",
                "suporte sugerido": "Al2O3",
            }])
            ranking.to_csv(prefix.with_name("ranking.csv"), index=False, encoding="utf-8-sig")
            ranking.to_csv(prefix.with_name("prioritarios.csv"), index=False, encoding="utf-8-sig")
            for name in ("metricas", "monte_carlo", "dominio", "figuras"):
                pd.DataFrame().to_csv(prefix.with_name(f"{name}.csv"), index=False, encoding="utf-8-sig")
            summary = prefix.with_name("resumo.json")
            summary.write_text(json.dumps({"n_candidatos_gerados": 100}), encoding="utf-8")
            paths = {
                "pdf": prefix.with_name("relatorio.pdf"), "ranking": prefix.with_name("ranking.csv"),
                "prioritarios": prefix.with_name("prioritarios.csv"), "metricas": prefix.with_name("metricas.csv"),
                "monte_carlo": prefix.with_name("monte_carlo.csv"), "dominio": prefix.with_name("dominio.csv"),
                "figuras": prefix.with_name("figuras.csv"), "resumo": summary,
            }
            generated = gerar_relatorio_cientifico_pdf(paths, "reforma", ["Ni", "Fe"], "")
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(generated)).pages)
            self.assertIn("Candidatos gerados: 100", text)
            self.assertIn("Classe interna não calibrada: alta", text)
            self.assertIn("Validação experimental: Não disponível nesta execução", text)


if __name__ == "__main__":
    unittest.main()
