import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE = Path(__file__).with_name("hierarchical_score_code.py").read_text(encoding="utf-8")
NAMESPACE = {"np": np, "pd": pd}
exec(compile(SOURCE.split("score_hierarquico_comparativo_df =")[0], "<hierarchical-score>", "exec"), NAMESPACE)
calculate = NAMESPACE["calcular_score_hierarquico"]


class HierarchicalScoreTests(unittest.TestCase):
    def test_complete_notebook_stage_preserves_metrics(self):
        import json
        notebook = json.loads(Path(__file__).with_name(
            "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
        ).read_text(encoding="utf-8"))
        embedded = next("".join(cell["source"]) for cell in notebook["cells"]
                        if cell["cell_type"] == "code" and
                        "def calcular_score_hierarquico" in "".join(cell["source"]))
        for source in (SOURCE, embedded):
            for reaction in ("reforma", "metanacao", "rwgs"):
                with self.subTest(reaction=reaction, embedded=source is embedded):
                    metrics = [{"grupo": "anterior", "valor": 100}]
                    def add(group, name, value, unit, interpretation):
                        metrics.append(dict(grupo=group, metrica=name, valor=value,
                                            unidade=unit, interpretacao=interpretation))
                    namespace = dict(np=np, pd=pd, reacao=reaction,
                        melhor_por_candidato_df=self.fixture(),
                        prioritarios_df=self.fixture().head(1),
                        linhas_metricas_triagem=metrics, adicionar_metrica=add,
                        display=lambda _: None)
                    exec(compile(source, "<complete-stage>", "exec"), namespace)
                    self.assertEqual(len(namespace["metricas_triagem_df"]), 2)
                    self.assertEqual(namespace["metricas_triagem_df"].iloc[-1]["grupo"],
                                     "score_hierarquico")

    def fixture(self):
        common = dict(score_final=.8, score_estabilidade=.8, score_redox=.8,
            score_redox_operando=.8, score_basicidade=.8, score_estabilidade_termica_operando=.8,
            score_atividade=.8, score_seletividade=.8, score_equilibrio_adsorcao=.8,
            score_compatibilidade_suporte=.8, score_interface_metal_suporte=.8,
            conversao_prevista_pct=80, seletividade_produto_prevista_pct=80,
            score_faixa_condicao=.8, score_anti_coque_avancado=.8, score_formacao_fase_ativa=.8,
            score_transporte=.9, risco_sinterizacao="baixo", fonte_estabilidade_triagem="MP",
            material_id="mp-1", matminer_usado=True, suporte_sugerido="MgAl2O4",
            rota_sintese_sugerida="impregnação", precursor_sugerido="nitrato",
            pretratamento_sugerido="calcinação", carga_metalica_pct_massa=10)
        good = dict(common, formula="NiFe-good", classe_dominio_aplicabilidade="dentro_do_dominio")
        bad = dict(common, formula="NiFe-bad", classe_dominio_aplicabilidade="fora_do_dominio",
            score_anti_coque_avancado=.2, score_transporte=.2, risco_sinterizacao="alto",
            suporte_sugerido="MgO ou Al2O3", rota_sintese_sugerida="", precursor_sugerido="",
            pretratamento_sugerido="", carga_metalica_pct_massa=np.nan)
        return pd.DataFrame([good, bad])

    def test_penalties_lower_incomplete_out_of_domain_candidate(self):
        result = calculate(self.fixture(), "reforma").set_index("formula")
        self.assertGreater(result.loc["NiFe-good", "score_hierarquico_proposto"], result.loc["NiFe-bad", "score_hierarquico_proposto"])
        self.assertEqual(result.loc["NiFe-bad", "penalidade_h_dominio"], 1.0)
        self.assertEqual(result.loc["NiFe-bad", "penalidade_h_incompletude"], 1.0)

    def test_is_parallel_and_bounded(self):
        source = self.fixture()
        result = calculate(source, "reforma")
        self.assertTrue(result.score_hierarquico_proposto.between(0, 1).all())
        self.assertTrue((source.score_final == .8).all())
        self.assertTrue((result.metodo_score_hierarquico == "técnico-heurístico sem calibração experimental").all())

    def test_no_promoter_has_redistributed_weights(self):
        source = self.fixture().head(1).assign(candidato_com_promotor=False)
        result = calculate(source, "reforma")
        self.assertTrue(pd.isna(result.loc[0, "score_h_funcao_promotor"]))


if __name__ == "__main__":
    unittest.main()
