import unittest
from pathlib import Path


class SidebarReactionTests(unittest.TestCase):
    def test_reaction_selector_is_not_hidden_in_popover(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertNotIn('with st.popover("Reação"', source)
        self.assertIn('reacao = st.selectbox(', source)
        self.assertIn('key="config_reacao"', source)

    def test_metal_count_is_direct_and_output_folder_is_hidden(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertNotIn('with st.popover("Número de metais ativos"', source)
        self.assertIn('n_metais_selecionado = st.selectbox(', source)
        self.assertNotIn('with st.popover("Pasta de saída"', source)
        self.assertNotIn('output_dir_texto', source)
        self.assertIn('output_dir = DEFAULT_OUTPUT_DIR.resolve()', source)

    def test_sidebar_labels_are_centered_and_promoter_choice_is_visible(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn(".catialab-sidebar-field-label", source)
        self.assertIn("text-align: center", source)
        self.assertIn("font-weight: 800", source)
        self.assertNotIn('with st.popover("Promotor"', source)
        self.assertIn('modo_promotor = st.radio(', source)
        self.assertIn('if modo_promotor == "Com promotor":', source)

    def test_sidebar_has_compact_status_and_guarded_run_button(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn(".catialab-config-row", source)
        self.assertIn(".step-ok", source)
        self.assertIn("configuracao_pronta =", source)
        self.assertIn("disabled=not configuracao_pronta", source)
        self.assertIn('st.caption("Para executar, complete: "', source)
        self.assertIn("position: fixed", source)
        self.assertIn("margin-top: -38px", source)
        self.assertIn("min-height: 24px", source)
        self.assertIn("padding-bottom: 76px", source)

    def test_periodic_table_uses_compact_full_grid(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn('min-width: 540px', source)
        self.assertIn('min-height: 25px', source)
        self.assertIn('max-height: none', source)
        self.assertIn("METAIS_ATIVOS_TRIAGEM", source)
        self.assertIn("ELEMENTOS_PROMOTORES_TRIAGEM", source)
        self.assertIn("periodic-legend", source)
        self.assertIn("disabled=not disponivel", source)
        self.assertIn('"Ac", "Th", "Pa", "U"', source)
        self.assertIn('"Rf", "Db", "Sg", "Bh"', source)
        self.assertIn("FAMILIAS_TABELA_PERIODICA", source)
        self.assertIn("periodic-family-legend", source)
        self.assertIn("periodic-family-marker", source)
        self.assertIn("contorno verde + ✓", source)
        self.assertIn(":has(.family-lantanideo) button[kind=\"tertiary\"]::before", source)
        self.assertIn("display:none!important", source)
        self.assertIn("NUMERO_ATOMICO", source)
        self.assertIn("ELEMENTOS_RADIOATIVOS", source)
        self.assertIn("ELEMENTOS_SINTETICOS", source)
        self.assertIn("ELEMENTOS_TOXICIDADE_ELEVADA", source)
        self.assertIn("element-risk-marker", source)
        self.assertIn("cobertura:", source)

    def test_results_explain_ranking_and_mobile_layout(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn("Por que ficou bem posicionado", source)
        self.assertIn("Limitações e penalidades", source)
        self.assertIn("Origem e tipo dos dados", source)
        self.assertIn('@media(max-width:700px)', source)
        self.assertIn('div[data-testid="stPills"]{overflow-x:auto', source)
        self.assertIn(".validation-kpi .validation-kpi-icon", source)
        self.assertIn('(\"±\", texto(\"RMSE CV', source)
        self.assertIn('(\"◎\", texto(\"Dentro do domínio', source)

    def test_scientific_report_is_pdf_only_in_download_panel(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        report_source = Path(__file__).with_name("scientific_pdf_report.py").read_text(encoding="utf-8")
        self.assertIn('("relatorio", paths["pdf"]', source)
        self.assertNotIn('("relatorio", paths["html"]', source)
        self.assertIn('".pdf": "application/pdf"', source)
        self.assertIn("Apêndice de reprodutibilidade", report_source)
        self.assertNotIn("Referências bibliográficas", report_source)


if __name__ == "__main__":
    unittest.main()
