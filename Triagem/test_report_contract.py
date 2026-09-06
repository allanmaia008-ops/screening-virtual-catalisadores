import ast
import json
import unittest
from pathlib import Path

import pandas as pd
from report_contract import audited_export, output_prefix, support_alternatives


class ReportContractTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(output_prefix("reforma", ["Ni"], "Fe"), "catailab_reforma-CH4-CO2_Ni_promotor-Fe")
        self.assertIn("La-Ni_sem-promotor", output_prefix("reforma", ["La", "Ni"], ""))

    def test_no_false_evidence(self):
        source = pd.DataFrame([dict(formula="Ni0.71Fe0.29", score_incerteza=.997,
            confiabilidade="alta", classe_dominio_aplicabilidade="fora_do_dominio",
            fonte_estabilidade_triagem="GNN_local_proxy", suporte_sugerido="MgAl2O4 ou Al2O3",
            rendimento_ou_produtividade_prevista_pct=37.2)])
        out = audited_export(source, "reforma").iloc[0]
        self.assertNotIn("score_incerteza", out.index)
        self.assertFalse(out.gnn_execucao_comprovada)
        self.assertIn("heurística", out.fonte_estabilidade_triagem)
        self.assertIn("Extrapolação", out.aviso_dominio)
        self.assertIn("Não definido", out.suporte_sugerido)
        self.assertTrue(pd.isna(out.rendimento_H2_validado_pct))
        self.assertIn("score_incerteza", source.columns)

    def test_valid_gnn(self):
        df = pd.DataFrame([dict(formula="Ni", fonte_estabilidade_triagem="GNN_local_proxy",
            modelo_gnn_local="CHGNet", energia_gnn_eV_atom=-3.1, gnn_local_usado=True)])
        self.assertTrue(audited_export(df, "reforma").iloc[0].gnn_execucao_comprovada)

    def test_alternatives_are_not_combined_materials(self):
        df = pd.DataFrame([dict(formula="Ni", suporte_sugerido="MgO-Al2O3, MgAl2O4 ou La2O3-Al2O3")])
        out = support_alternatives(df)
        self.assertEqual(len(out), 3)
        self.assertEqual(out.suporte.iloc[1], "MgAl2O4")
        self.assertTrue(out.carga_metalica_pct_massa.isna().all())

    def test_export_cell_uses_contract(self):
        nb = json.loads(Path(__file__).with_name("notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb").read_text(encoding="utf-8"))
        sources = [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
        export = next(s for s in sources if 'def traduzir_colunas' in s)
        tree = ast.parse(export)
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'traduzir_colunas']
        from report_contract import EXPORT_LABELS
        env = dict(audited_export=audited_export, reacao='reforma', nomes_colunas_pt={}, EXPORT_LABELS=EXPORT_LABELS)
        exec(compile(ast.Module(body=selected, type_ignores=[]), '<export>', 'exec'), env)
        out = env['traduzir_colunas'](pd.DataFrame([{'formula':'Ni','score_incerteza':.99,'score_final':.5}]))
        self.assertNotIn('score_incerteza', out)
        self.assertIn('Score final de priorização (0–1; não é probabilidade)', out)

    def test_notebook_syntax(self):
        nb = json.loads(Path(__file__).with_name("notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb").read_text(encoding="utf-8"))
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                ast.parse(''.join(cell['source']))


if __name__ == "__main__":
    unittest.main()
