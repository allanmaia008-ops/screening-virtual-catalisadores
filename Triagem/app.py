from __future__ import annotations

import base64
import html
import os
import re
import subprocess
import sys
import textwrap
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from nbclient import NotebookClient


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
NOTEBOOK_PATH = APP_DIR / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
BRASAO_PATH = APP_DIR / "assets" / "logo_ufrn_header.png"
PROJECT_LOGO_PATH = APP_DIR / "assets" / "logo_triagem_catalitica_v3.png"
LABTAM_LOGO_PATH = APP_DIR / "assets" / "logo_labtam.png"

PERFIL_PESQUISADOR = {
    "nome": "Allan Maia",
    "email": os.environ.get("CATAILAB_CONTACT_EMAIL", "allan.maia.008@ufrn.edu.br").strip(),
    "telefone": os.environ.get("CATAILAB_CONTACT_PHONE", "(88) 99909-6430").strip(),
    "lattes": os.environ.get("CATAILAB_LATTES_URL", "http://lattes.cnpq.br/0437324677042249").strip(),
}

TRADUCOES_EN = {
    "Triagem": "Screening",
    "Sobre": "About",
    "Pesquisa": "Research",
    "Contato": "Contact",
    "Programa de Pós-Graduação<br />em Química": "Graduate Program<br />in Chemistry",
    "Predição virtual de catalisadores e condições de síntese": "Virtual prediction of catalysts and synthesis conditions",
    "Configuração": "Configuration",
    "Reação": "Reaction",
    "Metanação de CO2": "CO₂ methanation",
    "Reforma de CH4": "CH₄ reforming",
    "Número de metais ativos": "Number of active metals",
    "Metais ativos": "Active metals",
    "Promotor": "Promoter",
    "Local de salvamento": "Output location",
    "Usar pasta padrão": "Use default folder",
    "Escolher outra pasta": "Choose another folder",
    "Pasta de destino dos resultados": "Results destination folder",
    "Executar triagem": "Run screening",
    "Resumo dos resultados": "Results summary",
    "Visão geral": "Overview",
    "Candidatos": "Candidates",
    "Classificação": "Ranking",
    "Incerteza": "Uncertainty",
    "Robustez e operação": "Robustness and operation",
    "Química": "Chemistry",
    "Validação": "Validation",
    "Visualização científica": "Scientific visualization",
    "Arquivos": "Files",
    "Exportações": "Exports",
    "Tabela ainda não disponível.": "Table not available yet.",
    "Catalisador para síntese": "Catalyst for synthesis",
    "Suporte sugerido": "Suggested support",
    "Rendimento ou produtividade prevista": "Predicted yield or productivity",
    "Condição e confiança": "Conditions and confidence",
    "Condição inicial de ensaio": "Initial test condition",
    "Confiabilidade da recomendação": "Recommendation confidence",
    "Robustez no Top 5": "Top 5 robustness",
    "Desempenho químico previsto": "Predicted chemical performance",
    "Conversão prevista": "Predicted conversion",
    "Seletividade prevista": "Predicted selectivity",
    "Estabilidade termodinâmica": "Thermodynamic stability",
    "Resistência à deposição de carbono": "Resistance to carbon deposition",
    "Justificativa química": "Chemical rationale",
    "Plano experimental inicial": "Initial experimental plan",
    "Evidência e ponto de atenção": "Evidence and point of attention",
    "Top 2 recomendados para síntese": "Top 2 recommended for synthesis",
    "Confiabilidade": "Confidence",
    "Rendimento previsto": "Predicted yield",
    "Suporte": "Support",
    "Condição sugerida": "Suggested condition",
    "Rota de síntese": "Synthesis route",
    "Justificativa química e do suporte": "Chemical and support rationale",
}


def idioma_atual() -> str:
    """Retorna o idioma selecionado na navegação."""
    return st.session_state.get("idioma", "pt")


def t(texto: str) -> str:
    """Traduz os textos principais da interface para inglês quando solicitado."""
    return TRADUCOES_EN.get(texto, texto) if idioma_atual() == "en" else texto


def obter_dado_publico(chave: str, padrao: str = "") -> str:
    """Lê dados públicos do perfil por secrets, ambiente ou valor padrão."""
    try:
        valor_secreto = st.secrets.get(chave, "")
    except Exception:
        valor_secreto = ""
    return str(valor_secreto or os.environ.get(chave, padrao)).strip()


def dados_pesquisador() -> dict[str, str]:
    """Consolida os dados públicos exibidos nas páginas institucionais."""
    return {
        "nome": obter_dado_publico("CATAILAB_RESEARCHER_NAME", PERFIL_PESQUISADOR["nome"]),
        "email": obter_dado_publico("CATAILAB_CONTACT_EMAIL", PERFIL_PESQUISADOR["email"]),
        "telefone": obter_dado_publico("CATAILAB_CONTACT_PHONE", PERFIL_PESQUISADOR["telefone"]),
        "lattes": obter_dado_publico("CATAILAB_LATTES_URL", PERFIL_PESQUISADOR["lattes"]),
    }


def obter_secret_streamlit(nome: str) -> str:
    """Le segredo do Streamlit ou variavel de ambiente sem expor o valor."""
    try:
        segredo = st.secrets.get(nome, "")
    except Exception:
        segredo = ""
    return str(segredo or os.environ.get(nome, "")).strip()


def obter_mp_api_key() -> str:
    """Le a chave do Materials Project sem grava-la no codigo publicado."""
    return obter_secret_streamlit("MP_API_KEY")



def garantir_pkg_resources() -> None:
    """Garante pkg_resources, exigido por versoes atuais do matminer."""
    try:
        __import__("pkg_resources")
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools<81"])
        __import__("pkg_resources")

def configurar_banco_incremental_github() -> None:
    """Configura variaveis para o notebook sincronizar dados incrementais no GitHub."""
    os.environ["TRIAGEM_GITHUB_OWNER"] = obter_secret_streamlit("TRIAGEM_GITHUB_OWNER") or "allanmaia008-ops"
    os.environ["TRIAGEM_GITHUB_REPO"] = obter_secret_streamlit("TRIAGEM_GITHUB_REPO") or "screening-virtual-catalisadores"
    os.environ["TRIAGEM_GITHUB_BRANCH"] = obter_secret_streamlit("TRIAGEM_GITHUB_BRANCH") or "main"
    os.environ["TRIAGEM_GITHUB_RANKING_PATH"] = "outputs/ranking_multicriterio_v2_incerteza_explicabilidade.csv"
    os.environ["TRIAGEM_GITHUB_CONSULTAS_PATH"] = "outputs/consultas_bases_externas.csv"
    os.environ["TRIAGEM_GITHUB_CATHUB_PATH"] = "outputs/catalysis_hub_incremental.csv"
    os.environ["TRIAGEM_GITHUB_GNN_PATH"] = "outputs/proxy_gnn_local.csv"
    token = obter_secret_streamlit("TRIAGEM_GITHUB_TOKEN") or obter_secret_streamlit("GITHUB_TOKEN")
    if token:
        os.environ["TRIAGEM_GITHUB_TOKEN"] = token
    else:
        os.environ.pop("TRIAGEM_GITHUB_TOKEN", None)


def limpar_simbolo_quimico(valor: str) -> str:
    """Normaliza um símbolo químico digitado pelo usuário."""
    valor = valor.strip()
    if not valor:
        return ""
    return valor[0].upper() + valor[1:].lower()


NOMES_ELEMENTOS_PARA_SIMBOLOS = {
    "cerio": "Ce",
    "lantanio": "La",
    "tungstenio": "W",
    "wolframio": "W",
    "niquel": "Ni",
    "cobalto": "Co",
    "ferro": "Fe",
    "rutenio": "Ru",
    "zirconio": "Zr",
    "magnesio": "Mg",
    "aluminio": "Al",
    "titanio": "Ti",
    "molibdenio": "Mo",
    "manganes": "Mn",
    "cobre": "Cu",
    "zinco": "Zn",
    "itrio": "Y",
}


def limpar_simbolo_quimico_basico(valor: str) -> str:
    """Normaliza símbolo ou nome químico digitado pelo usuário."""
    valor = str(valor).strip()
    if not valor:
        return ""
    chave_nome = normalizar_texto(valor).replace(" ", "_")
    if chave_nome in NOMES_ELEMENTOS_PARA_SIMBOLOS:
        return NOMES_ELEMENTOS_PARA_SIMBOLOS[chave_nome]
    if re.fullmatch(r"[A-Za-z]{1,2}", valor):
        return valor[0].upper() + valor[1:].lower()
    return valor[0].upper() + valor[1:].lower()


