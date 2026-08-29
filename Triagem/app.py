from __future__ import annotations

import base64
import hashlib
import html
import json
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
import plotly.graph_objects as go
import streamlit as st
from nbclient import NotebookClient


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
NOTEBOOK_PATH = APP_DIR / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
BRASAO_PATH = APP_DIR / "assets" / "logo_ufrn_header.png"
PROJECT_LOGO_PATH = APP_DIR / "assets" / "logo_triagem_catalitica_v3.png"
LABTAM_LOGO_PATH = APP_DIR / "assets" / "logo_labtam.png"
ESTRUTURAS_CATALITICAS = [
    APP_DIR / "assets" / "estrutura_catalitica_padrao_1.png",
    APP_DIR / "assets" / "estrutura_catalitica_padrao_2.png",
    APP_DIR / "assets" / "estrutura_catalitica_padrao_3.png",
    APP_DIR / "assets" / "estrutura_catalitica_padrao_4.png",
    APP_DIR / "assets" / "estrutura_catalitica_padrao_5.png",
]

CONFIGURACAO_VOLCANO = {
    "metanacao": {"descritor": "CO", "energia_otima": 0.85, "largura": 0.35},
    "reforma": {"descritor": "C", "energia_otima": 1.25, "largura": 0.45},
    "rwgs": {"descritor": "CO", "energia_otima": 0.70, "largura": 0.32},
}

BIBLIOTECA_SUPORTES_QUIMICA = [
    {"suporte": "Al2O3", "reacoes": ["metanacao", "rwgs"], "redox": 0.20, "basicidade": 0.25, "dispersao": 0.92, "estabilidade_termica": 0.78, "vacancia_oxigenio": 0.20, "afinidade_co2": 0.35, "risco_smsi": 0.20},
    {"suporte": "SiO2-Al2O3", "reacoes": ["metanacao"], "redox": 0.15, "basicidade": 0.22, "dispersao": 0.88, "estabilidade_termica": 0.72, "vacancia_oxigenio": 0.15, "afinidade_co2": 0.30, "risco_smsi": 0.15},
    {"suporte": "ZrO2", "reacoes": ["metanacao", "reforma", "rwgs"], "redox": 0.75, "basicidade": 0.45, "dispersao": 0.70, "estabilidade_termica": 0.90, "vacancia_oxigenio": 0.65, "afinidade_co2": 0.65, "risco_smsi": 0.45},
    {"suporte": "CeO2-ZrO2", "reacoes": ["metanacao", "reforma", "rwgs"], "redox": 1.00, "basicidade": 0.62, "dispersao": 0.72, "estabilidade_termica": 0.84, "vacancia_oxigenio": 1.00, "afinidade_co2": 0.82, "risco_smsi": 0.75},
    {"suporte": "Al2O3-CeO2-ZrO2", "reacoes": ["metanacao", "reforma"], "redox": 0.88, "basicidade": 0.56, "dispersao": 0.82, "estabilidade_termica": 0.82, "vacancia_oxigenio": 0.85, "afinidade_co2": 0.76, "risco_smsi": 0.62},
    {"suporte": "MgO-Al2O3", "reacoes": ["reforma"], "redox": 0.30, "basicidade": 0.92, "dispersao": 0.78, "estabilidade_termica": 0.88, "vacancia_oxigenio": 0.25, "afinidade_co2": 0.86, "risco_smsi": 0.25},
    {"suporte": "MgAl2O4", "reacoes": ["reforma"], "redox": 0.28, "basicidade": 0.88, "dispersao": 0.72, "estabilidade_termica": 0.94, "vacancia_oxigenio": 0.22, "afinidade_co2": 0.80, "risco_smsi": 0.22},
    {"suporte": "MgAlOx", "reacoes": ["reforma"], "redox": 0.35, "basicidade": 0.95, "dispersao": 0.80, "estabilidade_termica": 0.90, "vacancia_oxigenio": 0.28, "afinidade_co2": 0.88, "risco_smsi": 0.26},
    {"suporte": "La2O3-Al2O3", "reacoes": ["metanacao", "reforma"], "redox": 0.45, "basicidade": 0.88, "dispersao": 0.78, "estabilidade_termica": 0.82, "vacancia_oxigenio": 0.38, "afinidade_co2": 0.90, "risco_smsi": 0.32},
    {"suporte": "TiO2", "reacoes": ["metanacao", "rwgs"], "redox": 0.70, "basicidade": 0.30, "dispersao": 0.70, "estabilidade_termica": 0.76, "vacancia_oxigenio": 0.62, "afinidade_co2": 0.50, "risco_smsi": 0.82},
    {"suporte": "In2O3-ZrO2", "reacoes": ["rwgs"], "redox": 0.82, "basicidade": 0.42, "dispersao": 0.70, "estabilidade_termica": 0.78, "vacancia_oxigenio": 0.76, "afinidade_co2": 0.78, "risco_smsi": 0.48},
]

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
    "Todos os metais serão representados entre os 100 candidatos viáveis.": "All metals will be represented among the 100 viable candidates.",
    "Promotor": "Promoter",
    "Local de salvamento": "Output location",
    "Usar pasta padrão": "Use default folder",
    "Escolher outra pasta": "Choose another folder",
    "Pasta de destino dos resultados": "Results destination folder",
    "Executar triagem": "Run screening",
    "Resumo dos resultados": "Results summary",
    "Visão geral": "Overview",
    "Catalisadores recomendados": "Recommended catalysts",
    "Candidatos": "Candidates",
    "Classificação": "Ranking",
    "Incerteza": "Uncertainty",
    "Estabilidade catalítica e operação": "Catalytic stability and operation",
    "Química": "Chemistry",
    "Síntese": "Synthesis",
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
    "Permanência no Top 5": "Top 5 retention",
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
    "Principais recomendações": "Main recommendations",
    "Triagem virtual orientada por IA para sua reação.": "AI-guided virtual screening for your reaction.",
    "Candidatos prioritários para síntese": "Priority candidates for synthesis",
    "Classificação dos 10 primeiros": "Top 10 ranking",
    "Incerteza Monte Carlo": "Monte Carlo uncertainty",
    "Métricas de confiança": "Confidence metrics",
    "Descritores essenciais dos recomendados": "Key descriptors of recommended candidates",
    "Métricas químicas e DFT": "Chemical and DFT metrics",
    "Tríades metal-suporte-promotor avaliadas": "Evaluated metal-support-promoter triads",
    "Domínio de aplicabilidade": "Applicability domain",
    "Pareto e desejabilidade": "Pareto and desirability",
    "Métricas de validação científica": "Scientific validation metrics",
    "Validação quimiométrica": "Chemometric validation",
    "Validação avançada dos prioritários": "Advanced validation of priority candidates",
    "Correção de temperatura no Top 10": "Temperature correction for the Top 10",
    "Visualização científica interativa": "Interactive scientific visualization",
    "Gráficos": "Figures",
    "Preparação teórica de 100 g": "Theoretical preparation of 100 g",
    "Suporte sugerido": "Suggested support",
    "Condições iniciais": "Initial conditions",
    "Pré-tratamento": "Pretreatment",
    "Ponto de atenção": "Point of attention",
    "Pontuação final": "Final score",
    "Confiabilidade do modelo": "Model confidence",
    "Filtros aplicados": "Applied filters",
    "Predição de desempenho": "Performance prediction",
    "Candidatos finais": "Final candidates",
    "Espaço químico inicial": "Initial chemical space",
}


def idioma_atual() -> str:
    """Retorna o idioma selecionado na navegação."""
    return st.session_state.get("idioma", "pt")


def t(texto: str) -> str:
    """Traduz os textos principais da interface para inglês quando solicitado."""
    return TRADUCOES_EN.get(texto, texto) if idioma_atual() == "en" else texto


def formatar_formula_quimica(formula: object) -> str:
    """Converte algarismos estequiométricos em subscritos apenas para exibição."""
    texto_formula = str(formula).strip()
    texto_formula = re.sub(r"\s*-\s*", "–", texto_formula)
    return texto_formula.translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))


def traduzir_texto_exibicao(texto: str) -> str:
    """Traduz rótulos e mensagens conhecidas que já foram inseridos em cartões HTML."""
    if idioma_atual() != "en":
        return texto
    traducoes = {
        "Pontuação final": "Final score", "Confiabilidade do modelo": "Model confidence",
        "Suporte sugerido": "Suggested support", "Condições iniciais": "Initial conditions",
        "Rota de síntese": "Synthesis route", "Justificativa do suporte": "Support rationale",
        "Pré-tratamento": "Pretreatment", "Preparação teórica de 100 g": "Theoretical preparation of 100 g",
        "fase ativa": "active phase", "suporte": "support", "Massas elementares na fase ativa": "Elemental masses in the active phase",
        "Ponto de atenção": "Point of attention", "Não informado": "Not provided",
        "Triagem de Catalisadores": "Catalyst screening", "Quantidade de catalisadores": "Number of catalysts",
        "Critério químico": "Chemical criterion", "Retenção": "Retention", "catalisadores": "catalysts",
        "Geração combinatória de materiais": "Combinatorial generation of materials",
        "Propriedades físico-químicas": "Physicochemical properties",
        "Modelo de aprendizagem de máquina": "Machine-learning model",
        "Melhores candidatos priorizados": "Best prioritized candidates",
        "Combinações de metais ativos, promotor e composições geradas.": "Generated combinations of active metals, promoter, and compositions.",
        "Estabilidade termodinâmica, composição e regras químicas.": "Thermodynamic stability, composition, and chemical rules.",
        "Descritores catalíticos, DFT ou proxy e incerteza do modelo.": "Catalytic descriptors, DFT or proxy, and model uncertainty.",
        "Desempenho, estabilidade do ranking por Monte Carlo e viabilidade de síntese.": "Performance, Monte Carlo ranking stability, and synthesis feasibility.",
        "As massas dos sais precursores devem ser recalculadas conforme o sal, a pureza e a perda por calcinação.": "Precursor-salt masses must be recalculated according to the selected salt, purity, and calcination loss.",
        "impregnacao incipiente do metal ativo em suporte de alta area": "incipient-wetness impregnation of the active metal on a high-surface-area support",
        "suporte de alta area favorece dispersao da fase ativa em metanacao": "a high-surface-area support favors active-phase dispersion in methanation",
        "confirmar carga metalica e pH de impregnacao conforme solubilidade dos precursores": "confirm metal loading and impregnation pH according to precursor solubility",
        "Interações metal–suporte–promotor": "Metal–support–promoter interactions",
        "Componente eletrônico": "Electronic component", "Índice redox": "Redox index",
        "Componente estrutural": "Structural component", "interação eletrônica e estrutural": "electronic and structural interaction",
        "Interação metal–suporte": "Metal–support interaction", "Racional do suporte": "Support rationale",
        "Índice heurístico": "Heuristic index", "Modelo estrutural esquemático": "Schematic structural model",
        "Fase ativa": "Active phase", "Fórmulas e propriedades calculadas": "Calculated formulas and properties",
        "Distância do ótimo": "Distance from optimum", "Barreira aparente": "Apparent barrier",
        "Estabilidade térmica e resistência à formação de coque": "Thermal stability and resistance to coke formation",
        "Descritores químicos e relação estrutura–desempenho": "Chemical descriptors and structure–performance relationship",
        "Energia de adsorção": "Adsorption energy", "Afinidade por oxigênio": "Oxygen affinity",
        "Redutibilidade": "Reducibility", "Basicidade": "Basicity", "Resistência ao coque": "Coke resistance",
        "Estabilidade operacional": "Operational stability", "Proxy de resistência à sinterização": "Sintering-resistance proxy",
        "Maior é melhor": "Higher is better", "Maior depende da reação": "Higher depends on the reaction",
        "Próxima do ótimo é melhor": "Closer to the optimum is better", "Maior indica ancoragem favorável": "Higher indicates favorable anchoring",
        "Sugestão da triagem": "Screening suggestion", "Sem promotor": "No promoter",
        "Dispersão da fase ativa": "Active-phase dispersion", "Estabilidade térmica": "Thermal stability",
        "Capacidade redox": "Redox capacity", "Basicidade superficial": "Surface basicity",
        "Vacâncias de oxigênio": "Oxygen vacancies", "Afinidade por CO₂": "CO₂ affinity",
        "Excelente": "Excellent", "Boa": "Good", "Moderada": "Moderate", "Baixa": "Low",
        "O suporte sugerido pela triagem aparece primeiro. O índice heurístico compara dispersão, estabilidade térmica, redox, basicidade, afinidade por CO₂ e risco de SMSI; ele não refaz o ranking global nem substitui DFT explícita da interface.": "The support suggested by the screening appears first. The heuristic index compares dispersion, thermal stability, redox behavior, basicity, CO₂ affinity, and SMSI risk; it neither recomputes the global ranking nor replaces explicit interface DFT.",
        "A resistência à sinterização é um proxy estrutural/composicional; não representa um modelo temporal de crescimento de partículas.": "Sintering resistance is a structural/compositional proxy; it is not a time-dependent particle-growth model.",
        "Representação visual das fases; não corresponde a uma geometria atômica relaxada por DFT.": "Visual representation of the phases; it is not a DFT-relaxed atomic geometry.",
        "As cores representam as espécies indicadas na legenda e são atualizadas a cada triagem. O desenho é esquemático e não corresponde a uma geometria atômica relaxada por DFT.": "Colors represent the species indicated in the legend and are updated for each screening. The drawing is schematic and does not correspond to a DFT-relaxed atomic geometry.",
        "Descritores normalizados são proxies de triagem e devem ser confirmados por DFT de superfície e validação experimental.": "Normalized descriptors are screening proxies and must be confirmed by surface DFT and experimental validation.",
        "E<sub>ads</sub>, distância e barreira usam o descritor da reação; E<sub>GNN</sub> é uma predição de bulk e não uma energia explícita de superfície.": "E<sub>ads</sub>, distance, and barrier use the reaction descriptor; E<sub>GNN</sub> is a bulk prediction, not an explicit surface energy.",
        "Representação esquemática do catalisador": "Schematic catalyst representation",
        "DFT/proxy ajustado por Boltzmann": "Boltzmann-adjusted DFT/proxy",
        "Proxy redox normalizado": "Normalized redox proxy",
        "DFT ou proxy DFT normalizado": "Normalized DFT or DFT proxy",
        "Proxy de afinidade ácido–base": "Acid–base affinity proxy",
        "Índice composicional/cinético": "Compositional/kinetic index",
        "DFT/proxy com peso de Boltzmann": "Boltzmann-weighted DFT/proxy",
        "Estabilidade termodinâmica": "Thermodynamic stability", "Score final": "Final score",
        "Catalisador": "Catalyst", "Promotor": "Promoter", "Suporte": "Support",
        "eV/átomo": "eV/atom",
        "Fortalecimento da ligação M–S": "M–S bond strengthening",
        "Ligação eletrônica": "Electronic bonding", "Doação de elétrons": "Electron donation",
        "Retirada de elétrons": "Electron withdrawal", "Efeito estrutural": "Structural effect",
        "Dispersão": "Dispersion", "Transferência de carga": "Charge transfer",
        "Oxigênio da superfície": "Surface oxygen", "Matriz do suporte": "Support matrix",
        "Segundo metal ativo": "Second active metal",
        "Estimativas proxy derivadas dos descritores da triagem; confirmar por DFT de interface.": "Proxy estimates derived from the screening descriptors; confirm by interface DFT.",
        "Valores calculados de interface disponíveis na base local.": "Calculated interface values available in the local database.",
    }
    for origem, destino in sorted(traducoes.items(), key=lambda item: len(item[0]), reverse=True):
        texto = texto.replace(origem, destino)
    return texto


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


def corrigir_texto_portugues(texto: str) -> str:
    """Corrige termos recorrentes dos arquivos de resultados antes da exibição."""
    if idioma_atual() == "en":
        return texto
    correcoes = {
        "impregnacao": "impregnação", "calcinacao": "calcinação", "reducao": "redução",
        "oxidacao": "oxidação", "sintese": "síntese", "condicoes": "condições",
        "metanacao": "metanação", "adsorcao": "adsorção", "dessorcao": "dessorção",
        "formacao": "formação", "deposicao": "deposição", "avaliacao": "avaliação",
        "analise": "análise", "simulacao": "simulação", "recomendacao": "recomendação",
        "confianca": "confiança", "operacao": "operação", "decisao": "decisão",
        "quimicos": "químicos", "quimica": "química", "termica": "térmica",
        "metalica": "metálica", "area": "área", "razao": "razão",
        "dispersao": "dispersão", "predicao": "predição", "validacao": "validação",
        "selecao": "seleção", "classificacao": "classificação", "aplicabilidade": "aplicabilidade",
        "estequiometria": "estequiometria", "catalitico": "catalítico", "catalitica": "catalítica",
        "energetica": "energética", "evidencia": "evidência", "otimo": "ótimo",
    }
    resultado = str(texto)
    for origem, destino in correcoes.items():
        resultado = re.sub(rf"\b{origem}\b", destino, resultado, flags=re.IGNORECASE)
    return resultado


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


def numero_linha_opcoes(row: pd.Series, opcoes: list[list[str]]) -> float | None:
    """Lê uma métrica numérica usando alternativas de nomes de coluna."""
    coluna = encontrar_coluna_por_opcoes(pd.DataFrame(columns=row.index), opcoes)
    if coluna is None:
        return None
    valor = pd.to_numeric(pd.Series([row.get(coluna)]), errors="coerce").iloc[0]
    return None if pd.isna(valor) else float(valor)


def texto_linha_opcoes(row: pd.Series, opcoes: list[list[str]], padrao: str = "Não exportada") -> str:
    """Lê um texto usando alternativas de nomes de coluna."""
    coluna = encontrar_coluna_por_opcoes(pd.DataFrame(columns=row.index), opcoes)
    if coluna is None:
        return padrao
    valor = row.get(coluna)
    return padrao if valor is None or pd.isna(valor) or not str(valor).strip() else str(valor)


def mostrar_origem_e_confianca(row: pd.Series) -> None:
    """Expõe a procedência dos principais valores e os critérios de confiança."""
    if row.empty:
        return
    confiabilidade = extrair_confiabilidade(row)
    estabilidade = numero_linha_opcoes(row, [["estabilidade", "termodinamica"], ["energy", "above", "hull"]])
    score_confianca = numero_linha_opcoes(row, [["score", "confianca"], ["score", "incerteza"]])
    score_dft = numero_linha_opcoes(row, [["score", "dft"]])
    probabilidade_top5 = numero_linha_opcoes(row, [["probabilidade", "monte", "top", "5"], ["probabilidade", "top5"]])
    desvio_mc = numero_linha_opcoes(row, [["desvio", "monte", "score"], ["score", "final", "mc", "desvio"]])
    fonte_estabilidade = texto_linha_opcoes(row, [["fonte", "estabilidade"]])
    fonte_adsorcao = texto_linha_opcoes(row, [["fonte", "volcano"]])
    modelo_gnn = texto_linha_opcoes(row, [["modelo", "gnn"]])
    if normalizar_texto(fonte_estabilidade) == "mp":
        fonte_estabilidade = "Materials Project (MP)"

    def fmt(valor: float | None, casas: int = 3) -> str:
        return "Não exportado" if valor is None else f"{valor:.{casas}f}".replace(".", ",")

    itens_origem = [
        ("Composição", "Geração combinatória", "Metais ativos, promotor e passo estequiométrico definidos na configuração."),
        ("Estabilidade termodinâmica", fonte_estabilidade, "Consulta estrutural ou predição de bulk; não representa atividade catalítica."),
        ("Adsorção / vulcão", fonte_adsorcao, "Evidência do Catalysis-Hub quando disponível; caso contrário, proxy químico identificado no resultado."),
        ("Descritores estruturais", modelo_gnn, "GNN aplicada ao bulk ou estrutura proxy; não substitui DFT explícita de superfície."),
        ("Pontuação final", "Cálculo MCDA", "Soma multicritério normalizada, com pesos e penalizações definidos pelo perfil da reação."),
        ("Suporte e síntese", "Regra heurística química", "Sugestão baseada na composição e na reação; exige confirmação experimental."),
    ]
    origem_html = "".join(
        f"<article class='audit-item'><b>{html.escape(titulo)}</b><strong>{html.escape(corrigir_texto_portugues(fonte))}</strong><span>{html.escape(descricao)}</span></article>"
        for titulo, fonte, descricao in itens_origem
    )
    criterios = [
        ("Estabilidade", fmt(estabilidade) + " eV/átomo", estabilidade is not None and estabilidade <= 0.10, "≤ 0,10 eV/átomo"),
        ("Score de confiança", fmt(score_confianca), score_confianca is not None and score_confianca >= 0.65, "≥ 0,65"),
        ("Score DFT/proxy", fmt(score_dft), score_dft is not None and score_dft >= 0.60, "≥ 0,60"),
        ("Probabilidade de Top 5", "Não exportada" if probabilidade_top5 is None else f"{100 * probabilidade_top5:.1f}%".replace(".", ","), probabilidade_top5 is not None and probabilidade_top5 >= 0.30, "≥ 30%"),
    ]
    criterios_html = "".join(
        f"<div class='confidence-factor {'ok' if passou else 'attention'}'><b>{html.escape(nome)}</b><strong>{html.escape(valor)}</strong><span>Critério: {html.escape(limiar)}</span></div>"
        for nome, valor, passou, limiar in criterios
    )
    dispersao = "Não exportada" if desvio_mc is None else fmt(desvio_mc)
    with st.expander("Origem dos resultados e justificativa da confiança", expanded=False):
        st.markdown(
            f"<div class='audit-grid'>{origem_html}</div>"
            f"<h4 class='confidence-heading'>Confiabilidade classificada como {html.escape(confiabilidade.capitalize())}</h4>"
            f"<div class='confidence-grid'>{criterios_html}</div>"
            f"<p class='confidence-method'>A categoria alta exige simultaneamente os quatro critérios acima. A categoria média aceita estabilidade até 0,15 eV/átomo e score final ≥ 0,65. Nos demais casos, a confiança é baixa. Desvio Monte Carlo do score: <b>{html.escape(dispersao)}</b>. A confiança mede consistência da triagem e disponibilidade de evidências; não equivale à probabilidade de sucesso experimental.</p>",
            unsafe_allow_html=True,
        )


def cartao_html(rotulo: str, valor: str, destaque: bool = False, icone: str = "", nota: str = "", tamanho_valor: str = "clamp(1.35rem, 1.8vw, 1.85rem)") -> str:
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
            font-size: {tamanho_valor};
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
            text-align: justify;
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


