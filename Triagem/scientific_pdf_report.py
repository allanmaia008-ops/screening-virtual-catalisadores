"""Relatório científico PDF autocontido de uma triagem CatAiLab."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


AZUL = colors.HexColor("#153A70")
VERDE = colors.HexColor("#16843C")
CINZA = colors.HexColor("#52657A")
FUNDO = colors.HexColor("#F3F7F5")


def _texto(valor: object) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "-"
    texto = unicodedata.normalize("NFC", str(valor)).strip()
    for origem, destino in {"₂": "2", "₃": "3", "₄": "4", "²": "2", "³": "3", "→": "->", "–": "-", "—": "-", "−": "-", "±": "+/-"}.items():
        texto = texto.replace(origem, destino)
    return escape(re.sub(r"\s+", " ", texto))


def _normalizar(valor: object) -> str:
    return unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode().lower()


def _ler_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(caminho, encoding=encoding)
        except UnicodeDecodeError:
            pass
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()


def _achar_coluna(dataframe: pd.DataFrame, *termos: str) -> str | None:
    termos = tuple(_normalizar(termo) for termo in termos)
    return next((str(coluna) for coluna in dataframe.columns if all(termo in _normalizar(coluna) for termo in termos)), None)


def _valor(linha: pd.Series, alternativas: list[tuple[str, ...]]) -> str:
    quadro = pd.DataFrame(columns=linha.index)
    for termos in alternativas:
        coluna = _achar_coluna(quadro, *termos)
        if coluna and pd.notna(linha.get(coluna)) and str(linha.get(coluna)).strip():
            return _texto(linha.get(coluna))
    return "-"


def _tabela(dataframe: pd.DataFrame, estilos, limite: int = 10, colunas: int = 7):
    if dataframe.empty:
        return Paragraph("Dados não disponíveis nesta execução.", estilos["BodyText"])
    recorte = dataframe.iloc[:limite, :colunas]
    linhas = [[Paragraph(f"<b>{_texto(c)}</b>", estilos["TableHeader"]) for c in recorte.columns]]
    linhas.extend([[Paragraph(_texto(valor), estilos["TableText"]) for valor in linha] for linha in recorte.itertuples(index=False, name=None)])
    tabela = Table(linhas, colWidths=[267 * mm / len(recorte.columns)] * len(recorte.columns), repeatRows=1, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCD8D2")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO]), ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabela


def _selecionar_colunas(dataframe: pd.DataFrame, especificacao: list[tuple[str, tuple[str, ...]]]) -> pd.DataFrame:
    """Seleciona e ordena campos semanticamente, sem depender da posição no CSV."""
    if dataframe.empty:
        return dataframe
    selecionadas: dict[str, pd.Series] = {}
    for rotulo, termos in especificacao:
        coluna = _achar_coluna(dataframe, *termos)
        if coluna and coluna not in selecionadas:
            selecionadas[rotulo] = dataframe[coluna]
    return pd.DataFrame(selecionadas, index=dataframe.index)


def _rodape(canvas, documento) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7E3DD"))
    canvas.line(15 * mm, 13 * mm, landscape(A4)[0] - 15 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA)
    canvas.drawString(15 * mm, 8 * mm, "CatAiLab - Relatório científico de triagem virtual")
    canvas.drawRightString(landscape(A4)[0] - 15 * mm, 8 * mm, f"Página {documento.page}")
    canvas.restoreState()


def _figuras(figuras_df: pd.DataFrame, pasta: Path) -> list[Path]:
    coluna = _achar_coluna(figuras_df, "arquivo", "png")
    if not coluna:
        return []
    encontrados = []
    for valor in figuras_df[coluna].dropna().astype(str):
        caminho = Path(valor)
        if not caminho.is_absolute() or not caminho.exists():
            caminho = pasta / caminho.name
        if caminho.exists():
            encontrados.append(caminho)
    return encontrados


def _tabelas_figuras(caminhos: list[Path]) -> list[Table | Spacer]:
    """Distribui todas as figuras disponíveis em linhas de até três itens."""
    blocos: list[Table | Spacer] = []
    for inicio in range(0, len(caminhos), 3):
        grupo = caminhos[inicio:inicio + 3]
        blocos.append(Table(
            [[Image(str(caminho), width=82 * mm, height=60 * mm, kind="proportional") for caminho in grupo]],
            colWidths=[88 * mm] * len(grupo), hAlign="LEFT",
        ))
        blocos.append(Spacer(1, 4 * mm))
    return blocos


def _secao_sintese(estilos, sintese_pdf: pd.DataFrame, plano: dict | None) -> list:
    """Descreve a rota e, somente após confirmação, o balanço de um lote de 100 g."""
    etapas = ["Definir composição<br/>e suporte", "Pesar suporte<br/>e precursores", "Preparar solução<br/>e formar sólido", "Secar e<br/>calcinar", "Ativar e<br/>caracterizar"]
    celulas = []
    for indice, etapa in enumerate(etapas):
        if indice:
            celulas.append(Paragraph("&gt;", estilos["BodyText"]))
        celulas.append(Paragraph(f"<b>{indice + 1}. {etapa}</b>", estilos["TableText"]))
    fluxo = Table([celulas], colWidths=[47 * mm if i % 2 == 0 else 8 * mm for i in range(9)], hAlign="LEFT")
    fluxo.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FUNDO), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    blocos = [Paragraph("7. Plano de síntese e balanço de materiais", estilos["Section"]), fluxo, Spacer(1, 3 * mm)]
    if plano is None:
        blocos.extend([
            Paragraph("<b>Lote de referência:</b> 100 g de catalisador final = suporte + fase ativa + promotor. A fórmula do candidato é uma razão atômica, não uma carga mássica. Selecione um suporte e confirme cargas, precursores, pureza e recuperação na aba Síntese; então use 'Atualizar PDF com esta receita'.", estilos["Callout"]),
            _tabela(sintese_pdf, estilos, 5, 7),
        ])
        return blocos
    linhas = plano["materiais"]
    dados = pd.DataFrame([{
        "Função": linha["Função"], "Material / elemento": linha["Elemento"],
        "Fase final (g)": f'{linha["Massa da fase final (g)"]:.3f}',
        "Reagente / precursor": linha["Precursor"],
        "Pesar (g)": "não definido" if pd.isna(linha["Massa corrigida a pesar (g)"]) else f'{linha["Massa corrigida a pesar (g)"]:.3f}',
    } for linha in linhas])
    blocos.extend([
        Paragraph(f"<b>Candidato:</b> {_texto(plano['formula'])} | <b>Suporte escolhido:</b> {_texto(plano['suporte'])} | <b>Rota:</b> {_texto(plano['rota'])} | <b>Base das cargas:</b> {_texto(plano['base_carga'])}", estilos["BodyText"]),
        Paragraph(f"<b>Balanço final de 100 g:</b> suporte {plano['massa_suporte']:.3f} g + fase ativa {plano['massa_ativa']:.3f} g + promotor {plano['massa_promotor']:.3f} g. Os valores a pesar consideram pureza de {plano['pureza']:.1f}% e recuperação estimada de {plano['recuperacao']:.1f}%.", estilos["Callout"]),
        _tabela(dados, estilos, len(dados), 5), Spacer(1, 3 * mm),
        Paragraph(f"<b>Variáveis da preparação:</b> volume de poros {plano['volume_poroso']:.2f} cm³/g; preenchimento {plano['preenchimento']:.1f}%; solução inicial {_texto(plano['volume_solucao'])}; secagem {plano['temperatura_secagem']:.0f} °C; calcinação {plano['temperatura_calcinacao']:.0f} °C; perda prevista do suporte {plano['perda_suporte']:.1f}%; limite de concentração {plano['limite_molaridade']:.2f} mol/L. Confirmar experimentalmente pH, solvente, tempo, rampa, atmosfera, solubilidade e condições de ativação.", estilos["BodyText"]),
        Paragraph("Massas nominais, não protocolo validado. A massa dos sais inclui contraíons e água de hidratação que não integram necessariamente o catalisador final. Conferir hidratação e pureza no certificado, resíduo por TGA/DSC, balanço após tratamento e teor por ICP-OES/XRF. Precursor não definido impede uma massa a pesar confiável.", estilos["Callout"]),
    ])
    return blocos


def gerar_relatorio_cientifico_pdf(paths: dict[str, Path], reacao: str, metais: list[str], promotor: str, plano_sintese: dict | None = None) -> Path:
    """Cria o PDF com as seções solicitadas e sem referências bibliográficas."""
    destino = paths["pdf"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    ranking, prioritarios = _ler_csv(paths["ranking"]), _ler_csv(paths["prioritarios"])
    metricas, monte_carlo = _ler_csv(paths["metricas"]), _ler_csv(paths["monte_carlo"])
    dominio, figuras_df = _ler_csv(paths["dominio"]), _ler_csv(paths["figuras"])
    resumo = json.loads(paths["resumo"].read_text(encoding="utf-8-sig")) if paths["resumo"].exists() else {}
    instante = datetime.fromtimestamp(paths["resumo"].stat().st_mtime) if paths["resumo"].exists() else datetime.now()
    hash_execucao = hashlib.sha256(paths["resumo"].read_bytes()).hexdigest() if paths["resumo"].exists() else "indisponivel"

    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name="TitleCenter", parent=estilos["Title"], textColor=AZUL, alignment=TA_CENTER, fontSize=22, leading=27, spaceAfter=8))
    estilos.add(ParagraphStyle(name="Subtitle", parent=estilos["BodyText"], textColor=CINZA, alignment=TA_CENTER, fontSize=10, leading=14, spaceAfter=14))
    estilos.add(ParagraphStyle(name="Section", parent=estilos["Heading2"], textColor=AZUL, fontSize=14, leading=18, spaceBefore=8, spaceAfter=7))
    estilos.add(ParagraphStyle(name="Callout", parent=estilos["BodyText"], backColor=FUNDO, borderColor=VERDE, borderWidth=.6, borderPadding=7, textColor=colors.HexColor("#273D4B"), fontSize=9, leading=13, spaceAfter=8))
    estilos.add(ParagraphStyle(name="TableText", parent=estilos["BodyText"], fontSize=6.6, leading=8.3, textColor=colors.HexColor("#263B58")))
    estilos.add(ParagraphStyle(name="TableHeader", parent=estilos["TableText"], textColor=colors.white))
    estilos["BodyText"].fontSize, estilos["BodyText"].leading = 9, 13
    doc = SimpleDocTemplate(str(destino), pagesize=landscape(A4), rightMargin=15 * mm, leftMargin=15 * mm, topMargin=14 * mm, bottomMargin=18 * mm, title="Relatório científico CatAiLab", author="CatAiLab")

    ranking_pdf = _selecionar_colunas(ranking, [
        ("Fórmula", ("formula",)), ("Score final", ("score", "final")),
        ("Classe interna", ("classe", "indice", "interno")),
        ("Top 5 MC", ("probabilidade", "top", "5")),
        ("Desvio MC", ("desvio", "monte", "carlo")),
        ("Domínio", ("classe", "dominio")), ("Estabilidade", ("estabilidade", "termodinamica")),
        ("Suporte", ("suporte", "sugerido")),
    ])
    justificativa_pdf = _selecionar_colunas(prioritarios, [
        ("Fórmula", ("formula",)), ("Score final", ("score", "final")),
        ("Atividade", ("score", "atividade")), ("Seletividade", ("score", "seletividade")),
        ("Estabilidade", ("score", "estabilidade")), ("DFT/proxy", ("score", "dft")),
        ("Índice interno", ("indice", "evidencia", "interno")),
        ("Classe interna", ("classe", "indice", "interno")),
    ])
    sintese_pdf = _selecionar_colunas(prioritarios, [
        ("Fórmula", ("formula",)), ("Suporte", ("suporte", "sugerido")),
        ("Rota", ("rota", "sintese")), ("Pré-tratamento", ("pre", "tratamento")),
        ("Observação", ("observacao", "sintese")), ("Status da formulação", ("formulacao", "status")),
        ("Validação experimental", ("validacao", "experimental")),
    ])

    elementos = [Spacer(1, 8 * mm), Paragraph("Relatório científico de triagem virtual", estilos["TitleCenter"]),
        Paragraph(f"CatAiLab | {_texto(reacao).upper()} | {instante:%d/%m/%Y %H:%M}", estilos["Subtitle"]),
        Paragraph("Este documento registra uma triagem computacional. Previsões, proxies e heurísticas não constituem confirmação experimental nem resultado de DFT, salvo quando o campo estiver explicitamente identificado dessa forma.", estilos["Callout"]),
        Paragraph("1. Configuração da triagem", estilos["Section"]),
        Paragraph(f"<b>Reação:</b> {_texto(reacao)}<br/><b>Metais ativos:</b> {_texto(', '.join(metais))}<br/><b>Promotor:</b> {_texto(promotor or 'sem promotor')}<br/><b>Candidatos gerados:</b> {_texto(resumo.get('n_candidatos_gerados', resumo.get('candidatos_gerados', resumo.get('numero_candidatos_gerados', '-'))))}", estilos["BodyText"]),
        Paragraph("2. Metodologia e natureza dos dados", estilos["Section"]),
        Paragraph("A plataforma combina geração de composições, filtros químicos, descritores, modelos proxy, análise multicritério, Monte Carlo, domínio de aplicabilidade e viabilidade inicial de síntese. Cada resultado deve ser interpretado conforme sua origem declarada: experimental, DFT, previsão de modelo, proxy ou heurística.", estilos["BodyText"]), Spacer(1, 3 * mm), _tabela(metricas, estilos, 12, 4), PageBreak(),
        Paragraph("3. Ranking dos candidatos", estilos["Section"]), _tabela(ranking_pdf, estilos, 15, 8),
        Paragraph("4. Justificativa da pontuação", estilos["Section"]),
        Paragraph("A posição resulta da combinação de atividade, seletividade, estabilidade, robustez, incerteza e viabilidade. Uma boa posição indica prioridade computacional para validação; não comprova desempenho catalítico.", estilos["BodyText"]), Spacer(1, 3 * mm), _tabela(justificativa_pdf, estilos, 5, 8), PageBreak(),
        Paragraph("5. Gráficos e tabelas da execução", estilos["Section"])]

    imagens = _figuras(figuras_df, destino.parent)
    if imagens:
        elementos.extend(_tabelas_figuras(imagens))
    else:
        elementos.append(Paragraph("As figuras não estavam disponíveis para incorporação; as tabelas numéricas permanecem registradas.", estilos["Callout"]))
    elementos.extend([Spacer(1, 4 * mm), _tabela(monte_carlo, estilos, 10, 7), PageBreak(), Paragraph("6. Detalhamento dos candidatos prioritários", estilos["Section"])])
    if prioritarios.empty:
        elementos.append(Paragraph("Nenhum candidato prioritário foi registrado.", estilos["BodyText"]))
    else:
        for indice, (_, linha) in enumerate(prioritarios.head(5).iterrows(), 1):
            formula, suporte = _valor(linha, [("formula",), ("candidato",)]), _valor(linha, [("suporte",)])
            score = _valor(linha, [("score", "final"), ("pontuacao",)])
            classe = _valor(linha, [("classe", "indice", "interno")])
            validacao = _valor(linha, [("validacao", "experimental")])
            elementos.append(KeepTogether([Paragraph(f"<b>{indice}. {formula}</b>", estilos["Heading3"]), Paragraph(f"Suporte sugerido: {suporte} | Score: {score} | Classe interna não calibrada: {classe} | Validação experimental: {validacao}", estilos["BodyText"]), Spacer(1, 2 * mm)]))
    elementos.extend(_secao_sintese(estilos, sintese_pdf, plano_sintese))
    elementos.extend([PageBreak(),
        Paragraph("8. Incertezas, alertas e limitações", estilos["Section"]),
        Paragraph("Priorize candidatos com menor dispersão Monte Carlo e dentro do domínio. Elementos radioativos, sintéticos ou de toxicidade elevada exigem avaliação específica. A triagem não substitui caracterização estrutural, balanço de massa, conversão, seletividade, estabilidade temporal, DFT dedicado ou validação experimental.", estilos["Callout"]), _tabela(dominio, estilos, 12, 7),
        Paragraph("Apêndice de reprodutibilidade", estilos["Section"]),
        Paragraph(f"<b>Versão do painel:</b> CatAiLab 1.0<br/><b>Semente aleatória:</b> 42<br/><b>Data do snapshot:</b> {instante:%d/%m/%Y %H:%M:%S}<br/><b>Prefixo dos arquivos:</b> {_texto(resumo.get('prefixo_arquivos', destino.stem.replace('_relatorio_cientifico', '')))}<br/><b>Hash SHA-256 da configuração:</b> {hash_execucao}<br/><b>Formato:</b> PDF", estilos["BodyText"])])
    doc.build(elementos, onFirstPage=_rodape, onLaterPages=_rodape)
    return destino