def slug_texto(valor: str) -> str:
    """Cria um texto seguro para nomes de arquivos."""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", valor).strip("_")


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê CSV exportado pelo notebook preservando acentos quando possível."""
    if not caminho.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(caminho, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho)


def normalizar_texto(valor: str) -> str:
    """Remove acentos e padroniza texto para buscas internas."""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower().replace("�", "").replace("ï¿½", "").strip()


def encontrar_coluna(dataframe: pd.DataFrame, termos: list[str]) -> str | None:
    """Encontra a primeira coluna cujo nome contenha todos os termos informados."""
    termos_norm = [normalizar_texto(termo) for termo in termos]
    for coluna in dataframe.columns:
        coluna_norm = normalizar_texto(coluna)
        if all(termo in coluna_norm for termo in termos_norm):
            return coluna
    return None


def filtrar_metricas_por_termos(metricas_df: pd.DataFrame, termos: list[str]) -> pd.DataFrame:
    """Filtra linhas de métricas procurando os termos em todas as colunas."""
    if metricas_df.empty:
        return metricas_df
    termos_norm = [normalizar_texto(termo) for termo in termos]
    texto_linha = metricas_df.astype(str).agg(" ".join, axis=1).map(normalizar_texto)
    filtro = texto_linha.apply(lambda texto: any(termo in texto for termo in termos_norm))
    return metricas_df.loc[filtro].copy()


def extrair_metrica(metricas_df: pd.DataFrame, nome_parcial: str):
    """Extrai uma métrica pelo nome parcial em português."""
    if metricas_df.empty:
        return None
    coluna_metrica = encontrar_coluna(metricas_df, ["metrica"])
    coluna_valor = encontrar_coluna(metricas_df, ["valor"])
    if coluna_metrica is None and len(metricas_df.columns) >= 2:
        coluna_metrica = metricas_df.columns[1]
    if coluna_valor is None and len(metricas_df.columns) >= 3:
        coluna_valor = metricas_df.columns[2]
    if coluna_metrica is None or coluna_valor is None:
        return None
    termos = [termo for termo in normalizar_texto(nome_parcial).split() if len(termo) >= 2]
    metricas_normalizadas = metricas_df[coluna_metrica].astype(str).map(normalizar_texto)
    filtro = metricas_normalizadas.apply(lambda texto: all(termo in texto for termo in termos))
    if not filtro.any():
        return None
    return metricas_df.loc[filtro, coluna_valor].iloc[0]


def formatar_valor(valor, percentual: bool = False) -> str:
    """Formata valores de métrica para cartões visuais."""
    if valor is None or pd.isna(valor):
        return "-"
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if percentual:
        return f"{100 * numero:.0f}%"
    if abs(numero) >= 100:
        return f"{numero:.0f}"
    if abs(numero) >= 10:
        return f"{numero:.1f}"
    return f"{numero:.3f}".rstrip("0").rstrip(".")


def numero_coluna(dataframe: pd.DataFrame, termos: list[str], linhas: int | None = None, maior: bool = False, menor: bool = False):
    """Extrai resumo numerico de uma coluna encontrada por termos."""
    if dataframe.empty:
        return None
    coluna = encontrar_coluna(dataframe, termos)
    if coluna is None:
        return None
    serie = pd.to_numeric(dataframe[coluna], errors="coerce")
    if linhas is not None:
        serie = serie.head(linhas)
    serie = serie.dropna()
    if serie.empty:
        return None
    if maior:
        return float(serie.max())
    if menor:
        return float(serie.min())
    return float(serie.mean())


def valor_linha(row: pd.Series, termos: list[str], padrao: str = "-") -> str:
    """Extrai valor textual de uma linha por termos no nome da coluna."""
    coluna = encontrar_coluna(pd.DataFrame(columns=row.index), termos)
    if coluna is None:
        return padrao
    valor = row.get(coluna, padrao)
    if valor is None or pd.isna(valor):
        return padrao
    return str(valor)


def extrair_confiabilidade(row: pd.Series) -> str:
    """Extrai a confiabilidade evitando colunas incorretas ou texto corrompido."""
    coluna = encontrar_coluna(pd.DataFrame(columns=row.index), ["confiabilidade"])
    if coluna:
        valor = str(row.get(coluna, "")).strip()
        valor_norm = normalizar_texto(valor)
        if valor_norm in {"alta", "media", "baixa"}:
            return "média" if valor_norm == "media" else valor_norm
    for valor in row.astype(str).tolist():
        valor_norm = normalizar_texto(valor)
        if valor_norm in {"alta", "media", "baixa"}:
            return "média" if valor_norm == "media" else valor_norm
    return "-"


def cartao_html(rotulo: str, valor: str, destaque: bool = False, icone: str = "", nota: str = "") -> str:
    """Cria HTML de cartão centralizado."""
    cor_valor = "#C62828"
    fundo = "#F3FCF6" if destaque else "#F7FCF8"
    return f"""
    <div style="
        min-height: 92px;
        padding: 12px 9px;
        border: 1px solid #D8EEDC;
        border-radius: 12px;
        background: {fundo};
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            color: #111111;
            font-size: 0.78rem;
            font-weight: 850;
            line-height: 1.14;
            margin-bottom: 7px;
        ">{html.escape(icone)} <span>{html.escape(t(rotulo))}</span></div>
        <div style="
            color: #111111;
            font-family: Arial, Helvetica, sans-serif;
            font-size: clamp(1.35rem, 1.8vw, 1.85rem);
            font-weight: 900;
            line-height: 1.05;
            margin-bottom: 4px;
        ">{html.escape(valor)}</div>
        <div style="
            color: {cor_valor};
            font-family: Arial, Helvetica, sans-serif;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1.16;
            text-align: center;
            overflow-wrap: anywhere;
        ">{html.escape(nota)}</div>
    </div>
    """


def cartao_texto_html(titulo: str, texto: str, alerta: bool = False) -> str:
    """Cria um cartão textual para explicações químicas e operacionais."""
    cor_borda = "#C62828" if alerta else "#007A32"
    return f"""
    <div style="
        min-height: 188px;
        padding: 15px;
        border: 1px solid #D8EEDC;
        border-top: 4px solid {cor_borda};
        border-radius: 10px;
        background: #F7FCF8;
        color: #111111;
        font-family: Arial, Helvetica, sans-serif;
    ">
        <div style="
            margin-bottom: 10px;
            text-align: center;
            font-size: 1.02rem;
            font-weight: 850;
            line-height: 1.2;
        ">{html.escape(t(titulo))}</div>
        <div style="
            font-size: 0.94rem;
            line-height: 1.45;
            overflow-wrap: anywhere;
            white-space: pre-line;
        ">{html.escape(texto)}</div>
    </div>
    """


def mostrar_cartoes_metricas(metricas_df: pd.DataFrame, prioritarios_df: pd.DataFrame, monte_carlo_df: pd.DataFrame) -> None:
    """Mostra indicadores principais do funil no topo dos resultados."""
    n_gerados = extrair_metrica(metricas_df, "candidatos gerados")
    n_viaveis = extrair_metrica(metricas_df, "candidatos vi")
    taxa_viabilidade = extrair_metrica(metricas_df, "taxa de viabilidade")
    n_refinados = extrair_metrica(metricas_df, "candidatos refinados")
    if n_refinados is None:
        n_refinados = len(monte_carlo_df) if not monte_carlo_df.empty else None
    n_recomendados = extrair_metrica(metricas_df, "candidatos priorit")
    if n_recomendados is None:
        n_recomendados = len(prioritarios_df) if not prioritarios_df.empty else None
    cards = [
        ("Gerados", formatar_valor(n_gerados), False, "◌", "espaço químico inicial"),
        ("Viáveis", formatar_valor(n_viaveis), False, "⌕", "filtros de viabilidade"),
        ("Refinados", formatar_valor(n_refinados), False, "◈", "descritores e DFT"),
        ("Recomendados", formatar_valor(n_recomendados), True, "✓", "prioridade para síntese"),
        ("Viabilidade", formatar_valor(taxa_viabilidade, percentual=True), False, "◒", "retenção do funil"),
    ]
    colunas = st.columns(len(cards))
    for coluna, card in zip(colunas, cards):
        rotulo, valor, destaque, icone, nota = card
        coluna.markdown(cartao_html(rotulo, valor, destaque=destaque, icone=icone, nota=nota), unsafe_allow_html=True)


def mostrar_linha_cartoes(titulo: str, cards: list[tuple[str, str, bool]]) -> None:
    """Mostra uma linha de cartoes de decisao."""
    st.markdown(f"<h4 style='text-align:center;'>{html.escape(t(titulo))}</h4>", unsafe_allow_html=True)
    colunas = st.columns(len(cards))
    for coluna, (rotulo, valor, destaque) in zip(colunas, cards):
        coluna.markdown(cartao_html(rotulo, valor, destaque=destaque), unsafe_allow_html=True)


def mostrar_painel_decisao(
    metricas_df: pd.DataFrame,
    prioritarios_df: pd.DataFrame,
    classificacao_df: pd.DataFrame,
    monte_carlo_df: pd.DataFrame,
    desempenho_df: pd.DataFrame,
) -> None:
    """Mostra indicadores interpretativos para tomada de decisao."""
    if prioritarios_df.empty:
        st.markdown(
            "<div class='catialab-empty'><strong>A triagem ainda não foi executada</strong>"
            "Configure a reação, os metais ativos e o promotor na barra lateral. "
            "Depois execute a triagem para visualizar candidatos, scores, confiabilidade e condições sugeridas.</div>",
            unsafe_allow_html=True,
        )
        return

    top = prioritarios_df.iloc[0]

    def encontrar_opcao(opcoes: list[list[str]]) -> str | None:
        return encontrar_coluna_por_opcoes(pd.DataFrame(columns=top.index), opcoes)

    def texto_opcao(opcoes: list[list[str]], padrao: str = "-") -> str:
        coluna = encontrar_opcao(opcoes)
        if coluna is None:
            return padrao
        valor = top.get(coluna, padrao)
        return padrao if valor is None or pd.isna(valor) else str(valor)

    def numero_opcao(opcoes: list[list[str]]) -> float | None:
        coluna = encontrar_opcao(opcoes)
        if coluna is None:
            return None
        valor = pd.to_numeric(pd.Series([top.get(coluna)]), errors="coerce").iloc[0]
        return None if pd.isna(valor) else float(valor)

    def percentual(valor: float | None) -> str:
        return "-" if valor is None else f"{valor:.1f}%"

    formula = texto_opcao([["formula"], ["f"]])
    suporte = texto_opcao([["suporte", "sugerido"], ["suporte"]])
    rota_sintese = texto_opcao([["rota", "sintese"]])
    pretratamento = texto_opcao([["pretratamento"]])
    justificativa_suporte = texto_opcao([["justificativa", "suporte"], ["justificativa"]])
    observacao_sintese = texto_opcao([["observacao", "sintese"], ["observacao"]])
    regime = texto_opcao([["regime"]])
    confiabilidade = extrair_confiabilidade(top)
    conversao = numero_opcao([["conversao", "prevista"], ["conversao"]])
    seletividade = numero_opcao([["seletividade", "prevista"], ["seletividade"]])
    rendimento = numero_opcao([["rendimento", "produtividade", "prevista"], ["rendimento", "prevista"], ["rendimento"]])
    estabilidade = numero_opcao([["estabilidade", "termodinamica"], ["energy", "above", "hull"]])
    resistencia_coque = numero_opcao([["resistencia", "coque"]])
    distancia_volcano = numero_opcao([["distancia", "otimo", "volcano"]])
    energia_adsorcao = numero_opcao([["energia", "adsorcao", "volcano"], ["energia", "adsorcao"]])
    descritor_volcano = texto_opcao([["descritor", "volcano"]], "")
    fonte_volcano = texto_opcao([["fonte", "volcano"]], "")
    probabilidade_top5 = numero_opcao([["probabilidade", "top5"], ["probabilidade", "top", "5"]])
    condicao_inicial = montar_condicao_operacional(top)
    ghsv = numero_opcao([["ghsv"]])

    mostrar_linha_cartoes(
        "Decisão experimental",
        [
            ("Catalisador para síntese", formula, True),
            ("Suporte sugerido", suporte, False),
            ("Rendimento ou produtividade prevista", percentual(rendimento), True),
        ],
    )
    mostrar_linha_cartoes(
        "Condição e confiança",
        [
            ("Condição inicial de ensaio", f"{condicao_inicial} · {regime.replace('_', ' ')}" if regime != "-" else condicao_inicial, False),
            ("Confiabilidade da recomendação", confiabilidade.capitalize() if confiabilidade != "-" else "-", True),
            ("Robustez no Top 5", "-" if probabilidade_top5 is None else f"{100 * probabilidade_top5:.0f}%", False),
        ],
    )
    mostrar_linha_cartoes(
        "Desempenho químico previsto",
        [
            ("Conversão prevista", percentual(conversao), True),
            ("Seletividade prevista", percentual(seletividade), True),
            ("Estabilidade termodinâmica", "-" if estabilidade is None else f"{estabilidade:.3f} eV/átomo", False),
            ("Resistência à deposição de carbono", "-" if resistencia_coque is None else ("Alta" if resistencia_coque >= 0.70 else "Moderada" if resistencia_coque >= 0.45 else "Baixa"), False),
        ],
    )

    if distancia_volcano is not None and distancia_volcano <= 0.15:
        leitura_adsorcao = "Próxima do ótimo de adsorção"
    elif distancia_volcano is not None and distancia_volcano <= 0.30:
        leitura_adsorcao = "Adsorção intermediária"
    elif distancia_volcano is not None:
        leitura_adsorcao = "Adsorção distante do ótimo"
    else:
        leitura_adsorcao = "Energia de adsorção não disponível"
    if energia_adsorcao is not None:
        leitura_adsorcao += f" (ΔE = {energia_adsorcao:.3f} eV)"
    if descritor_volcano:
        leitura_adsorcao = f"{descritor_volcano}: {leitura_adsorcao}"

    if resistencia_coque is not None and resistencia_coque >= 0.70:
        principal_vantagem = "Boa resistência estimada à deposição de carbono"
    elif distancia_volcano is not None and distancia_volcano <= 0.15:
        principal_vantagem = "Adsorção próxima da região ótima de Sabatier"
    elif estabilidade is not None and estabilidade <= 0.10:
        principal_vantagem = "Boa estabilidade termodinâmica prevista"
    else:
        principal_vantagem = "Equilíbrio previsto entre atividade e estabilidade"

    if confiabilidade == "baixa":
        principal_risco = "Baixa confiança global na predição"
    elif estabilidade is not None and estabilidade > 0.15:
        principal_risco = "Metaestabilidade elevada para síntese e operação"
    elif distancia_volcano is not None and distancia_volcano > 0.30:
        principal_risco = "Energia de adsorção distante do ótimo"
    elif "proxy" in normalizar_texto(fonte_volcano):
        principal_risco = "Energia de adsorção estimada por proxy químico"
    else:
        principal_risco = "Requer confirmação experimental de atividade e superfície"

    col_quimica, col_plano, col_evidencia = st.columns(3)
    with col_quimica:
        st.markdown(cartao_texto_html("Justificativa química", f"{leitura_adsorcao}. {justificativa_suporte}"), unsafe_allow_html=True)
    with col_plano:
        st.markdown(cartao_texto_html("Plano experimental inicial", f"Rota: {rota_sintese}. Pré-tratamento: {pretratamento}. GHSV: {f'{ghsv:.0f} h⁻¹' if ghsv is not None else 'não informado'}."), unsafe_allow_html=True)
    with col_evidencia:
        st.markdown(cartao_texto_html("Evidência e ponto de atenção", f"Vantagem principal: {principal_vantagem}. Atenção: {principal_risco}. {observacao_sintese}", alerta=True), unsafe_allow_html=True)

    st.caption("Os valores desta tela são previsões de triagem virtual e devem ser confirmados por caracterização e ensaios catalíticos.")

def mostrar_robustez_operacao(
    metricas_df: pd.DataFrame,
    prioritarios_df: pd.DataFrame,
    classificacao_df: pd.DataFrame,
    monte_carlo_df: pd.DataFrame,
    desempenho_df: pd.DataFrame,
) -> None:
    """Mostra os indicadores operacionais e de robustez em uma aba dedicada."""
    if prioritarios_df.empty and monte_carlo_df.empty and desempenho_df.empty:
        st.info("Execute a triagem para visualizar os dados de robustez e opera\u00e7\u00e3o.")
        return

    top = prioritarios_df.iloc[0] if not prioritarios_df.empty else pd.Series(dtype=object)
    temperatura = valor_linha(top, ["temperatura"])
    pressao = valor_linha(top, ["press"])
    razao = valor_linha(top, ["razao"])
    prob_mc = numero_coluna(monte_carlo_df, ["probabilidade", "top"], linhas=10, maior=True)
    incert_mc = numero_coluna(monte_carlo_df, ["desvio", "score"], linhas=10)

    conf_predominante = "-"
    coluna_conf = encontrar_coluna(classificacao_df, ["confiabilidade"]) or encontrar_coluna(prioritarios_df, ["confiabilidade"])
    fonte_conf = classificacao_df if coluna_conf and coluna_conf in classificacao_df.columns else prioritarios_df
    if coluna_conf and not fonte_conf.empty:
        valores = fonte_conf[coluna_conf].astype(str).map(normalizar_texto)
        if not valores.empty:
            conf_predominante = valores.value_counts().idxmax()
            conf_predominante = "m\u00e9dia" if conf_predominante == "media" else conf_predominante

    melhor_regime = "-"
    if not desempenho_df.empty:
        col_regime = encontrar_coluna(desempenho_df, ["regime"])
        col_score_cond = encontrar_coluna(desempenho_df, ["score", "faixa"])
        if col_regime and col_score_cond:
            resumo_regime = desempenho_df.groupby(col_regime, as_index=False)[col_score_cond].mean()
            if not resumo_regime.empty:
                melhor_regime = str(resumo_regime.sort_values(col_score_cond, ascending=False).iloc[0][col_regime])

    mostrar_linha_cartoes(
        "Robustez e opera\u00e7\u00e3o",
        [
            ("Maior prob. MC Top 5", formatar_valor(prob_mc, percentual=True), True),
            ("Incerteza m\u00e9dia MC", formatar_valor(incert_mc), False),
            ("Confian\u00e7a predominante", conf_predominante, False),
            ("Melhor regime Top 10", melhor_regime, True),
            ("Condi\u00e7\u00e3o sugerida", f"{formatar_valor(temperatura)} \u00b0C | {formatar_valor(pressao)} bar | raz\u00e3o {razao}", False),
        ],
    )

    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        mostrar_tabela("Robustez Monte Carlo", monte_carlo_df, linhas=30)
    with col2:
        metricas_operacao_df = filtrar_metricas_por_termos(
            metricas_df,
            ["robustez", "monte carlo", "probabilidade", "desvio", "faixa", "condicao", "condi\u00e7\u00e3o", "operacao", "opera\u00e7\u00e3o", "regime"],
        )
        mostrar_tabela("M\u00e9tricas de robustez e opera\u00e7\u00e3o", metricas_operacao_df, linhas=30)

    mostrar_tabela("Desempenho por faixa de condi\u00e7\u00e3o", desempenho_df, linhas=30)

def mostrar_funil_visual(metricas_df: pd.DataFrame, prioritarios_df: pd.DataFrame, monte_carlo_df: pd.DataFrame) -> None:
    """Mostra a triagem como um funil horizontal de quatro níveis."""
    n_gerados = float(extrair_metrica(metricas_df, "candidatos gerados") or 0)
    n_viaveis = float(extrair_metrica(metricas_df, "candidatos vi") or 0)
    n_refinados_metricas = extrair_metrica(metricas_df, "candidatos refinados")
    if n_refinados_metricas is None:
        n_refinados_metricas = len(monte_carlo_df) if not monte_carlo_df.empty else 0
    n_recomendados_metricas = extrair_metrica(metricas_df, "candidatos priorit")
    if n_recomendados_metricas is None:
        n_recomendados_metricas = len(prioritarios_df) if not prioritarios_df.empty else 0
    n_refinados = float(n_refinados_metricas or 0)
    n_recomendados = float(n_recomendados_metricas or 0)
    if n_gerados == 0 and n_viaveis == 0 and n_refinados == 0 and n_recomendados == 0:
        st.info("O fluxo da triagem ser\u00e1 exibido ap\u00f3s a execu\u00e7\u00e3o da triagem.")
        return

    def retencao(valor: float, anterior: float | None) -> str:
        if anterior is None:
            return "100%"
        if anterior <= 0:
            return "-"
        return formatar_valor(valor / anterior, percentual=True)

    etapas = [
        {
            "rotulo": "Espaço químico inicial",
            "valor": n_gerados,
            "criterio": "Combinações de metais ativos, promotor e composições geradas.",
            "retencao": retencao(n_gerados, None),
            "cor": "#087CE5",
            "texto": "#FFFFFF",
            "largura": "100%",
        },
        {
            "rotulo": "Filtros aplicados",
            "valor": n_viaveis,
            "criterio": "Estabilidade termodinâmica, composição e regras químicas.",
            "retencao": retencao(n_viaveis, n_gerados),
            "cor": "#B9DCFF",
            "texto": "#126CC0",
            "largura": "90%",
        },
        {
            "rotulo": "Predição de desempenho",
            "valor": n_refinados,
            "criterio": "Descritores catalíticos, DFT ou proxy e incerteza do modelo.",
            "retencao": retencao(n_refinados, n_viaveis),
            "cor": "#DDF4E3",
            "texto": "#198443",
            "largura": "80%",
        },
        {
            "rotulo": "Candidatos para síntese",
            "valor": n_recomendados,
            "criterio": "Desempenho, robustez Monte Carlo e viabilidade de síntese.",
            "retencao": retencao(n_recomendados, n_refinados),
            "cor": "#E9F8ED",
            "texto": "#218C3A",
            "largura": "70%",
        },
    ]
    blocos = []
    for indice, etapa in enumerate(etapas):
        conector = "" if indice == len(etapas) - 1 else '<div class="funil-conector"><i></i><b></b></div>'
        blocos.append(
            f"""
            <div class="funil-linha">
                <div class="funil-etapa" style="--cor-etapa:{etapa['cor']}; --cor-texto:{etapa['texto']}; --largura:{etapa['largura']};">
                    <span>{html.escape(etapa['rotulo'])}</span>
                </div>
                <div class="funil-quantidade">
                    <strong>{html.escape(formatar_valor(etapa['valor']))}</strong>
                    <span>catalisadores</span>
                </div>
                <div class="funil-criterio">{html.escape(etapa['criterio'])}</div>
                <div class="funil-retencao"><span>Retenção</span><strong>{html.escape(etapa['retencao'])}</strong></div>
            </div>
            {conector}
            """
        )
    html_fluxo = textwrap.dedent(
        f"""
        <style>
            .fluxo-triagem {{
                width: 100%;
                box-sizing: border-box;
                padding: 18px 18px 16px 18px;
                border: 1px solid #D8EEF8;
                border-radius: 12px;
                background: #FFFFFF;
            }}
            .fluxo-titulo {{
                color: #0B4F7A;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1.18rem;
                font-weight: 800;
                margin-bottom: 16px;
                text-align: center;
            }}
            .fluxo-linha {{
                display: grid;
                grid-template-columns: 44px minmax(0, 1fr);
                gap: 14px;
                align-items: start;
            }}
            .fluxo-marcador {{
                width: 38px;
                height: 38px;
                border-radius: 999px;
                color: #FFFFFF;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1rem;
                font-weight: 850;
                box-shadow: 0 2px 8px rgba(11, 79, 122, 0.16);
            }}
            .fluxo-conteudo {{
                border: 1px solid #E3EFF5;
                border-radius: 10px;
                background: #F8FCFE;
                padding: 12px 14px;
            }}
            .fluxo-cabecalho {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 12px;
                color: #0B4F7A;
                font-family: Arial, Helvetica, sans-serif;
                font-weight: 800;
            }}
            .fluxo-cabecalho span {{
                font-size: 1rem;
            }}
            .fluxo-cabecalho strong {{
                color: #168AC8;
                font-size: 1.42rem;
                white-space: nowrap;
            }}
            .fluxo-barra-externa {{
                width: 100%;
                height: 10px;
                border-radius: 999px;
                background: #E9F4F9;
                overflow: hidden;
                margin: 9px 0 7px 0;
            }}
            .fluxo-barra-interna {{
                height: 100%;
                min-width: 18px;
                border-radius: 999px;
            }}
            .fluxo-criterio {{
                color: #526F82;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.91rem;
                line-height: 1.34;
                margin-top: 6px;
            }}
            .fluxo-retencao {{
                color: #315A6F;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.88rem;
                margin-top: 8px;
            }}
            .fluxo-seta {{
                color: #8BAFC0;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1.4rem;
                font-weight: 800;
                line-height: 1;
                margin: 8px 0 8px 18px;
            }}
            @media (max-width: 680px) {{
                .fluxo-triagem {{
                    padding: 14px;
                }}
                .fluxo-linha {{
                    grid-template-columns: 36px minmax(0, 1fr);
                    gap: 10px;
                }}
                .fluxo-marcador {{
                    width: 32px;
                    height: 32px;
                    font-size: 0.9rem;
                }}
                .fluxo-cabecalho {{
                    display: block;
                    text-align: left;
                }}
                .fluxo-cabecalho strong {{
                    display: block;
                    margin-top: 3px;
                }}
            }}
            .funil-triagem {{
                width: 100%;
                box-sizing: border-box;
                padding: 18px 18px 16px;
                border: 1px solid #D7E7F1;
                border-radius: 10px;
                background: #FFFFFF;
            }}
            .funil-titulo {{
                color: #122E63;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1.14rem;
                font-weight: 800;
                margin: 0 0 14px 8px;
            }}
            .funil-linha {{
                display: grid;
                grid-template-columns: minmax(250px, 1.35fr) 130px minmax(190px, 1fr) 92px;
                gap: 0;
                min-height: 70px;
                align-items: stretch;
            }}
            .funil-etapa {{
                align-self: center;
                display: flex;
                align-items: center;
                justify-content: center;
                width: var(--largura);
                min-height: 70px;
                box-sizing: border-box;
                padding: 12px 30px;
                clip-path: polygon(24px 0, calc(100% - 24px) 0, 100% 100%, 0 100%);
                background: var(--cor-etapa);
                color: var(--cor-texto);
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.98rem;
                font-weight: 800;
                text-align: center;
            }}
            .funil-quantidade, .funil-criterio, .funil-retencao {{
                display: flex;
                box-sizing: border-box;
                border: 1px solid #DCE6EF;
                background: #FBFDFF;
                font-family: Arial, Helvetica, sans-serif;
            }}
            .funil-quantidade {{
                flex-direction: column;
                justify-content: center;
                padding: 10px 14px;
                color: #182F61;
            }}
            .funil-quantidade strong {{
                font-size: 1.35rem;
                line-height: 1.1;
            }}
            .funil-quantidade span {{
                font-size: 0.82rem;
                margin-top: 3px;
            }}
            .funil-criterio {{
                align-items: center;
                padding: 10px 16px;
                color: #33486C;
                font-size: 0.86rem;
                line-height: 1.28;
            }}
            .funil-retencao {{
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 8px;
                color: #52708C;
                font-size: 0.72rem;
                text-align: center;
            }}
            .funil-retencao strong {{
                margin-top: 3px;
                color: #0B73D6;
                font-size: 1rem;
            }}
            .funil-conector {{
                position: relative;
                width: 46%;
                height: 20px;
                margin: 0 0 0 22%;
            }}
            .funil-conector i {{
                position: absolute;
                left: 50%;
                top: 0;
                height: 14px;
                border-left: 2px dotted #187FE4;
            }}
            .funil-conector b {{
                position: absolute;
                left: calc(50% - 3px);
                bottom: 0;
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #187FE4;
            }}
            @media (max-width: 840px) {{
                .funil-linha {{
                    grid-template-columns: 1fr 110px;
                    gap: 0;
                }}
                .funil-etapa {{ width: 100%; }}
                .funil-criterio, .funil-retencao {{ display: none; }}
                .funil-conector {{ width: 100%; margin-left: 0; }}
            }}
        </style>
        <div class="funil-triagem">
            <div class="funil-titulo">Triagem de candidatos</div>
            {''.join(blocos)}
        </div>
        """
    )
    st.html(html_fluxo)


def selecionar_colunas_tecnicas(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Seleciona colunas químicas essenciais para apresentação técnica."""
    if dataframe.empty:
        return dataframe
    grupos = [
        ["formula"],
        ["estabilidade"],
        ["score", "atividade"],
        ["score", "seletividade"],
        ["score", "dft"],
        ["score", "volcano"],
        ["coque"],
        ["confiabilidade"],
        ["temperatura"],
        ["pressao"],
        ["razao"],
    ]
    colunas = []
    for termos in grupos:
        coluna = encontrar_coluna(dataframe, termos)
        if coluna and coluna not in colunas:
            colunas.append(coluna)
    return dataframe[colunas] if colunas else dataframe


