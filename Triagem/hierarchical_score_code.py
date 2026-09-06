# Score hierárquico técnico-heurístico, calculado em paralelo ao ranking vigente.
# Os pesos não foram calibrados contra dados experimentais e não representam probabilidades.

PESOS_SCORE_HIERARQUICO = {
    "material": 0.40,
    "catalise": 0.30,
    "operacao": 0.15,
    "sintese": 0.15,
}
PESOS_PENALIZACOES_HIERARQUICAS = {
    "dominio": 0.10,
    "coque": 0.08,
    "sinterizacao": 0.06,
    "transporte": 0.04,
    "incompletude": 0.02,
}


def _h_num(row, coluna, padrao=0.5):
    valor = pd.to_numeric(pd.Series([row.get(coluna, padrao)]), errors="coerce").iloc[0]
    return float(np.clip(padrao if pd.isna(valor) else valor, 0.0, 1.0))


def _h_risco_classe(valor):
    texto = str(valor).strip().lower()
    return {"baixo": 0.0, "moderado": 0.5, "medio": 0.5, "médio": 0.5, "alto": 1.0}.get(texto, 0.5)


def _h_promotor_presente(row):
    valor = row.get("candidato_com_promotor", False)
    return bool(valor is True or str(valor).strip().lower() in {"true", "1", "sim"})


def _h_qualidade_evidencia(row):
    """Fator conservador de qualidade computacional; não é confiança probabilística."""
    gnn_usada = bool(row.get("gnn_local_usado", False))
    gnn_modelo = str(row.get("modelo_gnn_local", "")).strip()
    gnn_energia = pd.to_numeric(pd.Series([row.get("energia_gnn_eV_atom", np.nan)]), errors="coerce").iloc[0]
    gnn_valida = gnn_usada and bool(gnn_modelo) and pd.notna(gnn_energia)
    estrutura_real = str(row.get("material_id", "")).strip() not in {"", "nan", "None"}
    estrutura_proxy = str(row.get("estrutura_proxy_gnn", "")).strip() not in {"", "nan", "None"}
    dentro = str(row.get("classe_dominio_aplicabilidade", "")).lower() == "dentro_do_dominio"
    dft_executada = bool(row.get("dft_refinado", False)) and not bool(row.get("dft_proxy_usado", True))
    descritores = bool(row.get("matminer_usado", False) or row.get("pymatgen_usado", False))
    if estrutura_real and dft_executada:
        return 1.00, "estrutura real e cálculo físico executado"
    if estrutura_real and gnn_valida and dentro:
        return 0.90, "estrutura real e GNN executada dentro do domínio"
    if estrutura_real and descritores:
        return 0.80, "estrutura real e descritores computacionais"
    if estrutura_proxy or estrutura_real:
        return 0.65, "estrutura aproximada ou proxy documentado"
    fonte = str(row.get("fonte_estabilidade_triagem", "")).lower()
    if fonte and "heur" not in fonte and "não comprov" not in fonte and "nao comprov" not in fonte:
        return 0.50, "regra computacional sem cálculo estrutural comprovado"
    return 0.40, "fonte ou execução física não comprovada"


def _h_componentes(row, reacao):
    estrutura = _h_num(row, "score_estabilidade")
    redox = 0.55 * _h_num(row, "score_redox") + 0.45 * _h_num(row, "score_redox_operando")
    acido_base = _h_num(row, "score_basicidade")
    termica = _h_num(row, "score_estabilidade_termica_operando")
    material = 0.35 * estrutura + 0.25 * redox + 0.20 * acido_base + 0.20 * termica

    metal = 0.45 * _h_num(row, "score_atividade") + 0.30 * _h_num(row, "score_seletividade") + 0.25 * _h_num(row, "score_equilibrio_adsorcao")
    suporte = _h_num(row, "score_compatibilidade_suporte")
    interface = _h_num(row, "score_interface_metal_suporte")
    promotor_presente = _h_promotor_presente(row)
    promotor = np.clip(0.40 * _h_num(row, "score_redox") + 0.30 * _h_num(row, "score_basicidade") + 0.30 * interface, 0, 1)
    if promotor_presente:
        pesos_funcoes = {"metal": .40, "suporte": .25, "promotor": .15, "interface": .20}
        valores_funcoes = {"metal": metal, "suporte": suporte, "promotor": promotor, "interface": interface}
    else:
        # Redistribuição proporcional dos 15% do promotor.
        pesos_funcoes = {"metal": .470588, "suporte": .294118, "interface": .235294}
        valores_funcoes = {"metal": metal, "suporte": suporte, "interface": interface}
        promotor = np.nan
    geometrica = float(np.exp(sum(peso * np.log(max(valores_funcoes[nome], 1e-6)) for nome, peso in pesos_funcoes.items())))
    media = float(sum(peso * valores_funcoes[nome] for nome, peso in pesos_funcoes.items()))
    catalise = 0.60 * geometrica + 0.40 * media

    conversao = np.clip(float(row.get("conversao_prevista_pct", 50.0)) / 100.0, 0, 1)
    seletividade = np.clip(float(row.get("seletividade_produto_prevista_pct", 50.0)) / 100.0, 0, 1)
    faixa = _h_num(row, "score_faixa_condicao")
    desativacao = _h_num(row, "score_anti_coque_avancado") if reacao == "reforma" else 0.5 * termica + 0.5 * _h_num(row, "score_robustez_vies_sistematico")
    operacao = 0.35 * conversao + 0.25 * seletividade + 0.20 * faixa + 0.20 * desativacao

    suporte_texto = str(row.get("suporte_sugerido", "")).strip()
    rota_texto = str(row.get("rota_sintese_sugerida", "")).strip()
    precursor_texto = str(row.get("precursor_sugerido", "")).strip()
    tratamento_texto = str(row.get("pretratamento_sugerido", "")).strip()
    precursor = 0.75 if precursor_texto and precursor_texto.lower() not in {"nan", "não definido", "nao definido"} else 0.40
    rota = 0.75 if rota_texto and rota_texto.lower() not in {"nan", "não definida", "nao definida"} else 0.40
    formacao = _h_num(row, "score_formacao_fase_ativa")
    seguranca = 0.50  # neutro: toxicologia/pureza dos precursores não foram calculadas.
    custo = 0.50      # neutro: preços e disponibilidade não foram consultados.
    sintese = 0.30 * precursor + 0.25 * rota + 0.20 * formacao + 0.15 * seguranca + 0.10 * custo

    dominio = str(row.get("classe_dominio_aplicabilidade", "")).lower()
    p_dominio = 1.0 if dominio == "fora_do_dominio" else 0.5 if dominio in {"proximo_limite", "próximo_limite"} else 0.0 if dominio == "dentro_do_dominio" else 0.5
    p_coque = 1.0 - _h_num(row, "score_anti_coque_avancado") if reacao == "reforma" else 0.0
    p_sinterizacao = _h_risco_classe(row.get("risco_sinterizacao"))
    p_transporte = 1.0 - _h_num(row, "score_transporte")
    faltas = [
        not suporte_texto or " ou " in suporte_texto.lower(),
        not rota_texto,
        not precursor_texto,
        not tratamento_texto,
        pd.isna(pd.to_numeric(pd.Series([row.get("carga_metalica_pct_massa", np.nan)]), errors="coerce").iloc[0]),
    ]
    p_incompletude = sum(faltas) / len(faltas)
    return locals()