def mostrar_linha_cartoes(titulo: str, cards: list[tuple[str, str, bool]], tamanho_valor: str = "clamp(1.35rem, 1.8vw, 1.85rem)") -> None:
    """Mostra uma linha de cartoes de decisao."""
    st.markdown(f"<h4 style='text-align:center;'>{html.escape(t(titulo))}</h4>", unsafe_allow_html=True)
    colunas = st.columns(len(cards))
    for coluna, (rotulo, valor, destaque) in zip(colunas, cards):
        coluna.markdown(cartao_html(rotulo, valor, destaque=destaque, tamanho_valor=tamanho_valor), unsafe_allow_html=True)


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
        tamanho_valor="clamp(1.05rem, 1.25vw, 1.35rem)",
    )
    mostrar_linha_cartoes(
        "Condição e confiança",
        [
            ("Condição inicial de ensaio", f"{condicao_inicial} · {regime.replace('_', ' ')}" if regime != "-" else condicao_inicial, False),
            ("Confiabilidade da recomendação", confiabilidade.capitalize() if confiabilidade != "-" else "-", True),
            ("Permanência no Top 5", "-" if probabilidade_top5 is None else f"{100 * probabilidade_top5:.0f}%", False),
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
    """Mostra os indicadores de estabilidade catalítica e operação em uma aba dedicada."""
    if prioritarios_df.empty and monte_carlo_df.empty and desempenho_df.empty:
        st.info("Execute a triagem para visualizar os dados de estabilidade catalítica e opera\u00e7\u00e3o.")
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
        "Estabilidade catalítica e opera\u00e7\u00e3o",
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
        mostrar_tabela("Estabilidade do ranking (Monte Carlo)", monte_carlo_df, linhas=30)
    with col2:
        metricas_operacao_df = filtrar_metricas_por_termos(
            metricas_df,
            ["robustez", "monte carlo", "probabilidade", "desvio", "faixa", "condicao", "condi\u00e7\u00e3o", "operacao", "opera\u00e7\u00e3o", "regime"],
        )
        mostrar_tabela("M\u00e9tricas de estabilidade catalítica e opera\u00e7\u00e3o", metricas_operacao_df, linhas=30)

    mostrar_tabela("Desempenho por faixa de condi\u00e7\u00e3o", desempenho_df, linhas=30)

def mostrar_simulador_operacional(prioritarios_df: pd.DataFrame, classificacao_df: pd.DataFrame) -> None:
    """Renderiza um simulador de resposta operacional baseado nos resultados da triagem."""
    st.markdown("""<style>
    .operation-title{margin:8px 0 4px;color:#14213D;font-size:clamp(1.6rem,2.4vw,2.2rem);font-weight:850;letter-spacing:0}.operation-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:12px 0 14px}.operation-kpi,.operation-risk-card,.operation-note{border:1px solid #DCE6EE;border-radius:8px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.04)}.operation-kpi{min-height:104px;padding:15px 17px}.operation-kpi b{display:block;color:#14213D;font-size:.79rem}.operation-kpi strong{display:block;margin:9px 0 3px;color:#087A3B;font-size:1.48rem;line-height:1}.operation-kpi span,.operation-risk-card span{color:#64748B;font-size:.74rem;line-height:1.35}.operation-risk-card{min-height:335px;padding:17px;color:#14213D}.operation-risk-card h3{margin:0 0 16px;color:#087A3B;font-size:.92rem;line-height:1.25}.operation-risk-card b{display:block;color:#14213D;font-size:.76rem}.operation-risk-card strong{display:block;margin:5px 0 2px;color:#146CC1;font-size:1.32rem}.operation-risk-card hr{border:0;border-top:1px solid #E7EDF2;margin:14px 0}.operation-note{margin-top:8px;padding:16px;color:#334155;font-size:.83rem;line-height:1.55;background:#F7FCF8;border-color:#C9DFD0}@media(max-width:900px){.operation-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>""", unsafe_allow_html=True)
    if prioritarios_df.empty and classificacao_df.empty:
        st.info("Execute a triagem para visualizar o simulador operacional.")
        return
    candidatos = (prioritarios_df if not prioritarios_df.empty else classificacao_df).copy().head(10).reset_index(drop=True)
    coluna_formula = encontrar_coluna(candidatos, ["formula"]) or candidatos.columns[0]
    opcoes = candidatos[coluna_formula].astype(str).tolist()
    formula = st.selectbox("Candidato simulado", opcoes, format_func=formatar_formula_quimica, key="simulador_operacional_candidato")
    candidato = candidatos.loc[candidatos[coluna_formula].astype(str) == formula].iloc[0]
    def numero(row, termos, padrao):
        coluna = encontrar_coluna(pd.DataFrame(columns=row.index), termos)
        valor = pd.to_numeric(pd.Series([row.get(coluna, padrao) if coluna else padrao]), errors="coerce").iloc[0]
        return float(valor) if pd.notna(valor) else padrao
    temperatura_base, pressao_base, razao_base = float(np.clip(numero(candidato,["temperatura"],400),200,800)), float(np.clip(numero(candidato,["pressao"],10),1,30)), float(np.clip(numero(candidato,["razao"],3),.1,6))
    conversao_base, seletividade_base = float(np.clip(numero(candidato,["conversao","prevista"],55),1,98)), float(np.clip(numero(candidato,["seletividade","prevista"],80),1,99))
    score_material, resistencia_coque = float(np.clip(numero(candidato,["score","final"],.6),0,1)), float(np.clip(numero(candidato,["resistencia","coque"],.55),0,1))
    def resposta(temperatura_c, pressao_bar, razao_h2_co2):
        temperatura_c, pressao_bar, razao_h2_co2 = np.asarray(temperatura_c,dtype=float), np.asarray(pressao_bar,dtype=float), np.asarray(razao_h2_co2,dtype=float)
        fator_t = .42 + .58*np.exp(-((temperatura_c-temperatura_base)/190)**2); fator_p = .68 + .32*(1-np.exp(-pressao_bar/max(pressao_base,4)))/(1-np.exp(-30/max(pressao_base,4))); fator_r = .70 + .30*np.exp(-((razao_h2_co2-razao_base)/2.1)**2)
        conversao = np.clip(conversao_base*fator_t*fator_p*fator_r,0,100); seletividade = np.clip(seletividade_base*(.93+.07*fator_r)*(1.02-.00016*np.maximum(temperatura_c-temperatura_base,0)),0,100); rendimento = np.clip(conversao*seletividade/100,0,100)
        risco = np.clip((1-resistencia_coque)*(.55+.25*np.clip((temperatura_c-350)/450,0,1)+.20*np.clip((3-razao_h2_co2)/2,0,1)),0,1); robustez = np.clip(.55*rendimento/100+.25*score_material+.20*(1-risco),0,1)
        return conversao,seletividade,rendimento,robustez,risco
    st.markdown(f"<h2 class='operation-title'>{html.escape(t('Estabilidade catalítica e operação'))}</h2>",unsafe_allow_html=True)
    st.caption("Simulador operacional proxy: compara tendências previstas a partir dos descritores e do ranking. Não substitui ensaios cinéticos, balanço de massa ou validação experimental.")
    with st.container(border=True):
        st.markdown("#### Condições operacionais exploradas"); c1,c2,c3=st.columns(3)
        with c1: temperatura=st.slider("Temperatura (°C)",200,800,int(round(temperatura_base)),10,key="simulador_operacional_temperatura")
        with c2: pressao=st.slider("Pressão (bar)",1,30,int(round(pressao_base)),1,key="simulador_operacional_pressao")
        with c3: razao=st.slider("Razão H₂/CO₂ (mol/mol)",0.1,6.0,max(0.1,round(razao_base,1)),.1,key="simulador_operacional_razao")
    conversao,seletividade,rendimento,score_robustez,risco_coque=resposta(temperatura,pressao,razao); k_desativacao=.0004+.006*float(risco_coque); tempo_10_pct=.105/k_desativacao
    cards=[("Temperatura recomendada",f"{temperatura} °C",f"janela: {max(200,temperatura-60)}–{min(800,temperatura+60)} °C"),("Pressão recomendada",f"{pressao} bar",f"janela: {max(1,pressao-5)}–{min(30,pressao+5)} bar"),("Razão H₂/CO₂ recomendada",f"{razao:.1f} mol/mol",f"janela: {max(.1,razao-.7):.1f}–{min(6.,razao+.7):.1f} mol/mol"),("Rendimento previsto",f"{float(rendimento):.1f}%",f"conversão {float(conversao):.1f}% · seletividade {float(seletividade):.1f}%")]
    st.markdown("<div class='operation-kpis'>"+"".join(f"<div class='operation-kpi'><b>{html.escape(a)}</b><strong>{html.escape(b)}</strong><span>{html.escape(c)}</span></div>" for a,b,c in cards)+"</div>",unsafe_allow_html=True)
    temperaturas=np.arange(200,801,25); fig_atividade=go.Figure()
    for indice,(_,linha) in enumerate(candidatos.head(5).iterrows(),1):
        atividade=np.clip(100*(.42+.58*np.exp(-((temperaturas-numero(linha,["temperatura"],temperatura_base))/190)**2))*numero(linha,["conversao","prevista"],conversao_base)/max(conversao_base,1),0,120); fig_atividade.add_trace(go.Scatter(x=temperaturas,y=atividade,mode="lines+markers",name=f"{indice}. {formatar_formula_quimica(linha[coluna_formula])}"))
    fig_atividade.add_vline(x=temperatura,line_dash="dash",line_color="#64748B"); fig_atividade.update_layout(title="Atividade relativa versus temperatura",xaxis_title="Temperatura (°C)",yaxis_title="Atividade relativa (%)",height=335,margin=dict(l=35,r=15,t=50,b=35),legend=dict(font=dict(size=10)))
    grade_t,grade_p=np.linspace(200,800,51),np.linspace(1,30,31); tm,pm=np.meshgrid(grade_t,grade_p); _,_,grade_rendimento,grade_robustez,_=resposta(tm,pm,razao)
    fig_superficie=go.Figure(go.Contour(x=grade_t,y=grade_p,z=grade_rendimento,colorscale="YlGnBu",contours=dict(showlabels=True),colorbar=dict(title="Rendimento (%)"))); fig_superficie.add_trace(go.Scatter(x=[temperatura],y=[pressao],mode="markers",marker=dict(size=12,color="#14213D",symbol="star"),name="Condição simulada")); fig_superficie.update_layout(title="Superfície de resposta: rendimento previsto",xaxis_title="Temperatura (°C)",yaxis_title="Pressão (bar)",height=335,margin=dict(l=35,r=15,t=50,b=35))
    ca,cb,cc=st.columns([1.05,1.15,.8])
    with ca: st.plotly_chart(fig_atividade,width="stretch")
    with cb: st.plotly_chart(fig_superficie,width="stretch")
    with cc:
        nivel="Baixo" if risco_coque<.33 else "Moderado" if risco_coque<.66 else "Alto"; st.markdown("<div class='operation-risk-card'><h3>Resistência à deposição de carbono e desativação</h3>"+f"<b>Resistência estimada</b><strong>{resistencia_coque:.2f}</strong><span>(0 = baixa | 1 = alta)</span><hr><b>Tendência de formação de coque</b><strong>{nivel}</strong><span>índice proxy: {float(risco_coque):.2f}</span><hr><b>Taxa de desativação (proxy)</b><strong>{k_desativacao:.2e} h⁻¹</strong><span>tempo estimado para queda de 10%: {tempo_10_pct:.0f} h</span></div>",unsafe_allow_html=True)
    st.markdown("#### Avalie o desempenho em diferentes condições operacionais"); linhas_pressao=sorted(set([max(1,pressao-5),pressao,min(30,pressao+5)])); fig_conversao,fig_rendimento=go.Figure(),go.Figure()
    for p in linhas_pressao:
        conv,_,rend,_,_=resposta(temperaturas,p,razao); fig_conversao.add_trace(go.Scatter(x=temperaturas,y=conv,mode="lines+markers",name=f"Pressão: {p} bar")); fig_rendimento.add_trace(go.Scatter(x=temperaturas,y=rend,mode="lines+markers",name=f"Pressão: {p} bar"))
    for figura,titulo,eixo in [(fig_conversao,"Conversão de CO₂ prevista","Conversão de CO₂ (%)"),(fig_rendimento,"Rendimento previsto","Rendimento (%)")]: figura.add_vline(x=temperatura,line_dash="dash",line_color="#64748B"); figura.update_layout(title=titulo,xaxis_title="Temperatura (°C)",yaxis_title=eixo,height=315,margin=dict(l=35,r=15,t=50,b=35),legend=dict(orientation="h",y=1.12))
    mapa=go.Figure(go.Heatmap(x=grade_t,y=grade_p,z=grade_robustez,colorscale="RdYlGn",zmin=0,zmax=1,colorbar=dict(title="Índice"))); mapa.add_trace(go.Scatter(x=[temperatura],y=[pressao],mode="markers",marker=dict(size=10,color="#14213D",symbol="star"),name="Condição simulada")); mapa.update_layout(title="Mapa de estabilidade operacional",xaxis_title="Temperatura (°C)",yaxis_title="Pressão (bar)",height=315,margin=dict(l=35,r=15,t=50,b=35))
    g1,g2,g3=st.columns(3)
    with g1: st.plotly_chart(fig_conversao,width="stretch")
    with g2: st.plotly_chart(fig_rendimento,width="stretch")
    with g3: st.plotly_chart(mapa,width="stretch")
    pontos=pd.DataFrame({"Temperatura (°C)":tm.ravel(),"Pressão (bar)":pm.ravel(),"Rendimento (%)":grade_rendimento.ravel(),"Índice de estabilidade operacional":grade_robustez.ravel()}); janelas=pontos.sort_values(["Índice de estabilidade operacional","Rendimento (%)"],ascending=False).drop_duplicates(subset=["Temperatura (°C)"],keep="first").head(3).reset_index(drop=True); janelas.insert(0,"Janela",["Ótima","Alta","Boa"][:len(janelas)]); janelas["Razão H₂/CO₂"]=f"{razao:.1f}"; janelas["Conversão de CO₂ (%)"]=[float(resposta(r["Temperatura (°C)"],r["Pressão (bar)"],razao)[0]) for _,r in janelas.iterrows()]; janelas=janelas[["Janela","Temperatura (°C)","Pressão (bar)","Razão H₂/CO₂","Conversão de CO₂ (%)","Rendimento (%)","Índice de estabilidade operacional"]].round(2)
    st.markdown("#### Principais janelas operacionais"); st.dataframe(janelas,hide_index=True,width="stretch")
    st.markdown("#### Interpretação da simulação"); st.markdown(f"<div class='operation-note'><b>Candidato:</b> {html.escape(formatar_formula_quimica(formula))} &nbsp;·&nbsp; <b>Condição avaliada:</b> {temperatura} °C, {pressao} bar, H₂/CO₂ = {razao:.1f} &nbsp;·&nbsp; <b>Índice de estabilidade operacional:</b> {float(score_robustez):.2f}.<br>Os indicadores de coque e desativação são proxies relativos. Confirme-os por ensaios de tempo em operação.</div>",unsafe_allow_html=True)


def mostrar_painel_incerteza(monte_carlo_df: pd.DataFrame, dominio_df: pd.DataFrame, validacao_df: pd.DataFrame) -> None:
    """Exibe incerteza preditiva e ranking Monte Carlo em um painel científico."""
    if monte_carlo_df.empty:
        st.info("Execute a triagem para calcular a incerteza do modelo.")
        return
    formula = encontrar_coluna(monte_carlo_df, ["formula"]) or monte_carlo_df.columns[0]
    prob = encontrar_coluna(monte_carlo_df, ["probabilidade", "top"])
    media = encontrar_coluna(monte_carlo_df, ["media", "monte", "score"])
    desvio = encontrar_coluna(monte_carlo_df, ["desvio", "monte", "score"])
    inf = encontrar_coluna(monte_carlo_df, ["limite", "inferior", "top"])
    sup = encontrar_coluna(monte_carlo_df, ["limite", "superior", "top"])
    dados = pd.DataFrame({"Catalisador": monte_carlo_df[formula].astype(str).map(formatar_formula_quimica), "Probabilidade": pd.to_numeric(monte_carlo_df[prob], errors="coerce") if prob else np.nan, "Score médio": pd.to_numeric(monte_carlo_df[media], errors="coerce") if media else np.nan, "Desvio MC": pd.to_numeric(monte_carlo_df[desvio], errors="coerce") if desvio else np.nan, "LI 95%": pd.to_numeric(monte_carlo_df[inf], errors="coerce") if inf else np.nan, "LS 95%": pd.to_numeric(monte_carlo_df[sup], errors="coerce") if sup else np.nan}).sort_values("Probabilidade", ascending=False).head(10)
    cobertura = None
    if not dominio_df.empty:
        coluna = encontrar_coluna(dominio_df, ["dominio"]) or encontrar_coluna(dominio_df, ["status"])
        if coluna:
            cobertura = dominio_df[coluna].astype(str).map(normalizar_texto).str.contains("dentro|aceit", regex=True).mean()
    r2 = extrair_metrica(validacao_df, "r2") or extrair_metrica(validacao_df, "r²")
    cards = [("Incerteza média (desvio MC)", "-" if dados["Desvio MC"].isna().all() else f"{dados['Desvio MC'].mean():.3f}", "unid. do score"), ("Cobertura do domínio", "N/D" if cobertura is None else f"{100*cobertura:.0f}%", "dos candidatos"), ("Fora do domínio", "N/D" if cobertura is None else f"{100*(1-cobertura):.0f}%", "dos candidatos"), ("R² (validação)", "N/D" if r2 is None else formatar_valor(r2), "validação disponível")]
    html_cards = "".join(f"<div class='uncertainty-metric'><b>{a}</b><strong>{b}</strong><span>{c}</span></div>" for a,b,c in cards)
    st.markdown("<h3 class='uncertainty-title'>Confiança do modelo</h3>" + f"<div class='uncertainty-metrics'>{html_cards}</div>", unsafe_allow_html=True)
    a, b, c = st.columns([1.05, 1.2, .8])
    with a:
        st.markdown("#### Distribuição Monte Carlo")
        top = dados.iloc[0]
        if pd.notna(top["Score médio"]) and pd.notna(top["Desvio MC"]) and top["Desvio MC"] > 0:
            x = np.linspace(top["Score médio"]-4*top["Desvio MC"], top["Score médio"]+4*top["Desvio MC"], 100); y = np.exp(-.5*((x-top["Score médio"])/top["Desvio MC"])**2)/(top["Desvio MC"]*np.sqrt(2*np.pi))
            fig=go.Figure(go.Scatter(x=x,y=y,fill="tozeroy",line={"color":"#146CC1"})); fig.add_vline(x=top["Score médio"],line_dash="dash",line_color="#16843C"); fig.update_layout(height=280,margin=dict(l=5,r=5,t=5,b=5),xaxis_title="Score final",yaxis_title="Densidade",showlegend=False); st.plotly_chart(fig,width="stretch")
        else: st.info("Média e desvio Monte Carlo indisponíveis.")
    with b:
        st.markdown("#### Intervalos de probabilidade (95%)")
        tabela=dados[["Catalisador","Probabilidade","LI 95%","LS 95%"]].copy()
        for col in ["Probabilidade","LI 95%","LS 95%"]: tabela[col]=tabela[col].map(lambda v:"-" if pd.isna(v) else f"{100*v:.1f}%")
        st.dataframe(tabela,hide_index=True,width="stretch",height=318)
    with c:
        st.markdown("#### Probabilidade de estar no Top 5")
        fig=px.bar(dados.head(5).sort_values("Probabilidade"),x="Probabilidade",y="Catalisador",orientation="h",color_discrete_sequence=["#16843C"]); fig.update_layout(height=280,margin=dict(l=5,r=5,t=5,b=5),xaxis_tickformat=".0%",showlegend=False); st.plotly_chart(fig,width="stretch")
    a,b=st.columns([1.05,.95])
    with a:
        st.markdown("#### Incerteza versus score predito")
        fig=px.scatter(dados,x="Score médio",y="Desvio MC",color="Probabilidade",hover_name="Catalisador",color_continuous_scale="Viridis"); fig.update_layout(height=310,margin=dict(l=5,r=5,t=5,b=5)); st.plotly_chart(fig,width="stretch")
    with b:
        texto="O domínio de aplicabilidade não foi calculado nesta execução." if cobertura is None else f"{100*(1-cobertura):.0f}% dos candidatos estão fora do domínio de aplicabilidade."
        st.markdown(f"<div class='uncertainty-alert'><h4>Alerta de extrapolação</h4><strong>{html.escape(texto)}</strong><p>Priorize candidatos com menor dispersão Monte Carlo e maior probabilidade de Top 5. A confirmação experimental continua necessária.</p></div><div class='uncertainty-note'><h4>Nota importante</h4><p>A incerteza quantifica a dispersão das previsões do ensemble e da simulação de Monte Carlo. Ela não substitui a validação experimental.</p></div>",unsafe_allow_html=True)
    st.markdown("#### Ranking de candidatos com incerteza (Monte Carlo + ensemble)")
    st.dataframe(dados,hide_index=True,width="stretch",height=min(420, 38 + 35 * len(dados)))


def mostrar_painel_validacao(
    classificacao_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    dominio_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    validacao_quimio_df: pd.DataFrame,
    relatorio_validacao_df: pd.DataFrame,
) -> None:
    """Apresenta diagnósticos internos do modelo e limites de aplicabilidade da triagem."""
    if all(dataframe.empty for dataframe in [classificacao_df, ranking_df, dominio_df, pareto_df]):
        st.info("Execute a triagem para gerar os diagnósticos de validação e domínio de aplicabilidade.")
        return

    ingles = idioma_atual() == "en"

    def texto(portugues: str, ingles_texto: str) -> str:
        """Mantém os títulos dos gráficos no idioma selecionado sem alterar os dados científicos."""
        return ingles_texto if ingles else portugues

    fontes = [classificacao_df, ranking_df, pareto_df, dominio_df]
    formulas = []
    for fonte in fontes:
        coluna_formula = encontrar_coluna(fonte, ["formula"])
        if coluna_formula:
            formulas.extend(fonte[coluna_formula].dropna().astype(str).tolist())
    dados = pd.DataFrame({"formula": list(dict.fromkeys(formulas))})

    def anexar_coluna(nome: str, termos: list[str], numerica: bool = True) -> None:
        """Une um descritor por fórmula, respeitando a ordem de prioridade dos arquivos do fluxo."""
        dados[nome] = np.nan if numerica else ""
        for fonte in fontes:
            coluna_formula = encontrar_coluna(fonte, ["formula"])
            coluna_valor = encontrar_coluna(fonte, termos)
            if coluna_formula is None or coluna_valor is None:
                continue
            serie = fonte[[coluna_formula, coluna_valor]].copy()
            serie[coluna_formula] = serie[coluna_formula].astype(str)
            if numerica:
                serie[coluna_valor] = pd.to_numeric(serie[coluna_valor], errors="coerce")
                mapa = serie.groupby(coluna_formula)[coluna_valor].mean()
            else:
                mapa = serie.dropna(subset=[coluna_valor]).drop_duplicates(subset=[coluna_formula]).set_index(coluna_formula)[coluna_valor].astype(str)
            dados[nome] = dados[nome].where(dados[nome].notna() if numerica else dados[nome].astype(bool), dados["formula"].map(mapa))

    # Os campos abaixo já são produzidos pelo fluxo quimiométrico e não exigem reprocessar a triagem.
    anexar_coluna("score", ["score", "final"])
    anexar_coluna("mc_media", ["media", "monte", "score"])
    anexar_coluna("mc_desvio", ["desvio", "monte", "score"])
    anexar_coluna("pc1", ["componente", "principal", "1"])
    anexar_coluna("pc2", ["componente", "principal", "2"])
    anexar_coluna("grupo", ["grupo", "quimiometrico"], numerica=False)
    anexar_coluna("t2", ["hotelling", "t"])
    anexar_coluna("q_residual", ["q", "residual"])
    anexar_coluna("limiar_t2", ["limiar", "hotelling", "t"])
    anexar_coluna("limiar_q", ["limiar", "q", "residual"])
    anexar_coluna("dominio", ["classe", "dominio"], numerica=False)
    anexar_coluna("score_dominio", ["score", "dominio"])
    anexar_coluna("pareto", ["fronteira", "pareto"], numerica=False)
    anexar_coluna("desejabilidade", ["desejabilidade", "global"])
    anexar_coluna("atividade", ["score", "atividade"])
    anexar_coluna("seletividade", ["score", "seletividade"])
    dados["formula_exibicao"] = dados["formula"].map(formatar_formula_quimica)

    dados["dominio"] = dados["dominio"].fillna("não calculado").astype(str)
    dominio_norm = dados["dominio"].map(normalizar_texto)
    dados["classe_dominio"] = np.select(
        [dominio_norm.str.contains("fora"), dominio_norm.str.contains("atencao")],
        [texto("Fora do domínio", "Outside domain"), texto("Zona de atenção", "Attention zone")],
        default=texto("Dentro do domínio", "Within domain"),
    )
    cores_dominio = {
        texto("Dentro do domínio", "Within domain"): "#16843C",
        texto("Zona de atenção", "Attention zone"): "#D88D00",
        texto("Fora do domínio", "Outside domain"): "#D63B36",
    }
    dentro = dados["classe_dominio"].eq(texto("Dentro do domínio", "Within domain"))
    cobertura = float(dentro.mean()) if len(dados) else np.nan
    r2_cv = extrair_metrica(validacao_quimio_df, "melhor r2 cv pcr plsr")
    rmse_cv = extrair_metrica(validacao_quimio_df, "melhor rmse cv pcr plsr")
    spearman = extrair_metrica(validacao_quimio_df, "correlacao spearman ranking monte carlo")
    n_descritores = extrair_metrica(validacao_quimio_df, "numero de descritores quimiometricos")
    variancia_pca = extrair_metrica(validacao_quimio_df, "variancia explicada pc1 pc2")
    ensaios_doe = extrair_metrica(validacao_quimio_df, "ensaios doe sugeridos")
    n_dentro = int(dentro.sum())
    n_total = int(len(dados))

    st.markdown(
        """<style>
        .validation-title{margin:6px 0 13px;color:#14213D;font-size:clamp(1.62rem,2.35vw,2.2rem);font-weight:850;text-align:left}.validation-subtitle{margin:-6px 0 16px;color:#66758B;font-size:.84rem}.validation-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:0 0 14px}.validation-kpi{display:grid;grid-template-columns:52px 1fr;align-items:center;min-height:106px;padding:14px;border:1px solid #D9E5DF;border-radius:8px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.05)}.validation-kpi-icon{display:grid;width:42px;height:42px;place-items:center;border-radius:8px;background:#EEF7F1;color:#16843C;font-size:1rem;font-weight:900}.validation-kpi b{display:block;color:#263B58;font-size:.73rem;line-height:1.2}.validation-kpi strong{display:block;margin:5px 0 2px;color:#1262C5;font-size:1.52rem;line-height:1}.validation-kpi span{display:block;color:#64748B;font-size:.68rem;line-height:1.28}.validation-section{margin:15px 0 8px;color:#14213D;font-size:1.02rem;font-weight:850}.validation-panel{min-height:100%;padding:11px 12px 4px;border:1px solid #DCE6E0;border-radius:8px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.035)}.validation-panel h3{margin:0 0 5px;color:#153A70;font-size:.91rem;line-height:1.25}.validation-panel p{margin:0 0 7px;color:#6A7688;font-size:.66rem;line-height:1.35}.validation-note{min-height:100%;padding:18px;border:1px solid #7BC29B;border-radius:8px;background:#F5FCF7;color:#273D4B;font-size:.78rem;line-height:1.55}.validation-note h3{margin:0 0 10px;color:#087A3B;font-size:.96rem}.validation-note ul{margin:8px 0 0;padding-left:18px}.validation-summary{display:grid;gap:8px}.validation-summary div{padding:9px 10px;border-left:3px solid #16843C;background:#F7FAF8;color:#41556A;font-size:.73rem;line-height:1.38}.validation-summary b{display:block;color:#153A70;font-size:.76rem}@media(max-width:960px){.validation-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.validation-kpis{grid-template-columns:1fr}}
        </style>""",
        unsafe_allow_html=True,
    )
    titulo = texto("Validação e domínio de aplicabilidade", "Validation and applicability domain")
    subtitulo = texto(
        "Diagnósticos internos da triagem, qualidade do espaço quimiométrico e limites de extrapolação.",
        "Internal screening diagnostics, chemometric-space quality, and extrapolation limits.",
    )
    kpis = [
        ("R²", texto("R² CV do modelo proxy", "Proxy-model CV R²"), formatar_valor(r2_cv), texto("validação cruzada interna", "internal cross-validation")),
        ("RMSE", texto("RMSE CV do modelo proxy", "Proxy-model CV RMSE"), formatar_valor(rmse_cv), texto("alvo proxy; não experimental", "proxy target; not experimental")),
        ("ρ", texto("Estabilidade do ranking", "Ranking stability"), formatar_valor(spearman), texto("Spearman: nominal versus Monte Carlo", "Spearman: nominal versus Monte Carlo")),
        ("AD", texto("Dentro do domínio", "Within applicability domain"), "-" if pd.isna(cobertura) else f"{100 * cobertura:.1f}%", f"{n_dentro} {texto('de', 'of')} {n_total} {texto('candidatos', 'candidates')}"),
    ]
    kpis_html = "".join(f"<article class='validation-kpi'><span class='validation-kpi-icon'>{sigla}</span><div><b>{html.escape(nome)}</b><strong>{html.escape(valor)}</strong><span>{html.escape(nota)}</span></div></article>" for sigla, nome, valor, nota in kpis)
    st.markdown(f"<h2 class='validation-title'>{html.escape(titulo)}</h2><p class='validation-subtitle'>{html.escape(subtitulo)}</p><section class='validation-kpis'>{kpis_html}</section>", unsafe_allow_html=True)

    def configurar_figura(figura: go.Figure, titulo_figura: str, eixo_x: str, eixo_y: str, altura: int = 320) -> go.Figure:
        """Aplica a mesma identidade visual aos gráficos interativos de validação."""
        figura.update_layout(template="simple_white", title=titulo_figura, height=altura, margin=dict(l=42, r=14, t=48, b=42), font=dict(color="#24334E", size=11), legend=dict(font=dict(size=9), bgcolor="rgba(255,255,255,.82)"), xaxis_title=eixo_x, yaxis_title=eixo_y)
        figura.update_xaxes(gridcolor="#E7EDF2", zerolinecolor="#D9E1E8")
        figura.update_yaxes(gridcolor="#E7EDF2", zerolinecolor="#D9E1E8")
        return figura

    primeira, segunda, terceira = st.columns(3)
    with primeira:
        st.markdown(f"<div class='validation-panel'><h3>1. {html.escape(texto('Consistência do ranking', 'Ranking consistency'))}</h3><p>{html.escape(texto('Score nominal comparado à média da simulação Monte Carlo.', 'Nominal score compared with the Monte Carlo mean.'))}</p></div>", unsafe_allow_html=True)
        consistencia = dados.dropna(subset=["score", "mc_media"]).copy()
        if consistencia.empty:
            st.info(texto("A execução não contém pares de score nominal e Monte Carlo.", "This execution has no nominal-score and Monte Carlo pairs."))
        else:
            erro = consistencia["mc_desvio"].fillna(0).clip(lower=0)
            figura = go.Figure(go.Scatter(x=consistencia["score"], y=consistencia["mc_media"], mode="markers", marker=dict(color="#2168C5", size=9), error_y=dict(type="data", array=erro, visible=bool(erro.gt(0).any())), text=consistencia["formula_exibicao"], hovertemplate="%{text}<br>Score nominal: %{x:.3f}<br>Média MC: %{y:.3f}<extra></extra>", name=texto("Candidatos", "Candidates")))
            limite_min = float(np.nanmin(consistencia[["score", "mc_media"]].to_numpy()))
            limite_max = float(np.nanmax(consistencia[["score", "mc_media"]].to_numpy()))
            margem = max((limite_max - limite_min) * .08, .03)
            figura.add_trace(go.Scatter(x=[limite_min - margem, limite_max + margem], y=[limite_min - margem, limite_max + margem], mode="lines", line=dict(color="#48576A", dash="dash"), name="y = x"))
            st.plotly_chart(configurar_figura(figura, "", texto("Score nominal", "Nominal score"), texto("Média Monte Carlo", "Monte Carlo mean")), width="stretch")
    with segunda:
        st.markdown(f"<div class='validation-panel'><h3>2. {html.escape(texto('Domínio de aplicabilidade', 'Applicability domain'))}</h3><p>{html.escape(texto('Hotelling T² e Q residual; linhas tracejadas são os limiares calculados.', 'Hotelling T² and Q residual; dashed lines are calculated thresholds.'))}</p></div>", unsafe_allow_html=True)
        dominio_plot = dados.dropna(subset=["t2", "q_residual"]).copy()
        if dominio_plot.empty:
            st.info(texto("Os diagnósticos T² e Q residual não foram exportados.", "T² and Q-residual diagnostics were not exported."))
        else:
            dominio_plot["t2_plot"] = dominio_plot["t2"].clip(lower=1e-4)
            dominio_plot["q_plot"] = dominio_plot["q_residual"].clip(lower=1e-5)
            figura = px.scatter(dominio_plot, x="t2_plot", y="q_plot", color="classe_dominio", color_discrete_map=cores_dominio, hover_name="formula_exibicao", log_x=True, log_y=True)
            limiar_t2 = dominio_plot["limiar_t2"].dropna().median()
            limiar_q = dominio_plot["limiar_q"].dropna().median()
            if pd.notna(limiar_t2):
                figura.add_vline(x=float(limiar_t2), line_dash="dash", line_color="#E58A19")
            if pd.notna(limiar_q):
                figura.add_hline(y=float(limiar_q), line_dash="dot", line_color="#E58A19")
            st.plotly_chart(configurar_figura(figura, "", "Hotelling T²", "Q residual"), width="stretch")
    with terceira:
        st.markdown(f"<div class='validation-panel'><h3>3. {html.escape(texto('Mapa PCA do espaço químico', 'PCA map of chemical space'))}</h3><p>{html.escape(texto('A dispersão mostra a posição multivariada dos candidatos no espaço de descritores.', 'The scatter shows the multivariate position of candidates in descriptor space.'))}</p></div>", unsafe_allow_html=True)
        pca_plot = dados.dropna(subset=["pc1", "pc2"]).copy()
        if pca_plot.empty:
            st.info(texto("Os componentes principais não foram exportados nesta execução.", "Principal components were not exported in this run."))
        else:
            figura = px.scatter(pca_plot, x="pc1", y="pc2", color="classe_dominio", color_discrete_map=cores_dominio, symbol="grupo", hover_name="formula_exibicao", hover_data={"score": ":.3f", "score_dominio": ":.3f"})
            figura.add_hline(y=0, line_color="#C9D3DF", line_width=1)
            figura.add_vline(x=0, line_color="#C9D3DF", line_width=1)
            st.plotly_chart(configurar_figura(figura, "", "PC1", "PC2"), width="stretch")

    pareto_coluna, grupos_coluna = st.columns([1.16, .84])
    with pareto_coluna:
        st.markdown(f"<div class='validation-panel'><h3>4. {html.escape(texto('Fronteira de Pareto e desejabilidade', 'Pareto frontier and desirability'))}</h3><p>{html.escape(texto('Candidatos não dominados representam compromissos entre objetivos simultâneos.', 'Non-dominated candidates represent trade-offs between simultaneous objectives.'))}</p></div>", unsafe_allow_html=True)
        pareto_plot = dados.dropna(subset=["desejabilidade", "score"]).copy()
        eixo_x, eixo_y = "score", "desejabilidade"
        titulo_x, titulo_y = texto("Score final", "Final score"), texto("Desejabilidade global", "Global desirability")
        if dados["atividade"].notna().any() and dados["seletividade"].notna().any():
            pareto_plot = dados.dropna(subset=["atividade", "seletividade"]).copy()
            eixo_x, eixo_y = "atividade", "seletividade"
            titulo_x, titulo_y = texto("Score de atividade", "Activity score"), texto("Score de seletividade", "Selectivity score")
        if pareto_plot.empty:
            st.info(texto("Dados insuficientes para a fronteira de Pareto.", "Insufficient data for the Pareto frontier."))
        else:
            pareto_plot["pareto_sim"] = pareto_plot["pareto"].astype(str).map(normalizar_texto).isin(["true", "sim", "1"])
            figura = px.scatter(pareto_plot, x=eixo_x, y=eixo_y, color="pareto_sim", color_discrete_map={True: "#16843C", False: "#BBC7D2"}, hover_name="formula_exibicao", hover_data={"desejabilidade": ":.3f", "score_dominio": ":.3f"}, labels={"pareto_sim": texto("Fronteira de Pareto", "Pareto frontier")})
            fronteira = pareto_plot.loc[pareto_plot["pareto_sim"]].sort_values(eixo_x)
            if len(fronteira) > 1:
                figura.add_trace(go.Scatter(x=fronteira[eixo_x], y=fronteira[eixo_y], mode="lines", line=dict(color="#4E8BE2", dash="dash"), name=texto("Fronteira", "Frontier")))
            st.plotly_chart(configurar_figura(figura, "", titulo_x, titulo_y), width="stretch")
    with grupos_coluna:
        st.markdown(f"<div class='validation-panel'><h3>{html.escape(texto('Perfil por grupo quimiométrico', 'Chemometric-group profile'))}</h3><p>{html.escape(texto('Média de score e fração dentro do domínio por agrupamento PCA/K-means.', 'Mean score and within-domain fraction by PCA/K-means group.'))}</p></div>", unsafe_allow_html=True)
        grupos = dados[dados["grupo"].astype(str).str.len().gt(0)].copy()
        if grupos.empty:
            st.info(texto("Os grupos quimiométricos não foram exportados.", "Chemometric groups were not exported."))
        else:
            grupos["dentro"] = grupos["classe_dominio"].eq(texto("Dentro do domínio", "Within domain")).astype(float)
            resumo_grupos = grupos.groupby("grupo", as_index=False).agg(score=("score", "mean"), cobertura=("dentro", "mean"))
            figura = go.Figure()
            figura.add_trace(go.Bar(x=resumo_grupos["grupo"].astype(str), y=resumo_grupos["score"], name=texto("Score médio", "Mean score"), marker_color="#2168C5"))
            figura.add_trace(go.Bar(x=resumo_grupos["grupo"].astype(str), y=resumo_grupos["cobertura"], name=texto("Cobertura do domínio", "Domain coverage"), marker_color="#16843C"))
            figura.update_layout(barmode="group")
            st.plotly_chart(configurar_figura(figura, "", texto("Grupo", "Group"), texto("Índice (0–1)", "Index (0–1)")), width="stretch")

    decisao = dados.copy().sort_values(["score", "desejabilidade"], ascending=False, na_position="last").head(10)
    decisao["pareto_texto"] = decisao["pareto"].astype(str).map(normalizar_texto).isin(["true", "sim", "1"]).map({True: texto("Sim", "Yes"), False: texto("Não", "No")})
    decisao["acao"] = np.select(
        [decisao["classe_dominio"].eq(texto("Fora do domínio", "Outside domain")), decisao["classe_dominio"].eq(texto("Zona de atenção", "Attention zone")), decisao["pareto_texto"].eq(texto("Sim", "Yes"))],
        [texto("Não extrapolar: coletar evidências", "Do not extrapolate: collect evidence"), texto("Validar experimentalmente", "Validate experimentally"), texto("Priorizar para síntese", "Prioritize for synthesis")],
        default=texto("Confirmar em bancada", "Confirm in laboratory"),
    )
    tabela_decisao = decisao[["formula", "score", "classe_dominio", "t2", "q_residual", "desejabilidade", "pareto_texto", "acao"]].copy()
    tabela_decisao["formula"] = tabela_decisao["formula"].map(formatar_formula_quimica)
    tabela_decisao.insert(0, "#", range(1, len(tabela_decisao) + 1))
    tabela_decisao.columns = ["#", texto("Candidato", "Candidate"), texto("Score previsto", "Predicted score"), texto("Status de domínio", "Domain status"), "T²", "Q residual", texto("Desejabilidade", "Desirability"), texto("Pareto", "Pareto"), texto("Ação recomendada", "Recommended action")]
    for coluna in [texto("Score previsto", "Predicted score"), "T²", "Q residual", texto("Desejabilidade", "Desirability")]:
        tabela_decisao[coluna] = tabela_decisao[coluna].map(lambda valor: "-" if pd.isna(valor) else f"{float(valor):.3f}")

    coluna_tabela = st.container()
    coluna_nota = st.container()
    with coluna_tabela:
        st.markdown(f"<h3 class='validation-section'>5. {html.escape(texto('Decisão para candidatos', 'Candidate decision'))}</h3>", unsafe_allow_html=True)
        st.dataframe(tabela_decisao, hide_index=True, width="stretch")
    with coluna_nota:
        linhas_relatorio = []
        if not relatorio_validacao_df.empty:
            col_criterio = encontrar_coluna(relatorio_validacao_df, ["criterio"])
            col_status = encontrar_coluna(relatorio_validacao_df, ["status"])
            col_evidencia = encontrar_coluna(relatorio_validacao_df, ["evidencia"])
            if col_criterio and col_status and col_evidencia:
                for _, linha in relatorio_validacao_df.head(4).iterrows():
                    linhas_relatorio.append(f"<div><b>{html.escape(corrigir_texto_portugues(linha[col_criterio]))}</b>{html.escape(corrigir_texto_portugues(linha[col_status]))}: {html.escape(corrigir_texto_portugues(linha[col_evidencia]))}</div>")
        resumo_modelo = [
            f"<div><b>{html.escape(texto('Modelo de referência', 'Reference model'))}</b>PCR/PLSR {html.escape(texto('aplicado a alvos proxy', 'applied to proxy targets'))}.</div>",
            f"<div><b>{html.escape(texto('Descritores e PCA', 'Descriptors and PCA'))}</b>{formatar_valor(n_descritores)} {html.escape(texto('descritores; PC1 + PC2 =', 'descriptors; PC1 + PC2 ='))} {formatar_valor(variancia_pca, percentual=True)}.</div>",
            f"<div><b>{html.escape(texto('Planejamento experimental', 'Experimental design'))}</b>{formatar_valor(ensaios_doe)} {html.escape(texto('ensaios DOE sugeridos para confirmação', 'DOE experiments suggested for confirmation'))}.</div>",
        ]
        resumo_html = "".join(resumo_modelo + linhas_relatorio) if linhas_relatorio else "".join(resumo_modelo)
        nota = texto("Os painéis acima avaliam coerência interna, domínio de aplicabilidade e estabilidade do ranking. Eles não substituem conversão, seletividade, estabilidade temporal ou balanço de massa obtidos em experimento.", "The panels above assess internal consistency, applicability domain, and ranking stability. They do not replace conversion, selectivity, time-on-stream stability, or mass balance obtained experimentally.")
        st.markdown(f"<aside class='validation-note'><h3>{html.escape(texto('Nota científica', 'Scientific note'))}</h3><p>{html.escape(nota)}</p><div class='validation-summary'>{resumo_html}</div></aside>", unsafe_allow_html=True)


def mostrar_painel_arquivos(
    paths: dict[str, Path],
    metricas_df: pd.DataFrame,
    classificacao_df: pd.DataFrame,
    reacao: str,
) -> None:
    """Centraliza downloads, metadados da execução e rastreabilidade das fontes do fluxo."""
    ingles = idioma_atual() == "en"

    def texto(portugues: str, ingles_texto: str) -> str:
        """Traduz os rótulos do painel sem modificar nomes físicos de arquivos."""
        return ingles_texto if ingles else portugues

    def tamanho_legivel(caminho: Path) -> str:
        """Mostra o tamanho real do arquivo sem arredondar artificialmente valores pequenos."""
        tamanho = caminho.stat().st_size
        if tamanho < 1024 * 1024:
            return f"{tamanho / 1024:.1f} KB"
        return f"{tamanho / (1024 * 1024):.2f} MB"

    def tipo_arquivo(caminho: Path) -> str:
        """Normaliza a extensão para o selo exibido na lista de arquivos."""
        return {".xlsx": "XLSX", ".csv": "CSV", ".html": "HTML", ".json": "JSON"}.get(caminho.suffix.lower(), caminho.suffix.lstrip(".").upper() or "ARQ")

    arquivos = [
        ("resultados", paths["excel"], texto("Resultados completos da triagem com previsões e métricas.", "Complete screening results with predictions and metrics.")),
        ("ranking", paths["ranking"], texto("Ranking final após filtros, condições e ponderações.", "Final ranking after filters, conditions, and weights.")),
        ("metricas", paths["metricas"], texto("Métricas de funil, desempenho, estabilidade operacional e incerteza.", "Funnel, performance, operational stability, and uncertainty metrics.")),
        ("monte_carlo", paths["monte_carlo"], texto("Ranking e dispersão estimados pela simulação Monte Carlo.", "Ranking and dispersion estimated by Monte Carlo simulation.")),
        ("dominio", paths["dominio"], texto("Diagnóstico de Hotelling T², Q residual e domínio de aplicabilidade.", "Hotelling T², Q-residual, and applicability-domain diagnostic.")),
        ("pareto", paths["pareto"], texto("Compromissos multicritério e fronteira de Pareto.", "Multi-criteria trade-offs and Pareto frontier.")),
        ("validacao", paths["validacao_quimio"], texto("PCA, agrupamento, DOE e métricas de validação interna.", "PCA, clustering, DOE, and internal-validation metrics.")),
        ("relatorio", paths["html"], texto("Relatório HTML com resumo, análises e gráficos.", "HTML report with summary, analyses, and charts.")),
        ("configuracao", paths["resumo"], texto("Configuração, descritores e artefatos produzidos na execução.", "Configuration, descriptors, and artifacts produced in the run.")),
        ("figuras", paths["figuras"], texto("Índice dos gráficos e figuras científicas geradas.", "Index of generated scientific charts and figures.")),
    ]
    arquivos = [(chave, caminho, descricao) for chave, caminho, descricao in arquivos if caminho.exists()]
    if not arquivos:
        st.info(texto("Nenhum arquivo de resultado foi encontrado para esta execução.", "No result file was found for this run."))
        return

    resumo = {}
    if paths["resumo"].exists():
        try:
            resumo = json.loads(paths["resumo"].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            resumo = {}
    referencia_tempo = paths["resumo"] if paths["resumo"].exists() else max((caminho for _, caminho, _ in arquivos), key=lambda caminho: caminho.stat().st_mtime)
    data_execucao = datetime.fromtimestamp(referencia_tempo.stat().st_mtime)
    hash_execucao = hashlib.sha256(referencia_tempo.read_bytes()).hexdigest()
    id_execucao = f"RUN-{data_execucao:%Y%m%d}-{hash_execucao[:6].upper()}"
    n_avaliados = extrair_metrica(metricas_df, "candidatos gerados") or len(classificacao_df)
    nome_reacao = {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}.get(reacao, reacao)
    reacoes_equacao = {"metanacao": "CO₂ + 4H₂ → CH₄ + 2H₂O", "reforma": "CH₄ + CO₂ → 2CO + 2H₂", "rwgs": "CO₂ + H₂ → CO + H₂O"}
    primeira_linha = classificacao_df.iloc[0] if not classificacao_df.empty else pd.Series(dtype=object)
    temperatura = valor_linha(primeira_linha, ["temperatura"])
    pressao = valor_linha(primeira_linha, ["pressao"])
    nome_razao = valor_linha(primeira_linha, ["nome", "razao"])
    valor_razao = valor_linha(primeira_linha, ["valor", "razao"])
    condicoes = " · ".join(parte for parte in [f"T = {formatar_valor(temperatura)} °C" if temperatura not in ["", "-"] else "", f"P = {formatar_valor(pressao)} bar" if pressao not in ["", "-"] else "", f"{nome_razao} = {formatar_valor(valor_razao)}" if nome_razao not in ["", "-"] and valor_razao not in ["", "-"] else ""] if parte) or texto("Não registradas", "Not recorded")

    st.markdown(
        """<style>
        .files-title{margin:6px 0 12px;color:#14213D;font-size:clamp(1.62rem,2.4vw,2.2rem);font-weight:850}.files-main-grid{display:grid;grid-template-columns:minmax(0,1fr) 318px;gap:16px;align-items:start}.files-run-meta{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid #DCE6E0;border-radius:9px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.04);overflow:hidden}.files-run-meta div{min-height:82px;padding:14px;border-right:1px solid #E4EBE7}.files-run-meta div:last-child{border-right:0}.files-run-meta b{display:block;color:#263B58;font-size:.70rem}.files-run-meta strong{display:block;margin-top:8px;color:#087A3B;font-size:.91rem;line-height:1.25}.files-run-meta span{display:block;margin-top:7px;color:#244D92;font-size:.79rem;font-weight:800;line-height:1.28}.files-shell{margin-top:12px;padding:12px 14px;border:1px solid #DCE6E0;border-radius:9px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.04)}.files-shell h3{margin:0 0 10px;color:#153A70;font-size:1rem}.files-head{display:grid;grid-template-columns:1.30fr .58fr .90fr 1.90fr .52fr .32fr;gap:8px;padding:8px 10px;border-top:1px solid #E5EDE8;border-bottom:1px solid #E5EDE8;color:#334A69;font-size:.67rem;font-weight:850}.files-row{padding:8px 0;border-bottom:1px solid #E8EFEB}.files-row:last-child{border-bottom:0}.files-row [data-testid='stHorizontalBlock']{align-items:center}.files-file-name{color:#146CC1;font-size:.78rem;font-weight:850;overflow-wrap:anywhere}.files-file-type{display:inline-block;padding:4px 6px;border-radius:5px;background:#E7F5EC;color:#087A3B;font-size:.64rem;font-weight:850}.files-small{color:#455B74;font-size:.67rem;line-height:1.35}.files-repro{padding:17px;border:1px solid #DCE6E0;border-radius:9px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.04)}.files-repro h3{margin:0 0 12px;color:#087A3B;font-size:1rem}.files-repro-item{padding:12px 0;border-bottom:1px solid #E5EDE8}.files-repro-item:last-child{border-bottom:0}.files-repro-item b{display:block;color:#263B58;font-size:.72rem}.files-repro-item span{display:block;margin-top:6px;color:#1E61BC;font-size:.73rem;line-height:1.42;overflow-wrap:anywhere}.files-trace{margin-top:16px;padding:13px;border:1px solid #DCE6E0;border-radius:9px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.04)}.files-trace h3{margin:0;color:#153A70;font-size:1rem}.files-trace-note{margin:6px 0 12px;color:#A46900;font-size:.72rem;font-weight:750}.files-trace-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}.files-trace-card{min-height:130px;padding:12px;border:1px solid #DDE8E2;border-radius:7px;background:#FCFDFD}.files-trace-card b{display:block;color:#153A70;font-size:.78rem}.files-trace-card span{display:block;margin-top:8px;color:#465A70;font-size:.68rem;line-height:1.38}.files-trace-card strong{display:block;margin-top:8px;color:#087A3B;font-size:.68rem}.files-available{margin:10px 0 0;color:#66758B;font-size:.67rem}@media(max-width:1350px){.files-run-meta{grid-template-columns:repeat(3,minmax(0,1fr))}.files-run-meta div:nth-child(3){border-right:0}}@media(max-width:1080px){.files-main-grid{grid-template-columns:1fr}.files-trace-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:760px){.files-run-meta{grid-template-columns:repeat(2,minmax(0,1fr))}.files-run-meta div:nth-child(2){border-right:0}.files-trace-grid{grid-template-columns:1fr}.files-head{display:none}}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<style>
        .files-main-grid{grid-template-columns:1fr;gap:12px}
        .files-repro{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0;padding:0;overflow:hidden}
        .files-repro h3{grid-column:1/-1;margin:0;padding:13px 15px;border-bottom:1px solid #E5EDE8}
        .files-repro-item{min-height:94px;padding:12px 14px;border-right:1px solid #E5EDE8;border-bottom:0}
        .files-repro-item:last-child{border-right:0}
        @media(max-width:1080px){.files-repro{grid-template-columns:repeat(3,minmax(0,1fr))}}
        @media(max-width:760px){.files-repro{grid-template-columns:repeat(2,minmax(0,1fr))}}
        </style>""",
        unsafe_allow_html=True,
    )
    metadados = [
        (texto("ID da execução", "Run ID"), id_execucao),
        (texto("Reação", "Reaction"), reacoes_equacao.get(reacao, nome_reacao)),
        (texto("Data e hora", "Date and time"), data_execucao.strftime("%d/%m/%Y %H:%M:%S")),
        (texto("Fontes configuradas", "Configured sources"), texto("3 remotas + cache local", "3 remote + local cache")),
        (texto("Candidatos avaliados", "Candidates evaluated"), formatar_valor(n_avaliados)),
    ]
    metadados_html = "".join(f"<div><b>{html.escape(rotulo)}</b><strong>{html.escape(valor)}</strong></div>" for rotulo, valor in metadados)
    st.markdown(f"<h2 class='files-title'>{html.escape(texto('Resultados e arquivos da triagem', 'Screening results and files'))}</h2><div class='files-main-grid'><section><div class='files-run-meta'>{metadados_html}</div></section><aside class='files-repro'><h3>{html.escape(texto('Reprodutibilidade da triagem', 'Screening reproducibility'))}</h3><div class='files-repro-item'><b>{html.escape(texto('Versão do painel', 'Panel version'))}</b><span>CatAiLab 1.0</span></div><div class='files-repro-item'><b>{html.escape(texto('Semente aleatória', 'Random seed'))}</b><span>42</span></div><div class='files-repro-item'><b>{html.escape(texto('Snapshot dos resultados', 'Results snapshot'))}</b><span>{data_execucao.strftime('%d/%m/%Y %H:%M:%S')}</span></div><div class='files-repro-item'><b>{html.escape(texto('Condições de reação', 'Reaction conditions'))}</b><span>{html.escape(condicoes)}</span></div><div class='files-repro-item'><b>{html.escape(texto('Hash de verificação', 'Verification hash'))}</b><span>{hash_execucao[:24]}</span></div></aside></div>", unsafe_allow_html=True)

    st.markdown(f"<section class='files-shell'><h3>{html.escape(texto('Arquivos gerados', 'Generated files'))}</h3><div class='files-head'><span>{html.escape(texto('Arquivo', 'File'))}</span><span>{html.escape(texto('Tipo', 'Type'))}</span><span>{html.escape(texto('Data de geração', 'Generated at'))}</span><span>{html.escape(texto('Conteúdo de dados', 'Data contents'))}</span><span>{html.escape(texto('Tamanho', 'Size'))}</span><span>{html.escape(texto('Download', 'Download'))}</span></div></section>", unsafe_allow_html=True)
    for chave, caminho, descricao in arquivos:
        data_arquivo = datetime.fromtimestamp(caminho.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        col_nome, col_tipo, col_data, col_descricao, col_tamanho, col_download = st.columns([1.30, .58, .90, 1.90, .52, .32], gap="small")
        with col_nome:
            st.markdown(f"<div class='files-row'><span class='files-file-name'>{html.escape(caminho.name)}</span></div>", unsafe_allow_html=True)
        with col_tipo:
            st.markdown(f"<div class='files-row'><span class='files-file-type'>{tipo_arquivo(caminho)}</span></div>", unsafe_allow_html=True)
        with col_data:
            st.markdown(f"<div class='files-row'><span class='files-small'>{data_arquivo}</span></div>", unsafe_allow_html=True)
        with col_descricao:
            st.markdown(f"<div class='files-row'><span class='files-small'>{html.escape(descricao)}</span></div>", unsafe_allow_html=True)
        with col_tamanho:
            st.markdown(f"<div class='files-row'><span class='files-small'>{tamanho_legivel(caminho)}</span></div>", unsafe_allow_html=True)
        with col_download:
            st.download_button("⇩", data=caminho.read_bytes(), file_name=caminho.name, mime={".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".html": "text/html", ".json": "application/json"}.get(caminho.suffix.lower(), "text/csv"), key=f"download_{chave}_{slug_texto(caminho.name)}", help=texto("Baixar arquivo", "Download file"), width="stretch")
    st.markdown(f"<p class='files-available'>{html.escape(texto('Os arquivos listados estão disponíveis para download nesta execução.', 'Listed files are available for download in this run.'))}</p>", unsafe_allow_html=True)

    rastreabilidade = [
        ("1", "Materials Project", texto("Repositório de materiais", "Materials repository"), texto("Consulta incremental quando não há registro local.", "Incremental lookup when no local record exists."), texto("Fonte configurada", "Configured source")),
        ("2", "OQMD", texto("Banco de dados de materiais", "Materials database"), texto("Consulta sob demanda para propriedades ausentes.", "On-demand lookup for missing properties."), texto("Fonte configurada", "Configured source")),
        ("3", "Catalysis-Hub", texto("Dados catalíticos de superfície", "Surface catalytic data"), texto("Evidências DFT de adsorção quando disponíveis.", "DFT adsorption evidence when available."), texto("Fonte configurada", "Configured source")),
        ("4", texto("Cache local", "Local cache"), texto("Arquivos da execução", "Run files"), texto("CSV e JSON preservam os dados já consultados.", "CSV and JSON preserve data already retrieved."), texto("Fonte local", "Local source")),
        ("5", texto("Seleção final", "Final selection"), texto("Ranking multicritério", "Multi-criteria ranking"), texto("Filtros, desempenho, incerteza e viabilidade de síntese.", "Filters, performance, uncertainty, and synthesis feasibility."), texto("Candidatos finais", "Final candidates")),
    ]
    cards_rastro = "".join(f"<article class='files-trace-card'><b>{numero}. {html.escape(nome)}</b><span>{html.escape(tipo)}<br>{html.escape(descricao)}</span><strong>{html.escape(status)}</strong></article>" for numero, nome, tipo, descricao, status in rastreabilidade)
    st.markdown(f"<section class='files-trace'><h3>{html.escape(texto('Rastreabilidade', 'Traceability'))}</h3><p class='files-trace-note'>{html.escape(texto('Fontes de dados apoiam a triagem, mas não constituem prova de desempenho experimental.', 'Data sources support screening but do not constitute evidence of experimental performance.'))}</p><div class='files-trace-grid'>{cards_rastro}</div></section>", unsafe_allow_html=True)


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

    # Ícones científicos em SVG mantêm a leitura visual do funil sem depender de fontes externas.
    icone_espaco = '<svg viewBox="0 0 48 36" aria-hidden="true"><path d="M5 10 11 5h8l6 5v8l-6 5h-8l-6-5zM20 10l6-5h8l6 5v8l-6 5h-8l-6-5zM12.5 23l6-5h8l6 5v8l-6 5h-8l-6-5z"/></svg>'
    icone_filtro = '<svg viewBox="0 0 36 36" aria-hidden="true"><path d="M4 5h28L21 18v10l-6 3V18z"/><path d="M15 31h6"/></svg>'
    icone_predicao = '<svg viewBox="0 0 42 36" aria-hidden="true"><path d="M17 5c-5 0-8 4-8 9-3 1-5 4-5 8 0 5 4 9 9 9h5V5zM25 5c5 0 8 4 8 9 3 1 5 4 5 8 0 5-4 9-9 9h-5V5zM13 14h8M21 20h8M15 26h6"/></svg>'
    icone_alvo = '<svg viewBox="0 0 42 36" aria-hidden="true"><circle cx="17" cy="19" r="12"/><circle cx="17" cy="19" r="7"/><circle cx="17" cy="19" r="2"/><path d="m23 13 13-9M29 4h7v7"/></svg>'

    etapas = [
        {
            "rotulo": "Espaço químico inicial",
            "valor": n_gerados,
            "criterio": "Combinações de metais ativos, promotor e composições geradas.",
            "retencao": retencao(n_gerados, None),
            "cor": "#EEF6FF",
            "texto": "#0C5DB8",
            "borda": "#2B7FE4",
            "largura": "100%",
            "icone": icone_espaco,
            "subtitulo": "Geração combinatória de materiais",
            "cartao": "Espaço químico inicial",
        },
        {
            "rotulo": "Filtros aplicados",
            "valor": n_viaveis,
            "criterio": "Estabilidade termodinâmica, composição e regras químicas.",
            "retencao": retencao(n_viaveis, n_gerados),
            "cor": "#EFF9F3",
            "texto": "#167548",
            "borda": "#4AAB78",
            "largura": "84%",
            "icone": icone_filtro,
            "subtitulo": "Propriedades físico-químicas",
            "cartao": "Após filtros aplicados",
        },
        {
            "rotulo": "Predição de desempenho",
            "valor": n_refinados,
            "criterio": "Descritores catalíticos, DFT ou proxy e incerteza do modelo.",
            "retencao": retencao(n_refinados, n_viaveis),
            "cor": "#FFF8EA",
            "texto": "#A86400",
            "borda": "#E3A134",
            "largura": "68%",
            "icone": icone_predicao,
            "subtitulo": "Modelo de aprendizagem de máquina",
            "cartao": "Após predição",
        },
        {
            "rotulo": "Candidatos para síntese",
            "valor": n_recomendados,
            "criterio": "Desempenho, estabilidade do ranking por Monte Carlo e viabilidade de síntese.",
            "retencao": retencao(n_recomendados, n_refinados),
            "cor": "#F5F0FF",
            "texto": "#7340A3",
            "borda": "#9A70C8",
            "largura": "52%",
            "icone": icone_alvo,
            "subtitulo": "Melhores candidatos priorizados",
            "cartao": "Candidatos finais",
        },
    ]
    resumo_cartoes = []
    blocos = []
    for indice, etapa in enumerate(etapas):
        conector = "" if indice == len(etapas) - 1 else '<div class="funil-conector"><i></i><b></b></div>'
        resumo_cartoes.append(
            f"""
            <div class="funil-resumo-cartao">
                <span class="funil-resumo-icone">{etapa['icone']}</span>
                <div><span>{html.escape(etapa['cartao'])}</span><strong>{html.escape(formatar_valor(etapa['valor']))}</strong><small>catalisadores</small></div>
            </div>
            """
        )
        blocos.append(
            f"""
            <div class="funil-linha">
                <div class="funil-etapa" style="--cor-etapa:{etapa['cor']}; --cor-texto:{etapa['texto']}; --cor-borda:{etapa['borda']}; --largura:{etapa['largura']};">
                    <span class="funil-etapa-icone">{etapa['icone']}</span>
                    <div><strong>{html.escape(etapa['rotulo'])}</strong><small>{html.escape(etapa['subtitulo'])}</small></div>
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
                grid-template-columns: 40% 16% 33% 11%;
                gap: 0;
                min-height: 70px;
                align-items: stretch;
            }}
            .funil-etapa {{
                align-self: center;
                justify-self: center;
                display: flex;
                align-items: center;
                justify-content: center;
                width: var(--largura);
                min-height: 70px;
                box-sizing: border-box;
                padding: 12px 30px;
                clip-path: polygon(0 0, 100% 0, calc(100% - 24px) 100%, 24px 100%);
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
                align-items: center;
                justify-content: center;
                padding: 10px 14px;
                color: #182F61;
                text-align: center;
            }}
            .funil-quantidade strong {{
                font-size: 1.35rem;
                line-height: 1.1;
            }}
            .funil-quantidade span {{
                font-size: 0.82rem;
                margin-top: 3px;
            }}
            .funil-rotulo-longo {{
                font-size: 0.86rem;
                line-height: 1.18;
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
                width: 40%;
                height: 20px;
                margin: 0;
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
            .funil-triagem {{
                padding: 0;
                border: 0;
                background: transparent;
            }}
            .funil-titulo {{
                margin: 0 0 16px;
                color: #132D61;
                font-size: 1.45rem;
                font-weight: 850;
                text-align: center;
            }}
            .funil-resumos {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 12px;
                margin-bottom: 16px;
            }}
            .funil-resumo-cartao {{
                display: flex;
                align-items: center;
                gap: 14px;
                min-height: 98px;
                box-sizing: border-box;
                padding: 14px 16px;
                border: 1px solid #C9D8E8;
                border-radius: 8px;
                background: #FFFFFF;
                color: #17305F;
                font-family: Arial, Helvetica, sans-serif;
            }}
            .funil-resumo-icone {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 54px;
                height: 54px;
                border-radius: 8px;
                background: #EDF5FF;
                color: #126ACC;
                font-size: 2rem;
                font-weight: 700;
            }}
            .funil-resumo-icone svg {{ width: 34px; height: 30px; fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }}
            .funil-resumo-cartao div {{ display: flex; flex-direction: column; min-width: 0; }}
            .funil-resumo-cartao div > span {{ font-size: 0.82rem; font-weight: 750; line-height: 1.18; }}
            .funil-resumo-cartao strong {{ color: #145DB8; font-size: 1.55rem; line-height: 1.06; margin-top: 5px; }}
            .funil-resumo-cartao small {{ color: #3D5A86; font-size: 0.78rem; margin-top: 2px; }}
            .funil-painel {{
                box-sizing: border-box;
                padding: 12px 18px 16px;
                border: 1px solid #D6E2EF;
                border-radius: 8px;
                background: #FFFFFF;
            }}
            .funil-cabecalho, .funil-linha {{ grid-template-columns: 46% 16% 28% 10%; }}
            .funil-cabecalho {{
                display: grid;
                align-items: center;
                min-height: 28px;
                border-bottom: 1px solid #CDDCEB;
                color: #125FB6;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 0.8rem;
                font-weight: 800;
                text-align: center;
            }}
            .funil-linha {{
                display: grid;
                min-height: 82px;
                align-items: center;
                border-bottom: 1px dashed #D8E4EF;
            }}
            .funil-linha:last-of-type {{ border-bottom: 0; }}
            .funil-etapa {{
                align-self: center;
                justify-self: center;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 13px;
                width: var(--largura);
                min-height: 72px;
                padding: 10px 28px;
                border: 1.5px solid var(--cor-borda);
                clip-path: polygon(0 0, 100% 0, calc(100% - 20px) 100%, 20px 100%);
                background: var(--cor-etapa);
                color: var(--cor-texto);
                font-family: Arial, Helvetica, sans-serif;
                text-align: center;
            }}
            .funil-etapa-icone {{ display: flex; align-items: center; justify-content: center; width: 38px; height: 34px; line-height: 1; }}
            .funil-etapa-icone svg {{ width: 38px; height: 32px; fill: none; stroke: currentColor; stroke-width: 2.1; stroke-linecap: round; stroke-linejoin: round; }}
            .funil-etapa div {{ display: flex; flex-direction: column; gap: 4px; }}
            .funil-etapa strong {{ font-size: 0.96rem; line-height: 1.12; }}
            .funil-etapa small {{ font-size: 0.75rem; line-height: 1.18; }}
            .funil-quantidade, .funil-criterio, .funil-retencao {{
                display: flex;
                box-sizing: border-box;
                border: 0;
                background: transparent;
                font-family: Arial, Helvetica, sans-serif;
            }}
            .funil-quantidade {{ align-items: center; justify-content: center; padding: 8px; color: #135FB8; text-align: center; }}
            .funil-quantidade strong {{ font-size: 1.35rem; line-height: 1; }}
            .funil-quantidade span {{ display: none; }}
            .funil-criterio {{ align-items: center; justify-content: center; padding: 8px 12px; color: #344B70; font-size: 0.82rem; line-height: 1.28; text-align: center; }}
            .funil-retencao {{ align-items: center; justify-content: center; padding: 8px; text-align: center; }}
            .funil-retencao span {{ display: none; }}
            .funil-retencao strong {{ margin: 0; color: #135FB8; font-size: 1.08rem; }}
            .funil-conector {{ display: none; }}
            @media (max-width: 840px) {{
                .funil-resumos {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
                .funil-cabecalho {{ display: none; }}
                .funil-linha {{ grid-template-columns: 1fr 90px; min-height: 76px; }}
                .funil-etapa {{ width: 100%; }}
                .funil-criterio, .funil-retencao {{ display: none; }}
            }}
        </style>
        <div class="funil-triagem">
            <div class="funil-titulo">Triagem de Catalisadores</div>
            <div class="funil-resumos">{''.join(resumo_cartoes)}</div>
            <div class="funil-painel">
                <div class="funil-cabecalho"><span></span><span>Quantidade de catalisadores</span><span>Critério químico</span><span>Retenção</span></div>
                {''.join(blocos)}
            </div>
        </div>
        """
    )
    st.html(traduzir_texto_exibicao(html_fluxo))


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
        texto = f"{numero:.{casas}f}"
        if casas > 0:
            texto = texto.rstrip("0").rstrip(".")
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
        formula = formatar_formula_quimica(valor_linha(row, ["formula"], valor_linha(row, ["f"], "-")))
        suporte = formatar_formula_quimica(texto_curto(valor_linha(row, ["suporte"], "-"), limite=135))
        condicao = montar_condicao_operacional(row)
        conversao = formatar_numero_linha(row, ["conversao"], "%", casas=1)
        seletividade = formatar_numero_linha(row, ["seletividade"], "%", casas=1)
        confiabilidade = extrair_confiabilidade(row)
        estabilidade = formatar_numero_linha(row, ["estabilidade"], "eV/átomo", casas=3)
        rendimento = formatar_numero_linha(row, ["rendimento"], "%", casas=1)
        score_final = formatar_numero_linha(row, ["score", "final"], "", casas=3)
        rota_sintese = texto_curto(valor_linha(row, ["rota", "sintese"], "-"), limite=135)
        justificativa = texto_curto(
            valor_linha(row, ["justificativa"], valor_linha(row, ["observacao"], "Critérios combinados de estabilidade, atividade e consistência operacional.")),
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


def montar_celula_configuracao(
    reacao: str,
    metais: list[str],
    promotor: str,
    output_dir: Path,
    garantir_metais_nos_100: bool,
) -> str:
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

# Garante que todos os metais ativos sejam representados no conjunto de 100 candidatos viáveis.
GARANTIR_METAIS_NOS_100_VIAVEIS = {garantir_metais_nos_100!r}

# Mostra as escolhas usadas nesta execução.
print("Reação:", reacao_usuario)
print("Metais ativos:", metais_usuario)
print("Promotor:", promotor_usuario)
print("Representação nos 100 viáveis:", GARANTIR_METAIS_NOS_100_VIAVEIS)
""".strip()


def preparar_notebook_parametrizado(
    reacao: str,
    metais: list[str],
    promotor: str,
    output_dir: Path,
    garantir_metais_nos_100: bool,
):
    """Carrega o notebook base e substitui as células de perguntas por parâmetros da interface."""
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    celula_config = montar_celula_configuracao(reacao, metais, promotor, output_dir, garantir_metais_nos_100)
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


def executar_triagem(
    reacao: str,
    metais: list[str],
    promotor: str,
    output_dir: Path,
    garantir_metais_nos_100: bool,
) -> Path:
    """Executa o notebook parametrizado e salva uma cópia executada para auditoria."""
    garantir_pkg_resources()
    mp_api_key = obter_mp_api_key()
    if mp_api_key:
        os.environ["MP_API_KEY"] = mp_api_key
    configurar_banco_incremental_github()
    notebook = preparar_notebook_parametrizado(reacao, metais, promotor, output_dir, garantir_metais_nos_100)
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
    tabela = dataframe.head(linhas).copy()
    for coluna in tabela.columns:
        nome = normalizar_texto(coluna)
        if any(termo in nome for termo in ["formula", "composicao", "suporte", "adsorbato"]):
            tabela[coluna] = tabela[coluna].map(lambda valor: formatar_formula_quimica(valor) if pd.notna(valor) else valor)
        elif tabela[coluna].dtype == object:
            tabela[coluna] = tabela[coluna].map(lambda valor: corrigir_texto_portugues(valor) if pd.notna(valor) else valor)
    tabela_centralizada = tabela.style.set_properties(**{"text-align": "center"}).set_table_styles(
        [
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "center")]},
        ]
    )
    st.dataframe(tabela_centralizada, width="stretch", hide_index=True)


def montar_tabela_candidatos(fontes: list[pd.DataFrame], linhas: int = 10) -> pd.DataFrame:
    """Consolida candidatos distintos em uma tabela científica curta para decisão."""
    registros = []
    formulas_vistas = set()
    for dataframe in fontes:
        if dataframe.empty:
            continue
        coluna_formula = encontrar_coluna(dataframe, ["formula"]) or dataframe.columns[0]
        for _, linha in dataframe.iterrows():
            formula = str(linha.get(coluna_formula, "")).strip()
            chave = normalizar_texto(formula)
            if not formula or chave in formulas_vistas:
                continue
            formulas_vistas.add(chave)
            registros.append({
                "Fórmula": formula,
                "Suporte sugerido": corrigir_texto_portugues(valor_linha(linha, ["suporte", "sugerido"])),
                "Estabilidade termodinâmica (eV/átomo)": valor_linha(linha, ["estabilidade", "termodinamica"]),
                "Pontuação final (0-1)": valor_linha(linha, ["score", "final"]),
                "Incerteza (desvio Monte Carlo)": valor_linha(linha, ["desvio", "monte", "carlo"]),
                "Rota de síntese": corrigir_texto_portugues(valor_linha(linha, ["rota", "sintese"])),
                "Confiança": valor_linha(linha, ["confiabilidade"]),
                "Atividade": valor_linha(linha, ["score", "atividade"]),
                "Estabilidade": valor_linha(linha, ["score", "estabilidade"]),
                "Seletividade": valor_linha(linha, ["score", "seletividade"]),
                "Robustez": valor_linha(linha, ["score", "faixa", "condicao"]),
            })
            if len(registros) >= linhas:
                break
        if len(registros) >= linhas:
            break
    return pd.DataFrame(registros)


def mostrar_candidatos_prioritarios(metricas_df: pd.DataFrame, fontes: list[pd.DataFrame]) -> None:
    """Renderiza a aba de candidatos no formato resumido da referência visual."""
    candidatos_df = montar_tabela_candidatos(fontes, linhas=10)
    n_gerados = extrair_metrica(metricas_df, "candidatos gerados") or len(candidatos_df)
    n_viaveis = extrair_metrica(metricas_df, "candidatos vi") or len(candidatos_df)
    n_refinados = extrair_metrica(metricas_df, "candidatos refinados") or len(candidatos_df)
    n_finais = len(candidatos_df)
    def formatar_contagem(valor) -> str:
        """Exibe contagens inteiras em padrão brasileiro."""
        try:
            return f"{int(round(float(valor))):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "-"
    def formatar_decimal(valor) -> str:
        """Exibe métricas adimensionais e energéticas com três casas decimais."""
        try:
            return f"{float(valor):.3f}".replace(".", ",")
        except (TypeError, ValueError):
            return "-"
    st.markdown("<h3 class='candidate-title'>Candidatos prioritários para síntese</h3>", unsafe_allow_html=True)
    st.markdown("<p class='candidate-subtitle'>Triagem computacional multiobjetivo combinando estabilidade, desempenho e síntese.</p>", unsafe_allow_html=True)
    cards = [("Gerados", formatar_contagem(n_gerados), "candidatos", "base"), ("Viáveis", formatar_contagem(n_viaveis), "candidatos", "shield"), ("Refinados", formatar_contagem(n_refinados), "candidatos", "target"), ("Finais (Top 10)", formatar_contagem(n_finais), "candidatos", "trophy")]
    cards_html = "".join(f"<div class='candidate-metric'><div class='candidate-icon {icone}'></div><div><b>{html.escape(rotulo)}</b><strong>{html.escape(valor)}</strong><span>{html.escape(nota)}</span></div></div>" for rotulo, valor, nota, icone in cards)
    st.markdown(f"<div class='candidate-metrics'>{cards_html}</div>", unsafe_allow_html=True)
    if candidatos_df.empty:
        st.info(t("Tabela ainda não disponível."))
        return
    assinatura_triagem = "|".join(
        candidatos_df[["Fórmula", "Suporte sugerido"]]
        .head(3)
        .fillna("")
        .astype(str)
        .agg("~".join, axis=1)
    )
    deslocamento_paleta = sum(
        (indice + 1) * ord(caractere)
        for indice, caractere in enumerate(assinatura_triagem)
    ) % len(ESTRUTURAS_CATALITICAS)
    ordem_visual_podio = [1, 0, 2]
    classes_posicao = {0: "first", 1: "second", 2: "third"}
    rotulos_posicao = {0: "1", 1: "2", 2: "3"}
    podio_html = []
    for indice_candidato in ordem_visual_podio:
        if indice_candidato >= len(candidatos_df):
            continue
        linha_podio = candidatos_df.iloc[indice_candidato]
        caminho_imagem = ESTRUTURAS_CATALITICAS[
            (deslocamento_paleta + indice_candidato) % len(ESTRUTURAS_CATALITICAS)
        ]
        imagem_html = ""
        if caminho_imagem.exists():
            imagem_base64 = base64.b64encode(caminho_imagem.read_bytes()).decode("utf-8")
            imagem_html = (
                "<img src='data:image/png;base64,"
                f"{imagem_base64}' alt='Representação esquemática do catalisador'>"
            )
        podio_html.append(
            f"<article class='candidate-podium-card {classes_posicao[indice_candidato]}'>"
            f"<span class='candidate-podium-medal'>{rotulos_posicao[indice_candidato]}</span>"
            f"<div class='candidate-podium-image'>{imagem_html}</div>"
            f"<h4>{html.escape(formatar_formula_quimica(linha_podio['Fórmula']))}</h4>"
            "<span class='candidate-podium-label'>Suporte sugerido</span>"
            f"<p>{html.escape(formatar_formula_quimica(linha_podio['Suporte sugerido']))}</p>"
            "<div class='candidate-podium-score'><span>Pontuação final</span>"
            f"<strong>{html.escape(formatar_decimal(linha_podio['Pontuação final (0-1)']))}</strong></div>"
            "</article>"
        )
    st.markdown(
        "<section class='candidate-podium-section'>"
        f"<div class='candidate-podium'>{''.join(podio_html)}</div>"
        "<p class='candidate-podium-note'>Representações esquemáticas: as cores distinguem visualmente "
        "os candidatos e suas fases; não correspondem a geometrias estruturais calculadas por DFT.</p>"
        "</section>",
        unsafe_allow_html=True,
    )
    linhas_html = []
    for posicao, (_, linha) in enumerate(candidatos_df.iterrows(), start=1):
        estabilidade = formatar_decimal(linha["Estabilidade termodinâmica (eV/átomo)"])
        score = formatar_decimal(linha["Pontuação final (0-1)"])
        incerteza = formatar_decimal(linha["Incerteza (desvio Monte Carlo)"])
        confianca = linha["Confiança"]
        classe_confianca = "high" if normalizar_texto(confianca) == "alta" else "medium" if normalizar_texto(confianca) == "media" else "low"
        componentes = [formatar_decimal(linha[chave]) for chave in ["Atividade", "Estabilidade", "Seletividade", "Robustez"]]
        barras_componentes = "".join(f"<span>{html.escape(valor)}</span>" for valor in componentes)
        linhas_html.append("<tr>" f"<td>{posicao}</td><td><b>{html.escape(formatar_formula_quimica(linha['Fórmula']))}</b></td>" f"<td>{html.escape(formatar_formula_quimica(linha['Suporte sugerido']))}</td>" f"<td class='candidate-stability'>{html.escape(str(estabilidade))}</td>" f"<td class='candidate-score'>{html.escape(str(score))}</td>" f"<td class='candidate-uncertainty'>{html.escape(str(incerteza))}</td>" f"<td>{html.escape(str(linha['Rota de síntese']))}</td>" f"<td><span class='candidate-confidence {classe_confianca}'>{html.escape(str(confianca).capitalize())}</span></td>" f"<td><div class='candidate-score-stack'>{barras_componentes}</div></td>" "</tr>")
    tabela_html = "".join(linhas_html)
    st.markdown("<div class='candidate-results-layout'><div class='candidate-table-wrap'><table class='candidate-table'><thead><tr>" "<th>#</th><th>Fórmula</th><th>Suporte sugerido</th>" "<th>Estabilidade termodinâmica<br>(eV/átomo) ↓</th><th>Pontuação final<br>(0-1) ↑</th>" "<th>Incerteza<br>(desvio MC)</th><th>Rota de síntese</th><th>Confiança</th><th>Composição do score<br>(0-1)</th>" f"</tr></thead><tbody>{tabela_html}</tbody></table></div>" "<aside class='candidate-mcda-panel'><h4>Composição do score (MCDA)</h4>" "<div class='candidate-donut'><span>PESOS<br>(%)</span></div>" "<div class='candidate-mcda-item'><b>Atividade (40%)</b><span>Desempenho catalítico previsto (0-1)</span></div>" "<div class='candidate-mcda-item'><b>Estabilidade (30%)</b><span>Estabilidade termodinâmica (eV/átomo; mais negativa é melhor)</span></div>" "<div class='candidate-mcda-item'><b>Seletividade (20%)</b><span>Seletividade para o produto-alvo (0-1)</span></div>" "<div class='candidate-mcda-item'><b>Estabilidade operacional (10%)</b><span>Consistência diante de variações estruturais e operacionais (0-1)</span></div>" "<p>Score final: soma ponderada normalizada entre 0 e 1.</p></aside></div>" "<div class='candidate-legend'><span>↓ Valores mais negativos indicam maior estabilidade termodinâmica.</span>" "<span>↑ Valores mais altos indicam melhor desempenho global.</span>" "<span><i class='high'></i> Alta &nbsp; <i class='medium'></i> Média &nbsp; <i class='low'></i> Baixa</span></div>", unsafe_allow_html=True)
    mostrar_origem_e_confianca(fontes[0].iloc[0] if fontes and not fontes[0].empty else pd.Series(dtype=object))


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
                "_formula": formatar_formula_quimica(valor_linha(row, ["formula"], valor_linha(row, ["f"], "-"))),
                "_score_final": formatar_numero_linha(row, ["score", "final"], casas=3),
                "_suporte": formatar_formula_quimica(texto_curto(valor_linha(row, ["suporte"], "-"), limite=120)),
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
    figuras_df: pd.DataFrame,
) -> None:
    """Apresenta os gráficos centrais e a ficha de leitura científica dos candidatos."""
    st.markdown(
        """<style>
        .science-page-title{margin:4px 0 2px;color:#14213D;font-size:clamp(1.55rem,2.25vw,2.25rem)!important;font-weight:850;text-align:center}.science-page-subtitle{margin:0 0 16px;color:#64748B;font-size:.88rem!important;text-align:center}.science-card-title{margin:0 0 3px;color:#153A70;font-size:.88rem!important;font-weight:850!important;line-height:1.28!important}.science-card-note{margin:0 0 10px;color:#66758B;font-size:.70rem!important;line-height:1.38}.science-detail{min-height:100%;padding:16px;border-left:4px solid #16843C;border-radius:7px;background:#F8FCF9}.science-detail h3{margin:0 0 13px;color:#14213D;font-size:1.18rem!important}.science-detail-score{float:right;margin-left:10px;padding:7px 9px;border-radius:6px;background:#E4F5E9;color:#087A3B;font-size:.72rem;font-weight:850;text-align:center}.science-detail-score strong{display:block;font-size:1.35rem}.science-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:13px 0}.science-detail-grid span{display:block;color:#64748B;font-size:.68rem}.science-detail-grid b{display:block;margin-top:2px;color:#153A70;font-size:.79rem;overflow-wrap:anywhere}.science-model-image{width:100%;height:245px;object-fit:contain;display:block;mix-blend-mode:multiply}.science-model-note{margin:5px 0 0;color:#66758B;font-size:.69rem;line-height:1.35}.science-restored-title{margin:26px 0 3px;color:#14213D;font-size:1.2rem!important;font-weight:850}.science-restored-subtitle{margin:0 0 13px;color:#66758B;font-size:.8rem!important}.science-figure-card{min-height:100%;padding:10px;border:1px solid #DCE6E0;border-radius:8px;background:#FFF;box-shadow:0 3px 10px rgba(20,33,61,.035)}.science-figure-card h4{margin:5px 0 3px;color:#153A70;font-size:.85rem!important}.science-figure-card p{margin:0;color:#66758B;font-size:.72rem!important;line-height:1.38}.science-figure-card img{border:1px solid #E3ECE6;border-radius:6px}@media(max-width:780px){.science-detail-grid{grid-template-columns:1fr}.science-model-image{height:205px}}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown("<h2 class='science-page-title'>Visualização científica</h2><p class='science-page-subtitle'>Explore as relações entre estabilidade, atividade prevista, descritores e viabilidade de síntese.</p>", unsafe_allow_html=True)

    fontes = [classificacao_df, ranking_df, prioritarios_df, monte_carlo_df]

    def dados_grafico(opcoes_x: list[list[str]], opcoes_y: list[list[str]]) -> tuple[pd.DataFrame, str | None, str | None]:
        fonte = escolher_fonte_plotly(fontes, opcoes_x, opcoes_y)
        if fonte.empty:
            return pd.DataFrame(), None, None
        x_col = encontrar_coluna_por_opcoes(fonte, opcoes_x)
        y_col = encontrar_coluna_por_opcoes(fonte, opcoes_y)
        if x_col is None or y_col is None:
            return pd.DataFrame(), None, None
        dados = preparar_dados_plotly(fonte, limite=350)
        dados[x_col] = pd.to_numeric(dados[x_col], errors="coerce")
        dados[y_col] = pd.to_numeric(dados[y_col], errors="coerce")
        return dados.dropna(subset=[x_col, y_col]).copy(), x_col, y_col

    def aplicar_estilo(figura: go.Figure, altura: int = 360) -> None:
        figura.update_layout(height=altura, margin={"l": 42, "r": 22, "t": 14, "b": 42}, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font={"color": "#14213D", "size": 11}, coloraxis_colorbar={"title": "Score"})
        figura.update_xaxes(showgrid=True, gridcolor="#E7EDF0", zeroline=False, automargin=True)
        figura.update_yaxes(showgrid=True, gridcolor="#E7EDF0", zeroline=False, automargin=True)

    coluna_volcano, coluna_estabilidade, coluna_modelo = st.columns([1, 1, 1])
    dados_volcano, energia_col, taxa_col = dados_grafico(
        [["energia", "adsor"], ["adsorcao"], ["adsorção"]],
        [["score", "vulc"], ["score", "volcano"], ["taxa", "relativa", "volcano"]],
    )
    with coluna_volcano:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Diagrama de vulcão: atividade vs. energia de adsorção</h3><p class='science-card-note'>Avalia o princípio de Sabatier: a atividade tende a ser maior quando a adsorção do intermediário-chave é moderada.</p>", unsafe_allow_html=True)
            if not dados_volcano.empty and energia_col and taxa_col:
                score_col = encontrar_coluna_por_opcoes(dados_volcano, [["score", "final"]])
                cor = score_col if score_col else taxa_col
                figura_volcano = px.scatter(dados_volcano, x=energia_col, y=taxa_col, color=cor, color_continuous_scale="Turbo", custom_data=["_formula", "_suporte", "_score_final", "_rota"])
                x_min, x_max = float(dados_volcano[energia_col].min()), float(dados_volcano[energia_col].max())
                x_otimo = float(dados_volcano.loc[dados_volcano[taxa_col].idxmax(), energia_col])
                largura = max((x_max - x_min) / 3, 0.15)
                x_referencia = np.linspace(x_min - 0.05 * largura, x_max + 0.05 * largura, 140)
                y_referencia = float(dados_volcano[taxa_col].max()) * np.exp(-((x_referencia - x_otimo) / largura) ** 2)
                figura_volcano.add_trace(go.Scatter(x=x_referencia, y=y_referencia, mode="lines", name="Referência de Sabatier", line={"color": "#526071", "dash": "dash", "width": 2}, hoverinfo="skip"))
                figura_volcano.add_vline(x=x_otimo, line_dash="dot", line_color="#16843C")
                figura_volcano.update_traces(selector={"mode": "markers"}, marker={"size": 9, "line": {"color": "#FFFFFF", "width": 0.8}}, hovertemplate="<b>%{customdata[0]}</b><br>Energia de adsorção: %{x:.3f} eV<br>Atividade relativa: %{y:.3f}<br>Score final: %{customdata[2]}<br>Suporte: %{customdata[1]}<br>Rota: %{customdata[3]}<extra></extra>")
                aplicar_estilo(figura_volcano)
                figura_volcano.update_xaxes(title_text="Energia de adsorção (eV)")
                figura_volcano.update_yaxes(title_text="Atividade relativa (proxy)")
                st.plotly_chart(figura_volcano, width="stretch", key="visualizacao_volcano")
            else:
                st.info("Dados de adsorção insuficientes para gerar o diagrama de vulcão.")

    dados_estabilidade, estabilidade_col, score_col = dados_grafico(
        [["estabilidade"]],
        [["score", "final"], ["desejabilidade", "global"]],
    )
    with coluna_estabilidade:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Estabilidade termodinâmica vs. score final</h3><p class='science-card-note'>Mostra o compromisso entre uma fase mais estável e o desempenho global previsto pela triagem.</p>", unsafe_allow_html=True)
            if not dados_estabilidade.empty and estabilidade_col and score_col:
                figura_estabilidade = px.scatter(dados_estabilidade, x=estabilidade_col, y=score_col, color=score_col, color_continuous_scale="Turbo", custom_data=["_formula", "_suporte", "_score_final", "_rota"])
                if len(dados_estabilidade) > 2 and dados_estabilidade[estabilidade_col].nunique() > 1:
                    coef = np.polyfit(dados_estabilidade[estabilidade_col], dados_estabilidade[score_col], 1)
                    x_linha = np.linspace(float(dados_estabilidade[estabilidade_col].min()), float(dados_estabilidade[estabilidade_col].max()), 80)
                    figura_estabilidade.add_trace(go.Scatter(x=x_linha, y=coef[0] * x_linha + coef[1], mode="lines", name="Tendência linear", line={"color": "#66758B", "dash": "dash"}, hoverinfo="skip"))
                figura_estabilidade.add_vline(x=0.10, line_color="#16843C", line_dash="dash", line_width=2, annotation_text="Limiar principal: 0,10 eV/átomo", annotation_position="top left")
                figura_estabilidade.add_vline(x=0.15, line_color="#C53939", line_dash="dot", line_width=2, annotation_text="Limiar exploratório: 0,15 eV/átomo", annotation_position="top right")
                figura_estabilidade.update_traces(selector={"mode": "markers"}, marker={"size": 9, "line": {"color": "#FFFFFF", "width": 0.8}}, hovertemplate="<b>%{customdata[0]}</b><br>Estabilidade: %{x:.3f} eV/átomo<br>Score final: %{y:.3f}<br>Suporte: %{customdata[1]}<br>Rota: %{customdata[3]}<extra></extra>")
                aplicar_estilo(figura_estabilidade)
                figura_estabilidade.update_xaxes(title_text="Estabilidade termodinâmica (eV/átomo; menor é melhor)", range=[min(float(dados_estabilidade[estabilidade_col].min()) - 0.03, -0.01), max(float(dados_estabilidade[estabilidade_col].max()) + 0.03, 0.16)])
                figura_estabilidade.update_yaxes(title_text="Score final (0–1)")
                st.plotly_chart(figura_estabilidade, width="stretch", key="visualizacao_estabilidade")
            else:
                st.info("Dados de estabilidade e score insuficientes para o gráfico.")

    fontes_para_ficha = [dataframe for dataframe in [prioritarios_df, classificacao_df, ranking_df] if not dataframe.empty]
    base_ficha = pd.concat(fontes_para_ficha, ignore_index=True, sort=False) if fontes_para_ficha else pd.DataFrame()
    formula_coluna = encontrar_coluna_por_opcoes(base_ficha, [["formula"], ["fórmula"], ["f"]]) if not base_ficha.empty else None
    if formula_coluna:
        base_ficha = base_ficha.drop_duplicates(subset=[formula_coluna]).copy()
    selecionado = None
    with coluna_modelo:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Modelo estrutural esquemático do catalisador</h3><p class='science-card-note'>Use a ficha para relacionar a composição recomendada aos descritores que sustentam sua priorização.</p>", unsafe_allow_html=True)
            if formula_coluna and not base_ficha.empty:
                opcoes_formula = base_ficha[formula_coluna].astype(str).tolist()
                formula_escolhida = st.selectbox("Candidato em destaque", opcoes_formula, format_func=formatar_formula_quimica, key="visualizacao_candidato")
                selecionado = base_ficha.loc[base_ficha[formula_coluna].astype(str) == formula_escolhida].iloc[0]
                indice_estrutura = sum(ord(caractere) for caractere in formula_escolhida) % len(ESTRUTURAS_CATALITICAS)
                caminho_estrutura = ESTRUTURAS_CATALITICAS[indice_estrutura]
                if caminho_estrutura.exists():
                    st.image(str(caminho_estrutura), width="stretch")
                st.markdown("<p class='science-model-note'>A imagem é uma representação esquemática das fases catalíticas; não substitui uma estrutura relaxada por DFT ou caracterização experimental.</p>", unsafe_allow_html=True)
            else:
                st.info("A ficha estrutural será exibida após a geração dos candidatos.")

    coluna_paralelo = st.container()
    coluna_detalhes = st.container()
    with coluna_paralelo:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Paralelo de descritores catalíticos</h3><p class='science-card-note'>Cada linha representa um candidato. O gráfico ajuda a identificar combinações de descritores associadas a maior pontuação.</p>", unsafe_allow_html=True)
            if not base_ficha.empty:
                base_paralela = preparar_dados_plotly(base_ficha, limite=180)
                configuracoes = [
                    ("Score final", [["score", "final"]]),
                    ("Energia de adsorção (eV)", [["energia", "adsor"]]),
                    ("Score vulcão", [["score", "vulc"], ["score", "volcano"]]),
                    ("Estabilidade (eV/átomo)", [["estabilidade"]]),
                    ("DFT/proxy DFT", [["score", "dft"], ["score", "gnn"]]),
                    ("Resistência ao coque", [["score", "resist", "coque"]]),
                ]
                dimensoes, score_cor = [], None
                for rotulo, opcoes in configuracoes:
                    coluna = encontrar_coluna_por_opcoes(base_paralela, opcoes)
                    if coluna is None:
                        continue
                    valores = pd.to_numeric(base_paralela[coluna], errors="coerce")
                    if valores.notna().sum() < 3 or valores.nunique(dropna=True) < 2:
                        continue
                    dimensoes.append(dict(label=rotulo, values=valores, range=[float(valores.min()), float(valores.max())]))
                    if rotulo == "Score final":
                        score_cor = valores
                if len(dimensoes) >= 3:
                    cor_linhas = score_cor if score_cor is not None else pd.Series(np.arange(len(base_paralela)), index=base_paralela.index)
                    figura_paralela = go.Figure(go.Parcoords(line={"color": cor_linhas, "colorscale": "Turbo", "showscale": True, "colorbar": {"title": "Score"}}, dimensions=dimensoes))
                    figura_paralela.update_layout(height=390, margin={"l": 24, "r": 32, "t": 14, "b": 20}, paper_bgcolor="#FFFFFF", font={"color": "#14213D"})
                    st.plotly_chart(figura_paralela, width="stretch", key="visualizacao_paralela")
                else:
                    st.info("São necessários ao menos três descritores numéricos variáveis para a comparação paralela.")
            else:
                st.info("Descritores ainda não disponíveis.")

    with coluna_detalhes:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Detalhes do candidato selecionado</h3><p class='science-card-note'>Resumo dos valores usados para interpretar a recomendação, sem substituir validação experimental.</p>", unsafe_allow_html=True)
            if selecionado is not None:
                formula = valor_linha(selecionado, ["formula"], valor_linha(selecionado, ["f"], "-"))
                suporte = valor_linha(selecionado, ["suporte"], "Não informado")
                score = formatar_numero_linha(selecionado, ["score", "final"], casas=3)
                detalhes = [
                    ("Suporte sugerido", formatar_formula_quimica(suporte)),
                    ("Energia de adsorção", formatar_numero_linha(selecionado, ["energia", "adsor"], "eV", casas=3)),
                    ("Estabilidade", formatar_numero_linha(selecionado, ["estabilidade"], "eV/átomo", casas=3)),
                    ("Score vulcão", formatar_numero_linha(selecionado, ["score", "volcano"], casas=3)),
                    ("DFT/proxy DFT", formatar_numero_linha(selecionado, ["score", "dft"], casas=3)),
                    ("Condição inicial", montar_condicao_operacional(selecionado)),
                ]
                detalhes_html = "".join(f"<div><span>{html.escape(rotulo)}</span><b>{html.escape(str(valor))}</b></div>" for rotulo, valor in detalhes)
                st.markdown(f"<article class='science-detail'><div class='science-detail-score'>Score final<strong>{html.escape(score)}</strong></div><h3>{html.escape(formatar_formula_quimica(formula))}</h3><div class='science-detail-grid'>{detalhes_html}</div></article>", unsafe_allow_html=True)
            else:
                st.info("Selecione um candidato quando os resultados estiverem disponíveis.")

    coluna_cinetica = st.container()
    coluna_leitura_cinetica = st.container()
    dados_cinetica, taxa_cinetica_col, score_cinetica_col = dados_grafico(
        [["taxa", "relativa", "cinet"], ["score", "cinet"], ["taxa", "relativa", "volcano"], ["score", "volcano"]],
        [["score", "final"], ["rendimento"]],
    )
    with coluna_cinetica:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Cinética simplificada (proxy) vs. score final</h3><p class='science-card-note'>Confronta a taxa relativa estimada pelo modelo simplificado com a pontuação multicritério do candidato.</p>", unsafe_allow_html=True)
            if not dados_cinetica.empty and taxa_cinetica_col and score_cinetica_col:
                cor_cinetica = encontrar_coluna_por_opcoes(dados_cinetica, [["score", "final"]]) or score_cinetica_col
                figura_cinetica = px.scatter(dados_cinetica, x=taxa_cinetica_col, y=score_cinetica_col, color=cor_cinetica, color_continuous_scale="Turbo", custom_data=["_formula", "_suporte", "_score_final", "_rota"])
                figura_cinetica.update_traces(marker={"size": 9, "line": {"color": "#FFFFFF", "width": 0.8}}, hovertemplate="<b>%{customdata[0]}</b><br>Taxa relativa (proxy): %{x:.3f}<br>Score final: %{y:.3f}<br>Suporte: %{customdata[1]}<br>Rota: %{customdata[3]}<extra></extra>")
                aplicar_estilo(figura_cinetica, altura=330)
                figura_cinetica.update_xaxes(title_text="Taxa relativa estimada (proxy)")
                figura_cinetica.update_yaxes(title_text="Score final (0–1)")
                st.plotly_chart(figura_cinetica, width="stretch", key="visualizacao_cinetica")
            else:
                st.info("Dados de taxa relativa insuficientes para o gráfico cinético simplificado.")
    with coluna_leitura_cinetica:
        with st.container(border=True):
            st.markdown("<h3 class='science-card-title'>Como interpretar</h3><p class='science-card-note'>Este gráfico auxilia a verificar se o ganho de atividade proxy acompanha o score final. Ele não calcula mecanismos elementares, coberturas ou barreiras de ativação completas.</p><p class='science-card-note'><b>Objetivo:</b> destacar candidatos com resposta cinética proxy coerente com estabilidade, seletividade e consistência operacional.</p>", unsafe_allow_html=True)

    st.markdown("<p class='science-restored-title'>Gráficos complementares gerados pela execução</p><p class='science-restored-subtitle'>Estas figuras recuperam as análises de ranking, incerteza, operação e quimiometria salvas com a triagem.</p>", unsafe_allow_html=True)
    mostrar_figuras(figuras_df)


def mostrar_figuras(figuras_df: pd.DataFrame) -> None:
    """Renderiza as figuras geradas com uma explicação para sua leitura científica."""
    if figuras_df.empty:
        st.info("Figuras ainda não disponíveis.")
        return

    coluna_png = next((c for c in figuras_df.columns if "PNG" in c.upper()), None)
    if coluna_png is None:
        st.info("A tabela de figuras não contém caminho PNG.")
        return

    explicacoes = {
        "ranking": ("Ranking por pontuação final", "Compara os candidatos segundo o score multicritério usado para priorizar a validação experimental."),
        "estabilidade": ("Estabilidade termodinâmica", "Relaciona a estabilidade prevista à pontuação global para revelar compromissos do ranking."),
        "volcano": ("Diagrama de vulcão", "Avalia a proximidade ao regime de adsorção moderada associado ao princípio de Sabatier."),
        "monte_carlo": ("Estabilidade do ranking por Monte Carlo", "Mostra como perturbações nos descritores afetam a permanência dos candidatos no ranking."),
        "desempenho_faixa": ("Desempenho em faixa de condições", "Examina a variação de desempenho previsto ao redor das condições operacionais de interesse."),
        "sensibilidade": ("Sensibilidade dos descritores", "Indica quais descritores mais influenciam a pontuação calculada."),
        "pca": ("Diversidade quimiométrica", "Projeta os descritores em componentes principais para visualizar a diversidade química dos candidatos."),
        "grupos": ("Grupos quimiométricos", "Agrupa candidatos com perfis de descritores semelhantes."),
        "doe": ("Planejamento experimental", "Mostra combinações de síntese que podem ser avaliadas para explorar o espaço experimental."),
        "correlacao": ("Correlação entre descritores", "Identifica descritores redundantes ou correlacionados que merecem interpretação conjunta."),
        "outliers": ("Diagnóstico de outliers", "Sinaliza candidatos com comportamento incomum no espaço de descritores."),
        "dominio": ("Domínio de aplicabilidade", "Mostra se a previsão está dentro de uma região química representada pelo conjunto de referência."),
        "pareto": ("Pareto e desejabilidade", "Expõe candidatos não dominados quando objetivos de atividade, estabilidade e síntese competem."),
        "validacao": ("Validação e consistência", "Resume a consistência interna do ranking e os indicadores de validação disponíveis."),
        "regressao": ("Regressão quimiométrica", "Compara a resposta do modelo proxy com a tendência de referência usada na avaliação interna."),
    }
    colunas = st.columns(2)
    for indice, (_, row) in enumerate(figuras_df.iterrows()):
        caminho = Path(str(row[coluna_png]))
        if caminho.exists():
            identificador = normalizar_texto(str(row.get("figura", caminho.stem)))
            titulo, explicacao = next((valor for chave, valor in explicacoes.items() if chave in identificador), (caminho.stem.replace("_", " ").capitalize(), "Figura gerada pela execução para apoiar a interpretação do processo de triagem."))
            with colunas[indice % 2]:
                st.markdown("<div class='science-figure-card'>", unsafe_allow_html=True)
                st.image(str(caminho), width="stretch")
                st.markdown(f"<h4>{html.escape(titulo)}</h4><p>{html.escape(explicacao)}</p></div>", unsafe_allow_html=True)


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
            <div class="catialab-institutional-header" style="
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
            html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main { max-width: 100%; overflow-x: hidden !important; }
            [data-testid="stMainBlockContainer"] { width: 100%; max-width: 1480px; min-width: 0; padding-inline: clamp(1rem, 3vw, 3.5rem); }
            [data-testid="stHorizontalBlock"], [data-testid="stColumn"], [data-testid="stVerticalBlock"] { min-width: 0; max-width: 100%; }
            [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], .stImage, svg, canvas { max-width: 100% !important; }
            [data-testid="stPills"] { width: 100%; margin: 6px 0 20px; }
            [data-testid="stPills"] [role="listbox"] { display: flex; flex-wrap: wrap; justify-content: center; gap: 7px 9px; overflow: visible; }
            [data-testid="stPills"] button { min-height: 42px; padding: 8px 13px; border-radius: 7px; font-weight: 800; white-space: normal; text-align: center; }
            .audit-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 4px 0 18px; }
            .audit-item { min-height: 116px; padding: 13px; border: 1px solid #DCE6E0; border-radius: 7px; background: #FFFFFF; }
            .audit-item b, .audit-item strong, .audit-item span { display: block; }
            .audit-item b { color: #14213D; font-size: .80rem; }.audit-item strong { margin: 7px 0 5px; color: #087A3B; font-size: .78rem; }.audit-item span { color: #5D6B7C; font-size: .73rem; line-height: 1.4; }
            .confidence-heading { margin: 4px 0 10px; color: #14213D; }.confidence-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
            .confidence-factor { padding: 12px; border: 1px solid #DCE6E0; border-top: 4px solid #D49A12; border-radius: 7px; background: #FFFFFF; }.confidence-factor.ok { border-top-color: #16843C; background: #F6FCF8; }
            .confidence-factor b, .confidence-factor strong, .confidence-factor span { display: block; }.confidence-factor b { color: #334A69; font-size: .74rem; }.confidence-factor strong { margin: 6px 0; color: #14213D; font-size: 1.05rem; }.confidence-factor span, .confidence-method { color: #5D6B7C; font-size: .72rem; line-height: 1.42; }
            .confidence-method { margin: 12px 0 2px; padding: 11px 13px; border-left: 4px solid #146CC1; background: #F5F9FD; }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #E7F6ED 0%, #F5FBF7 100%);
                border-right: 1px solid #B9DDC7;
            }
            section[data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 270px;
            }
            section[data-testid="stSidebar"][aria-expanded="false"] {
                width: 0 !important;
                min-width: 0 !important;
                border-right: 0 !important;
            }
            div[data-testid="stAppViewContainer"] main,
            div[data-testid="stMain"] {
                width: 100%;
                min-width: 0;
                flex: 1 1 auto;
            }
            div[data-testid="stMainBlockContainer"] {
                width: 100%;
                max-width: 100%;
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
            .catialab-config-preview { margin: -2px 0 12px 0; padding: 0 8px 12px 8px; border-bottom: 1px solid #B9DDC7; color: #173D2B; font-size: 0.86rem; font-weight: 700; line-height: 1.45; text-align: left; }
            .catialab-config-preview .reaction-name { color: #173D2B; font-weight: 800; }
            .catialab-config-preview .reaction-equation { color: #3E5872; font-size: 0.9rem; font-weight: 700; margin-top: 2px; }
            .catialab-metal-chip { display: inline-flex; align-items: center; justify-content: center; min-width: 31px; min-height: 27px; margin: 2px 4px 0 0; padding: 0 8px; border: 1px solid #78B99A; border-radius: 999px; background: rgba(255, 255, 255, 0.72); color: #197A4B; font-size: 0.83rem; font-weight: 850; }
            .catialab-config-status { margin: 11px 0 13px 0; padding: 0; border: 0; background: transparent; color: #173D2B; font-size: 0.86rem; font-weight: 800; line-height: 1.55; text-align: center; }
            .catialab-config-status strong { color: #173D2B; font-weight: 850; }
            .catialab-dashboard-title {
                color: #14213D;
                font-family: Arial, Helvetica, sans-serif;
                font-size: clamp(1.35rem, 2vw, 1.8rem);
                font-weight: 850;
                letter-spacing: 0;
                margin: 0;
                text-align: center;
            }
            .catialab-dashboard-subtitle { color: #64748B; font-size: 0.9rem; margin: 4px 0 18px 0; text-align: center; }
            .candidate-title { margin: 4px 0 3px; color: #14213D; font-size: 1.45rem; font-weight: 850; text-align: center; }
            .candidate-subtitle { margin: 0 0 16px; color: #64748B; font-size: 0.92rem; text-align: center; }
            .candidate-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
            .candidate-metric { display: flex; min-height: 102px; align-items: center; gap: 13px; padding: 14px; border: 1px solid #DCE6EE; border-radius: 8px; background: #FFFFFF; box-shadow: 0 3px 10px rgba(20, 33, 61, 0.04); }
            .candidate-metric b { display: block; color: #14213D; font-size: 0.8rem; } .candidate-metric strong { display: block; color: #087A3B; font-size: 1.55rem; line-height: 1.1; margin-top: 7px; } .candidate-metric span { color: #64748B; font-size: 0.76rem; }
            .candidate-icon { width: 45px; height: 45px; flex: 0 0 45px; border: 3px solid #087A3B; border-radius: 8px; position: relative; }
            .candidate-icon.base::before, .candidate-icon.base::after { content: ''; position: absolute; left: 8px; right: 8px; height: 9px; border: 3px solid #087A3B; border-radius: 50%; } .candidate-icon.base::before { top: 7px; } .candidate-icon.base::after { bottom: 7px; }
            .candidate-icon.shield { clip-path: polygon(50% 0, 92% 16%, 86% 71%, 50% 100%, 14% 71%, 8% 16%); border-radius: 0; } .candidate-icon.target { border-radius: 50%; } .candidate-icon.target::before { content: ''; position: absolute; inset: 9px; border: 3px solid #087A3B; border-radius: 50%; } .candidate-icon.trophy { border-radius: 0 0 14px 14px; border-top-width: 4px; } .candidate-icon.trophy::after { content: ''; position: absolute; width: 18px; height: 3px; background: #087A3B; bottom: -9px; left: 10px; }
            .candidate-podium-section { margin: 34px 0 22px; padding-bottom: 8px; border: 1px solid #DCE6EE; border-radius: 8px; background: #FFFFFF; }
            .candidate-podium { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; align-items: end; padding: 22px 18px 0; border-bottom: 1px solid #DCE6EE; background: linear-gradient(180deg, #F7FCF8, #FFFFFF); }
            .candidate-podium-card { --podium-color: #9AA4B2; position: relative; display: grid; min-height: 260px; grid-template-columns: minmax(120px, 46%) 1fr; grid-template-rows: auto auto auto 1fr; column-gap: 14px; align-items: center; padding: 18px 18px 22px; border: 1px solid color-mix(in srgb, var(--podium-color) 55%, #DCE6EE); border-radius: 10px 10px 0 0; background: #FFFFFF; box-shadow: 0 7px 18px rgba(20, 33, 61, 0.06); }
            .candidate-podium-card::after { content: ''; position: absolute; right: -12px; bottom: -2px; left: -12px; height: 14px; border-radius: 3px 3px 0 0; background: linear-gradient(90deg, color-mix(in srgb, var(--podium-color) 72%, #FFFFFF), var(--podium-color), color-mix(in srgb, var(--podium-color) 72%, #FFFFFF)); }
            .candidate-podium-card.first { --podium-color: #E5A600; min-height: 294px; transform: translateY(-16px); }
            .candidate-podium-card.second { --podium-color: #919AA7; }
            .candidate-podium-card.third { --podium-color: #C46F3C; }
            .candidate-podium-medal { position: absolute; z-index: 2; top: -16px; left: -9px; display: grid; width: 42px; height: 42px; place-items: center; border: 3px solid color-mix(in srgb, var(--podium-color) 70%, #FFFFFF); border-radius: 50%; background: var(--podium-color); color: #FFFFFF; box-shadow: 0 3px 7px rgba(20, 33, 61, 0.16); font-size: 1.18rem; font-weight: 850; }
            .candidate-podium-image { grid-row: 1 / 5; display: grid; min-height: 170px; place-items: center; overflow: hidden; border-radius: 8px; background: #FBFCFD; }
            .candidate-podium-image img { width: 100%; height: 170px; object-fit: contain; mix-blend-mode: multiply; }
            .candidate-podium-card h4 { align-self: end; margin: 0; color: #14213D; font-size: 0.8rem; line-height: 1.25; text-align: left; white-space: nowrap; }
            .candidate-podium-label { align-self: end; margin-top: 9px; color: #718096; font-size: 0.73rem; }
            .candidate-podium-card p { align-self: start; margin: 2px 0 10px; color: #087A3B; font-size: 0.8rem; font-weight: 750; line-height: 1.25; }
            .candidate-podium-score { align-self: end; padding: 8px 10px; border: 1px solid #CFE4D5; border-radius: 7px; background: #F5FBF7; text-align: center; }
            .candidate-podium-score span { display: block; color: #355D47; font-size: 0.7rem; }
            .candidate-podium-score strong { display: block; margin-top: 2px; color: #087A3B; font-size: 1.18rem; }
            .candidate-podium-note { margin: 9px 0 0; color: #64748B; font-size: 0.7rem; line-height: 1.35; text-align: center; }
            .candidate-table-wrap { overflow-x: auto; border: 1px solid #DCE6EE; border-radius: 8px; background: #FFFFFF; } .candidate-table { width: 100%; min-width: 960px; border-collapse: collapse; color: #14213D; font-size: 0.8rem; } .candidate-table th { padding: 12px 9px; border-bottom: 1px solid #DCE6EE; background: #FAFCFD; font-weight: 850; text-align: center; } .candidate-table td { padding: 10px 9px; border-bottom: 1px solid #E7EDF2; text-align: center; vertical-align: middle; } .candidate-table tr:last-child td { border-bottom: 0; } .candidate-table td:nth-child(7) { max-width: 260px; text-align: left; }
            .candidate-results-layout { display: grid; grid-template-columns: minmax(0, 1fr) 250px; gap: 14px; align-items: stretch; }
            .candidate-stability, .candidate-score { color: #2267C6; font-weight: 850; } .candidate-uncertainty { color: #B56400; font-weight: 850; } .candidate-confidence { display: inline-block; min-width: 61px; padding: 3px 8px; border: 1px solid currentColor; border-radius: 999px; font-weight: 850; } .candidate-confidence.high { color: #087A3B; background: #F1FBF4; } .candidate-confidence.medium { color: #B56400; background: #FFF9EC; } .candidate-confidence.low { color: #C53939; background: #FFF5F5; }
            .candidate-score-stack { display: grid; grid-template-columns: repeat(4, 1fr); min-width: 170px; overflow: hidden; border: 1px solid #B6D2F0; border-radius: 4px; } .candidate-score-stack span { padding: 3px 2px; border-right: 1px solid #FFFFFF; background: #D6E9FB; color: #173D2B; font-size: 0.69rem; font-weight: 850; } .candidate-score-stack span:nth-child(1) { background: #0D5EBA; color: #FFFFFF; } .candidate-score-stack span:nth-child(2) { background: #3E85CF; color: #FFFFFF; } .candidate-score-stack span:nth-child(3) { background: #77ADE2; color: #FFFFFF; } .candidate-score-stack span:nth-child(4) { border-right: 0; }
            .candidate-legend { display: flex; justify-content: space-between; gap: 10px; padding: 12px 5px 0; color: #64748B; font-size: 0.72rem; } .candidate-legend i { display: inline-block; width: 10px; height: 10px; margin-right: 3px; border: 2px solid currentColor; border-radius: 50%; vertical-align: -1px; } .candidate-legend .high { color: #087A3B; } .candidate-legend .medium { color: #B56400; } .candidate-legend .low { color: #C53939; }
            .candidate-mcda-panel { height: 100%; box-sizing: border-box; padding: 14px; border: 1px solid #DCE6EE; border-radius: 8px; background: #FFFFFF; color: #14213D; } .candidate-mcda-panel h4 { margin: 0 0 9px; color: #087A3B; font-size: 0.9rem; text-align: center; } .candidate-donut { display: grid; width: 126px; height: 126px; margin: 0 auto 12px; place-items: center; border-radius: 50%; background: conic-gradient(#0D5EBA 0 40%, #3E85CF 40% 70%, #77ADE2 70% 90%, #BCD9F5 90%); } .candidate-donut::before { content: ''; grid-area: 1 / 1; width: 63px; height: 63px; border-radius: 50%; background: #FFFFFF; } .candidate-donut span { z-index: 1; grid-area: 1 / 1; color: #14213D; font-size: 0.72rem; font-weight: 850; line-height: 1.25; text-align: center; } .candidate-mcda-item { margin-top: 9px; padding-left: 10px; border-left: 5px solid #0D5EBA; } .candidate-mcda-item:nth-of-type(3) { border-color: #3E85CF; } .candidate-mcda-item:nth-of-type(4) { border-color: #77ADE2; } .candidate-mcda-item:nth-of-type(5) { border-color: #BCD9F5; } .candidate-mcda-item b { display: block; font-size: 0.76rem; } .candidate-mcda-item span { display: block; margin-top: 2px; color: #4A5B73; font-size: 0.69rem; line-height: 1.28; } .candidate-mcda-panel p { margin: 12px 0 0; padding: 8px; border-radius: 6px; background: #FFF8E9; color: #6D5516; font-size: 0.7rem; line-height: 1.35; }
            @media (max-width: 1080px) { .candidate-results-layout { grid-template-columns: 1fr; } .candidate-mcda-panel { max-width: none; } } @media (max-width: 900px) { .candidate-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .candidate-podium { grid-template-columns: 1fr; gap: 26px; } .candidate-podium-card, .candidate-podium-card.first { min-height: 240px; transform: none; } .candidate-podium-card.first { order: -1; } .candidate-legend { display: grid; } } @media (max-width: 560px) { .candidate-podium-card { grid-template-columns: 1fr; text-align: center; } .candidate-podium-image { grid-row: auto; min-height: 145px; } .candidate-podium-image img { height: 145px; } .candidate-podium-card h4, .candidate-podium-label { text-align: center; } }
            .uncertainty-title { margin: 6px 0 12px; color: #14213D; font-size: 1rem; font-weight: 850; text-transform: uppercase; } .uncertainty-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:16px; } .uncertainty-metric { min-height:98px; padding:14px; border:1px solid #DCE6EE; border-radius:8px; background:#FFF; box-shadow:0 3px 10px rgba(20,33,61,.04); } .uncertainty-metric b{display:block;color:#14213D;font-size:.78rem}.uncertainty-metric strong{display:block;margin:9px 0 3px;color:#146CC1;font-size:1.45rem}.uncertainty-metric span{color:#64748B;font-size:.74rem}.uncertainty-alert{min-height:130px;padding:18px;border:1px solid #F2CD72;border-radius:8px;background:#FFF9EA;color:#5F4A11}.uncertainty-alert h4{margin:0 0 9px;color:#4E3A00;font-size:1rem;text-transform:uppercase}.uncertainty-alert strong{color:#B84B16}.uncertainty-alert p,.uncertainty-note p{font-size:.82rem;line-height:1.45}.uncertainty-note{margin-top:12px;padding:18px;border:1px solid #C9DFD0;border-radius:8px;background:#F7FCF8;color:#253D50}.uncertainty-note h4{margin:0;color:#087A3B;font-size:1rem}@media(max-width:900px){.uncertainty-metrics{grid-template-columns:repeat(2,minmax(0,1fr)}}
            .candidate-results-layout { grid-template-columns: 1fr !important; min-width:0; }
            .candidate-table-wrap { width:100%; max-width:100%; }
            .candidate-table { min-width:820px !important; table-layout:fixed; font-size:.74rem !important; }
            .candidate-table th,.candidate-table td { padding-inline:6px !important; overflow-wrap:anywhere; }
            .candidate-mcda-panel { display:grid; grid-template-columns:150px repeat(4,minmax(0,1fr)); gap:12px; align-items:center; }
            .candidate-mcda-panel h4 { grid-column:1/-1; }.candidate-mcda-panel .candidate-donut { grid-row:2/4; margin:auto; }.candidate-mcda-panel p { grid-column:2/-1; }
            .catialab-summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 14px 0 20px 0; }
            .catialab-summary-card { min-height: 132px; padding: 17px 18px 14px 18px; border: 1px solid #DCE6EE; border-radius: 9px; background: #FFFFFF; box-shadow: 0 5px 16px rgba(20, 33, 61, 0.06); }
            .catialab-summary-label { color: #14213D; font-size: 0.82rem; font-weight: 800; }
            .catialab-summary-value { color: #218C3A; font-size: 1.9rem; font-weight: 900; line-height: 1.1; margin-top: 13px; }
            .catialab-summary-value.blue { color: #146CC1; }
            .catialab-summary-note { color: #64748B; font-size: 0.75rem; margin-top: 5px; }
            .catialab-summary-accent { color: #218C3A; font-size: 0.78rem; font-weight: 750; margin-top: 10px; }
            @media (max-width: 860px) {
                .catialab-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                .candidate-mcda-panel,.audit-grid,.confidence-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
                .candidate-mcda-panel .candidate-donut { grid-row:auto; }.candidate-mcda-panel p { grid-column:1/-1; }
            }
            @media (max-width: 560px) { [data-testid="stMainBlockContainer"]{padding-inline:.75rem}.candidate-mcda-panel,.audit-grid,.confidence-grid{grid-template-columns:1fr} }
            .catialab-institutional-header { max-width:100%; box-sizing:border-box; }
            @media(max-width:1100px){.catialab-institutional-header{grid-template-columns:minmax(160px,1fr) minmax(230px,1.25fr) minmax(160px,1fr)!important;column-gap:8px!important}.catialab-institutional-header>div{transform:none!important}.catialab-institutional-header img{max-width:100%!important}}
            @media(max-width:700px){.catialab-institutional-header{grid-template-columns:1fr!important;row-gap:12px}.catialab-institutional-header>div:nth-child(1),.catialab-institutional-header>div:nth-child(3){display:none!important}}
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
            button[data-baseweb="tab"],
            div[data-testid="stTab"] {
                min-height: 46px;
                padding: 0 17px;
                font-weight: 750;
                color: #263B58;
                font-size: 0.88rem;
                letter-spacing: 0;
            }
            div[data-baseweb="tab-list"],
            div[role="tablist"] {
                gap: 18px;
                border-bottom: 1px solid var(--catialab-line);
            }
            button[data-baseweb="tab"][aria-selected="true"],
            div[data-testid="stTab"][aria-selected="true"] {
                color: #146CC1 !important;
                font-weight: 850 !important;
                border-bottom: 3px solid #146CC1 !important;
            }
            div[data-testid="stTab"][aria-selected="true"] p {
                color: #146CC1 !important;
            }
            div[data-testid="stTab"][aria-selected="true"] .react-aria-SelectionIndicator {
                background: #146CC1 !important;
            }
            button[data-baseweb="tab"]:hover,
            div[data-testid="stTab"]:hover {
                color: #146CC1;
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
                div[data-baseweb="tab-list"],
                div[role="tablist"] {
                    overflow-x: auto;
                    justify-content: flex-start;
                    gap: 6px;
                }
                button[data-baseweb="tab"],
                div[data-testid="stTab"] { padding: 0 12px; font-size: 0.82rem; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_titulo_dashboard() -> None:
    """Apresenta o titulo executivo da tela principal conforme o painel de referencia."""
    st.markdown(
        f"<div class='catialab-dashboard-title'>{html.escape(t('Principais recomendações'))}</div>"
        f"<div class='catialab-dashboard-subtitle'>{html.escape(t('Triagem virtual orientada por IA para sua reação.'))}</div>",
        unsafe_allow_html=True,
    )


MASSAS_ATOMICAS_G_MOL = {"Al": 26.982, "Ce": 140.116, "Co": 58.933, "Cu": 63.546, "Fe": 55.845, "La": 138.905, "Mg": 24.305, "Mo": 95.950, "Ni": 58.693, "Pd": 106.420, "Pt": 195.084, "Rh": 102.906, "Ru": 101.070, "Ti": 47.867, "W": 183.840, "Y": 88.906, "Zn": 65.380, "Zr": 91.224}


# Reúne precursores de composição definida para converter carga metálica em massa de sal.
PRECURSORES_PADRAO = {
    "Al": {"nome": "Nitrato de alumínio nonahidratado", "formula": "Al(NO3)3·9H2O", "massa_molar": 375.13, "atomos_metal": 1},
    "Ce": {"nome": "Nitrato de cério(III) hexahidratado", "formula": "Ce(NO3)3·6H2O", "massa_molar": 434.22, "atomos_metal": 1},
    "Co": {"nome": "Nitrato de cobalto(II) hexahidratado", "formula": "Co(NO3)2·6H2O", "massa_molar": 291.03, "atomos_metal": 1},
    "Cu": {"nome": "Nitrato de cobre(II) trihidratado", "formula": "Cu(NO3)2·3H2O", "massa_molar": 241.60, "atomos_metal": 1},
    "Fe": {"nome": "Nitrato de ferro(III) nonahidratado", "formula": "Fe(NO3)3·9H2O", "massa_molar": 404.00, "atomos_metal": 1},
    "La": {"nome": "Nitrato de lantânio(III) hexahidratado", "formula": "La(NO3)3·6H2O", "massa_molar": 433.01, "atomos_metal": 1},
    "Mg": {"nome": "Nitrato de magnésio hexahidratado", "formula": "Mg(NO3)2·6H2O", "massa_molar": 256.41, "atomos_metal": 1},
    "Mo": {"nome": "Heptamolibdato de amônio tetrahidratado", "formula": "(NH4)6Mo7O24·4H2O", "massa_molar": 1235.86, "atomos_metal": 7},
    "Ni": {"nome": "Nitrato de níquel(II) hexahidratado", "formula": "Ni(NO3)2·6H2O", "massa_molar": 290.79, "atomos_metal": 1},
    "Y": {"nome": "Nitrato de ítrio(III) hexahidratado", "formula": "Y(NO3)3·6H2O", "massa_molar": 383.01, "atomos_metal": 1},
    "Zn": {"nome": "Nitrato de zinco hexahidratado", "formula": "Zn(NO3)2·6H2O", "massa_molar": 297.49, "atomos_metal": 1},
}


def composicao_metalica_formula(formula: str, metais_preferidos: list[str]) -> list[tuple[str, float]]:
    """Extrai a razão atômica dos metais da fórmula do candidato sem interpretar o suporte."""
    formula_ascii = str(formula).translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    formula_ativa = re.split(r"\s*/\s*|\s+ou\s+", formula_ascii, maxsplit=1, flags=re.IGNORECASE)[0]
    componentes = [(elemento, float(indice or 1.0)) for elemento, indice in re.findall(r"([A-Z][a-z]?)([0-9]*\.?[0-9]*)", formula_ativa)]
    selecionados = [(elemento, indice) for elemento, indice in componentes if elemento in metais_preferidos and elemento in MASSAS_ATOMICAS_G_MOL]
    if selecionados:
        return selecionados
    return [(elemento, indice) for elemento, indice in componentes if elemento in MASSAS_ATOMICAS_G_MOL and elemento != "O"]


def procedimento_sintese_html(rota: str, temperatura_secagem: float, temperatura_calcinacao: float) -> str:
    """Monta um protocolo orientativo específico para a rota escolhida."""
    protocolos = {
        "Impregnação por umidade incipiente": [
            "Determinar experimentalmente o volume de poros do suporte seco.",
            "Dissolver os precursores no volume calculado, verificando solubilidade e compatibilidade.",
            "Adicionar a solução gradualmente ao suporte sob mistura uniforme, sem formar líquido livre.",
            "Envelhecer o sólido úmido, secar com rampa moderada e evitar migração macroscópica dos sais.",
            "Calcinar com atmosfera e rampa compatíveis com a decomposição dos precursores.",
            "Ativar ou reduzir somente após confirmar a fase formada por DRX, TGA/DSC ou técnica equivalente.",
        ],
        "Impregnação úmida": [
            "Dissolver os precursores em excesso controlado de solvente.",
            "Adicionar o suporte e manter agitação e temperatura compatíveis com a estabilidade da solução.",
            "Remover o solvente lentamente para limitar redistribuição e cristalização externa do precursor.",
            "Secar até massa constante, calcinar e ativar conforme a química dos precursores.",
            "Confirmar teor metálico e homogeneidade por ICP-OES, XRF ou método analítico apropriado.",
        ],
        "Coprecipitação": [
            "Preparar soluções dos sais nas razões molares calculadas.",
            "Adicionar o precipitante com controle contínuo de pH, temperatura e taxa de adição.",
            "Envelhecer o precipitado pelo tempo definido para estabilizar composição e textura.",
            "Filtrar e lavar até remover nitratos, cloretos e álcalis residuais.",
            "Secar com controle de retração, calcinar e reduzir conforme a fase ativa desejada.",
        ],
        "Sol-gel": [
            "Preparar a solução dos precursores e definir água, solvente, complexante e catalisador ácido ou básico.",
            "Controlar hidrólise, condensação, pH e sequência de adição para evitar segregação.",
            "Envelhecer o gel e realizar troca de solvente quando necessária.",
            "Secar lentamente para reduzir tensão capilar, retração e formação de trincas.",
            "Calcinar com rampa compatível com a remoção dos orgânicos e estabilização da porosidade.",
        ],
    }
    etapas = protocolos.get(rota, protocolos["Impregnação úmida"])
    itens = "".join(f"<li><b>{indice}.</b> {html.escape(etapa)}</li>" for indice, etapa in enumerate(etapas, 1))
    return (
        f"<div class='synthesis-procedure'><h3>{html.escape(rota)}</h3><ol>{itens}</ol>"
        f"<p><b>Parâmetros iniciais:</b> secagem a {temperatura_secagem:.0f} °C e calcinação a "
        f"{temperatura_calcinacao:.0f} °C. Estes valores devem ser confirmados por TGA/DSC e literatura do precursor.</p></div>"
    )


def mostrar_planejamento_sintese(
    prioritarios_df: pd.DataFrame,
    metais_configurados: list[str],
    promotor_configurado: str,
) -> None:
    """Calcula uma receita nominal por precursor e oferece uma calculadora estequiométrica livre."""
    st.markdown(
        "<div class='synthesis-title'>Instruções e cálculo para síntese</div>"
        "<div class='synthesis-subtitle'>Balanço nominal entre fase final, precursores, suporte e solução de preparação.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<style>
        .synthesis-title{margin:8px 0 4px;color:#14213D;font-size:1.75rem;font-weight:850;text-align:center}
        .synthesis-subtitle{margin-bottom:18px;color:#5C6B80;font-size:.96rem;text-align:center}
        .synthesis-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:14px 0}
        .synthesis-kpi{padding:15px;border:1px solid #D8E5DE;border-radius:8px;background:#FFF;text-align:center}
        .synthesis-kpi b{display:block;color:#52637A;font-size:.8rem}.synthesis-kpi strong{display:block;margin-top:8px;color:#087A3B;font-size:1.3rem}
        .synthesis-procedure{margin:14px 0;padding:17px 20px;border:1px solid #CFE1D5;border-radius:8px;background:#F8FCF9;color:#263B58}
        .synthesis-procedure h3{margin:0 0 10px;color:#087A3B;font-size:1.05rem}.synthesis-procedure ol{margin:0;padding-left:0;list-style:none}
        .synthesis-procedure li{margin:7px 0;font-size:.9rem;line-height:1.45}.synthesis-procedure p{margin:12px 0 0;padding-top:10px;border-top:1px solid #DCE8E0;font-size:.86rem;line-height:1.45}
        .synthesis-warning{margin:14px 0;padding:12px 14px;border-left:4px solid #E5A600;background:#FFF9E9;color:#655016;font-size:.88rem;line-height:1.45}
        @media(max-width:900px){.synthesis-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        </style>""",
        unsafe_allow_html=True,
    )

    if prioritarios_df.empty:
        st.info("Execute a triagem para gerar a receita vinculada ao candidato. A calculadora livre permanece disponível abaixo.")
    else:
        coluna_formula = encontrar_coluna(prioritarios_df, ["formula"]) or prioritarios_df.columns[0]
        coluna_suporte = encontrar_coluna(prioritarios_df, ["suporte"])
        formulas = prioritarios_df[coluna_formula].astype(str).head(10).tolist()
        formula = st.selectbox("Candidato para a receita", formulas, key="sintese_candidato")
        linha = prioritarios_df[prioritarios_df[coluna_formula].astype(str) == formula].iloc[0]
        suporte_bruto = str(linha.get(coluna_suporte, "Al2O3")) if coluna_suporte else "Al2O3"
        suporte = re.split(r"\s+ou\s+|\s*/\s*", suporte_bruto, maxsplit=1, flags=re.IGNORECASE)[0]

        c1, c2, c3, c4 = st.columns(4)
        massa_final = c1.number_input("Massa final desejada (g)", min_value=0.1, value=100.0, step=10.0, key="sintese_massa_final")
        carga_ativa = c2.number_input("Fase ativa (% m/m)", min_value=0.0, max_value=100.0, value=15.0, step=0.5, key="sintese_carga_ativa")
        carga_promotor = c3.number_input("Promotor (% m/m)", min_value=0.0, max_value=50.0, value=5.0 if promotor_configurado else 0.0, step=0.5, key="sintese_carga_promotor")
        rota = c4.selectbox("Procedimento de síntese", ["Impregnação por umidade incipiente", "Impregnação úmida", "Coprecipitação", "Sol-gel"], key="sintese_rota")

        d1, d2, d3, d4 = st.columns(4)
        pureza = d1.number_input("Pureza dos precursores (%)", min_value=1.0, max_value=100.0, value=100.0, step=0.1, key="sintese_pureza")
        recuperacao = d2.number_input("Recuperação global estimada (%)", min_value=1.0, max_value=100.0, value=100.0, step=0.5, key="sintese_recuperacao")
        volume_poroso = d3.number_input("Volume de poros (cm³/g)", min_value=0.0, value=0.80, step=0.05, key="sintese_volume_poroso")
        preenchimento = d4.number_input("Preenchimento dos poros (%)", min_value=1.0, max_value=150.0, value=90.0, step=5.0, key="sintese_preenchimento")

        e1, e2 = st.columns(2)
        temperatura_secagem = e1.number_input("Temperatura de secagem (°C)", min_value=20.0, max_value=300.0, value=100.0, step=5.0, key="sintese_secagem")
        temperatura_calcinacao = e2.number_input("Temperatura de calcinação (°C)", min_value=100.0, max_value=1200.0, value=500.0, step=25.0, key="sintese_calcinacao")

        if carga_ativa + carga_promotor >= 100.0:
            st.error("A soma da fase ativa e do promotor deve ser menor que 100%.")
        else:
            massa_ativa = massa_final * carga_ativa / 100.0
            massa_promotor = massa_final * carga_promotor / 100.0
            massa_suporte = massa_final - massa_ativa - massa_promotor
            componentes = composicao_metalica_formula(formula, metais_configurados)
            denominador = sum(MASSAS_ATOMICAS_G_MOL[elemento] * indice for elemento, indice in componentes)
            linhas = []
            mols_precursores = 0.0
            for elemento, indice in componentes:
                fracao_massica = MASSAS_ATOMICAS_G_MOL[elemento] * indice / denominador if denominador else 0.0
                massa_elemento = massa_ativa * fracao_massica
                precursor = PRECURSORES_PADRAO.get(elemento)
                if precursor:
                    massa_pura = massa_elemento * precursor["massa_molar"] / (precursor["atomos_metal"] * MASSAS_ATOMICAS_G_MOL[elemento])
                    massa_pesar = massa_pura / (pureza / 100.0) / (recuperacao / 100.0)
                    mols_precursores += massa_pura / precursor["massa_molar"]
                    nome_precursor = f'{precursor["nome"]} ({formatar_formula_quimica(precursor["formula"])})'
                else:
                    massa_pura = np.nan
                    massa_pesar = np.nan
                    nome_precursor = "Definir precursor e massa molar na calculadora livre"
                linhas.append({"Função": "Fase ativa", "Elemento/fase": elemento, "Precursor": nome_precursor, "Massa final alvo (g)": massa_elemento, "Massa de precursor puro (g)": massa_pura, "Massa corrigida a pesar (g)": massa_pesar})
            if promotor_configurado and carga_promotor > 0:
                precursor = PRECURSORES_PADRAO.get(promotor_configurado)
                if precursor and promotor_configurado in MASSAS_ATOMICAS_G_MOL:
                    massa_pura = massa_promotor * precursor["massa_molar"] / (precursor["atomos_metal"] * MASSAS_ATOMICAS_G_MOL[promotor_configurado])
                    massa_pesar = massa_pura / (pureza / 100.0) / (recuperacao / 100.0)
                    mols_precursores += massa_pura / precursor["massa_molar"]
                    nome_precursor = f'{precursor["nome"]} ({formatar_formula_quimica(precursor["formula"])})'
                else:
                    massa_pura = np.nan
                    massa_pesar = np.nan
                    nome_precursor = "Definir precursor e massa molar na calculadora livre"
                linhas.append({"Função": "Promotor", "Elemento/fase": promotor_configurado, "Precursor": nome_precursor, "Massa final alvo (g)": massa_promotor, "Massa de precursor puro (g)": massa_pura, "Massa corrigida a pesar (g)": massa_pesar})
            linhas.append({"Função": "Suporte", "Elemento/fase": suporte, "Precursor": f"{formatar_formula_quimica(suporte)} fornecido na forma final", "Massa final alvo (g)": massa_suporte, "Massa de precursor puro (g)": massa_suporte, "Massa corrigida a pesar (g)": massa_suporte / (recuperacao / 100.0)})
            receita_df = pd.DataFrame(linhas)
            colunas_numericas = receita_df.select_dtypes(include=[np.number]).columns
            receita_df[colunas_numericas] = receita_df[colunas_numericas].round(3)

            # Calcula o solvente pelo volume de poros somente nas rotas de impregnação.
            if rota == "Impregnação por umidade incipiente":
                volume_solucao = massa_suporte * volume_poroso * preenchimento / 100.0
            elif rota == "Impregnação úmida":
                volume_solucao = massa_suporte * volume_poroso * max(2.0, preenchimento / 100.0)
            else:
                volume_solucao = np.nan
            molaridade_aproximada = mols_precursores / (volume_solucao / 1000.0) if np.isfinite(volume_solucao) and volume_solucao > 0 else np.nan
            volume_exibicao = f"{volume_solucao:.2f} mL" if np.isfinite(volume_solucao) else "Definir por concentração"
            st.markdown(
                f"<div class='synthesis-grid'><div class='synthesis-kpi'><b>Catalisador final</b><strong>{massa_final:.2f} g</strong></div>"
                f"<div class='synthesis-kpi'><b>Fase ativa</b><strong>{massa_ativa:.2f} g</strong></div>"
                f"<div class='synthesis-kpi'><b>Suporte final</b><strong>{massa_suporte:.2f} g</strong></div>"
                f"<div class='synthesis-kpi'><b>Volume inicial de solução</b><strong>{volume_exibicao}</strong></div></div>",
                unsafe_allow_html=True,
            )
            st.dataframe(receita_df, width="stretch", hide_index=True)
            if np.isfinite(molaridade_aproximada):
                st.caption(f"Concentração metálica total aproximada da solução: {molaridade_aproximada:.3f} mol/L. Verifique solubilidade individual, pH e volume real dos sais.")
            else:
                st.caption("Na coprecipitação e no sol-gel, defina o volume a partir da concentração dos precursores, do pH, do complexante e da cinética de adição; o volume de poros não determina essa quantidade.")
            st.html(procedimento_sintese_html(rota, temperatura_secagem, temperatura_calcinacao))
            st.markdown(
                "<div class='synthesis-warning'><b>Base do cálculo:</b> as cargas da fase ativa e do promotor são tratadas como equivalentes metálicos. "
                "O suporte é considerado já disponível na fase final. Caso seja preparado a partir de boehmita, hidróxido, carbonato ou gel, use a calculadora abaixo "
                "com a massa molar da fase final ou o fator de resíduo obtido por TGA. A receita é nominal e deve ser confirmada por análise química e balanço após calcinação.</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Calculadora estequiométrica livre")
    st.caption("Informe cada fase final e o respectivo precursor. A razão estequiométrica representa mol de precursor necessário por mol da fase final.")
    numero_reagentes = st.number_input("Número de reagentes ou componentes", min_value=1, max_value=6, value=3, step=1, key="calc_numero_reagentes")
    massa_lote = st.number_input("Massa final do lote (g)", min_value=0.01, value=100.0, step=10.0, key="calc_massa_lote")
    with st.form("form_calculadora_sintese"):
        entradas = []
        for indice in range(int(numero_reagentes)):
            st.markdown(f"**Componente {indice + 1}**")
            col1, col2, col3 = st.columns(3)
            nome = col1.text_input("Nome do reagente/precursor", value="", key=f"calc_nome_{indice}")
            fracao = col2.number_input("Fase final (% m/m)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key=f"calc_fracao_{indice}")
            massa_molar_precursor = col3.number_input("Massa molar do precursor (g/mol)", min_value=0.0, value=0.0, step=1.0, key=f"calc_mm_prec_{indice}")
            col4, col5, col6 = st.columns(3)
            massa_molar_final = col4.number_input("Massa molar da fase final (g/mol)", min_value=0.0, value=0.0, step=1.0, key=f"calc_mm_final_{indice}")
            razao = col5.number_input("mol precursor/mol fase final", min_value=0.0, value=1.0, step=0.1, key=f"calc_razao_{indice}")
            pureza_item = col6.number_input("Pureza do reagente (%)", min_value=0.1, max_value=100.0, value=100.0, step=0.1, key=f"calc_pureza_{indice}")
            recuperacao_item = st.number_input("Recuperação prevista do componente (%)", min_value=0.1, max_value=100.0, value=100.0, step=0.5, key=f"calc_recuperacao_{indice}")
            entradas.append((nome, fracao, massa_molar_precursor, massa_molar_final, razao, pureza_item, recuperacao_item))
        calcular = st.form_submit_button("Calcular quantidades", type="primary", width="stretch")

    if calcular:
        soma_fracoes = sum(item[1] for item in entradas)
        if soma_fracoes > 100.0 + 1e-9:
            st.error("A soma das porcentagens das fases finais ultrapassa 100%.")
        else:
            resultados = []
            for nome, fracao, mm_precursor, mm_final, razao, pureza_item, recuperacao_item in entradas:
                massa_fase = massa_lote * fracao / 100.0
                if mm_precursor <= 0 or mm_final <= 0:
                    massa_pura = np.nan
                    massa_corrigida = np.nan
                else:
                    mols_fase = massa_fase / mm_final
                    massa_pura = mols_fase * razao * mm_precursor
                    massa_corrigida = massa_pura / (pureza_item / 100.0) / (recuperacao_item / 100.0)
                resultados.append({"Reagente/precursor": nome or "Não informado", "Fase final (% m/m)": fracao, "Massa da fase final (g)": massa_fase, "Massa pura do precursor (g)": massa_pura, "Massa corrigida a pesar (g)": massa_corrigida})
            if soma_fracoes < 100.0:
                resultados.append({"Reagente/precursor": "Componente restante/suporte", "Fase final (% m/m)": 100.0 - soma_fracoes, "Massa da fase final (g)": massa_lote * (100.0 - soma_fracoes) / 100.0, "Massa pura do precursor (g)": np.nan, "Massa corrigida a pesar (g)": np.nan})
            resultado_df = pd.DataFrame(resultados)
            numericas = resultado_df.select_dtypes(include=[np.number]).columns
            resultado_df[numericas] = resultado_df[numericas].round(4)
            st.dataframe(resultado_df, width="stretch", hide_index=True)
            st.info("Use a massa corrigida somente quando pureza, estequiometria e recuperação forem sustentadas por certificado, TGA ou validação experimental.")



def mostrar_recomendacoes_sintese(prioritarios_df: pd.DataFrame) -> None:
    """Apresenta os dois candidatos prioritários com os dados de síntese essenciais."""
    if prioritarios_df.empty:
        st.info("Execute a triagem para gerar recomendações de síntese.")
        return

    def texto(row: pd.Series, opcoes: list[list[str]], padrao: str = "Não informado") -> str:
        coluna = encontrar_coluna_por_opcoes(pd.DataFrame(columns=row.index), opcoes)
        valor = row.get(coluna, padrao) if coluna else padrao
        return padrao if valor is None or pd.isna(valor) or str(valor).strip() == "" else str(valor)

    def numero(row: pd.Series, opcoes: list[list[str]]) -> float | None:
        coluna = encontrar_coluna_por_opcoes(pd.DataFrame(columns=row.index), opcoes)
        valor = pd.to_numeric(pd.Series([row.get(coluna)]), errors="coerce").iloc[0] if coluna else np.nan
        return None if pd.isna(valor) else float(valor)

    def massas_formula(formula: str, massa_ativa: float) -> str:
        formula = str(formula).translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
        partes = [(e, float(q or 1)) for e, q in re.findall(r"([A-Z][a-z]?)([0-9]*\.?[0-9]*)", formula) if e in MASSAS_ATOMICAS_G_MOL]
        massa_molar = sum(MASSAS_ATOMICAS_G_MOL[e] * q for e, q in partes)
        if not massa_molar:
            return "Não foi possível converter a fórmula automaticamente."
        return " · ".join(f"{e}: {massa_ativa * MASSAS_ATOMICAS_G_MOL[e] * q / massa_molar:.2f} g" for e, q in partes)

    st.markdown("""<style>
    .rec-grade{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:16px 0 26px}.rec-card{border:1px solid #CBD9D3;border-left:4px solid var(--rec);border-radius:9px;overflow:hidden;background:#fff;box-shadow:0 5px 16px rgba(20,33,61,.06)}.rec-head{display:flex;align-items:center;gap:12px;padding:17px 21px 12px}.rec-rank{display:grid;place-items:center;width:35px;height:35px;border-radius:50%;background:var(--rec);color:#fff;font-weight:800}.rec-name{color:#112446;font-size:1.15rem;font-weight:850}.rec-dot{width:16px;height:16px;margin-left:auto;border-radius:50%;background:var(--rec)}.rec-main{display:grid;grid-template-columns:1fr .88fr;gap:13px;padding:0 21px 15px}.rec-formula{display:grid;place-items:center;min-height:90px;padding:10px;background:#F1F9F4;color:var(--rec);border-radius:7px;font-family:Georgia,serif;font-size:1.55rem;font-weight:800;text-align:center;word-break:break-word}.rec-score{padding:14px;border:1px solid #DFE8E4;border-radius:7px}.rec-score span,.rec-score small{color:#4A5B73;font-size:.77rem}.rec-score strong{display:block;margin:7px 0;color:var(--rec);font-size:1.65rem}.rec-bar{height:7px;margin-top:7px;background:#E5ECE8;border-radius:8px;overflow:hidden}.rec-bar i{display:block;height:100%;width:var(--conf);background:var(--rec);border-radius:8px}.rec-list{margin:0 21px 20px;border:1px solid #E1E9E5;border-radius:7px;overflow:hidden}.rec-item{display:grid;grid-template-columns:145px 1fr;gap:10px;padding:10px 12px;border-bottom:1px solid #E5ECE8;color:#35465E;font-size:.83rem;line-height:1.38}.rec-item:last-child{border-bottom:0}.rec-item b{color:#163259}.rec-batch{padding:11px 12px;background:#F7FBF8;color:#2B405B;font-size:.8rem;line-height:1.42}.rec-note{margin:0 21px 20px;padding:10px 12px;background:#FFF8E9;border-radius:6px;color:#6D5516;font-size:.78rem;line-height:1.38;text-align:justify}@media(max-width:900px){.rec-grade{grid-template-columns:1fr}}@media(max-width:520px){.rec-main,.rec-item{grid-template-columns:1fr;gap:4px}}</style>""", unsafe_allow_html=True)
    st.markdown("""<style>
    .rec-card:nth-child(1){--metal-a:#0EA5A8;--metal-b:#8B5CF6;--promoter:#F59E0B}.rec-card:nth-child(2){--metal-a:#2563EB;--metal-b:#06B6D4;--promoter:#FACC15}
    .rec-name{font-size:.94rem;line-height:1.25}.rec-main{grid-template-columns:1.25fr .88fr;align-items:stretch}.rec-formula{position:relative;display:flex;align-items:flex-end;justify-content:center;min-height:205px;padding:15px 12px 17px;overflow:hidden;background:linear-gradient(180deg,#FAFCFD 0%,#F4F7F8 100%);color:#112446;font-family:Arial,Helvetica,sans-serif;font-size:.9rem;font-weight:800;letter-spacing:0}.rec-formula::before{content:'';position:absolute;inset:22px 20px 44px;background:radial-gradient(circle at 8% 72%,#DCE3E8 0 11px,transparent 12px),radial-gradient(circle at 20% 74%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 34% 73%,#D7DEE4 0 13px,transparent 14px),radial-gradient(circle at 48% 74%,#EDF0F2 0 12px,transparent 13px),radial-gradient(circle at 62% 73%,#D6DDE3 0 13px,transparent 14px),radial-gradient(circle at 76% 74%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 90% 72%,#D9E0E5 0 11px,transparent 12px),radial-gradient(circle at 14% 49%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 30% 49%,#D8E0E5 0 13px,transparent 14px),radial-gradient(circle at 46% 50%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 62% 49%,#D6DEE4 0 13px,transparent 14px),radial-gradient(circle at 78% 50%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 23% 28%,#D7DFE5 0 13px,transparent 14px),radial-gradient(circle at 42% 28%,#EEF1F3 0 12px,transparent 13px),radial-gradient(circle at 61% 28%,#D8E0E6 0 13px,transparent 14px),radial-gradient(circle at 80% 28%,#EDF1F3 0 12px,transparent 13px)}.rec-formula::after{content:'';position:absolute;inset:22px 20px 44px;background:radial-gradient(circle at 28% 41%,var(--metal-a) 0 12px,transparent 13px),radial-gradient(circle at 49% 38%,var(--metal-b) 0 13px,transparent 14px),radial-gradient(circle at 71% 42%,var(--metal-a) 0 12px,transparent 13px),radial-gradient(circle at 38% 21%,var(--promoter) 0 10px,transparent 11px),radial-gradient(circle at 61% 20%,var(--metal-b) 0 11px,transparent 12px);filter:drop-shadow(0 4px 3px rgba(20,33,61,.18))}.rec-formula{isolation:isolate}.rec-formula::before,.rec-formula::after{z-index:-1}.rec-formula{ text-shadow:0 1px 0 #FFF }.rec-formula::first-line{background:rgba(255,255,255,.88)}
    .rec-formula{border:1px solid #EDF1F3}.rec-formula{box-shadow:inset 0 -1px 0 rgba(20,33,61,.04)}.rec-score{background:linear-gradient(180deg,#F5FCF7 0%,#FFFFFF 52%)}
    </style>""", unsafe_allow_html=True)
    st.markdown("<style>.rec-formula::before,.rec-formula::after{z-index:0!important}</style>", unsafe_allow_html=True)
    st.markdown("""<style>
    .rec-formula{flex-direction:column;gap:7px;align-items:center;justify-content:flex-end;background:#F8FAFB}.rec-formula::before,.rec-formula::after{display:none!important}.rec-formula img.rec-catalyst-image{width:100%;height:145px;object-fit:contain;display:block;mix-blend-mode:multiply}.rec-formula{font-size:.82rem;color:#112446}
    </style>""", unsafe_allow_html=True)

    def imagem_estrutura(posicao: int) -> str:
        """Retorna a imagem ilustrativa correspondente à composição colorida do card."""
        caminho = ESTRUTURAS_CATALITICAS[(posicao - 1) % len(ESTRUTURAS_CATALITICAS)]
        if not caminho.exists():
            return ""
        imagem = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        return f"<img class='rec-catalyst-image' src='data:image/png;base64,{imagem}' alt='Representação esquemática do catalisador'>"

    cards = []
    for posicao, (_, row) in enumerate(prioritarios_df.head(2).iterrows(), 1):
        formula = texto(row, [["formula"], ["f"]], "Composição não informada")
        suporte = corrigir_texto_portugues(texto(row, [["suporte", "sugerido"], ["suporte"]]))
        rota = corrigir_texto_portugues(texto(row, [["rota", "sintese"], ["rota"]]))
        justificativa = corrigir_texto_portugues(texto(row, [["justificativa", "suporte"], ["justificativa"]]))
        pretratamento = corrigir_texto_portugues(texto(row, [["pretratamento"]]))
        observacao = corrigir_texto_portugues(texto(row, [["observacao", "sintese"], ["observacao"]]))
        score = numero(row, [["score", "final"], ["score"]])
        classe_confianca = extrair_confiabilidade(row)
        score_confianca = numero(row, [["score", "confianca"], ["score", "incerteza"]])
        confianca = float(100 * np.clip(score_confianca, 0, 1)) if score_confianca is not None else 0.0
        texto_confianca = (
            f"{confianca:.1f}% ({classe_confianca})".replace(".", ",")
            if score_confianca is not None
            else classe_confianca.capitalize()
        )
        carga = float(np.clip(numero(row, [["teor", "fase", "ativa"], ["carga", "metal"], ["loading"]]) or 15, 1, 90))
        condicoes = montar_condicao_operacional(row)
        formula = formatar_formula_quimica(formula)
        suporte = formatar_formula_quimica(suporte)
        cor = "#16843C" if posicao == 1 else "#D99A00"
        estrutura = imagem_estrutura(posicao)
        cards.append(f"<article class='rec-card' style='--rec:{cor};--conf:{confianca}%'><div class='rec-head'><span class='rec-rank'>{posicao}</span><span class='rec-name'>{html.escape(formula)} / {html.escape(suporte)}</span><i class='rec-dot'></i></div><div class='rec-main'><div class='rec-formula'>{estrutura}<span>{html.escape(formula)}</span></div><div class='rec-score'><span>Pontuação final</span><strong>{'-' if score is None else f'{score:.2f}'} <small>/ 1,00</small></strong><span>Score de confiança: {html.escape(texto_confianca)}</span><div class='rec-bar'><i></i></div></div></div><div class='rec-list'><div class='rec-item'><b>Suporte sugerido</b><span>{html.escape(suporte)}</span></div><div class='rec-item'><b>Condições iniciais</b><span>{html.escape(condicoes)}</span></div><div class='rec-item'><b>Rota de síntese</b><span>{html.escape(rota)}</span></div><div class='rec-item'><b>Justificativa do suporte</b><span>{html.escape(justificativa)}</span></div><div class='rec-item'><b>Pré-tratamento</b><span>{html.escape(pretratamento)}</span></div><div class='rec-batch'><b>Preparação teórica de 100 g:</b> fase ativa {carga:.1f} g ({carga:.1f}% m/m) e suporte {100-carga:.1f} g. <b>Massas elementares na fase ativa:</b> {html.escape(massas_formula(formula, carga))}.</div></div><div class='rec-note'><b>Ponto de atenção:</b> {html.escape(observacao)} As massas dos sais precursores devem ser recalculadas conforme o sal, a pureza e a perda por calcinação.</div></article>")
    st.markdown(f"<div class='rec-grade'>{traduzir_texto_exibicao(''.join(cards))}</div>", unsafe_allow_html=True)
    mostrar_origem_e_confianca(prioritarios_df.iloc[0])


def mostrar_resumo_dashboard(metricas_df: pd.DataFrame, prioritarios_df: pd.DataFrame, monte_carlo_df: pd.DataFrame) -> None:
    """Mostra quatro indicadores executivos no formato da referencia visual."""
    n_gerados = extrair_metrica(metricas_df, "candidatos gerados") or 0
    n_recomendados = extrair_metrica(metricas_df, "candidatos priorit") or len(prioritarios_df)
    n_refinados = extrair_metrica(metricas_df, "candidatos refinados") or len(monte_carlo_df)
    top = prioritarios_df.iloc[0] if not prioritarios_df.empty else pd.Series(dtype=object)
    formula = formatar_formula_quimica(valor_linha(top, ["formula", "f"], "Aguardando triagem"))
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


def mostrar_painel_quimica(
    prioritarios_df: pd.DataFrame,
    classificacao_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    metais_selecionados: list[str],
    promotor_selecionado: str,
    reacao: str,
) -> None:
    """Apresenta relações químicas, descritores e evidências do candidato prioritário."""
    if prioritarios_df.empty:
        st.info("Execute uma triagem para gerar o painel químico.")
        return

    st.markdown(
        """
        <style>
        .chem-top-grid{display:grid;grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr);gap:14px;align-items:start}.chem-column{display:grid;gap:14px}.chem-panel{border:1px solid #D7E3DD;border-radius:8px;background:#FFF;color:#14213D;box-shadow:0 3px 11px rgba(20,33,61,.04);overflow:hidden}.chem-panel h3{margin:0!important;padding:11px 14px!important;border-bottom:1px solid #E5EDE8;color:#153A70!important;font-size:.96rem!important;line-height:1.25!important;font-weight:850!important}.chem-interaction-stage{position:relative;display:grid;grid-template-columns:minmax(66px,1fr) 50px 78px 50px minmax(66px,1fr);grid-template-rows:82px 28px 86px;align-items:center;min-height:240px;padding:8px 10px 14px;background:linear-gradient(180deg,#FFF,#F9FCFA)}.chem-sphere{z-index:2;display:grid;place-items:center;border-radius:50%;color:#FFF;font-weight:900;box-shadow:inset -10px -12px 18px rgba(0,0,0,.18),0 7px 14px rgba(20,33,61,.16)}.chem-sphere.promoter{grid-column:2;width:48px;height:48px;background:#45A85A}.chem-sphere.metal{grid-column:3;width:76px;height:76px;background:#174A93;font-size:1.05rem}.chem-sphere.support{grid-column:4;width:48px;height:48px;background:#19A2B8}.chem-effect{font-size:.59rem;line-height:1.34;overflow-wrap:anywhere}.chem-effect b,.chem-effect span{display:block}.chem-effect span{margin-top:4px;color:#087A3B}.chem-effect.electronic{grid-column:1;text-align:right}.chem-effect.structural{grid-column:5}.chem-arrows{grid-column:2/5;grid-row:2;color:#2385C7;font-size:.64rem;font-weight:750;text-align:center}.chem-support-lattice{grid-column:1/6;grid-row:3;display:grid;grid-template-columns:repeat(9,18px);justify-content:center;gap:2px}.chem-support-lattice i{width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#F7F8F9,#8B959D 65%,#59636B);box-shadow:0 2px 4px rgba(20,33,61,.18)}.chem-support-lattice i:nth-child(3n){background:radial-gradient(circle at 35% 30%,#FF7B6A,#C62828 70%)}.chem-anchor{position:absolute;right:12px;bottom:5px;left:12px;color:#B45A17;font-size:.62rem;text-align:center}.chem-anchor b,.chem-anchor span{display:block}.chem-support-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:12px}.chem-support-card{min-height:156px;padding:12px;border:1px solid #D9E4DF;border-radius:7px;background:#FCFDFD}.chem-support-card.selected{border:2px solid #1A9A50;background:#F6FCF8}.chem-support-card h4{margin:0 0 8px;color:#153A70;font-size:.92rem;text-align:center}.chem-support-card.selected h4{color:#087A3B}.chem-support-card ul{margin:0;padding-left:17px;color:#40536A;font-size:.67rem;line-height:1.45}.chem-support-card strong{display:block;margin-top:10px;padding:5px;border-radius:5px;background:#EEF7F1;color:#087A3B;font-size:.68rem;text-align:center}.chem-method-note{margin:0;padding:9px 13px;color:#64748B;font-size:.65rem;line-height:1.4}.chem-method-note.centered{text-align:center}.chem-structure-body{display:grid;grid-template-columns:138px 1fr;gap:8px;align-items:center;padding:10px 14px}.chem-phase-legend{display:grid;gap:9px;color:#263B58;font-size:.66rem}.chem-phase-legend span{display:flex;align-items:flex-start;gap:7px;line-height:1.3}.chem-phase-legend i{display:inline-block;flex:0 0 12px;width:12px;height:12px;border-radius:50%}.chem-phase-legend .active{background:#174A93}.chem-phase-legend .promoter{background:#19A2B8}.chem-phase-legend .support{background:#C6CDD2}.chem-structure-image{display:grid;min-height:205px;place-items:center}.chem-structure-image img{width:100%;height:205px;object-fit:contain;mix-blend-mode:multiply}.chem-table-wrap{overflow-x:auto}.chem-table{width:100%;min-width:650px;border-collapse:collapse;font-size:.67rem}.chem-table th,.chem-table td{padding:8px 7px;border-right:1px solid #E3EAE6;border-bottom:1px solid #E3EAE6;text-align:center}.chem-table th{background:#F4F8F6;color:#153A70;font-weight:850}.chem-table td:nth-child(2),.chem-table td:last-child{color:#087A3B;font-weight:800}.chem-gauges{margin:14px 0 24px}.chem-gauge-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;padding:16px}.chem-gauge-item{text-align:center}.chem-gauge-item>b{display:block;min-height:34px;color:#263B58;font-size:.7rem}.chem-gauge{display:grid;width:88px;height:88px;margin:4px auto 7px;place-items:center;border-radius:50%;background:conic-gradient(#16843C var(--gauge),#E4ECE7 0)}.chem-gauge:before{content:'';grid-area:1/1;width:64px;height:64px;border-radius:50%;background:#FFF}.chem-gauge span{z-index:1;grid-area:1/1;color:#14213D;font-size:1.25rem;font-weight:900}.chem-gauge-item small{color:#16843C;font-weight:750}.chem-section-title{margin:25px 0 12px;color:#14213D;font-size:1.55rem;text-align:center}.chem-descriptor-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-top:12px}.chem-descriptor{min-height:168px;padding:13px 11px;border:1px solid #D7E3DD;border-radius:8px;background:#FFF;text-align:center}.chem-descriptor h4{min-height:38px;margin:0;color:#087A3B;font-size:.76rem}.chem-descriptor strong{display:block;margin:10px 0;color:#146CC1;font-size:1.35rem}.chem-descriptor span{display:block;min-height:48px;color:#40536A;font-size:.66rem;line-height:1.35}.chem-descriptor b{display:block;margin-top:8px;color:#087A3B;font-size:.67rem}.chem-panel sub,.chem-support-card sub,.chem-table sub{font-size:.72em}.stPlotlyChart{border:1px solid #D7E3DD;border-radius:8px;overflow:hidden;background:#FFF}@media(max-width:1050px){.chem-top-grid{grid-template-columns:1fr}.chem-descriptor-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:760px){.chem-support-grid,.chem-gauge-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.chem-interaction-stage{grid-template-columns:1fr 58px 82px 58px 1fr}.chem-structure-body{grid-template-columns:1fr}.chem-descriptor-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:520px){.chem-support-grid,.chem-gauge-grid,.chem-descriptor-grid{grid-template-columns:1fr}.chem-interaction-stage{grid-template-columns:1fr 52px 70px 52px 1fr;padding-inline:6px}.chem-effect{font-size:.58rem}.chem-sphere.metal{width:70px;height:70px}.chem-sphere.promoter,.chem-sphere.support{width:48px;height:48px}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .chem-support-card em{display:block;margin:-3px 0 7px;color:#087A3B;font-size:.6rem;font-style:normal;font-weight:800;text-align:center}
        .chem-interaction-stage{display:block;position:relative;min-height:310px;padding:10px 12px 8px;background:linear-gradient(180deg,#FFF 0%,#FBFDFC 100%)}
        .chem-bond-strength{position:absolute;top:9px;left:50%;width:150px;transform:translateX(-50%);color:#153A70;font-size:.66rem;font-weight:800;line-height:1.35;text-align:center}.chem-bond-strength span{display:block;margin-top:2px}
        .chem-effect{position:absolute;z-index:3;width:82px;font-size:.57rem;line-height:1.38}.chem-effect b,.chem-effect span{display:block}.chem-effect span{margin-top:3px;font-weight:750}
        .chem-effect.electronic{top:90px;left:8px;text-align:left;color:#07823F}.chem-effect.structural{top:90px;right:4px;text-align:left;color:#1667B8}
        .chem-sphere{position:absolute;z-index:4;display:grid;place-items:center;border-radius:50%;color:#FFF;font-weight:900;box-shadow:inset -10px -12px 18px rgba(0,0,0,.18),0 7px 14px rgba(20,33,61,.17)}
        .chem-sphere.promoter{top:73px;left:24%;width:50px;height:50px;background:#45A85A}.chem-sphere.metal{top:67px;left:50%;width:82px;height:82px;transform:translateX(-50%);background:#174A93;font-size:1.12rem}.chem-sphere.support{top:73px;right:24%;width:50px;height:50px;background:#19A2B8}
        .chem-link{position:absolute;z-index:2;height:0;border-top:2px dashed currentColor;transform-origin:left center}.chem-link.e1{top:101px;left:36%;width:15%;color:#45A85A;transform:rotate(14deg)}.chem-link.e2{top:121px;left:36%;width:18%;color:#45A85A;transform:rotate(31deg)}.chem-link.s1{top:102px;left:62%;width:14%;color:#258DD0;transform:rotate(166deg)}.chem-link.s2{top:122px;left:63%;width:18%;color:#258DD0;transform:rotate(149deg)}
        .chem-anchor-links{position:absolute;z-index:2;top:144px;left:50%;width:150px;height:75px;transform:translateX(-50%)}.chem-anchor-links i{position:absolute;top:0;left:50%;height:72px;border-left:2px dashed #F07822;transform-origin:top center}.chem-anchor-links i:nth-child(1){transform:rotate(0deg)}.chem-anchor-links i:nth-child(2){transform:rotate(17deg)}.chem-anchor-links i:nth-child(3){transform:rotate(-17deg)}.chem-anchor-links i:nth-child(4){transform:rotate(32deg)}.chem-anchor-links i:nth-child(5){transform:rotate(-32deg)}
        .chem-support-lattice{position:absolute;right:18px;bottom:49px;left:18px;display:grid;grid-template-columns:repeat(13,18px);justify-content:center;gap:1px 3px}.chem-support-lattice i{width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#F7F8F9,#8B959D 65%,#59636B);box-shadow:0 2px 4px rgba(20,33,61,.18)}.chem-support-lattice i:nth-child(3n){background:radial-gradient(circle at 35% 30%,#FF7B6A,#C62828 70%)}
        .chem-charge-transfer{position:absolute;right:10px;bottom:8px;left:10px;color:#D65B13;font-size:.63rem;font-weight:800;line-height:1.35;text-align:center}.chem-charge-transfer span{display:block}
        .chem-proxy-note{margin:0;padding:7px 12px 9px;border-top:1px solid #EDF2EF;color:#6A7688;font-size:.59rem;line-height:1.35;text-align:center}
        .chem-interaction-diagram{padding:2px 4px 0;background:linear-gradient(180deg,#FFF,#FBFDFC)}.chem-interaction-diagram svg{display:block;width:100%;height:auto;max-height:300px}.chem-interaction-diagram .interacao-titulo{fill:#153A70;font:700 12px Arial,sans-serif}.chem-interaction-diagram .interacao-valor{fill:#153A70;font:800 12px Arial,sans-serif}.chem-interaction-diagram .interacao-verde{fill:#07823F;font:700 12px Arial,sans-serif}.chem-interaction-diagram .interacao-azul{fill:#1667B8;font:700 12px Arial,sans-serif}.chem-interaction-diagram .interacao-laranja{fill:#D65B13;font:700 11px Arial,sans-serif}.chem-interaction-diagram .interacao-atomo{fill:#FFF;font:800 17px Arial,sans-serif}.chem-interaction-diagram .interacao-metal-atomo{fill:#FFF;font:800 29px Arial,sans-serif}.chem-interaction-diagram .interacao-seta-verde{fill:none;stroke:#3AAB59;stroke-width:1.6;stroke-dasharray:5 4}.chem-interaction-diagram .interacao-seta-azul{fill:none;stroke:#278CD1;stroke-width:1.6;stroke-dasharray:5 4}.chem-interaction-diagram .interacao-ancoragem{fill:none;stroke:#F07822;stroke-width:1.55;stroke-dasharray:4 4}.chem-interaction-diagram .interacao-ligacao-suporte{fill:none;stroke:#8E9AA4;stroke-width:2.2;stroke-linecap:round;opacity:.72}
        .chem-structure-body{grid-template-columns:138px 1fr;gap:8px;align-items:center;padding:10px 14px}.chem-phase-legend .active{background:#174A93}.chem-phase-legend .promoter{background:#19A2B8}.chem-phase-legend .support{background:#C6CDD2}
        @media(max-width:620px){.chem-interaction-stage{min-height:335px}.chem-effect{width:78px;font-size:.54rem}.chem-effect.electronic{left:4px}.chem-effect.structural{right:2px}.chem-sphere.promoter{left:25%}.chem-sphere.support{right:25%}.chem-support-lattice{grid-template-columns:repeat(9,18px)}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    def numero_quimico(row: pd.Series, opcoes: list[list[str]], padrao: float = np.nan) -> float:
        """Converte a primeira coluna compatível em número sem inventar valores ausentes."""
        for termos in opcoes:
            coluna = encontrar_coluna(pd.DataFrame([row]), termos)
            if coluna:
                valor = pd.to_numeric(pd.Series([row.get(coluna)]), errors="coerce").iloc[0]
                if pd.notna(valor):
                    return float(valor)
        return padrao

    def fmt(valor: float, casas: int = 2, sufixo: str = "") -> str:
        """Formata valores científicos no padrão decimal brasileiro."""
        if pd.isna(valor):
            return "-"
        return f"{valor:.{casas}f}".replace(".", ",") + sufixo

    def formula_html(formula: str) -> str:
        """Exibe índices estequiométricos como subscritos sem alterar a fórmula original."""
        formula_segura = html.escape(str(formula))
        return re.sub(r"(?<=[A-Za-z])(\d+(?:\.\d+)?)", r"<sub>\1</sub>", formula_segura)

    def adequacao_suporte(suporte: dict[str, object]) -> float:
        """Calcula o índice heurístico com os mesmos eixos químicos da biblioteca do notebook."""
        pesos = {
            "metanacao": {"dispersao": 0.30, "redox": 0.25, "estabilidade_termica": 0.20, "afinidade_co2": 0.15, "vacancia_oxigenio": 0.10},
            "reforma": {"basicidade": 0.30, "estabilidade_termica": 0.25, "dispersao": 0.20, "afinidade_co2": 0.15, "redox": 0.10},
            "rwgs": {"redox": 0.30, "vacancia_oxigenio": 0.25, "afinidade_co2": 0.20, "dispersao": 0.15, "estabilidade_termica": 0.10},
        }.get(reacao, {"dispersao": 0.30, "redox": 0.25, "estabilidade_termica": 0.20, "afinidade_co2": 0.15, "vacancia_oxigenio": 0.10})
        indice = sum(float(suporte.get(eixo, 0.0)) * peso for eixo, peso in pesos.items())
        penalidade_smsi = 0.08 * max(float(suporte.get("risco_smsi", 0.0)) - 0.75, 0.0) / 0.25
        return float(np.clip(indice - penalidade_smsi, 0.0, 1.0))

    top = prioritarios_df.iloc[0]
    formula = str(valor_linha(top, ["formula"], valor_linha(top, ["f"], "-")))
    suporte_sugerido = corrigir_texto_portugues(valor_linha(top, ["suporte", "sugerido"], "-"))
    tipo_candidato = normalizar_texto(valor_linha(top, ["tipo", "candidato"], ""))
    elementos_formula = list(dict.fromkeys(re.findall(r"[A-Z][a-z]?", formula)))
    metais_ativos = list(dict.fromkeys(metais_selecionados or []))
    promotor = promotor_selecionado.strip()
    if not metais_ativos:
        if "promovido" in tipo_candidato and len(elementos_formula) > 1:
            metais_ativos = elementos_formula[:-1]
            promotor = promotor or elementos_formula[-1]
        else:
            metais_ativos = [elemento for elemento in elementos_formula if elemento != promotor]
    metal_principal = " / ".join(metais_ativos) if metais_ativos else (elementos_formula[0] if elementos_formula else "M")
    promotor_exibicao = promotor or "Sem promotor"

    score_redox = numero_quimico(top, [["score", "redox"]], 0.0)
    score_estrutural = numero_quimico(top, [["score", "quimico", "pymatgen"], ["score", "pymatgen"]], 0.0)
    score_interacao = numero_quimico(top, [["score", "dft", "ajustado", "boltzmann"], ["score", "dft", "proxy"]], 0.0)
    score_estabilidade = numero_quimico(top, [["score", "estabilidade"]], 0.0)
    score_coque = numero_quimico(top, [["score", "resistencia", "coque"]], 0.0)
    score_robustez = numero_quimico(top, [["score", "faixa", "condicao"]], 0.0)
    score_confianca = numero_quimico(top, [["score", "confianca"]], 0.0)

    # Prioriza grandezas de interface calculadas e usa proxies apenas quando elas ainda não existem na base.
    delta_e_ms = numero_quimico(top, [["energia", "interacao", "metal", "suporte"], ["energia", "ancoragem"]], np.nan)
    delta_q = numero_quimico(top, [["delta", "q", "eletron"], ["transferencia", "eletron"]], np.nan)
    delta_d = numero_quimico(top, [["variacao", "distancia", "metal", "suporte"], ["distorcao", "estrutural"]], np.nan)
    delta_rho = numero_quimico(top, [["delta", "rho"], ["redistribuicao", "carga"]], np.nan)
    usa_proxy_interacao = any(pd.isna(valor) for valor in [delta_e_ms, delta_q, delta_d, delta_rho])
    delta_e_ms = -0.60 * score_interacao if pd.isna(delta_e_ms) else delta_e_ms
    delta_q = 0.30 * (score_redox - 0.50) if pd.isna(delta_q) else delta_q
    delta_d = 0.24 * (score_estrutural - 0.50) if pd.isna(delta_d) else delta_d
    delta_rho = -0.20 * score_interacao if pd.isna(delta_rho) else delta_rho

    def fmt_delta(valor: float, unidade: str) -> str:
        """Exibe o sinal do efeito calculado para facilitar a interpretação química."""
        sinal = "+" if valor > 0 else ""
        return f"{sinal}{valor:.2f}".replace(".", ",") + f" {unidade}"

    # Identifica separadamente o metal principal, o promotor/segundo metal e o cátion do suporte.
    metal_central = metais_ativos[0] if metais_ativos else metal_principal
    atomos_suporte = [atomo for atomo in re.findall(r"[A-Z][a-z]?", suporte_sugerido) if atomo != "O"]
    atomo_suporte = atomos_suporte[0] if atomos_suporte else "S"
    atomo_lateral = metais_ativos[1] if len(metais_ativos) > 1 else atomo_suporte
    atomo_promotor = promotor if promotor else (metais_ativos[1] if len(metais_ativos) > 1 else "—")
    efeito_eletronico = "Doação de elétrons" if delta_q >= 0 else "Retirada de elétrons"

    # Desenha a interação M–S no mesmo arranjo visual da referência e atualiza átomos e deltas por candidato.
    nodos_suporte = []
    ligacoes_suporte_interacao = []
    for linha in range(3):
        for coluna in range(15):
            x = 38 + coluna * 34 + (linha % 2) * 17
            y = 205 + linha * 19
            if coluna < 14:
                ligacoes_suporte_interacao.append(f"<path d='M{x} {y} L{x + 34} {y}' class='interacao-ligacao-suporte'/>")
            if linha < 2:
                ligacoes_suporte_interacao.append(f"<path d='M{x} {y} L{x + 17} {y + 19}' class='interacao-ligacao-suporte'/>")
            nodos_suporte.append(f"<circle cx='{x}' cy='{y}' r='8.5' fill='url(#interacao-suporte)'/>")
    oxigenios_interacao = "".join(
        f"<circle cx='{x}' cy='195' r='6' fill='url(#interacao-oxigenio)'/>" for x in [75, 126, 177, 228, 279, 330, 381, 432, 483]
    )
    linhas_ancoragem = "".join(
        f"<path d='M280 159 L{x} 195' class='interacao-ancoragem'/>" for x in [177, 228, 279, 330, 381]
    )
    svg_interacao = f"""
    <svg viewBox='0 0 560 285' role='img' aria-label='Diagrama de interações metal suporte promotor'>
      <defs>
        <radialGradient id='interacao-metal' cx='30%' cy='24%'><stop offset='0%' stop-color='#DCEBFF'/><stop offset='40%' stop-color='#174A93'/><stop offset='100%' stop-color='#082A66'/></radialGradient>
        <radialGradient id='interacao-promotor' cx='30%' cy='24%'><stop offset='0%' stop-color='#CEFFD8'/><stop offset='42%' stop-color='#43A955'/><stop offset='100%' stop-color='#176F2C'/></radialGradient>
        <radialGradient id='interacao-lateral' cx='30%' cy='24%'><stop offset='0%' stop-color='#D5F7FF'/><stop offset='42%' stop-color='#1CA5C5'/><stop offset='100%' stop-color='#08748E'/></radialGradient>
        <radialGradient id='interacao-suporte' cx='30%' cy='24%'><stop offset='0%' stop-color='#FFFFFF'/><stop offset='45%' stop-color='#B7C0C6'/><stop offset='100%' stop-color='#6C7881'/></radialGradient>
        <radialGradient id='interacao-oxigenio' cx='30%' cy='24%'><stop offset='0%' stop-color='#FFD8D8'/><stop offset='42%' stop-color='#D93C3C'/><stop offset='100%' stop-color='#84212A'/></radialGradient>
        <marker id='seta-verde' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 Z' fill='#3AAB59'/></marker>
        <marker id='seta-azul' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 Z' fill='#278CD1'/></marker>
      </defs>
      <text x='280' y='25' class='interacao-titulo' text-anchor='middle'>Fortalecimento da ligação M–S</text>
      <text x='280' y='43' class='interacao-valor' text-anchor='middle'>ΔE = {fmt_delta(delta_e_ms, 'eV')}</text>
      <text x='12' y='90' class='interacao-verde'>Ligação eletrônica</text>
      <text x='12' y='108' class='interacao-verde'>{efeito_eletronico}</text>
      <text x='12' y='133' class='interacao-verde interacao-valor'>Δq = {fmt_delta(delta_q, 'e')}</text>
      <text x='548' y='90' class='interacao-azul' text-anchor='end'>Efeito estrutural</text>
      <text x='548' y='108' class='interacao-azul' text-anchor='end'>Dispersão</text>
      <text x='548' y='133' class='interacao-azul interacao-valor' text-anchor='end'>Δd = {fmt_delta(delta_d, 'Å')}</text>
      <path d='M183 104 C210 105 220 115 237 123' class='interacao-seta-verde' marker-end='url(#seta-verde)'/>
      <path d='M183 111 C215 126 222 143 244 148' class='interacao-seta-verde' marker-end='url(#seta-verde)'/>
      <path d='M377 104 C350 105 340 115 323 123' class='interacao-seta-azul' marker-end='url(#seta-azul)'/>
      <path d='M377 111 C345 126 338 143 316 148' class='interacao-seta-azul' marker-end='url(#seta-azul)'/>
      <circle cx='164' cy='103' r='20' fill='url(#interacao-promotor)'/><text x='164' y='109' class='interacao-atomo' text-anchor='middle'>{html.escape(atomo_promotor)}</text>
      <circle cx='280' cy='120' r='45' fill='url(#interacao-metal)'/><text x='280' y='128' class='interacao-metal-atomo' text-anchor='middle'>{html.escape(metal_central)}</text>
      <circle cx='397' cy='103' r='20' fill='url(#interacao-lateral)'/><text x='397' y='109' class='interacao-atomo' text-anchor='middle'>{html.escape(atomo_lateral)}</text>
      {linhas_ancoragem}
      {''.join(ligacoes_suporte_interacao)}
      {''.join(nodos_suporte)}
      {oxigenios_interacao}
      <text x='280' y='269' class='interacao-laranja' text-anchor='middle'>Transferência de carga</text>
      <text x='280' y='282' class='interacao-laranja interacao-valor' text-anchor='middle'>Δρ = {fmt_delta(delta_rho, '|e|')}</text>
    </svg>
    """

    # Recupera a ilustração estrutural previamente adotada no painel da direita.
    assinatura = sum((indice + 1) * ord(caractere) for indice, caractere in enumerate(formula))
    caminho_estrutura = ESTRUTURAS_CATALITICAS[assinatura % len(ESTRUTURAS_CATALITICAS)]
    estrutura_html = ""
    if caminho_estrutura.exists():
        estrutura_base64 = base64.b64encode(caminho_estrutura.read_bytes()).decode("utf-8")
        estrutura_html = f"<img src='data:image/png;base64,{estrutura_base64}' alt='Representação esquemática do catalisador'>"

    suportes_reacao = [suporte for suporte in BIBLIOTECA_SUPORTES_QUIMICA if reacao in suporte["reacoes"]]
    suporte_normalizado = normalizar_texto(suporte_sugerido).replace(" ", "")
    sugeridos = [suporte for suporte in suportes_reacao if normalizar_texto(str(suporte["suporte"])).replace(" ", "") in suporte_normalizado]
    restantes = sorted([suporte for suporte in suportes_reacao if suporte not in sugeridos], key=adequacao_suporte, reverse=True)
    suportes_exibidos = (sugeridos + restantes)[:3]
    nomes_propriedades = {
        "dispersao": "Dispersão da fase ativa",
        "estabilidade_termica": "Estabilidade térmica",
        "redox": "Capacidade redox",
        "basicidade": "Basicidade superficial",
        "vacancia_oxigenio": "Vacâncias de oxigênio",
        "afinidade_co2": "Afinidade por CO₂",
    }
    cards_suporte = []
    for indice, suporte in enumerate(suportes_exibidos):
        propriedades = sorted(nomes_propriedades, key=lambda chave: float(suporte[chave]), reverse=True)[:3]
        itens = "".join(f"<li>{html.escape(nomes_propriedades[chave])}: {fmt(float(suporte[chave]), 2)}</li>" for chave in propriedades)
        classe = " selected" if indice == 0 else ""
        selo_suporte = "<em>Sugestão da triagem</em>" if indice == 0 else ""
        cards_suporte.append(
            f"<article class='chem-support-card{classe}'><h4>{formula_html(str(suporte['suporte']))}</h4>{selo_suporte}"
            f"<ul>{itens}</ul><strong>Índice heurístico: {fmt(adequacao_suporte(suporte), 2)}</strong></article>"
        )

    fontes = [dataframe for dataframe in [classificacao_df, ranking_df, prioritarios_df] if not dataframe.empty]
    base_quimica = pd.concat(fontes, ignore_index=True, sort=False) if fontes else prioritarios_df.copy()
    coluna_formula = encontrar_coluna(base_quimica, ["formula"]) or encontrar_coluna(base_quimica, ["f"])
    if coluna_formula:
        base_quimica = base_quimica.drop_duplicates(subset=[coluna_formula]).head(20).copy()

    linhas_propriedades = []
    for posicao, (_, row) in enumerate(base_quimica.head(5).iterrows(), 1):
        formula_row = str(row.get(coluna_formula, "-")) if coluna_formula else "-"
        linhas_propriedades.append(
            "<tr>"
            f"<td>{posicao}</td><td>{formula_html(formula_row)}</td>"
            f"<td>{fmt(numero_quimico(row, [['energia', 'adsorcao', 'volcano']]), 3)}</td>"
            f"<td>{fmt(numero_quimico(row, [['distancia', 'otimo', 'volcano']]), 3)}</td>"
            f"<td>{fmt(numero_quimico(row, [['barreira', 'aparente', 'volcano']]), 3)}</td>"
            f"<td>{fmt(numero_quimico(row, [['energia', 'gnn', 'local']]), 3)}</td>"
            f"<td>{fmt(numero_quimico(row, [['score', 'final']]), 3)}</td></tr>"
        )

    def classe_gauge(valor: float) -> tuple[str, str]:
        percentual = int(round(100 * float(np.clip(valor, 0.0, 1.0))))
        classe = "Excelente" if percentual >= 80 else "Boa" if percentual >= 65 else "Moderada" if percentual >= 45 else "Baixa"
        return str(percentual), classe

    gauges = []
    for titulo, valor in [
        ("Estabilidade termodinâmica", score_estabilidade),
        ("Proxy de resistência à sinterização", score_estrutural),
        ("Estabilidade operacional", score_robustez),
        ("Resistência ao coque", score_coque),
    ]:
        percentual, classe = classe_gauge(valor)
        gauges.append(
            f"<div class='chem-gauge-item'><b>{html.escape(titulo)}</b><div class='chem-gauge' style='--gauge:{percentual}%'><span>{percentual}</span></div><small>{classe}</small></div>"
        )

    html_superior = f"""
    <section class="chem-top-grid">
      <div class="chem-column">
        <article class="chem-panel chem-interactions"><h3>Interações metal–suporte–promotor</h3>
          <div class="chem-interaction-diagram">{svg_interacao}</div>
          <p class="chem-proxy-note">{'Estimativas proxy derivadas dos descritores da triagem; confirmar por DFT de interface.' if usa_proxy_interacao else 'Valores calculados de interface disponíveis na base local.'}</p>
        </article>
        <article class="chem-panel"><h3>Racional do suporte</h3><div class="chem-support-grid">{''.join(cards_suporte)}</div>
          <p class="chem-method-note">O suporte sugerido pela triagem aparece primeiro. O índice heurístico compara dispersão, estabilidade térmica, redox, basicidade, afinidade por CO₂ e risco de SMSI; ele não refaz o ranking global nem substitui DFT explícita da interface.</p>
        </article>
      </div>
      <div class="chem-column">
        <article class="chem-panel chem-structure"><h3>Modelo estrutural esquemático ({formula_html(formula)} / {formula_html(suporte_sugerido)})</h3>
          <div class="chem-structure-body"><div class="chem-phase-legend"><span><i class="active"></i>Fase ativa: {html.escape(metal_principal)}</span><span><i class="promoter"></i>Promotor: {html.escape(promotor_exibicao)}</span><span><i class="support"></i>Suporte: {html.escape(suporte_sugerido)}</span></div><div class="chem-structure-image">{estrutura_html}</div></div>
          <p class="chem-method-note">Representação visual das fases; não corresponde a uma geometria atômica relaxada por DFT.</p>
        </article>
        <article class="chem-panel"><h3>Fórmulas e propriedades calculadas</h3><div class="chem-table-wrap"><table class="chem-table"><thead><tr><th>#</th><th>Catalisador</th><th>E<sub>ads</sub> (eV)</th><th>Distância do ótimo (eV)</th><th>Barreira aparente (eV)</th><th>E<sub>GNN</sub> (eV/átomo)</th><th>Score final</th></tr></thead><tbody>{''.join(linhas_propriedades)}</tbody></table></div>
          <p class="chem-method-note">E<sub>ads</sub>, distância e barreira usam o descritor da reação; E<sub>GNN</sub> é uma predição de bulk e não uma energia explícita de superfície.</p>
        </article>
      </div>
    </section>
    <article class="chem-panel chem-gauges"><h3>Estabilidade térmica e resistência à formação de coque</h3><div class="chem-gauge-grid">{''.join(gauges)}</div><p class="chem-method-note centered">A resistência à sinterização é um proxy estrutural/composicional; não representa um modelo temporal de crescimento de partículas.</p></article>
    """
    st.markdown(traduzir_texto_exibicao(html_superior), unsafe_allow_html=True)

    st.markdown(traduzir_texto_exibicao("<h2 class='chem-section-title'>Descritores químicos e relação estrutura–desempenho</h2>"), unsafe_allow_html=True)
    cfg_volcano = CONFIGURACAO_VOLCANO.get(reacao, CONFIGURACAO_VOLCANO["metanacao"])
    modo_ingles = idioma_atual() == "en"
    energia_col = encontrar_coluna_por_opcoes(base_quimica, [["energia", "adsorcao", "volcano"]])
    score_volcano_col = encontrar_coluna_por_opcoes(base_quimica, [["score", "volcano"], ["taxa", "relativa", "volcano"]])
    score_final_col = encontrar_coluna_por_opcoes(base_quimica, [["score", "final"]])
    estabilidade_col = encontrar_coluna_por_opcoes(base_quimica, [["estabilidade", "termodinamica"]])
    coluna_suporte = encontrar_coluna_por_opcoes(base_quimica, [["suporte", "sugerido"], ["suporte"]])

    coluna_grafico_1, coluna_grafico_2 = st.columns(2)
    with coluna_grafico_1:
        if energia_col and score_volcano_col and coluna_formula:
            dados_volcano = base_quimica[[coluna_formula, energia_col, score_volcano_col] + ([coluna_suporte] if coluna_suporte else [])].copy()
            dados_volcano[energia_col] = pd.to_numeric(dados_volcano[energia_col], errors="coerce")
            dados_volcano[score_volcano_col] = pd.to_numeric(dados_volcano[score_volcano_col], errors="coerce")
            dados_volcano = dados_volcano.dropna(subset=[energia_col, score_volcano_col])
            x_curva = np.linspace(cfg_volcano["energia_otima"] - 2.2 * cfg_volcano["largura"], cfg_volcano["energia_otima"] + 2.2 * cfg_volcano["largura"], 180)
            y_curva = np.exp(-np.abs(x_curva - cfg_volcano["energia_otima"]) / cfg_volcano["largura"])
            figura_volcano = go.Figure()
            figura_volcano.add_vrect(x0=cfg_volcano["energia_otima"] - cfg_volcano["largura"], x1=cfg_volcano["energia_otima"] + cfg_volcano["largura"], fillcolor="#DFF3E4", opacity=0.45, line_width=0)
            figura_volcano.add_trace(go.Scatter(x=x_curva, y=y_curva, mode="lines", name="Sabatier trend" if modo_ingles else "Tendência de Sabatier", line={"color": "#355070", "dash": "dash", "width": 2}))
            figura_volcano.add_trace(go.Scatter(x=dados_volcano[energia_col], y=dados_volcano[score_volcano_col], mode="markers", name="Candidates" if modo_ingles else "Candidatos", text=dados_volcano[coluna_formula], customdata=dados_volcano[[coluna_suporte]].to_numpy() if coluna_suporte else None, marker={"size": 10, "color": "#0B7A3B", "line": {"width": 1, "color": "#FFFFFF"}}, hovertemplate="<b>%{text}</b><br>Eads: %{x:.3f} eV<br>" + ("Relative activity" if modo_ingles else "Atividade relativa") + ": %{y:.3f}" + (("<br>Support" if modo_ingles else "<br>Suporte") + ": %{customdata[0]}" if coluna_suporte else "") + "<extra></extra>"))
            figura_volcano.add_vline(x=cfg_volcano["energia_otima"], line_dash="dot", line_color="#16843C", annotation_text="Sabatier optimum" if modo_ingles else "Ótimo de Sabatier")
            titulo_volcano = f"Relative activity (proxy) vs {cfg_volcano['descritor']} adsorption energy" if modo_ingles else f"Atividade relativa (proxy) vs energia de adsorção de {cfg_volcano['descritor']}"
            figura_volcano.update_layout(title={"text": titulo_volcano, "x": 0.5}, xaxis_title="Adsorption energy (eV)" if modo_ingles else "Energia de adsorção (eV)", yaxis_title="Relative activity (0–1)" if modo_ingles else "Atividade relativa (0–1)", height=470, margin={"l": 72, "r": 22, "t": 76, "b": 62}, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font={"color": "#14213D"}, legend={"orientation": "h", "y": 1.12})
            figura_volcano.update_xaxes(gridcolor="#E6EEE9", automargin=True)
            figura_volcano.update_yaxes(gridcolor="#E6EEE9", range=[0, 1.08], automargin=True)
            st.plotly_chart(figura_volcano, width="stretch", key="quimica_volcano", theme=None)
        else:
            st.info("Dados de adsorção insuficientes para o gráfico de Sabatier.")

    with coluna_grafico_2:
        if score_final_col and estabilidade_col and coluna_formula:
            dados_estabilidade = base_quimica[[coluna_formula, score_final_col, estabilidade_col] + ([coluna_suporte] if coluna_suporte else [])].copy()
            dados_estabilidade[score_final_col] = pd.to_numeric(dados_estabilidade[score_final_col], errors="coerce")
            dados_estabilidade[estabilidade_col] = pd.to_numeric(dados_estabilidade[estabilidade_col], errors="coerce")
            dados_estabilidade = dados_estabilidade.dropna(subset=[score_final_col, estabilidade_col])
            figura_estabilidade = px.scatter(dados_estabilidade, x=score_final_col, y=estabilidade_col, color=score_final_col, color_continuous_scale="Tealgrn", custom_data=[coluna_formula] + ([coluna_suporte] if coluna_suporte else []))
            figura_estabilidade.update_traces(marker={"size": 10, "line": {"width": 0.8, "color": "#FFFFFF"}}, hovertemplate="<b>%{customdata[0]}</b><br>" + ("Final score" if modo_ingles else "Score final") + ": %{x:.3f}<br>" + ("Stability" if modo_ingles else "Estabilidade") + ": %{y:.3f} eV/atom" + (("<br>Support" if modo_ingles else "<br>Suporte") + ": %{customdata[1]}" if coluna_suporte else "") + "<extra></extra>")
            if not dados_estabilidade.empty:
                primeiro = dados_estabilidade.iloc[0]
                figura_estabilidade.add_annotation(x=primeiro[score_final_col], y=primeiro[estabilidade_col], text=str(primeiro[coluna_formula]), showarrow=True, arrowcolor="#153A70", ax=32, ay=-32, font={"color": "#153A70", "size": 11})
            figura_estabilidade.update_layout(title={"text": "Thermodynamic stability vs final score" if modo_ingles else "Estabilidade termodinâmica vs score final", "x": 0.5}, xaxis_title="Final score (0–1)" if modo_ingles else "Score final (0–1)", yaxis_title="Thermodynamic stability (eV/atom; lower is better)" if modo_ingles else "Estabilidade termodinâmica (eV/átomo; menor é melhor)", height=470, margin={"l": 86, "r": 28, "t": 76, "b": 62}, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font={"color": "#14213D"}, coloraxis_colorbar={"title": "Score"})
            figura_estabilidade.update_xaxes(gridcolor="#E6EEE9", automargin=True)
            figura_estabilidade.update_yaxes(gridcolor="#E6EEE9", automargin=True)
            st.plotly_chart(figura_estabilidade, width="stretch", key="quimica_estabilidade", theme=None)
        else:
            st.info("Dados insuficientes para relacionar estabilidade e score final.")

    energia_adsorcao = numero_quimico(top, [["energia", "adsorcao", "volcano"]])
    distancia_otimo = numero_quimico(top, [["distancia", "otimo", "volcano"]])
    score_dft = numero_quimico(top, [["score", "dft", "proxy"]])
    descritores = [
        ("Energia de adsorção", fmt(energia_adsorcao, 3, " eV"), f"Distância do ótimo: {fmt(distancia_otimo, 3, ' eV')}", "Próxima do ótimo é melhor"),
        ("Afinidade por oxigênio", fmt(score_redox, 2), "Proxy redox normalizado (0–1)", "Maior é melhor"),
        ("Redutibilidade", fmt(score_dft, 2), "DFT ou proxy DFT normalizado (0–1)", "Maior é melhor"),
        ("Basicidade", fmt(numero_quimico(top, [["score", "basicidade"]]), 2), "Proxy de afinidade ácido–base (0–1)", "Maior depende da reação"),
        ("Resistência ao coque", fmt(score_coque, 2), "Índice composicional/cinético (0–1)", "Maior é melhor"),
        ("Interação metal–suporte", fmt(score_interacao, 2), "DFT/proxy com peso de Boltzmann (0–1)", "Maior indica ancoragem favorável"),
    ]
    cards_descritores = "".join(f"<article class='chem-descriptor'><h4>{html.escape(titulo)}</h4><strong>{html.escape(valor)}</strong><span>{html.escape(fonte)}</span><b>{html.escape(sentido)}</b></article>" for titulo, valor, fonte, sentido in descritores)
    st.markdown(traduzir_texto_exibicao(f"<div class='chem-descriptor-grid'>{cards_descritores}</div><p class='chem-method-note centered'>Descritores normalizados são proxies de triagem e devem ser confirmados por DFT de superfície e validação experimental.</p>"), unsafe_allow_html=True)


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
    ajuda_bandeira = "Translate to English" if idioma_atual() == "pt" else "Traduzir para português"
    if colunas[-1].button(bandeira, key="nav_idioma", help=ajuda_bandeira, width="stretch"):
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
                "CatAiLab é uma plataforma de triagem virtual para priorizar catalisadores e condições "
                "de síntese para metanação de CO₂, reforma de CH₄ e RWGS. Ela apoia a decisão "
                "experimental com estabilidade termodinâmica, descritores químicos, dados ou proxies "
                "DFT, estabilidade operacional, incerteza e critérios de síntese."
            )
            desenvolvimento = (
                "O desenvolvimento integra Materials Project, OQMD e Catalysis-Hub com descritores "
                "do matminer e pymatgen, avaliação de estabilidade, análise tipo vulcão, simulação "
                "de Monte Carlo, quimiometria e recomendação de suporte e rota de síntese."
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
            perfil = f"{dados['nome']} é o pesquisador e desenvolvedor responsável pelo CatAiLab."
            titulo_perfil, titulo_citacao = "Pesquisador e desenvolvedor", "Forma de citação"
            citacao = (
                "MAIA, Allan. CatAiLab: triagem virtual de catalisadores e condições de síntese. "
                "Software científico. Universidade Federal do Rio Grande do Norte, 2026. "
                "Disponível em: https://triagemufrn.streamlit.app/."
            )
        col1, col2 = st.columns(2)
        col1.markdown(cartao_texto_html(titulo_perfil, perfil), unsafe_allow_html=True)
        col2.markdown(cartao_texto_html(titulo_citacao, citacao), unsafe_allow_html=True)
        st.link_button("Curriculum Lattes" if idioma_atual() == "en" else "Currículo Lattes", dados["lattes"])

    elif pagina == "contato":
        st.markdown(f"<h2 style='text-align:center;'>{html.escape(t('Contato'))}</h2>", unsafe_allow_html=True)
        titulo = "Contact" if idioma_atual() == "en" else "Contato profissional"
        texto = f"E-mail: {dados['email']}\n\nTelefone: {dados['telefone']}\n\nCurrículo Lattes: {dados['lattes']}"
        col1, col2 = st.columns([1.2, 0.8])
        col1.markdown(cartao_texto_html(titulo, texto), unsafe_allow_html=True)
        with col2:
            st.link_button("Email", f"mailto:{dados['email']}", width="stretch")
            st.link_button("WhatsApp / telefone", f"tel:{telefone_link}", width="stretch")
            st.link_button("Currículo Lattes", dados["lattes"], width="stretch")


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
    # Estiliza os elementos como teclas físicas sem alterar a lógica de seleção química.
    st.markdown(
        """
        <style>
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] {
            min-width: 900px;
            gap: 4px !important;
            padding: 1px 2px 7px;
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] {
            min-width: 44px !important;
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
            position: relative;
            min-height: 42px !important;
            height: 42px;
            padding: 0 !important;
            border: 1px solid #5E96AD !important;
            border-radius: 7px !important;
            background: linear-gradient(145deg, #EAF8FC 0%, #9DD9E8 52%, #49A9C4 100%) !important;
            color: #073B50 !important;
            box-shadow: 0 5px 0 #2B7189, 0 8px 12px rgba(15, 57, 74, 0.24) !important;
            font-size: 0.78rem !important;
            font-weight: 900 !important;
            line-height: 1 !important;
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
            transform: translateY(0);
            transition: transform 90ms ease, box-shadow 90ms ease, filter 120ms ease;
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {
            filter: brightness(1.08) saturate(1.08);
            transform: translateY(-1px);
            box-shadow: 0 6px 0 #2B7189, 0 10px 15px rgba(15, 57, 74, 0.28) !important;
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:active {
            animation: tecla-periodica-pressionada 180ms ease-out;
            transform: translateY(5px);
            box-shadow: 0 0 0 #2B7189, 0 2px 4px rgba(15, 57, 74, 0.20) !important;
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(145deg, #D8FFE3 0%, #56D77C 48%, #07913B 100%) !important;
            border-color: #087A38 !important;
            color: #073B1D !important;
            box-shadow: 0 1px 0 #075F2C, 0 3px 7px rgba(7, 95, 44, 0.28) !important;
            transform: translateY(4px);
        }
        div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button * {
            margin: 0 !important;
            color: inherit !important;
            font-size: inherit !important;
            font-weight: inherit !important;
        }
        @keyframes tecla-periodica-pressionada {
            0% { transform: translateY(0); box-shadow: 0 5px 0 #2B7189, 0 8px 12px rgba(15, 57, 74, 0.24); }
            55% { transform: translateY(5px); box-shadow: 0 0 0 #2B7189, 0 2px 4px rgba(15, 57, 74, 0.20); }
            100% { transform: translateY(3px); box-shadow: 0 2px 0 #2B7189, 0 4px 7px rgba(15, 57, 74, 0.22); }
        }
        @media (prefers-reduced-motion: reduce) {
            div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
                animation: none !important;
                transition: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    nomes_reacao = {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}
    equacoes_reacao = {"metanacao": "CO₂ + 4H₂ → CH₄ + 2H₂O", "reforma": "CH₄ + CO₂ → 2CO + 2H₂", "rwgs": "CO₂ + H₂ → CO + H₂O"}

    with st.popover("Reação", icon=":material/science:", width="stretch"):
        reacao = st.selectbox("Reação-alvo", ["metanacao", "reforma", "rwgs"], index=None, placeholder="Selecione a reação", format_func=lambda x: {"metanacao": "Metanação de CO₂", "reforma": "Reforma de CH₄", "rwgs": "RWGS"}[x], key="config_reacao")
    if reacao:
        st.markdown("<div class='catialab-config-preview'>" f"<div class='reaction-name'>{nomes_reacao[reacao]}</div>" f"<div class='reaction-equation'>{equacoes_reacao[reacao]}</div>" "</div>", unsafe_allow_html=True)

    with st.popover("Número de metais ativos", icon=":material/format_list_numbered:", width="stretch"):
        n_metais_selecionado = st.selectbox("Quantidade de metais ativos", [1, 2, 3, 4], index=None, placeholder="Selecione a quantidade", key="config_n_metais")
    n_metais = int(n_metais_selecionado or 0)

    with st.popover("Metais ativos", icon=":material/hub:", width="stretch"):
        metais = selecionar_metais_tabela_periodica(n_metais)
        st.caption(t("Todos os metais serão representados entre os 100 candidatos viáveis."))
    garantir_metais_nos_100 = True
    if metais:
        chips_metais = "".join(f"<span class='catialab-metal-chip'>{html.escape(metal)}</span>" for metal in metais)
        st.markdown(f"<div class='catialab-config-preview'>{chips_metais}</div>", unsafe_allow_html=True)

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
    resumo_regra = "metais garantidos nos 100 viáveis"
    resumo_promotor = promotor if promotor else ("sem promotor" if modo_promotor == "Sem promotor" else "não definido")
    resumo_reacao = nomes_reacao.get(reacao, "não definida")
    st.markdown(
        f"<div class='catialab-config-status'><strong>Configuração atual</strong><br>"
        f"{html.escape(resumo_reacao)}<br>{html.escape(resumo_metais)}<br>"
        f"{html.escape(resumo_regra)}<br>{html.escape(resumo_promotor)}</div>",
        unsafe_allow_html=True,
    )
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
                notebook_executado = executar_triagem(
                    reacao,
                    metais,
                    promotor,
                    output_dir,
                    garantir_metais_nos_100,
                )
        except Exception as erro_execucao:
            st.error("A triagem não foi concluída. Verifique os detalhes técnicos abaixo.")
            with st.expander("Detalhes técnicos do erro"):
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

st.markdown(
    """<style>
    /* Amplia textos de leitura sem modificar os tamanhos dos titulos h1-h4. */
    div[data-testid="stTabPanel"] p,
    div[data-testid="stTabPanel"] li,
    div[data-testid="stTabPanel"] td,
    div[data-testid="stTabPanel"] th,
    div[data-testid="stTabPanel"] label,
    div[data-testid="stTabPanel"] button,
    div[data-testid="stTabPanel"] input,
    div[data-testid="stTabPanel"] select,
    div[data-testid="stTabPanel"] textarea,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] button {
        font-size: 0.96rem !important;
        line-height: 1.48 !important;
    }
    div[data-testid="stTabPanel"] [class$="-note"],
    div[data-testid="stTabPanel"] [class$="-subtitle"],
    div[data-testid="stTabPanel"] [class$="-description"],
    div[data-testid="stTabPanel"] [class$="-detail"],
    div[data-testid="stTabPanel"] [class$="-meta"],
    div[data-testid="stTabPanel"] [class$="-label"] {
        font-size: 0.94rem !important;
        line-height: 1.45 !important;
    }
    /* Destaca a navegacao por abas sem alterar os titulos internos das paginas. */
    div[data-testid="stTabs"] div[role="tablist"] {
        min-height: 56px;
        gap: clamp(8px, 1.1vw, 18px);
    }
    button[data-baseweb="tab"],
    div[data-testid="stTab"] {
        min-height: 54px !important;
        padding: 0 14px !important;
    }
    button[data-baseweb="tab"] p,
    div[data-testid="stTab"] p {
        font-size: clamp(1rem, 0.95vw, 1.10rem) !important;
        font-weight: 780 !important;
        line-height: 1.18 !important;
        white-space: nowrap;
    }

    div[data-testid="stTab"][aria-selected="true"],
    div[data-testid="stTab"][aria-selected="true"] p {
        color: #146CC1 !important;
        font-weight: 850 !important;
    }
    div[data-testid="stTab"][aria-selected="true"] .react-aria-SelectionIndicator {
        background: #146CC1 !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

secoes_resultados = {
    "recomendados": f"⌂  {t('Catalisadores recomendados')}",
    "candidatos": f"⌕  {t('Candidatos')}",
    "quimica": f"⚗  {t('Química')}",
    "sintese": f"⚖  {t('Síntese')}",
    "incerteza": f"◌  {t('Incerteza')}",
    "robustez": f"◈  {t('Estabilidade catalítica e operação')}",
    "validacao": f"✓  {t('Validação')}",
    "visualizacao": f"▥  {t('Visualização científica')}",
    "arquivos": f"▤  {t('Arquivos')}",
}
secao_resultados = st.pills(
    "Seção dos resultados",
    options=list(secoes_resultados),
    default=st.session_state.get("secao_resultados_atual", "recomendados"),
    format_func=lambda chave: secoes_resultados[chave],
    selection_mode="single",
    label_visibility="collapsed",
    key="navegacao_resultados",
) or "recomendados"
st.session_state["secao_resultados_atual"] = secao_resultados

if secao_resultados == "recomendados":
    renderizar_titulo_dashboard()
    mostrar_recomendacoes_sintese(prioritarios_df)
    mostrar_funil_visual(metricas_df, prioritarios_df, monte_carlo_df)
elif secao_resultados == "candidatos":
    mostrar_candidatos_prioritarios(metricas_df, [prioritarios_df, classificacao_df, ranking_df])
elif secao_resultados == "quimica":
    mostrar_painel_quimica(
        prioritarios_df,
        classificacao_df,
        ranking_df,
        metais,
        promotor,
        reacao_resultado,
    )
elif secao_resultados == "sintese":
    mostrar_planejamento_sintese(prioritarios_df, metais, promotor)
elif secao_resultados == "incerteza":
    mostrar_painel_incerteza(monte_carlo_df, dominio_df, validacao_quimio_df)
elif secao_resultados == "robustez":
    mostrar_simulador_operacional(prioritarios_df, classificacao_df)
elif secao_resultados == "validacao":
    mostrar_painel_validacao(
        classificacao_df,
        ranking_df,
        dominio_df,
        pareto_df,
        validacao_quimio_df,
        validacao_avancada_df,
    )
elif secao_resultados == "visualizacao":
    mostrar_visualizacao_cientifica_plotly(prioritarios_df, classificacao_df, ranking_df, monte_carlo_df, figuras_df)
elif secao_resultados == "arquivos":
    mostrar_painel_arquivos(paths, metricas_df, classificacao_df, reacao_resultado)
