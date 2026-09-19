import ast
import unittest
from pathlib import Path


class SidebarReactionTests(unittest.TestCase):
    def test_reaction_selector_is_not_hidden_in_popover(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertNotIn('with st.popover("Reação"', source)
        self.assertIn('reacao = st.selectbox(', source)
        self.assertIn('key="config_reacao"', source)

    def test_only_supported_reactions_are_offered_and_empty_results_message_is_removed(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn('nomes_reacao = {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}', source)
        self.assertNotIn("Execute a triagem para visualizar e baixar os resultados desta sessão.", source)

    def test_english_mode_covers_sidebar_and_generated_components(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn("def ativar_traducao_streamlit()", source)
        self.assertIn('ativar_traducao_streamlit()', source.split('st.set_page_config', 1)[1])
        self.assertIn('"Configurações da Triagem": "Screening settings"', source)
        self.assertIn('"Reação-alvo": "Target reaction"', source)
        self.assertIn('"Número de metais ativos": "Number of active metals"', source)
        self.assertIn('"Sem promotor": "Without promoter"', source)
        self.assertIn('setattr(DeltaGenerator, "dataframe", wrapper_dataframe)', source)
        self.assertIn('setattr(DeltaGenerator, "plotly_chart", wrapper_plotly)', source)
        self.assertIn('setattr(DeltaGenerator, "tabs", wrapper_tabs)', source)

    def test_translation_preserves_embedded_base64_images(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn('re.sub(r"data:[^\\s\'\\"<>]+", proteger_recurso, valor)', source)
        self.assertIn('traduzido.replace(f"__CATAILAB_RESOURCE_{indice}__", recurso)', source)
        self.assertIn('texto = re.sub(r"data:[^\\s\'\\"<>]+", proteger_recurso, texto)', source)
        self.assertIn('texto.replace(f"__CATAILAB_EMBEDDED_{indice}__", recurso)', source)

    def test_candidate_cards_and_audit_have_english_translations(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        expected = [
            '"Origem dos resultados e justificativa da classificação interna": "Result provenance and internal-classification rationale"',
            '"Representações esquemáticas: as cores distinguem visualmente os candidatos e suas fases; não correspondem a geometrias estruturais calculadas por DFT.": "Schematic representations:',
            '"Fórmula": "Formula"',
            '"Composição do score": "Score composition"',
            '"Classificação<br>interna": "Internal<br>classification"',
            '"impregnacao incipiente do metal ativo em suporte de alta area": "incipient-wetness impregnation',
        ]
        for fragment in expected:
            self.assertIn(fragment, source)

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
        self.assertIn('max-height: calc(100dvh - 16px)', source)
        self.assertIn('transform: translate(-50%, -50%)', source)
        self.assertIn('overflow-y: auto', source)
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

    def test_candidates_show_internal_classification_without_calibration_claim(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertIn('"Classificação interna": internal_classification(linha)', source)
        self.assertIn("Classificação interna não calibrada", source)
        self.assertIn("def extrair_validacao_experimental", source)
        self.assertIn("Status independente da classificação interna", source)
        self.assertNotIn('return "não validada experimentalmente"', source)
        self.assertIn('"unknown")', source)

    def test_scientific_report_is_pdf_only_in_download_panel(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        report_source = Path(__file__).with_name("scientific_pdf_report.py").read_text(encoding="utf-8")
        self.assertIn('("relatorio", paths["pdf"]', source)
        self.assertNotIn('("relatorio", paths["html"]', source)
        self.assertIn('".pdf": "application/pdf"', source)
        self.assertIn("Apêndice de reprodutibilidade", report_source)
        self.assertNotIn("Referências bibliográficas", report_source)

    def test_local_background_execution_has_queue_progress_and_no_cache_reuse(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        jobs = Path(__file__).with_name("triage_jobs.py").read_text(encoding="utf-8")
        worker = Path(__file__).with_name("triage_worker.py").read_text(encoding="utf-8")
        self.assertIn("start_worker", source)
        self.assertIn("@st.fragment(run_every=2)", source)
        self.assertIn("catialab-loading-spinner", source)
        self.assertIn("html.escape(etapa_exibida)", source)
        self.assertNotIn("A configuração permanece bloqueada até a execução terminar.", source)
        self.assertIn("disabled=not configuracao_pronta or job_ativo", source)
        self.assertIn("Apenas uma execução pesada", source)
        self.assertIn("max_age_hours=24", source)
        self.assertIn("subprocess.Popen", jobs)
        self.assertIn("O_CREAT | os.O_EXCL", worker)
        self.assertNotIn("Usar resultado existente", source)

    def test_progress_fragment_does_not_reference_figure_locals(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        progress_names = {
            node.id for node in ast.walk(functions["mostrar_progresso_job"])
            if isinstance(node, ast.Name)
        }
        self.assertNotIn("figuras_df", progress_names)
        self.assertNotIn("coluna_png", progress_names)
        self.assertNotIn("explicacoes", progress_names)
        figures_names = {
            node.id for node in ast.walk(functions["mostrar_figuras"])
            if isinstance(node, ast.Name)
        }
        self.assertIn("figuras_df", figures_names)
        self.assertIn("coluna_png", figures_names)

    def test_english_progress_and_generated_panels_are_localized(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        worker = Path(__file__).with_name("triage_worker.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        translations = next(
            ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "TRADUCOES_EN" for target in node.targets)
        )
        worker_tree = ast.parse(worker)
        stages = next(
            ast.literal_eval(node.value) for node in worker_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "STAGES" for target in node.targets)
        )
        for stage in stages:
            self.assertIn(stage, translations)
        for label in (
            "Em andamento:", "Progresso da triagem:", "Metais de transição",
            "Instruções e cálculo para síntese", "Alternativa sugerida pela triagem",
            "Temperatura recomendada", "janela:", "Procedimento de síntese",
            "R² (validação)", "Nota importante", "Como interpretar",
            "Gráficos complementares gerados pela execução", "Calcular quantidades",
        ):
            self.assertIn(label, translations)
        self.assertIn('st.progress(progresso, text=_traduzir_interface(', source)
        self.assertIn('st.progress(0, text=_traduzir_interface(', source)
        self.assertIn('def _traduzir_tabela_visual(dados):', source)
        self.assertIn('def _traduzir_figura_visual(dados):', source)
        self.assertIn('def figura_suplementar_ingles(', source)
        self.assertIn('figura_inglesa = figura_suplementar_ingles(', source)
        self.assertIn('st.plotly_chart(figura_inglesa,', source)
        self.assertIn('titulo_arquivo = titulos_arquivos.get(', source)
        self.assertIn('format_func=t, key="sintese_rota"', source)
        self.assertIn('etapa_exibida = str(_traduzir_interface(etapa))', source)

    def test_research_collaboration_citation_and_no_lattes_button(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        research = source.split('elif pagina == "pesquisa":', 1)[1].split('elif pagina == "contato":', 1)[0]
        self.assertIn("Renata Martins Braga", research)
        self.assertIn("BRAGA, Renata Martins", research)
        self.assertNotIn("st.link_button", research)


if __name__ == "__main__":
    unittest.main()
