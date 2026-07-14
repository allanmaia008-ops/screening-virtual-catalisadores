from __future__ import annotations

import base64
import html
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import nbformat
import pandas as pd
import streamlit as st
from nbclient import NotebookClient


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
NOTEBOOK_PATH = APP_DIR / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
BRASAO_PATH = APP_DIR / "assets" / "logo_ufrn_header.png"
PROJECT_LOGO_PATH = APP_DIR / "assets" / "logo_triagem_catalitica.png"


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
    return texto.lower().replace("�", "").strip()


def encontrar_coluna(dataframe: pd.DataFrame, termos: list[str]) -> str | None:
    """Encontra a primeira coluna cujo nome contenha todos os termos informados."""
    termos_norm = [normalizar_texto(termo) for termo in termos]
    for coluna in dataframe.columns:
        coluna_norm = normalizar_texto(coluna)
        if all(termo in coluna_norm for termo in termos_norm):
            return coluna
    return None


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


def cartao_html(rotulo: str, valor: str, destaque: bool = False) -> str:
    """Cria HTML de cartão centralizado."""
    cor_valor = "#C62828"
    fundo = "#F3FBFF" if destaque else "#F6FBFE"
    return f"""
    <div style="
        min-height: 92px;
        padding: 12px 9px;
        border: 1px solid #D8EEF8;
        border-radius: 12px;
        background: {fundo};
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    ">
        <div style="
            color: #526F82;
            font-family: Arial, Helvetica, sans-serif;
            font-size: clamp(1.0rem, 1.08vw, 1.14rem);
            font-weight: 850;
            line-height: 1.14;
            margin-bottom: 7px;
        ">{html.escape(rotulo)}</div>
        <div style="
            color: {cor_valor};
            font-family: Arial, Helvetica, sans-serif;
            font-size: clamp(0.82rem, 0.95vw, 1.0rem);
            font-weight: 750;
            line-height: 1.16;
            text-align: center;
            overflow-wrap: anywhere;
        ">{html.escape(valor)}</div>
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
        ("Gerados", formatar_valor(n_gerados)),
        ("Viáveis", formatar_valor(n_viaveis)),
        ("Refinados", formatar_valor(n_refinados)),
        ("Recomendados", formatar_valor(n_recomendados), True),
        ("Viabilidade", formatar_valor(taxa_viabilidade, percentual=True)),
    ]
    colunas = st.columns(len(cards))
    for coluna, card in zip(colunas, cards):
        rotulo, valor = card[0], card[1]
        destaque = bool(card[2]) if len(card) > 2 else False
        coluna.markdown(cartao_html(rotulo, valor, destaque=destaque), unsafe_allow_html=True)


def mostrar_linha_cartoes(titulo: str, cards: list[tuple[str, str, bool]]) -> None:
    """Mostra uma linha de cartoes de decisao."""
    st.markdown(f"<h4 style='text-align:center;'>{html.escape(titulo)}</h4>", unsafe_allow_html=True)
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
        st.info("Execute a triagem para visualizar o painel de decis\u00e3o.")
        return

    top = prioritarios_df.iloc[0]
    candidato = valor_linha(top, ["formula"])
    suporte = valor_linha(top, ["suporte"])
    regime = valor_linha(top, ["regime"])
    score_final = valor_linha(top, ["score", "final"])
    confiabilidade = extrair_confiabilidade(top)
    temperatura = valor_linha(top, ["temperatura"])
    pressao = valor_linha(top, ["press"])
    razao = valor_linha(top, ["razao"])

    mostrar_linha_cartoes(
        "Resultado principal",
        [
            ("Candidato para s\u00edntese", candidato, True),
            ("Suporte sugerido", suporte, False),
            ("Regime recomendado", regime, False),
            ("Score final", formatar_valor(score_final), True),
            ("Confiabilidade", confiabilidade, False),
        ],
    )

    fonte_score = classificacao_df if not classificacao_df.empty else prioritarios_df
    if len(fonte_score) < 3 and not monte_carlo_df.empty:
        fonte_score = monte_carlo_df
    coluna_score = encontrar_coluna(fonte_score, ["score", "final"]) or encontrar_coluna(fonte_score, ["media", "monte", "carlo"])
    score_medio = None
    diferenca_top = None
    empate = "-"
    if coluna_score:
        scores = pd.to_numeric(fonte_score[coluna_score], errors="coerce").dropna().head(10)
        if not scores.empty:
            score_medio = float(scores.mean())
        if len(scores) >= 2:
            diferenca_top = abs(float(scores.iloc[0]) - float(scores.iloc[1]))
            empate = "sim" if diferenca_top <= 0.01 else "n\u00e3o"

    mostrar_linha_cartoes(
        "Qualidade do ranking",
        [
            ("Candidatos no Top 10", formatar_valor(len(monte_carlo_df) if not monte_carlo_df.empty else len(classificacao_df)), False),
            ("Score m\u00e9dio Top 10", formatar_valor(score_medio), True),
            ("Diferen\u00e7a 1\u00ba-2\u00ba", formatar_valor(diferenca_top), False),
            ("Empate t\u00e9cnico", empate, False),
        ],
    )

    estabilidade_media = numero_coluna(classificacao_df, ["estabilidade"], linhas=10)
    if estabilidade_media is None:
        estabilidade_media = numero_coluna(prioritarios_df, ["estabilidade"], linhas=10)
    melhor_estabilidade = numero_coluna(classificacao_df, ["estabilidade"], linhas=10, menor=True)
    if melhor_estabilidade is None:
        melhor_estabilidade = numero_coluna(prioritarios_df, ["estabilidade"], linhas=10, menor=True)
    coque = numero_coluna(classificacao_df, ["coque"], linhas=10)
    if coque is None:
        coque = numero_coluna(prioritarios_df, ["coque"], linhas=10)

    mostrar_linha_cartoes(
        "Viabilidade qu\u00edmica",
        [
            ("Estabilidade m\u00e9dia", f"{formatar_valor(estabilidade_media)} eV/\u00e1tomo" if estabilidade_media is not None else "-", False),
            ("Melhor estabilidade", f"{formatar_valor(melhor_estabilidade)} eV/\u00e1tomo" if melhor_estabilidade is not None else "-", False),
            ("Resist\u00eancia a coque", formatar_valor(coque), False),
            ("Viabilidade global", formatar_valor(extrair_metrica(metricas_df, "taxa de viabilidade"), percentual=True), True),
        ],
    )

    prob_mc = numero_coluna(monte_carlo_df, ["probabilidade", "top"], linhas=10, maior=True)
    incert_mc = numero_coluna(monte_carlo_df, ["desvio", "score"], linhas=10)
    conf_predominante = "-"
    coluna_conf = encontrar_coluna(classificacao_df, ["confiabilidade"]) or encontrar_coluna(prioritarios_df, ["confiabilidade"])
    fonte_conf = classificacao_df if coluna_conf in classificacao_df.columns else prioritarios_df
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


def mostrar_funil_visual(metricas_df: pd.DataFrame, prioritarios_df: pd.DataFrame, monte_carlo_df: pd.DataFrame) -> None:
    """Mostra a triagem como um fluxo vertical com criterios e retencao."""
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
            "rotulo": "Candidatos gerados",
            "valor": n_gerados,
            "criterio": "Combina\u00e7\u00f5es de fase ativa, promotor e suporte definidas pela gera\u00e7\u00e3o de candidatos.",
            "retencao": retencao(n_gerados, None),
            "cor": "#168AC8",
        },
        {
            "rotulo": "Candidatos vi\u00e1veis",
            "valor": n_viaveis,
            "criterio": "Filtro de estabilidade termodin\u00e2mica, viabilidade qu\u00edmica e descritores iniciais.",
            "retencao": retencao(n_viaveis, n_gerados),
            "cor": "#2FA7B2",
        },
        {
            "rotulo": "Candidatos refinados",
            "valor": n_refinados,
            "criterio": "Refinamento por descritores catal\u00edticos, dados DFT ou proxies e penaliza\u00e7\u00e3o de incerteza.",
            "retencao": retencao(n_refinados, n_viaveis),
            "cor": "#0B6F8F",
        },
        {
            "rotulo": "Recomendados para s\u00edntese",
            "valor": n_recomendados,
            "criterio": "Sele\u00e7\u00e3o final por score multicrit\u00e9rio, robustez Monte Carlo e condi\u00e7\u00f5es desej\u00e1veis de s\u00edntese.",
            "retencao": retencao(n_recomendados, n_refinados),
            "cor": "#C7A548",
        },
    ]
    blocos = []
    for indice, etapa in enumerate(etapas):
        conector = "" if indice == len(etapas) - 1 else '<div class="fluxo-conector"></div>'
        blocos.append(
            f"""
            <div class="fluxo-item">
                <div class="fluxo-marcador" style="background:{etapa['cor']};">{indice + 1}</div>
                <div class="fluxo-card">
                    <div class="fluxo-topo">
                        <span>{html.escape(etapa['rotulo'])}</span>
                        <strong>{html.escape(formatar_valor(etapa['valor']))}</strong>
                    </div>
                    <div class="fluxo-criterio">{html.escape(etapa['criterio'])}</div>
                    <div class="fluxo-retencao">Reten\u00e7\u00e3o nesta etapa: <strong>{html.escape(etapa['retencao'])}</strong></div>
                </div>
            </div>
            {conector}
            """
        )
    st.html(
        f"""
        <style>
            .fluxo-triagem {{
                padding: 14px 14px 12px 14px;
                border: 1px solid #D8EEF8;
                border-radius: 12px;
                background: #FFFFFF;
            }}
            .fluxo-titulo {{
                color: #0B4F7A;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 1.05rem;
                font-weight: 800;
                margin-bottom: 12px;
            }}
            .fluxo-item {{
                display: grid;
                grid-template-columns: 34px minmax(0, 1fr);
                gap: 10px;
                align-items: start;
            }}
            .fluxo-marcador {{
                width: 34px;
                height: 34px;
                border-radius: 999px;
                color: #FFFFFF;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.92rem;
                font-weight: 850;
                box-shadow: 0 2px 8px rgba(11, 79, 122, 0.16);
            }}
            .fluxo-card {{
                border: 1px solid #E3EFF5;
                border-radius: 10px;
                background: #F8FCFE;
                padding: 10px 12px;
            }}
            .fluxo-topo {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 12px;
                color: #0B4F7A;
                font-family: Arial, Helvetica, sans-serif;
                font-weight: 800;
            }}
            .fluxo-topo strong {{
                color: #168AC8;
                font-size: 1.28rem;
                white-space: nowrap;
            }}
            .fluxo-criterio {{
                color: #526F82;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.86rem;
                line-height: 1.28;
                margin-top: 5px;
            }}
            .fluxo-retencao {{
                color: #315A6F;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.82rem;
                margin-top: 7px;
            }}
            .fluxo-conector {{
                width: 2px;
                height: 18px;
                background: #BFDDEB;
                margin: 4px 0 4px 16px;
            }}
        </style>
        <div class="fluxo-triagem">
            <div class="fluxo-titulo">Fluxo vertical da triagem</div>
            {''.join(blocos)}
        </div>
        """
    )


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
                border: 1px solid #E3EFF5;
                border-radius: 10px;
                background: #FFFFFF;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            ">
                <div style="
                    color: #60798A;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 0.86rem;
                    font-weight: 650;
                    line-height: 1.16;
                    margin-bottom: 8px;
                ">{html.escape(rotulo)}</div>
                <div style="
                    color: #0B4F7A;
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
    mp_api_key = obter_mp_api_key()
    if mp_api_key:
        os.environ["MP_API_KEY"] = mp_api_key
    configurar_banco_incremental_github()
    notebook = preparar_notebook_parametrizado(reacao, metais, promotor, output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metais_slug = slug_texto("_".join(metais))
    promotor_slug = slug_texto(promotor)
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
        "excel": output_dir / f"{prefixo}_resultados.xlsx",
        "html": output_dir / f"{prefixo}_relatorio.html",
        "resumo": output_dir / f"{prefixo}_resumo.json",
    }


def mostrar_tabela(titulo: str, dataframe: pd.DataFrame, linhas: int = 20) -> None:
    """Mostra uma tabela apenas quando ela existe."""
    st.markdown(f"<h3 style='text-align:center;'>{html.escape(titulo)}</h3>", unsafe_allow_html=True)
    if dataframe.empty:
        st.info("Tabela ainda não disponível.")
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
                color: #0B4F7A;
                background: #FFFFFF;
                border: 1px solid #D8EEF8;
                border-radius: 10px;
                overflow: hidden;
            }}
            .classificacao-top10 th {{
                background: #EAF7FC;
                color: #0B4F7A;
                font-weight: 850;
                text-align: center;
                padding: 11px 14px;
                border-bottom: 1px solid #CFE7F2;
            }}
            .classificacao-top10 td {{
                text-align: center;
                padding: 10px 14px;
                border-bottom: 1px solid #EDF4F8;
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
        projeto_base64 = base64.b64encode(PROJECT_LOGO_PATH.read_bytes()).decode("utf-8") if PROJECT_LOGO_PATH.exists() else ""
        projeto_img = (
            f"""<img src="data:image/png;base64,{projeto_base64}" style="
                width: min(320px, 26vw);
                max-height: 120px;
                object-fit: contain;
                display: block;
            " />"""
            if projeto_base64
            else ""
        )
        st.markdown(
            f"""
            <div style="
                width: 100%;
                padding: 12px 18px;
                margin: 0 auto 14px auto;
                background: linear-gradient(180deg, #F3FBFF 0%, #EAF7FC 100%);
                border-radius: 14px;
                border: 1px solid #D8EEF8;
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
                        color: #0B4F7A;
                        font-family: Arial, Helvetica, sans-serif;
                        font-size: clamp(0.78rem, 0.95vw, 0.98rem);
                        font-weight: 750;
                        line-height: 1.16;
                        letter-spacing: 0;
                        text-align: center;
                    ">
                        Programa de Pós-Graduação<br />em Química
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
                            color: #168AC8;
                            font-family: Arial, Helvetica, sans-serif;
                            font-size: clamp(1.9rem, 3.2vw, 3.2rem);
                            font-weight: 850;
                            line-height: 1.02;
                            letter-spacing: 0;
                            text-align: center;
                        ">
                            Screening Virtual
                        </div>
                    </div>
                    <div style="
                        color: #526F82;
                        font-family: Arial, Helvetica, sans-serif;
                        font-size: clamp(0.95rem, 1.2vw, 1.18rem);
                        font-weight: 550;
                        line-height: 1.28;
                        letter-spacing: 0;
                        margin-top: 6px;
                        text-align: center;
                    ">
                        Predição virtual de catalisadores e condições de síntese
                    </div>
                </div>
                <div style="
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    min-width: 0;
                    transform: translateX(19px);
                ">
                    {projeto_img}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title("Screening Virtual")


st.set_page_config(page_title="Triagem virtual de catalisadores", layout="wide")
renderizar_cabecalho()

with st.sidebar:
    st.header("Configuração")
    reacao = st.selectbox("Reação", ["metanacao", "reforma", "rwgs"], format_func=lambda x: {"metanacao": "Metanação de CO2", "reforma": "Reforma de CH4", "rwgs": "RWGS"}[x])
    n_metais = st.number_input("Número de metais ativos", min_value=1, max_value=4, value=1, step=1)
    metais_padrao = ["Fe", "Co", "Ni", "Cu"]
    metais = []
    for indice_metal in range(int(n_metais)):
        valor_padrao = metais_padrao[indice_metal] if indice_metal < len(metais_padrao) else ""
        metal_informado = limpar_simbolo_quimico(
            st.text_input(
                f"Metal ativo {indice_metal + 1}",
                value=valor_padrao,
                key=f"metal_ativo_{indice_metal + 1}",
            )
        )
        if metal_informado:
            metais.append(metal_informado)
    promotor = limpar_simbolo_quimico(st.text_input("Promotor", value="La"))
    destino_saida = st.radio("Local de salvamento", ["Usar pasta padrão", "Escolher outra pasta"], horizontal=False)
    if destino_saida == "Escolher outra pasta":
        output_dir_texto = st.text_input("Pasta de destino dos resultados", value="", placeholder="Digite ou cole a pasta de destino")
    else:
        output_dir_texto = ""
    executar = st.button("Executar triagem", type="primary")

metais_unicos = list(dict.fromkeys(metais))
metais_repetidos = len(metais_unicos) != len(metais)
metais = metais_unicos
output_dir = Path(output_dir_texto).expanduser().resolve() if output_dir_texto else DEFAULT_OUTPUT_DIR.resolve()

if metais_repetidos:
    st.warning("Há metais ativos repetidos. Cada metal ativo deve ser informado apenas uma vez.")
elif len(metais) != int(n_metais):
    st.warning("Preencha todos os campos de metal ativo antes de executar.")

if executar:
    if not metais:
        st.error("Informe pelo menos um metal ativo.")
    elif metais_repetidos:
        st.error("Remova metais ativos repetidos antes de executar.")
    elif len(metais) != int(n_metais):
        st.error("Preencha todos os campos de metal ativo antes de executar.")
    elif not promotor:
        st.error("Informe o promotor.")
    else:
        with st.spinner("Executando consultas, descritores, ranking, incerteza e figuras. Esta etapa pode demorar."):
            notebook_executado = executar_triagem(reacao, metais, promotor, output_dir)
        st.session_state["ultima_reacao"] = reacao
        st.session_state["ultima_saida"] = str(output_dir)
        st.session_state["ultimo_notebook"] = str(notebook_executado)
        st.success("Triagem concluída.")

reacao_resultado = st.session_state.get("ultima_reacao", reacao)
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

st.markdown("<h3 style='text-align:center; color:#111111; margin-bottom: 0.6rem;'>Resumo dos resultados</h3>", unsafe_allow_html=True)
mostrar_painel_decisao(metricas_df, prioritarios_df, classificacao_df, monte_carlo_df, desempenho_df)

aba_geral, aba_candidatos, aba_ranking, aba_incerteza, aba_quimica, aba_figuras, aba_arquivos = st.tabs([
    "Visão geral",
    "Candidatos",
    "Classifica\u00e7\u00e3o",
    "Incerteza",
    "Química",
    "Figuras",
    "Arquivos",
])

with aba_geral:
    col_resumo, col_funil = st.columns([1.0, 1.1])
    with col_resumo:
        mostrar_tabela("Top 2 recomendados", prioritarios_df, linhas=2)
    with col_funil:
        mostrar_funil_visual(metricas_df, prioritarios_df, monte_carlo_df)
    mostrar_tabela("Resumo tecnico dos recomendados", selecionar_colunas_tecnicas(prioritarios_df), linhas=10)

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
        mostrar_tabela("Métricas de confiança", metricas_df[metricas_df.iloc[:, 0].astype(str).map(normalizar_texto).str.contains("confianca", na=False)] if not metricas_df.empty else metricas_df, linhas=20)

with aba_quimica:
    col1, col2 = st.columns([1.1, 1.0])
    with col1:
        mostrar_tabela("Descritores essenciais dos recomendados", selecionar_colunas_tecnicas(prioritarios_df), linhas=10)
    with col2:
        mostrar_tabela("Métricas químicas e DFT", metricas_df[metricas_df.iloc[:, 0].astype(str).map(normalizar_texto).str.contains("dft|volcano|descritores", na=False)] if not metricas_df.empty else metricas_df, linhas=30)

with aba_figuras:
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
