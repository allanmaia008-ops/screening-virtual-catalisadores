"""Evidence-aware exports. Scores are not experimental probabilities or yields."""
import json
import re
import unicodedata

import numpy as np
import pandas as pd


def output_prefix(reaction, metals, promoter):
    def slug(value):
        value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    reaction = {"reforma": "reforma-CH4-CO2", "metanacao": "metanacao-CO2", "rwgs": "RWGS-CO2"}.get(reaction, reaction)
    promoter = "sem-promotor" if not promoter else "promotor-" + slug(promoter)
    return "catailab_" + slug(reaction) + "_" + "-".join(map(slug, metals)) + "_" + promoter


def audited_export(frame, reaction):
    """Keep internal numerical scores intact; expose their actual evidence limits."""
    result = frame.copy()
    if "formula" not in result:
        return result
    if "score_incerteza" in result:
        result["indice_evidencia_interno_0_1"] = result.pop("score_incerteza")
    if "confiabilidade" in result:
        result["classe_indice_interno_nao_calibrado"] = result.pop("confiabilidade")
    result["validacao_experimental"] = "Não disponível nesta execução"
    domain = result.get("classe_dominio_aplicabilidade", pd.Series("nao_avaliado", index=result.index))
    result["aviso_dominio"] = domain.map(lambda x: "Extrapolação: não interpretar como previsão validada" if str(x) == "fora_do_dominio" else "Domínio de referência não equivale a validação experimental")
    if "fonte_estabilidade_triagem" in result:
        result["fonte_estabilidade_original"] = result["fonte_estabilidade_triagem"]
        model = result.get("modelo_gnn_local", pd.Series("", index=result.index)).fillna("").astype(str)
        energy = pd.to_numeric(result.get("energia_gnn_eV_atom", pd.Series(np.nan, index=result.index)), errors="coerce")
        used = result.get("gnn_local_usado", pd.Series(False, index=result.index)).map(lambda x: x is True or str(x).lower() in ("true", "1"))
        valid = used & model.str.strip().ne("") & np.isfinite(energy)
        claimed = result["fonte_estabilidade_triagem"].astype(str).str.contains("GNN", case=False, na=False)
        result.loc[claimed & ~valid, "fonte_estabilidade_triagem"] = "Estimativa heurística; execução GNN não comprovada"
        result["gnn_execucao_comprovada"] = valid
        result["versao_gnn_registrada"] = result.get("versao_gnn_local", "Não registrada")
    if "suporte_sugerido" in result:
        result["alternativas_suporte"] = result["suporte_sugerido"].fillna("").astype(str)
        ambiguous = result["alternativas_suporte"].str.contains(r"\s+ou\s+", regex=True)
        # Preserve the proposed alternatives; status records that none was selected.
        result.loc[ambiguous, "suporte_sugerido"] = result.loc[ambiguous, "alternativas_suporte"]
        result["formulacao_status"] = np.where(ambiguous, "Incompleta: suporte e cargas devem ser definidos", "Carga total e preparação precisam de confirmação")
    result["base_formula"] = "Proporção atômica; não representa teor em massa do catalisador suportado"
    result["teores_massa_catalisador_final"] = "Não definidos nesta triagem; não inferir da fórmula atômica"
    replacements = {
        "score_resistencia_coque": "indice_resistencia_coque_composicional_0_1",
        "taxa_desativacao_coque_proxy": "indice_desativacao_coque_proxy_sem_calibracao",
        "taxa_desativacao_coque_condicao": "indice_desativacao_condicional_sem_calibracao",
        "conversao_prevista_pct": "conversao_proxy_nao_calibrada_pct",
        "seletividade_produto_prevista_pct": "seletividade_proxy_nao_calibrada_pct",
        "rendimento_ou_produtividade_prevista_pct": "indice_rendimento_proxy_pct",
    }
    result = result.rename(columns=replacements)
    result["interpretacao_coque"] = "Índice composicional e penalidade operacional têm bases distintas; não são massa de carbono nem vida útil"
    result["definicao_indice_rendimento"] = "Conversão proxy x seletividade proxy / 100; não é produtividade nem rendimento de H2 validado"
    if reaction == "reforma":
        for col in ("conversao_CH4_validada_pct", "conversao_CO2_validada_pct", "rendimento_H2_validado_pct", "razao_H2_CO_validada"):
            result[col] = np.nan
    result["produtividade_fisica"] = np.nan
    return result


EXPORT_LABELS = {
    "score_final": "Score final de priorização (0–1; não é probabilidade)",
    "indice_evidencia_interno_0_1": "Índice interno de evidência (não é probabilidade)",
    "probabilidade_top5_mc": "Frequência no Top 5 sob perturbações Monte Carlo (0–1)",
    "conversao_proxy_nao_calibrada_pct": "Conversão proxy não calibrada (%)",
    "seletividade_proxy_nao_calibrada_pct": "Seletividade proxy não calibrada (%)",
    "indice_rendimento_proxy_pct": "Índice de rendimento proxy (%)",
    "indice_resistencia_coque_composicional_0_1": "Resistência composicional ao coque (índice 0–1)",
}

REPORT_NOTICE = """<section><h2>Limites científicos e definição dos resultados</h2>
<p>A pontuação multicritério prioriza candidatos; não é probabilidade de acerto.
O Monte Carlo mede estabilidade do ranking sob as perturbações assumidas, não validação experimental.
Candidatos fora do domínio são extrapolações. Os indicadores de conversão, seletividade e rendimento
são proxies não calibrados. Não há produtividade física, rendimento de H₂ validado ou tempo de vida
experimental calculados nesta execução. Campos vazios significam não calculado, nunca zero.</p>
<p>As fórmulas indicam proporções atômicas. Suportes alternativos não constituem um único material.
Antes da síntese, definir suporte, carga total, precursores, pureza e tratamentos térmicos.
Os índices de coque composicional e operacional não devem ser confundidos com massa de carbono.</p></section>"""


def support_alternatives(frame):
    records = []
    if "formula" not in frame or "suporte_sugerido" not in frame:
        return pd.DataFrame()
    for _, row in frame.iterrows():
        options = re.split(r",\s*|\s+ou\s+", str(row["suporte_sugerido"]))
        for i, support in enumerate(options, 1):
            records.append({"candidato": row["formula"], "alternativa": i,
                "suporte": support.strip(), "status": "Hipótese de formulação; desempenho não recalculado por suporte",
                "carga_metalica_pct_massa": None, "carga_promotor_pct_massa": None,
                "rota_proposta": row.get("rota_sintese_sugerida", "Não definida"),
                "tratamento_proposto": row.get("pretratamento_sugerido", "Não definido")})
    return pd.DataFrame(records).drop_duplicates()