def calcular_score_hierarquico(df, reacao):
    linhas = []
    for _, row in df.iterrows():
        c = _h_componentes(row, reacao)
        qualidade, base_evidencia = _h_qualidade_evidencia(row)
        bruto = sum(PESOS_SCORE_HIERARQUICO[n] * c[n] for n in PESOS_SCORE_HIERARQUICO)
        penalidade = sum(PESOS_PENALIZACOES_HIERARQUICAS[n] * c["p_" + n] for n in PESOS_PENALIZACOES_HIERARQUICAS)
        final = float(np.clip(qualidade * bruto - penalidade, 0, 1))
        classe = "prioritário computacional" if final >= .75 else "promissor" if final >= .60 else "exploratório" if final >= .45 else "baixa prioridade"
        linhas.append({
            "formula": row.get("formula", ""), "score_final_vigente": row.get("score_final", np.nan),
            "score_hierarquico_proposto": final, "classe_prioridade_hierarquica": classe,
            "qualidade_evidencia_computacional": qualidade, "base_qualidade_evidencia": base_evidencia,
            "score_h_material": c["material"], "score_h_catalise_bifuncional": c["catalise"],
            "score_h_operacao": c["operacao"], "score_h_sintese": c["sintese"],
            "score_h_funcao_metal": c["metal"], "score_h_funcao_suporte": c["suporte"],
            "score_h_funcao_promotor": c["promotor"], "score_h_interface": c["interface"],
            "penalidade_h_dominio": c["p_dominio"], "penalidade_h_coque": c["p_coque"],
            "penalidade_h_sinterizacao": c["p_sinterizacao"], "penalidade_h_transporte": c["p_transporte"],
            "penalidade_h_incompletude": c["p_incompletude"], "penalidade_h_total_ponderada": penalidade,
            "metodo_score_hierarquico": "técnico-heurístico sem calibração experimental",
        })
    resultado = pd.DataFrame(linhas).sort_values("score_hierarquico_proposto", ascending=False).reset_index(drop=True)
    resultado["posicao_score_hierarquico"] = np.arange(1, len(resultado) + 1)
    resultado["posicao_score_vigente"] = pd.to_numeric(resultado["score_final_vigente"], errors="coerce").rank(ascending=False, method="min")
    resultado["mudanca_posicao_hierarquico"] = resultado["posicao_score_vigente"] - resultado["posicao_score_hierarquico"]
    return resultado


score_hierarquico_comparativo_df = calcular_score_hierarquico(melhor_por_candidato_df, reacao)
colunas_hierarquicas = [c for c in score_hierarquico_comparativo_df.columns if c != "formula"]
melhor_por_candidato_df = melhor_por_candidato_df.drop(columns=colunas_hierarquicas, errors="ignore").merge(score_hierarquico_comparativo_df, on="formula", how="left", validate="one_to_one")
prioritarios_df = prioritarios_df.drop(columns=colunas_hierarquicas, errors="ignore").merge(score_hierarquico_comparativo_df, on="formula", how="left", validate="one_to_one")
ranking_hierarquico_proposto_df = melhor_por_candidato_df.sort_values("score_hierarquico_proposto", ascending=False).reset_index(drop=True)

adicionar_metrica("score_hierarquico", "score hierárquico médio Top 10", float(score_hierarquico_comparativo_df["score_hierarquico_proposto"].mean()), "0-1", "Score técnico-heurístico paralelo, sem calibração experimental.")
metricas_triagem_df = pd.DataFrame(metricas_triagem)

print("Comparação entre ranking vigente e score hierárquico proposto:")
display(score_hierarquico_comparativo_df.head(10))