def mostrar_resumo_top(prioritarios_df: pd.DataFrame) -> None:
    """Mostra o primeiro candidato como resumo visual."""
    if prioritarios_df.empty:
        st.info("Execute a triagem para visualizar o candidato mais promissor.")
        return
    top = prioritarios_df.iloc[0]
    coluna_formula = encontrar_coluna(prioritarios_df, ["formula"]) or prioritarios_df.columns[0]
    coluna_suporte = encontrar_coluna(prioritarios_df, ["suporte"])
    coluna_score = encontrar_coluna(prioritarios_df, ["score", "final"])
    itens = [
        ("Top candidato", str(top.get(coluna_formula, "-"))),
        ("Suporte sugerido", str(top.get(coluna_suporte, "-")) if coluna_suporte else "-"),
        ("Score final", formatar_valor(top.get(coluna_score)) if coluna_score else "-"),
        ("Confiabilidade", extrair_confiabilidade(top)),
    ]
    colunas = st.columns([1.2, 1.4, 1.0, 1.0])
    for coluna, (rotulo, valor) in zip(colunas, itens):
        coluna.markdown(
            f"""
            <div style="
                min-height: 92px;
                padding: 12px 10px;
                border: 1px solid #E2F0E6;
                border-radius: 10px;
                background: #FFFFFF;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            ">
                <div style="
                    color: #111111;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 0.86rem;
                    font-weight: 650;
                    line-height: 1.16;
                    margin-bottom: 8px;
                ">{html.escape(rotulo)}</div>
                <div style="
                    color: #111111;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 1.12rem;
                    font-weight: 800;
                    line-height: 1.12;
                    text-align: center;
                    overflow-wrap: anywhere;
                ">{html.escape(valor)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def formatar_numero_linha(row: pd.Series, termos: list[str], unidade: str = "", casas: int | None = None) -> str:
    """Extrai e formata um valor numerico de uma linha."""
    coluna = encontrar_coluna(pd.DataFrame(columns=row.index), termos)
    if coluna is None:
        return "-"
    valor = row.get(coluna)
    if valor is None or pd.isna(valor):
        return "-"
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        texto = str(valor).strip()
        return f"{texto} {unidade}".strip() if texto else "-"
    if casas is None:
        texto = formatar_valor(numero)
    else:
        texto = f"{numero:.{casas}f}".rstrip("0").rstrip(".")
    return f"{texto} {unidade}".strip()


def montar_condicao_operacional(row: pd.Series) -> str:
    """Monta texto curto com as condicoes operacionais sugeridas."""
    temperatura = formatar_numero_linha(row, ["temperatura"], "°C", casas=0)
    pressao = formatar_numero_linha(row, ["press"], "bar", casas=1)
    razao_nome = valor_linha(row, ["nome", "raz"], "")
    if razao_nome == "-":
        razao_nome = valor_linha(row, ["razao_nome"], "")
    razao_valor = valor_linha(row, ["valor", "raz"], "")
    if razao_valor == "-":
        razao_valor = valor_linha(row, ["razao"], "")
    partes = [parte for parte in [temperatura, pressao] if parte != "-"]
    if razao_nome and razao_nome != "-":
        razao_limpa = razao_nome.replace("CH4", "CH₄").replace("CO2", "CO₂").replace("H2", "H₂")
        partes.append(f"{razao_limpa} = {formatar_valor(razao_valor)}" if razao_valor and razao_valor != "-" else razao_limpa)
    return " · ".join(partes) if partes else "-"


def texto_curto(valor: str, limite: int = 150) -> str:
    """Limita texto longo para manter os cards legiveis."""
    texto = " ".join(str(valor or "-").split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


def mostrar_top2_recomendados_amigavel(prioritarios_df: pd.DataFrame) -> None:
    """Mostra os dois recomendados principais em cards amigaveis, sem tabela extensa."""
    st.markdown("<h3 style='text-align:center;'>Top 2 recomendados para síntese</h3>", unsafe_allow_html=True)
    if prioritarios_df.empty:
        st.info("Execute a triagem para visualizar os candidatos recomendados.")
        return

    cards_html = []
    for posicao, (_, row) in enumerate(prioritarios_df.head(2).iterrows(), start=1):
        formula = valor_linha(row, ["formula"], valor_linha(row, ["f"], "-"))
        suporte = texto_curto(valor_linha(row, ["suporte"], "-"), limite=135)
        condicao = montar_condicao_operacional(row)
        conversao = formatar_numero_linha(row, ["conversao"], "%", casas=1)
        seletividade = formatar_numero_linha(row, ["seletividade"], "%", casas=1)
        confiabilidade = extrair_confiabilidade(row)
        estabilidade = formatar_numero_linha(row, ["estabilidade"], "eV/átomo", casas=3)
        rendimento = formatar_numero_linha(row, ["rendimento"], "%", casas=1)
        score_final = formatar_numero_linha(row, ["score", "final"], "", casas=3)
        rota_sintese = texto_curto(valor_linha(row, ["rota", "sintese"], "-"), limite=135)
        justificativa = texto_curto(
            valor_linha(row, ["justificativa"], valor_linha(row, ["observacao"], "Critérios combinados de estabilidade, atividade e robustez.")),
            limite=155,
        )
        cor_posicao = "#007A32" if posicao == 1 else "#E0A800"
        cor_texto_posicao = "#FFFFFF" if posicao == 1 else "#111111"
        cards_html.append(
            f"""
            <article class="top2-card">
                <div class="top2-card-head">
                    <span class="top2-badge" style="background:{cor_posicao}; color:{cor_texto_posicao};">#{posicao}</span>
                    <div>
                        <div class="top2-label">Candidato</div>
                        <div class="top2-formula">{html.escape(formula)}</div>
                    </div>
                </div>
                <div class="top2-score">
                    <div><span>Score final</span><strong>{html.escape(score_final)}</strong><em>/ 1,00</em></div>
                    <div class="top2-confidence"><span>Confiança do modelo</span><strong>{html.escape(confiabilidade.capitalize())}</strong><div class="top2-confidence-track"><i style="width:{'92' if confiabilidade == 'alta' else '68' if confiabilidade == 'média' else '42'}%;"></i></div></div>
                </div>
                <div class="top2-metrics">
                    <div><span>Conversão prevista</span><strong>{html.escape(conversao)}</strong></div>
                    <div><span>Seletividade prevista</span><strong>{html.escape(seletividade)}</strong></div>
                    <div><span>Confiabilidade</span><strong>{html.escape(confiabilidade)}</strong></div>
                    <div><span>Rendimento previsto</span><strong>{html.escape(rendimento)}</strong></div>
                </div>
                <div class="top2-info"><span>Suporte</span><strong>{html.escape(suporte)}</strong></div>
                <div class="top2-info"><span>Condição sugerida</span><strong>{html.escape(condicao)}</strong></div>
                <div class="top2-info"><span>Rota de síntese</span><strong>{html.escape(rota_sintese)}</strong></div>
                <div class="top2-info"><span>Estabilidade termodinâmica</span><strong>{html.escape(estabilidade)}</strong></div>
                <div class="top2-why">
                    <span>Justificativa química e do suporte</span>
                    <p>{html.escape(justificativa)}</p>
                </div>
            </article>
            """
        )

    st.html(
        f"""
        <style>
            .top2-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
                margin: 6px 0 18px 0;
            }}
            .top2-card {{
                border: 1px solid #D8EEDC;
                border-radius: 14px;
                background: linear-gradient(180deg, #FFFFFF 0%, #F7FCF8 100%);
                box-shadow: 0 10px 24px rgba(0, 107, 42, 0.08);
                padding: 16px 16px 14px 16px;
                min-height: 250px;
                font-family: Arial, Helvetica, sans-serif;
                color: #173D24;
            }}
            .top2-card-head {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 14px;
            }}
            .top2-badge {{
                width: 44px;
                height: 44px;
                border-radius: 50%;
                color: #FFFFFF;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 1.02rem;
                font-weight: 850;
                flex: 0 0 auto;
            }}
            .top2-label {{
                color: #111111;
                font-size: 0.78rem;
                font-weight: 750;
                text-transform: uppercase;
                letter-spacing: 0.02em;
            }}
            .top2-formula {{
                color: #C62828;
                font-size: clamp(1.35rem, 2vw, 1.9rem);
                font-weight: 900;
                line-height: 1.1;
                overflow-wrap: anywhere;
            }}
            .top2-score {{
                display: grid;
                grid-template-columns: 1fr 1.35fr;
                gap: 10px;
                margin: 0 0 12px 0;
            }}
            .top2-score > div {{
                border: 1px solid #E2F0E6;
                border-radius: 10px;
                background: #FFFFFF;
                padding: 10px;
            }}
            .top2-score span,
            .top2-confidence span {{
                display: block;
                color: #334155;
                font-size: 0.72rem;
                font-weight: 750;
                margin-bottom: 4px;
            }}
            .top2-score strong {{
                color: #007A32;
                font-size: 1.45rem;
                font-weight: 900;
            }}
            .top2-score em {{
                color: #64748B;
                font-size: 0.8rem;
                font-style: normal;
                margin-left: 4px;
            }}
            .top2-confidence strong {{
                color: #14213D;
                font-size: 0.9rem;
            }}
            .top2-confidence-track {{
                height: 7px;
                margin-top: 7px;
                border-radius: 99px;
                background: #E2E8F0;
                overflow: hidden;
            }}
            .top2-confidence-track i {{
                display: block;
                height: 100%;
                border-radius: inherit;
                background: #007A32;
            }}
            .top2-metrics {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 8px;
                margin-bottom: 12px;
            }}
            .top2-metrics div {{
                border: 1px solid #E2F0E6;
                border-radius: 10px;
                background: #FFFFFF;
                padding: 9px 8px;
                text-align: center;
            }}
            .top2-metrics span,
            .top2-info span {{
                display: block;
                color: #111111;
                font-size: 0.74rem;
                font-weight: 750;
                line-height: 1.12;
                margin-bottom: 3px;
            }}
            .top2-metrics strong {{
                color: #111111;
                font-size: 0.98rem;
                font-weight: 850;
                line-height: 1.12;
                overflow-wrap: anywhere;
            }}
            .top2-info {{
                margin: 8px 0;
            }}
            .top2-info strong {{
                color: #173D24;
                font-size: 0.92rem;
                font-weight: 750;
                line-height: 1.22;
                overflow-wrap: anywhere;
            }}
            .top2-why {{
                margin: 12px 0 0 0;
                padding-top: 10px;
                border-top: 1px solid #E2F0E6;
            }}
            .top2-why span {{
                display: block;
                color: #111111;
                font-size: 0.76rem;
                font-weight: 800;
                line-height: 1.12;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.02em;
            }}
            .top2-why p {{
                margin: 0;
                color: #111111;
                font-size: 0.9rem;
                line-height: 1.28;
            }}
            @media (max-width: 860px) {{
                .top2-grid {{
                    grid-template-columns: 1fr;
                }}
                .top2-metrics {{
                    grid-template-columns: 1fr;
                }}
                .top2-score {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        <div class="top2-grid">
            {''.join(cards_html)}
        </div>
        """
    )


def montar_celula_configuracao(reacao: str, metais: list[str], promotor: str, output_dir: Path) -> str:
    """Monta a célula que substitui as perguntas interativas do notebook."""
    metais_repr = repr(metais)
    promotor_repr = repr(promotor)
    output_repr = repr(str(output_dir))
    return f"""
# Define json para manter compatibilidade com o restante do notebook.
import json

# Define os para manter compatibilidade com rotinas que leem variáveis de ambiente.
import os

# Define sys para manter compatibilidade com instalação/importação opcional de dependências.
import sys

# Define subprocess para manter compatibilidade com instalações opcionais executadas pelo notebook.
import subprocess

# Define time para manter compatibilidade com pausas entre consultas externas.
import time

# Importa getpass para manter compatibilidade com a configuração de chave do Materials Project.
from getpass import getpass

# Importa math para cálculos numéricos usados nos descritores e condições.
import math

# Importa re para extrair símbolos químicos de fórmulas.
import re

# Importa html para escapar textos no relatorio HTML.
import html

# Importa base64 para embutir figuras no relatorio HTML.
import base64

# Importa requests para consultas REST quando disponíveis.
import requests

# Importa Path para manipular pastas e arquivos de forma robusta.
from pathlib import Path

# Importa numpy para cálculos vetoriais e geração de ruído estatístico.
import numpy as np

# Importa pandas para manipulação das tabelas de candidatos e resultados.
import pandas as pd

# Define a pasta em que o notebook está sendo executado.
CWD = Path.cwd()

# Define a raiz do projeto mesmo quando o notebook roda dentro da pasta Triagem.
PROJECT_ROOT = CWD.parent if CWD.name.lower() == "triagem" else CWD

# Define a pasta local do projeto onde ficam bases auxiliares usadas pela triagem.
PROJECT_DATA_DIR = PROJECT_ROOT / "outputs"

# Lê a chave do Materials Project por variável de ambiente/secrets, sem gravá-la no notebook.
MP_API_KEY_SALVA = os.environ.get("MP_API_KEY", "").strip()

# Define a pasta de saída escolhida na interface Streamlit.
OUTPUT_DIR = Path({output_repr}).expanduser().resolve()

# Cria a pasta de saída caso ela ainda não exista.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define o arquivo local com ranking/propriedades já derivadas do notebook base.
RANKING_FILE = PROJECT_DATA_DIR / "ranking_multicriterio_v2_incerteza_explicabilidade.csv"

# Mostra as pastas principais para conferência.
print("Raiz do projeto:", PROJECT_ROOT)
print("Pasta de dados locais:", PROJECT_DATA_DIR)
print("Pasta de saída:", OUTPUT_DIR)
print("Base local de triagem existe?", RANKING_FILE.exists())

# Define a reação escolhida na interface Streamlit.
reacao_usuario = {reacao!r}

# Define a quantidade de metais ativos escolhida na interface Streamlit.
n_metais_usuario = {len(metais)}

# Define os metais ativos escolhidos na interface Streamlit.
metais_usuario = {metais_repr}

# Define o promotor escolhido na interface Streamlit.
promotor_usuario = {promotor_repr}

# Mostra as escolhas usadas nesta execução.
print("Reação:", reacao_usuario)
print("Metais ativos:", metais_usuario)
print("Promotor:", promotor_usuario)
""".strip()


def preparar_notebook_parametrizado(reacao: str, metais: list[str], promotor: str, output_dir: Path):
    """Carrega o notebook base e substitui as células de perguntas por parâmetros da interface."""
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    celula_config = montar_celula_configuracao(reacao, metais, promotor, output_dir)
    substituiu_config = False
    substituiu_entrada = False

    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "pasta_saida_usuario = input" in cell.source:
            cell.source = celula_config
            substituiu_config = True
        elif "reacao_usuario = perguntar" in cell.source:
            cell.source = "# Entradas já definidas pela interface Streamlit na etapa anterior."
            substituiu_entrada = True

    if not substituiu_config:
        raise RuntimeError("Não encontrei a célula de preparação do ambiente no notebook.")
    if not substituiu_entrada:
        raise RuntimeError("Não encontrei a célula de entrada do usuário no notebook.")
    return notebook


def executar_triagem(reacao: str, metais: list[str], promotor: str, output_dir: Path) -> Path:
    """Executa o notebook parametrizado e salva uma cópia executada para auditoria."""
    garantir_pkg_resources()
    mp_api_key = obter_mp_api_key()
    if mp_api_key:
        os.environ["MP_API_KEY"] = mp_api_key
    configurar_banco_incremental_github()
    notebook = preparar_notebook_parametrizado(reacao, metais, promotor, output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metais_slug = slug_texto("_".join(metais))
    promotor_slug = slug_texto(promotor) or "sem_promotor"
    output_notebook = APP_DIR / f"execucao_streamlit_{reacao}_{metais_slug}_{promotor_slug}_{timestamp}.ipynb"
    client = NotebookClient(
        notebook,
        timeout=1800,
        kernel_name="python3",
        resources={"metadata": {"path": str(APP_DIR)}},
    )
    client.execute()
    nbformat.write(notebook, output_notebook)
    return output_notebook


def caminhos_resultado(output_dir: Path, reacao: str) -> dict[str, Path]:
    """Agrupa os caminhos de saída gerados pelo notebook para a reação selecionada."""
    prefixo = f"disciplina_fluxo_{reacao}"
    return {
        "prioritarios": output_dir / f"{prefixo}_prioritarios_sintese.csv",
        "ranking": output_dir / f"{prefixo}_ranking_condicoes.csv",
        "classificacao": output_dir / f"{prefixo}_melhor_condicao_por_candidato.csv",
        "metricas": output_dir / f"{prefixo}_metricas_triagem.csv",
        "monte_carlo": output_dir / f"{prefixo}_monte_carlo_ranking.csv",
        "desempenho": output_dir / f"{prefixo}_desempenho_faixa_condicoes.csv",
        "figuras": output_dir / f"{prefixo}_figuras_geradas.csv",
        "dominio": output_dir / f"{prefixo}_dominio_aplicabilidade.csv",
        "pareto": output_dir / f"{prefixo}_pareto_desejabilidade.csv",
        "validacao_quimio": output_dir / f"{prefixo}_validacao_quimiometrica.csv",
        "validacao_avancada": output_dir / f"{prefixo}_validacao_avancada.csv",
        "correcao_temperatura": output_dir / f"{prefixo}_correcao_temperatura_top10.csv",
        "excel": output_dir / f"{prefixo}_resultados.xlsx",
        "html": output_dir / f"{prefixo}_relatorio.html",
        "resumo": output_dir / f"{prefixo}_resumo.json",
    }


def mostrar_tabela(titulo: str, dataframe: pd.DataFrame, linhas: int = 20) -> None:
    """Mostra uma tabela apenas quando ela existe."""
    st.markdown(f"<h3 style='text-align:center;'>{html.escape(t(titulo))}</h3>", unsafe_allow_html=True)
    if dataframe.empty:
        st.info(t("Tabela ainda não disponível."))
        return
    tabela = dataframe.head(linhas)
    tabela_centralizada = tabela.style.set_properties(**{"text-align": "center"}).set_table_styles(
        [
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "center")]},
        ]
    )
    st.dataframe(tabela_centralizada, width="stretch", hide_index=True)


def selecionar_classificacao_formula(dataframe: pd.DataFrame, linhas: int = 10) -> pd.DataFrame:
    """Cria uma tabela curta com classificacao e formula."""
    if dataframe.empty:
        return dataframe
    coluna_formula = encontrar_coluna(dataframe, ["formula"]) or encontrar_coluna(dataframe, ["f"])
    if coluna_formula is None:
        coluna_formula = dataframe.columns[0]
    tabela = dataframe.head(linhas).copy()
    tabela.insert(0, "Classifica\u00e7\u00e3o", range(1, len(tabela) + 1))
    return tabela[["Classifica\u00e7\u00e3o", coluna_formula]].rename(columns={coluna_formula: "F\u00f3rmula"})


def montar_classificacao_top10(fontes: list[pd.DataFrame], linhas: int = 10) -> pd.DataFrame:
    """Monta top 10 por formula usando fontes em ordem de prioridade."""
    formulas = []
    vistos = set()
    for dataframe in fontes:
        if dataframe.empty:
            continue
        coluna_formula = encontrar_coluna(dataframe, ["formula"]) or encontrar_coluna(dataframe, ["f"])
        if coluna_formula is None:
            coluna_formula = dataframe.columns[0]
        for formula in dataframe[coluna_formula].astype(str):
            formula_limpa = formula.strip()
            chave = normalizar_texto(formula_limpa)
            if formula_limpa and chave not in vistos:
                vistos.add(chave)
                formulas.append(formula_limpa)
            if len(formulas) >= linhas:
                break
        if len(formulas) >= linhas:
            break
    return pd.DataFrame({
        "Classifica\u00e7\u00e3o": range(1, len(formulas) + 1),
        "F\u00f3rmula": formulas,
    })


def mostrar_classificacao_centralizada(titulo: str, dataframe: pd.DataFrame) -> None:
    """Mostra classificacao com titulo, cabecalho e valores centralizados."""
    st.markdown(f"<h3 style='text-align:center;'>{html.escape(titulo)}</h3>", unsafe_allow_html=True)
    if dataframe.empty:
        st.info("Classifica\u00e7\u00e3o ainda n\u00e3o dispon\u00edvel.")
        return
    tabela_html = dataframe.to_html(index=False, escape=True, border=0)
    st.html(
        f"""
        <style>
            .classificacao-top10-wrap {{
                display: flex;
                justify-content: center;
                width: 100%;
            }}
            .classificacao-top10 {{
                border-collapse: collapse;
                min-width: min(520px, 100%);
                font-family: Arial, Helvetica, sans-serif;
                color: #111111;
                background: #FFFFFF;
                border: 1px solid #D8EEDC;
                border-radius: 10px;
                overflow: hidden;
            }}
            .classificacao-top10 th {{
                background: #EAF8EF;
                color: #111111;
                font-weight: 850;
                text-align: center;
                padding: 11px 14px;
                border-bottom: 1px solid #CFE8D6;
            }}
            .classificacao-top10 td {{
                text-align: center;
                padding: 10px 14px;
                border-bottom: 1px solid #EEF6F0;
                font-weight: 650;
            }}
            .classificacao-top10 tr:last-child td {{
                border-bottom: 0;
            }}
        </style>
        <div class="classificacao-top10-wrap">
            {tabela_html.replace('<table border="0" class="dataframe">', '<table class="classificacao-top10">')}
        </div>
        """
    )


def encontrar_coluna_por_opcoes(dataframe: pd.DataFrame, opcoes: list[list[str]]) -> str | None:
    """Encontra coluna testando varias combinacoes de termos."""
    for termos in opcoes:
        coluna = encontrar_coluna(dataframe, termos)
        if coluna:
            return coluna
    return None


def preparar_dados_plotly(dataframe: pd.DataFrame, limite: int = 300) -> pd.DataFrame:
    """Prepara colunas auxiliares para tooltips interativos."""
    if dataframe.empty:
        return dataframe
    df = dataframe.head(limite).copy()
    linhas = []
    for _, row in df.iterrows():
        linhas.append(
            {
                "_formula": valor_linha(row, ["formula"], valor_linha(row, ["f"], "-")),
                "_score_final": formatar_numero_linha(row, ["score", "final"], casas=3),
                "_suporte": texto_curto(valor_linha(row, ["suporte"], "-"), limite=120),
                "_rota": texto_curto(valor_linha(row, ["rota"], "-"), limite=120),
                "_condicao": montar_condicao_operacional(row),
                "_confiabilidade": extrair_confiabilidade(row),
                "_estabilidade": formatar_numero_linha(row, ["estabilidade"], "eV/átomo", casas=3),
                "_rendimento": formatar_numero_linha(row, ["rendimento"], "%", casas=1),
                "_energia_adsorcao": formatar_numero_linha(row, ["energia", "adsor"], "eV", casas=3),
                "_score_volcano": formatar_numero_linha(row, ["score", "vulc"], casas=3),
            }
        )
    auxiliares = pd.DataFrame(linhas, index=df.index)
    for coluna in auxiliares.columns:
        df[coluna] = auxiliares[coluna]
    return df


def renderizar_scatter_plotly(
    titulo: str,
    dataframe: pd.DataFrame,
    opcoes_x: list[list[str]],
    opcoes_y: list[list[str]],
    limite: int = 300,
) -> bool:
    """Renderiza um grafico de dispersao interativo quando as colunas existem."""
    if dataframe.empty:
        return False
    x_col = encontrar_coluna_por_opcoes(dataframe, opcoes_x)
    y_col = encontrar_coluna_por_opcoes(dataframe, opcoes_y)
    if x_col is None or y_col is None:
        return False
    df = preparar_dados_plotly(dataframe, limite=limite)
    df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df = df.dropna(subset=[x_col, y_col]).copy()
    if df.empty:
        return False

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color="_confiabilidade",
        color_discrete_map={"alta": "#2E7D32", "média": "#F9A825", "baixa": "#C62828", "-": "#78909C"},
        custom_data=[
            "_formula",
            "_score_final",
            "_suporte",
            "_rota",
            "_condicao",
            "_confiabilidade",
            "_estabilidade",
            "_rendimento",
            "_energia_adsorcao",
            "_score_volcano",
        ],
        title=titulo,
    )
    fig.update_traces(
        marker={"size": 10, "opacity": 0.78, "line": {"width": 0.7, "color": "#263238"}},
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Score final: %{customdata[1]}<br>"
            "Confiabilidade: %{customdata[5]}<br>"
            "Suporte: %{customdata[2]}<br>"
            "Rota de síntese: %{customdata[3]}<br>"
            "Condição: %{customdata[4]}<br>"
            "Estabilidade: %{customdata[6]}<br>"
            "Rendimento previsto: %{customdata[7]}<br>"
            "Energia de adsorção: %{customdata[8]}<br>"
            "Score volcano: %{customdata[9]}<extra></extra>"
        ),
    )
    fig.update_layout(
        title={"x": 0.5, "xanchor": "center"},
        legend_title_text="Confiabilidade",
        margin={"l": 20, "r": 20, "t": 62, "b": 20},
        height=520,
        hovermode="closest",
    )
    fig.update_xaxes(title_text=x_col, showgrid=True, gridcolor="#E8F3EA")
    fig.update_yaxes(title_text=y_col, showgrid=True, gridcolor="#E8F3EA")
    st.plotly_chart(fig, width="stretch")
    return True


def escolher_fonte_plotly(fontes: list[pd.DataFrame], opcoes_x: list[list[str]], opcoes_y: list[list[str]]) -> pd.DataFrame:
    """Escolhe a primeira fonte que possui as colunas necessarias para Plotly."""
    for dataframe in fontes:
        if dataframe.empty:
            continue
        if encontrar_coluna_por_opcoes(dataframe, opcoes_x) and encontrar_coluna_por_opcoes(dataframe, opcoes_y):
            return dataframe
    return pd.DataFrame()


def mostrar_visualizacao_cientifica_plotly(
    prioritarios_df: pd.DataFrame,
    classificacao_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    monte_carlo_df: pd.DataFrame,
) -> None:
    """Mostra graficos interativos para exploracao cientifica sem poluir os pontos."""
    st.markdown("<h3 style='text-align:center;'>Visualização científica interativa</h3>", unsafe_allow_html=True)
    fontes = [classificacao_df, ranking_df, prioritarios_df, monte_carlo_df]

    fonte_volcano = escolher_fonte_plotly(
        fontes,
        [["energia", "adsor"], ["adsorcao"], ["adsorção"]],
        [["score", "vulc"], ["score", "volcano"], ["taxa", "relativa"]],
    )
    gerou_volcano = renderizar_scatter_plotly(
        "Volcano plot interativo",
        fonte_volcano,
        [["energia", "adsor"], ["adsorcao"], ["adsorção"]],
        [["score", "vulc"], ["score", "volcano"], ["taxa", "relativa"]],
    )

    fonte_dispersao = escolher_fonte_plotly(
        fontes,
        [["estabilidade"]],
        [["score", "final"], ["desejabilidade", "global"]],
    )
    gerou_dispersao = renderizar_scatter_plotly(
        "Estabilidade termodinâmica vs score final",
        fonte_dispersao,
        [["estabilidade"]],
        [["score", "final"], ["desejabilidade", "global"]],
    )

    if not gerou_volcano and not gerou_dispersao:
        st.info("Ainda não há colunas numéricas suficientes para gerar gráficos Plotly interativos.")


def mostrar_figuras(figuras_df: pd.DataFrame) -> None:
    """Renderiza as figuras geradas pelo notebook."""
    st.markdown("<h3 style='text-align:center;'>Figuras</h3>", unsafe_allow_html=True)
    if figuras_df.empty:
        st.info("Figuras ainda não disponíveis.")
        return

    coluna_png = next((c for c in figuras_df.columns if "PNG" in c.upper()), None)
    if coluna_png is None:
        st.info("A tabela de figuras não contém caminho PNG.")
        return

    for _, row in figuras_df.iterrows():
        caminho = Path(str(row[coluna_png]))
        if caminho.exists():
            st.image(str(caminho), caption=caminho.name, width="stretch")


def renderizar_cabecalho() -> None:
    """Renderiza o cabeçalho institucional sem exibir caminhos locais."""
    if BRASAO_PATH.exists():
        imagem_base64 = base64.b64encode(BRASAO_PATH.read_bytes()).decode("utf-8")
        labtam_base64 = base64.b64encode(LABTAM_LOGO_PATH.read_bytes()).decode("utf-8") if LABTAM_LOGO_PATH.exists() else ""
        labtam_img = (
            f"""<img src="data:image/png;base64,{labtam_base64}" alt="LabTAm UFRN" style="
                width: min(240px, 20vw);
                max-height: 94px;
                object-fit: contain;
                display: block;
            " />"""
            if labtam_base64
            else ""
        )
        st.markdown(
            f"""
            <div style="
                width: 100%;
                padding: 12px 18px;
                margin: 0 auto 14px auto;
                background: linear-gradient(180deg, #F3FCF6 0%, #EAF8EF 100%);
                border-radius: 14px;
                border: 1px solid #D8EEDC;
                display: grid;
                grid-template-columns: minmax(260px, 330px) minmax(320px, 1fr) minmax(260px, 330px);
                align-items: center;
                column-gap: 18px;
            ">
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    min-width: 0;
                    text-align: center;
                    transform: translateX(-19px);
                ">
                    <img src="data:image/png;base64,{imagem_base64}" style="
                        width: min(150px, 30vw);
                        max-height: 86px;
                        object-fit: contain;
                        display: block;
                    " />
                    <div style="
                        color: #111111;
                        font-family: Arial, Helvetica, sans-serif;
                        font-size: clamp(0.78rem, 0.95vw, 0.98rem);
                        font-weight: 750;
                        line-height: 1.16;
                        letter-spacing: 0;
                        text-align: center;
                    ">
                        {t("Programa de Pós-Graduação<br />em Química")}
                    </div>
                </div>
                <div style="
                    text-align: center;
                    min-width: 0;
                ">
                    <div style="
                        display: block;
                    ">
                        <div style="
                            color: #111111;
                            font-family: Arial, Helvetica, sans-serif;
                            font-size: clamp(1.9rem, 3.2vw, 3.2rem);
                            font-weight: 850;
                            line-height: 1.02;
                            letter-spacing: 0;
                            text-align: center;
                        ">
                            CatAiLab
                        </div>
                    </div>
                    <div style="
                        color: #111111;
                        font-family: Arial, Helvetica, sans-serif;
                        font-size: clamp(0.95rem, 1.2vw, 1.18rem);
                        font-weight: 550;
                        line-height: 1.28;
                        letter-spacing: 0;
                        margin-top: 6px;
                        text-align: center;
                    ">
                        {t("Predição virtual de catalisadores e condições de síntese")}
                    </div>
                </div>
                <div style="
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    min-width: 0;
                    transform: translateX(19px);
                ">
                    {labtam_img}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title("CatAiLab")


def renderizar_logo_projeto_sidebar() -> None:
    """Renderiza a marca do projeto no painel lateral."""
    logo_html = ""
    if PROJECT_LOGO_PATH.exists():
        logo_base64 = base64.b64encode(PROJECT_LOGO_PATH.read_bytes()).decode("utf-8")
        logo_html = (
            "<div class='catialab-sidebar-project-logo'>"
            f"<img src='data:image/png;base64,{logo_base64}' alt='Logotipo CatAiLab'>"
            "</div>"
        )
    st.markdown(
        f"""
        <div class="catialab-sidebar-brand">
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def aplicar_estilo_interface() -> None:
    """Aplica ajustes visuais globais sem alterar o cabeçalho institucional."""
    st.markdown(
        """
        <style>
            :root {
                --catialab-green: #007A32;
                --catialab-blue: #1E88E5;
                --catialab-ink: #14213D;
                --catialab-line: #D8EEDC;
                --catialab-soft: #F5FBF7;
            }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #E7F6ED 0%, #F5FBF7 100%);
                border-right: 1px solid #B9DDC7;
                min-width: 270px;
            }
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3,
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] .stMarkdown {
                color: #173D2B;
            }
            .catialab-sidebar-brand {
                padding: 8px 6px 18px 6px;
                border-bottom: 1px solid #B9DDC7;
                margin-bottom: 12px;
                text-align: center;
            }
            .catialab-sidebar-brand-title {
                color: #14213D;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1.45rem;
                font-weight: 850;
                letter-spacing: 0;
            }
            .catialab-sidebar-brand-subtitle {
                color: #197A4B;
                font-size: 0.76rem;
                font-weight: 700;
                margin-top: 3px;
            }
            .catialab-sidebar-project-logo { display: flex; justify-content: center; align-items: center; margin: 0 0 10px 0; }
            .catialab-sidebar-project-logo img { width: min(160px, 82%); max-height: 82px; object-fit: contain; display: block; }
            section[data-testid="stSidebar"] .catialab-section-note {
                background: rgba(255, 255, 255, 0.72);
                border-color: #B9DDC7;
                color: #315843;
            }
            section[data-testid="stSidebar"] .catialab-section-note strong { color: #173D2B; }
            section[data-testid="stSidebar"] div[data-testid="stRadio"] label p { color: #315843; }
            section[data-testid="stSidebar"] div[data-testid="stPopover"] > button { width: 100%; min-height: 48px; justify-content: flex-start; border: 1px solid #A8D3B9; border-radius: 8px; background: rgba(255, 255, 255, 0.88); color: #173D2B; font-weight: 800; box-shadow: 0 2px 7px rgba(25, 122, 75, 0.06); }
            section[data-testid="stSidebar"] div[data-testid="stPopover"] > button *, section[data-testid="stSidebar"] div[data-testid="stPopover"] > button p, section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { font-weight: 850 !important; }
            section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { text-align: center; }
            section[data-testid="stSidebar"] button[kind="secondary"], section[data-testid="stSidebar"] button[kind="secondary"] p, section[data-testid="stSidebar"] button[kind="secondary"] span { font-weight: 850 !important; }
            section[data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover { border-color: #197A4B; background: #FFFFFF; color: #145F3B; }
            section[data-testid="stSidebar"] [data-testid="stPopoverBody"] div[data-testid="stColumn"] div[data-testid="stButton"] > button { min-height: 30px; min-width: 0; padding: 2px 0; border-radius: 4px; font-size: 0.68rem; line-height: 1; }
            section[data-testid="stSidebar"] [data-testid="stPopoverBody"] div[data-testid="stColumn"] div[data-testid="stButton"] > button[kind="primary"] { background: #197A4B; border-color: #197A4B; color: #FFFFFF; }
            section[data-testid="stSidebar"] div[data-testid="stPopover"] { margin-bottom: 7px; }
            .catialab-config-status { margin: 11px 0 13px 0; padding: 0; border: 0; background: transparent; color: #173D2B; font-size: 0.86rem; font-weight: 800; line-height: 1.55; text-align: center; }
            .catialab-config-status strong { color: #173D2B; font-weight: 850; }
            .catialab-dashboard-title {
                color: #14213D;
                font-family: Arial, Helvetica, sans-serif;
                font-size: clamp(1.55rem, 2.5vw, 2.35rem);
                font-weight: 850;
                letter-spacing: 0;
                margin: 0;
            }
            .catialab-dashboard-subtitle { color: #64748B; font-size: 0.98rem; margin: 4px 0 18px 0; }
            .catialab-summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 14px 0 20px 0; }
            .catialab-summary-card { min-height: 132px; padding: 17px 18px 14px 18px; border: 1px solid #DCE6EE; border-radius: 9px; background: #FFFFFF; box-shadow: 0 5px 16px rgba(20, 33, 61, 0.06); }
            .catialab-summary-label { color: #14213D; font-size: 0.82rem; font-weight: 800; }
            .catialab-summary-value { color: #218C3A; font-size: 1.9rem; font-weight: 900; line-height: 1.1; margin-top: 13px; }
            .catialab-summary-value.blue { color: #146CC1; }
            .catialab-summary-note { color: #64748B; font-size: 0.75rem; margin-top: 5px; }
            .catialab-summary-accent { color: #218C3A; font-size: 0.78rem; font-weight: 750; margin-top: 10px; }
            @media (max-width: 860px) {
                .catialab-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            }
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3 {
                color: #173D2B;
                letter-spacing: 0;
            }
            div[data-baseweb="select"] > div,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stTextInput"] input {
                border-color: #C9DFD0;
                border-radius: 8px;
                min-height: 42px;
            }
            div[data-testid="stNumberInput"] input:focus,
            div[data-testid="stTextInput"] input:focus {
                border-color: var(--catialab-blue);
                box-shadow: 0 0 0 1px var(--catialab-blue);
            }
            div[data-testid="stButton"] > button[kind="primary"] {
                min-height: 48px;
                border-radius: 8px;
                background: var(--catialab-blue);
                border: 1px solid var(--catialab-blue);
                font-weight: 800;
                box-shadow: 0 5px 12px rgba(30, 136, 229, 0.18);
            }
            section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] { display: block; width: min(190px, 100%); margin-left: auto; margin-right: auto; }
            div[data-testid="stButton"] > button[kind="primary"]:hover {
                background: #1565C0;
                border-color: #1565C0;
            }
            button[data-baseweb="tab"] {
                font-weight: 700;
                color: var(--catialab-ink);
            }
            div[data-baseweb="tab-list"] {
                gap: 4px;
                border-bottom: 1px solid var(--catialab-line);
            }
            .catialab-section-note {
                padding: 10px 12px;
                margin: 0 0 12px 0;
                border: 1px solid var(--catialab-line);
                border-left: 4px solid var(--catialab-blue);
                border-radius: 8px;
                background: #FFFFFF;
                color: #334155;
                font-size: 0.86rem;
                line-height: 1.35;
            }
            .catialab-section-note strong {
                display: block;
                color: var(--catialab-ink);
                margin-bottom: 3px;
            }
            @media (max-width: 860px) {
                div[data-baseweb="tab-list"] {
                    overflow-x: auto;
                    justify-content: flex-start;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_titulo_dashboard() -> None:
    """Apresenta o titulo executivo da tela principal conforme o painel de referencia."""
    st.markdown(
        "<div class='catialab-dashboard-title'>Recomendacoes de Catalisadores</div>"
        "<div class='catialab-dashboard-subtitle'>Triagem virtual orientada por IA para sua reacao alvo.</div>",
        unsafe_allow_html=True,
    )


def mostrar_resumo_dashboard(metricas_df: pd.DataFrame, prioritarios_df: pd.DataFrame, monte_carlo_df: pd.DataFrame) -> None:
    """Mostra quatro indicadores executivos no formato da referencia visual."""
    n_gerados = extrair_metrica(metricas_df, "candidatos gerados") or 0
    n_recomendados = extrair_metrica(metricas_df, "candidatos priorit") or len(prioritarios_df)
    n_refinados = extrair_metrica(metricas_df, "candidatos refinados") or len(monte_carlo_df)
    top = prioritarios_df.iloc[0] if not prioritarios_df.empty else pd.Series(dtype=object)
    formula = valor_linha(top, ["formula", "f"], "Aguardando triagem")
    score = pd.to_numeric(pd.Series([valor_linha(top, ["score", "final"], np.nan)]), errors="coerce").iloc[0]
    confiabilidade = extrair_confiabilidade(top) if not prioritarios_df.empty else "-"
    confiabilidade_num = {"alta": "0,86", "média": "0,68", "media": "0,68", "baixa": "0,42"}.get(normalizar_texto(confiabilidade), "-")
    rendimento = pd.to_numeric(pd.Series([valor_linha(top, ["rendimento", "prevista"], np.nan)]), errors="coerce").iloc[0]
    desempenho = "-" if pd.isna(rendimento) else f"{float(rendimento):.1f}"
    cards = [("Candidato para síntese", formula, f"{n_recomendados} selecionados de {n_gerados}", ""), ("Confiabilidade", confiabilidade_num, "média da recomendação", "Alta" if normalizar_texto(confiabilidade) == "alta" else confiabilidade.capitalize()), ("Triagem", str(n_gerados), "catalisadores avaliados", "Concluída" if n_gerados else "Aguardando dados"), ("Melhor desempenho previsto", desempenho, "índice de rendimento", f"Catalisador: {formula}")]
    blocos = [f"<div class='catialab-summary-card'><div class='catialab-summary-label'>{html.escape(str(rotulo))}</div><div class='catialab-summary-value {'blue' if indice == 2 else ''}'>{html.escape(str(valor))}</div><div class='catialab-summary-note'>{html.escape(str(nota))}</div><div class='catialab-summary-accent'>{html.escape(str(rodape))}</div></div>" for indice, (rotulo, valor, nota, rodape) in enumerate(cards)]
    st.markdown(f"<div class='catialab-summary-grid'>{''.join(blocos)}</div>", unsafe_allow_html=True)


def mostrar_indicadores_quimicos(prioritarios_df: pd.DataFrame) -> None:
    """Resume os descritores químicos em indicadores legíveis para decisão experimental."""
    if prioritarios_df.empty:
        return
    top = prioritarios_df.iloc[0]
    estabilidade = pd.to_numeric(pd.Series([valor_linha(top, ["estabilidade", "termodinamica"], np.nan)]), errors="coerce").iloc[0]
    adsorcao = pd.to_numeric(pd.Series([valor_linha(top, ["energia", "adsorcao", "volcano"], np.nan)]), errors="coerce").iloc[0]
    coque = pd.to_numeric(pd.Series([valor_linha(top, ["resistencia", "coque"], np.nan)]), errors="coerce").iloc[0]
    distancia = pd.to_numeric(pd.Series([valor_linha(top, ["distancia", "otimo", "volcano"], np.nan)]), errors="coerce").iloc[0]
    resistencia = "-" if pd.isna(coque) else ("Alta" if coque >= 0.70 else "Moderada" if coque >= 0.45 else "Baixa")
    adsorcao_txt = "-" if pd.isna(adsorcao) else f"{float(adsorcao):.3f} eV"
    distancia_txt = "-" if pd.isna(distancia) else ("Próxima do ótimo" if distancia <= 0.15 else "Intermediária" if distancia <= 0.30 else "Distante do ótimo")
    mostrar_linha_cartoes("Indicadores químicos do candidato para síntese", [
        ("Estabilidade termodinâmica", "-" if pd.isna(estabilidade) else f"{float(estabilidade):.3f} eV/átomo", False),
        ("Energia de adsorção", adsorcao_txt, True),
        ("Posição no gráfico vulcão", distancia_txt, False),
        ("Resistência à deposição de carbono", resistencia, True),
    ])


def renderizar_navegacao() -> str:
    """Exibe a navegacao principal e o seletor de idioma."""
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "triagem"
    if "idioma" not in st.session_state:
        st.session_state["idioma"] = "pt"

    opcoes = [
        ("triagem", "Triagem", "nav_triagem"),
        ("sobre", "Sobre", "nav_sobre"),
        ("pesquisa", "Pesquisa", "nav_pesquisa"),
        ("contato", "Contato", "nav_contato"),
    ]
    colunas = st.columns([1.12, 1.0, 1.0, 1.0, 0.36])
    for coluna, (pagina, rotulo, chave) in zip(colunas[:-1], opcoes):
        tipo = "primary" if st.session_state["pagina_atual"] == pagina else "secondary"
        if coluna.button(t(rotulo), key=chave, type=tipo, width="stretch"):
            st.session_state["pagina_atual"] = pagina
            st.rerun()

    bandeira = "🇺🇸" if idioma_atual() == "pt" else "🇧🇷"
    rotulo_idioma = "Translate to English" if idioma_atual() == "pt" else "Traduzir para portugues"
    if colunas[-1].button(bandeira, key="nav_idioma", help=rotulo_idioma, width="stretch"):
        st.session_state["idioma"] = "en" if idioma_atual() == "pt" else "pt"
        st.rerun()
    st.divider()
    return st.session_state["pagina_atual"]


def renderizar_pagina_institucional(pagina: str) -> None:
    """Apresenta informacoes institucionais fora do fluxo de triagem."""
    dados = dados_pesquisador()
    telefone_numerico = re.sub(r"\D", "", dados["telefone"])
    telefone_link = f"+{telefone_numerico}" if telefone_numerico.startswith("55") else f"+55{telefone_numerico}"

    if pagina == "sobre":
        st.markdown(f"<h2 style='text-align:center;'>{html.escape(t('Sobre'))}</h2>", unsafe_allow_html=True)
        if idioma_atual() == "en":
            finalidade = (
                "CatAiLab is a virtual-screening platform that prioritizes catalysts and synthesis "
                "conditions for CO2 methanation, CH4 reforming, and RWGS. It supports experimental "
                "decisions using thermodynamic stability, chemical descriptors, DFT data or proxies, "
                "operational robustness, uncertainty, and synthesis criteria."
            )
            desenvolvimento = (
                "Its development integrates Materials Project, OQMD, and Catalysis-Hub with matminer "
                "and pymatgen descriptors, stability assessment, volcano-style analysis, Monte Carlo "
                "simulation, chemometrics, and recommendations for support and synthesis route."
            )
            titulo_finalidade, titulo_desenvolvimento = "Purpose", "Development"
        else:
            finalidade = (
                "CatAiLab e uma plataforma de triagem virtual para priorizar catalisadores e condicoes "
                "de sintese para metanacao de CO2, reforma de CH4 e RWGS. Ela apoia a decisao "
                "experimental com estabilidade termodinamica, descritores quimicos, dados ou proxies "
                "DFT, robustez operacional, incerteza e criterios de sintese."
            )
            desenvolvimento = (
                "O desenvolvimento integra Materials Project, OQMD e Catalysis-Hub com descritores "
                "do matminer e pymatgen, avaliacao de estabilidade, analise tipo volcano, simulacao "
                "de Monte Carlo, quimiometria e recomendacao de suporte e rota de sintese."
            )
            titulo_finalidade, titulo_desenvolvimento = "Finalidade", "Desenvolvimento"
        col1, col2 = st.columns(2)
        col1.markdown(cartao_texto_html(titulo_finalidade, finalidade), unsafe_allow_html=True)
        col2.markdown(cartao_texto_html(titulo_desenvolvimento, desenvolvimento), unsafe_allow_html=True)

    elif pagina == "pesquisa":
        st.markdown(f"<h2 style='text-align:center;'>{html.escape(t('Pesquisa'))}</h2>", unsafe_allow_html=True)
        if idioma_atual() == "en":
            perfil = f"{dados['nome']} is the researcher and developer responsible for CatAiLab."
            titulo_perfil, titulo_citacao = "Researcher and developer", "Suggested citation"
            citacao = (
                "MAIA, Allan. CatAiLab: virtual screening of catalysts and synthesis conditions. "
                "Scientific software. Federal University of Rio Grande do Norte, 2026. "
                "Available at: https://triagemufrn.streamlit.app/."
            )
        else:
            perfil = f"{dados['nome']} e o pesquisador e desenvolvedor responsavel pelo CatAiLab."
            titulo_perfil, titulo_citacao = "Pesquisador e desenvolvedor", "Forma de citacao"
            citacao = (
                "MAIA, Allan. CatAiLab: triagem virtual de catalisadores e condicoes de sintese. "
                "Software cientifico. Universidade Federal do Rio Grande do Norte, 2026. "
                "Disponivel em: https://triagemufrn.streamlit.app/."
            )
        col1, col2 = st.columns(2)
        col1.markdown(cartao_texto_html(titulo_perfil, perfil), unsafe_allow_html=True)
        col2.markdown(cartao_texto_html(titulo_citacao, citacao), unsafe_allow_html=True)
        st.link_button("Curriculum Lattes" if idioma_atual() == "en" else "Curriculo Lattes", dados["lattes"])

    elif pagina == "contato":
        st.markdown(f"<h2 style='text-align:center;'>{html.escape(t('Contato'))}</h2>", unsafe_allow_html=True)
        titulo = "Contact" if idioma_atual() == "en" else "Contato profissional"
        texto = f"Email: {dados['email']}\n\nTelefone: {dados['telefone']}\n\nCurriculo Lattes: {dados['lattes']}"
        col1, col2 = st.columns([1.2, 0.8])
        col1.markdown(cartao_texto_html(titulo, texto), unsafe_allow_html=True)
        with col2:
            st.link_button("Email", f"mailto:{dados['email']}", width="stretch")
            st.link_button("WhatsApp / telefone", f"tel:{telefone_link}", width="stretch")
            st.link_button("Curriculo Lattes", dados["lattes"], width="stretch")


TABELA_PERIODICA = [
    ["H", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "He"],
    ["Li", "Be", None, None, None, None, None, None, None, None, None, None, "B", "C", "N", "O", "F", "Ne"],
    ["Na", "Mg", None, None, None, None, None, None, None, None, None, None, "Al", "Si", "P", "S", "Cl", "Ar"],
    ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
    ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
    ["Cs", "Ba", None, "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
    ["Fr", "Ra", None, "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
    [None, None, None, "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
    [None, None, None, "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
]


def selecionar_metais_tabela_periodica(n_metais: int) -> list[str]:
    """Exibe uma tabela periódica clicável e retorna os metais ativos selecionados."""
    chave_selecao = "config_metal_selecionados"
    selecionados = list(dict.fromkeys(st.session_state.get(chave_selecao, [])))
    if n_metais <= 0:
        st.caption("Selecione primeiro o número de metais ativos.")
        return []

    selecionados = selecionados[:n_metais]
    st.session_state[chave_selecao] = selecionados
    st.caption(f"Selecione até {n_metais} elemento(s). Clique novamente para remover.")
    for linha, elementos in enumerate(TABELA_PERIODICA):
        colunas = st.columns(18, gap="small")
        for coluna, elemento in enumerate(elementos):
            if elemento is None:
                continue
            selecionado = elemento in selecionados
            if colunas[coluna].button(elemento, key=f"periodica_{linha}_{elemento}", type="primary" if selecionado else "secondary", help=f"Selecionar {elemento}", width="stretch"):
                if selecionado:
                    selecionados.remove(elemento)
                elif len(selecionados) < n_metais:
                    selecionados.append(elemento)
                else:
                    st.warning(f"Selecione no máximo {n_metais} elemento(s).")
                st.session_state[chave_selecao] = selecionados
                st.rerun()

    if selecionados:
        st.markdown(f"**Seleção atual:** {', '.join(selecionados)}")
        if st.button("Limpar seleção", key="limpar_metais_periodica", width="stretch"):
            st.session_state[chave_selecao] = []
            st.rerun()
    return selecionados


st.set_page_config(page_title="CatAiLab", layout="wide")
aplicar_estilo_interface()
renderizar_cabecalho()
pagina_atual = renderizar_navegacao()
if pagina_atual != "triagem":
    renderizar_pagina_institucional(pagina_atual)
    st.stop()

with st.sidebar:
    renderizar_logo_projeto_sidebar()
    st.caption("Configurações da Triagem")

    with st.popover("Reação", icon=":material/science:", width="stretch"):
        reacao = st.selectbox("Reação-alvo", ["metanacao", "reforma", "rwgs"], index=None, placeholder="Selecione a reação", format_func=lambda x: {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}[x], key="config_reacao")

    with st.popover("Número de metais ativos", icon=":material/format_list_numbered:", width="stretch"):
        n_metais_selecionado = st.selectbox("Quantidade de metais ativos", [1, 2, 3, 4], index=None, placeholder="Selecione a quantidade", key="config_n_metais")
    n_metais = int(n_metais_selecionado or 0)

    with st.popover("Metais ativos", icon=":material/hub:", width="stretch"):
        metais = selecionar_metais_tabela_periodica(n_metais)

    with st.popover("Promotor", icon=":material/add_circle:", width="stretch"):
        modo_promotor = st.radio("Uso de promotor", ["Sem promotor", "Com promotor"], index=None, horizontal=True, key="config_modo_promotor")
        promotor = ""
        if modo_promotor == "Com promotor":
            opcoes_promotores = ["Ce", "La", "Mg", "K", "Na", "Zr", "Sr", "Pr", "Nd", "Ca", "Y", "Outro"]
            opcao_promotor = st.selectbox("Elemento promotor", opcoes_promotores, index=None, placeholder="Selecione o promotor", key="config_promotor_opcao")
            if opcao_promotor == "Outro":
                opcao_promotor = st.text_input("Símbolo do promotor", value="", max_chars=2, key="config_promotor_outro")
            promotor = limpar_simbolo_quimico(opcao_promotor or "")

    with st.popover("Pasta de saída", icon=":material/folder_open:", width="stretch"):
        destino_saida = st.radio("Local de salvamento", ["Usar pasta padrão", "Escolher outra pasta"], horizontal=False)
        if destino_saida == "Escolher outra pasta":
            output_dir_texto = st.text_input("Pasta de destino dos resultados", value="", placeholder="Digite ou cole a pasta de destino")
        else:
            output_dir_texto = ""

    resumo_metais = ", ".join(metais) if metais else "não definidos"
    resumo_promotor = promotor if promotor else ("sem promotor" if modo_promotor == "Sem promotor" else "não definido")
    resumo_reacao = {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}.get(reacao, "não definida")
    st.markdown(f"<div class='catialab-config-status'><strong>Configuração atual</strong><br>{html.escape(resumo_reacao)}<br>{html.escape(resumo_metais)}<br>{html.escape(resumo_promotor)}</div>", unsafe_allow_html=True)
    espaco_esquerdo, coluna_executar, espaco_direito = st.columns([0.35, 1.8, 0.35])
    with coluna_executar:
        executar = st.button(t("Executar triagem"), type="primary", width="stretch")

metais_unicos = list(dict.fromkeys(metais))
metais_repetidos = len(metais_unicos) != len(metais)
metais = metais_unicos
output_dir = Path(output_dir_texto).expanduser().resolve() if output_dir_texto else DEFAULT_OUTPUT_DIR.resolve()

if metais_repetidos:
    st.warning("Há metais ativos repetidos. Cada metal ativo deve ser informado apenas uma vez.")
elif n_metais and len(metais) != n_metais:
    st.warning("Preencha todos os campos de metal ativo antes de executar.")

if executar:
    if not reacao:
        st.error("Selecione a reação-alvo.")
    elif not n_metais:
        st.error("Selecione o número de metais ativos.")
    elif not metais:
        st.error("Informe pelo menos um metal ativo.")
    elif metais_repetidos:
        st.error("Remova metais ativos repetidos antes de executar.")
    elif len(metais) != n_metais:
        st.error("Preencha todos os campos de metal ativo antes de executar.")
    elif modo_promotor is None:
        st.error("Informe se a triagem será realizada com ou sem promotor.")
    elif modo_promotor == "Com promotor" and not promotor:
        st.error("Selecione ou digite o promotor.")
    else:
        try:
            with st.spinner("Executando consultas, descritores, ranking, incerteza, validação avançada e figuras. Esta etapa pode demorar."):
                notebook_executado = executar_triagem(reacao, metais, promotor, output_dir)
        except Exception as erro_execucao:
            st.error("A triagem nao foi concluida. Verifique os detalhes tecnicos abaixo.")
            with st.expander("Detalhes tecnicos do erro"):
                st.code("".join(traceback.format_exception(erro_execucao))[-6000:])
        else:
            st.session_state["ultima_reacao"] = reacao
            st.session_state["ultima_saida"] = str(output_dir)
            st.session_state["ultimo_notebook"] = str(notebook_executado)
            st.success("Triagem concluída.")

reacao_resultado = st.session_state.get("ultima_reacao") or reacao or "metanacao"
saida_resultado = Path(st.session_state.get("ultima_saida", str(output_dir)))
paths = caminhos_resultado(saida_resultado, reacao_resultado)

if "ultimo_notebook" in st.session_state:
    st.info("Execução concluída e registrada para auditoria local.")

prioritarios_df = ler_csv(paths["prioritarios"])
ranking_df = ler_csv(paths["ranking"])
classificacao_df = ler_csv(paths["classificacao"])
metricas_df = ler_csv(paths["metricas"])
monte_carlo_df = ler_csv(paths["monte_carlo"])
desempenho_df = ler_csv(paths["desempenho"])
figuras_df = ler_csv(paths["figuras"])
dominio_df = ler_csv(paths["dominio"])
pareto_df = ler_csv(paths["pareto"])
validacao_quimio_df = ler_csv(paths["validacao_quimio"])
validacao_avancada_df = ler_csv(paths["validacao_avancada"])
correcao_temperatura_df = ler_csv(paths["correcao_temperatura"])

renderizar_titulo_dashboard()
mostrar_resumo_dashboard(metricas_df, prioritarios_df, monte_carlo_df)
mostrar_funil_visual(metricas_df, prioritarios_df, monte_carlo_df)
mostrar_painel_decisao(metricas_df, prioritarios_df, classificacao_df, monte_carlo_df, desempenho_df)

aba_geral, aba_candidatos, aba_ranking, aba_incerteza, aba_robustez, aba_quimica, aba_validacao, aba_figuras, aba_arquivos = st.tabs([
    "Visão geral",
    "Candidatos",
    "Classifica\u00e7\u00e3o",
    "Incerteza",
    "Robustez e opera\u00e7\u00e3o",
    "Química",
    "Validação",
    "Visualização científica",
    "Arquivos",
])

with aba_geral:
    mostrar_top2_recomendados_amigavel(prioritarios_df)

with aba_candidatos:
    mostrar_tabela("Candidatos prioritários para síntese", prioritarios_df, linhas=20)

with aba_ranking:
    top10_df = montar_classificacao_top10([classificacao_df, monte_carlo_df, ranking_df], linhas=10)
    mostrar_classificacao_centralizada("Classifica\u00e7\u00e3o dos 10 primeiros", top10_df)

with aba_incerteza:
    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        mostrar_tabela("Incerteza Monte Carlo", monte_carlo_df, linhas=30)
    with col2:
        metricas_confianca_df = filtrar_metricas_por_termos(
            metricas_df,
            ["confianca", "confiabilidade", "incerteza", "monte carlo", "ic95"],
        )
        mostrar_tabela("Métricas de confiança", metricas_confianca_df, linhas=30)

with aba_robustez:
    mostrar_robustez_operacao(metricas_df, prioritarios_df, classificacao_df, monte_carlo_df, desempenho_df)

with aba_quimica:
    mostrar_indicadores_quimicos(prioritarios_df)
    col1, col2 = st.columns([1.1, 1.0])
    with col1:
        mostrar_tabela("Descritores essenciais dos recomendados", selecionar_colunas_tecnicas(prioritarios_df), linhas=10)
    with col2:
        metricas_quimicas_df = filtrar_metricas_por_termos(
            metricas_df,
            ["dft", "volcano", "descritores", "quimica", "quimiometria", "adsorcao"],
        )
        mostrar_tabela("Métricas químicas e DFT", metricas_quimicas_df, linhas=30)

with aba_validacao:
    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        mostrar_tabela("Domínio de aplicabilidade", dominio_df, linhas=20)
    with col2:
        mostrar_tabela("Pareto e desejabilidade", pareto_df, linhas=20)
    metricas_validacao_df = filtrar_metricas_por_termos(
        metricas_df,
        ["dominio", "pareto", "desejabilidade", "hotelling", "q residual", "quimiometria"],
    )
    mostrar_tabela("Métricas de validação científica", metricas_validacao_df, linhas=30)
    mostrar_tabela("Validação quimiométrica", validacao_quimio_df, linhas=30)
    mostrar_tabela("Validação avançada dos prioritários", validacao_avancada_df, linhas=10)
    mostrar_tabela("Correção de temperatura no Top 10", correcao_temperatura_df, linhas=10)

with aba_figuras:
    mostrar_visualizacao_cientifica_plotly(prioritarios_df, classificacao_df, ranking_df, monte_carlo_df)
    st.divider()
    mostrar_figuras(figuras_df)

with aba_arquivos:
    st.markdown("<h3 style='text-align:center;'>Exporta\u00e7\u00f5es</h3>", unsafe_allow_html=True)
    if paths["excel"].exists():
        st.download_button(
            "Baixar resultados em Excel",
            data=paths["excel"].read_bytes(),
            file_name=paths["excel"].name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("O arquivo Excel será disponibilizado após a execução da triagem.")
    if paths["html"].exists():
        st.download_button(
            "Baixar relatório HTML",
            data=paths["html"].read_bytes(),
            file_name=paths["html"].name,
            mime="text/html",
        )
    arquivos_disponiveis = [
        ("Candidatos prioritários", paths["prioritarios"]),
        ("Ranking completo", paths["ranking"]),
        ("Métricas", paths["metricas"]),
        ("Monte Carlo", paths["monte_carlo"]),
        ("Domínio de aplicabilidade", paths["dominio"]),
        ("Pareto e desejabilidade", paths["pareto"]),
        ("Validação quimiométrica", paths["validacao_quimio"]),
        ("Validação avançada", paths["validacao_avancada"]),
        ("Correção de temperatura Top 10", paths["correcao_temperatura"]),
        ("Índice de figuras", paths["figuras"]),
    ]
    for rotulo, caminho in arquivos_disponiveis:
        if caminho.exists():
            st.download_button(
                f"Baixar {rotulo} CSV",
                data=caminho.read_bytes(),
                file_name=caminho.name,
                mime="text/csv",
            )
