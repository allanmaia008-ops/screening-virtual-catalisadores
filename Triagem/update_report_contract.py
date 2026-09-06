"""Synchronize export contract into generator and existing notebook without regeneration."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
contract = (ROOT / "report_contract.py").read_text(encoding="utf-8")
hierarchical = (ROOT / "hierarchical_score_code.py").read_text(encoding="utf-8")


def update(source):
    source = source.replace('prefixo = f"disciplina_fluxo_{reacao}"', 'prefixo = output_prefix(reacao, metais_usuario, promotor_usuario)')
    source = source.replace('FIGURE_DIR / f"{nome_base}.png"', 'FIGURE_DIR / f"{prefixo}_{nome_base}.png"')
    source = source.replace('FIGURE_DIR / f"{nome_base}.pdf"', 'FIGURE_DIR / f"{prefixo}_{nome_base}.pdf"')
    source = source.replace('return df.rename(columns={col: nomes_colunas_pt.get(col, col) for col in df.columns})', 'df = audited_export(df, reacao)\n    labels = {**nomes_colunas_pt, **EXPORT_LABELS}\n    return df.rename(columns={col: labels.get(col, col) for col in df.columns})')
    if '{REPORT_NOTICE}' not in source:
        source = source.replace('{cartoes_html}\n', '{cartoes_html}\n{REPORT_NOTICE}\n')
    source = source.replace('"reacao": reacao,\n    "perfil": perfil["nome"],', '"prefixo_arquivos": prefixo,\n    "reacao": reacao,\n    "perfil": perfil["nome"],')
    if 'alternativas_formulacao_df = support_alternatives' not in source:
        source = source.replace('# Salva o ranking completo catalisador-condição.', 'alternativas_formulacao_df = support_alternatives(melhor_por_candidato_df)\nalternativas_formulacao_df.to_csv(OUTPUT_DIR / f"{prefixo}_alternativas_formulacao.csv", index=False, encoding="utf-8-sig")\n\n# Salva o ranking completo catalisador-condição.')
        source = source.replace('{REPORT_NOTICE}\n', '{REPORT_NOTICE}\n<h2>Alternativas de formulação: suporte e cargas a definir</h2>\n{tabela_html(alternativas_formulacao_df, linhas=len(alternativas_formulacao_df))}\n')
    if 'score_hierarquico_comparativo.csv' not in source:
        source = source.replace('# Salva o ranking completo catalisador-condição.', 'traduzir_colunas(score_hierarquico_comparativo_df).to_csv(OUTPUT_DIR / f"{prefixo}_score_hierarquico_comparativo.csv", index=False, encoding="utf-8-sig")\n\n# Salva o ranking completo catalisador-condição.')
        source = source.replace('<h2>Top 2 candidatos recomendados</h2>', '<h2>Comparação: score vigente e score hierárquico proposto</h2>\n{tabela_html(score_hierarquico_comparativo_df, linhas=10)}\n<h2>Top 2 candidatos recomendados pelo ranking vigente</h2>')
        source = source.replace('"prefixo_arquivos": prefixo,', '"prefixo_arquivos": prefixo,\n    "arquivo_score_hierarquico_comparativo": str(OUTPUT_DIR / f"{prefixo}_score_hierarquico_comparativo.csv"),\n    "score_hierarquico_status": "proposta técnico-heurística sem calibração experimental; ranking vigente preservado",')
    if 'sheet_name="Score_hierarquico"' not in source:
        source = source.replace('with pd.ExcelWriter(OUTPUT_DIR / f"{prefixo}_resultados.xlsx", engine="openpyxl") as writer:', 'with pd.ExcelWriter(OUTPUT_DIR / f"{prefixo}_resultados.xlsx", engine="openpyxl") as writer:\n    traduzir_colunas(score_hierarquico_comparativo_df).to_excel(writer, sheet_name="Score_hierarquico", index=False)')
    metadata = ('    "prefixo_arquivos": prefixo,\n'
        '    "arquivo_score_hierarquico_comparativo": str(OUTPUT_DIR / f"{prefixo}_score_hierarquico_comparativo.csv"),\n'
        '    "score_hierarquico_status": "proposta técnico-heurística sem calibração experimental; ranking vigente preservado",\n')
    repeated = re.compile(r'(?:' + re.escape(metadata) + r'){2,}')
    return repeated.sub(metadata, source)


path = ROOT / "make_notebook_fluxo_proposto_disciplina.py"
source = update(path.read_text(encoding="utf-8"))
# Embed instead of requiring a local import when users run the notebook elsewhere.
if 'contract_position = next(' not in source:
    source = source.replace('nbf.write(nb, NOTEBOOK)', 'contract_position = next(i for i, cell in enumerate(nb.cells) if "prefixo = output_prefix" in cell.source)\nnb.cells.insert(contract_position, code((SCRIPT_DIR / "report_contract.py").read_text(encoding="utf-8")))\nnbf.write(nb, NOTEBOOK)')
path.write_text(source, encoding="utf-8")
path = ROOT / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"
nb = json.loads(path.read_text(encoding="utf-8"))
for cell in nb["cells"]:
    text = "".join(cell["source"])
    cell["source"] = (contract if 'def audited_export(' in text else update(text)).splitlines(keepends=True)
if not any('def audited_export(' in ''.join(c['source']) for c in nb['cells']):
    # Place after setup/import cells, before the first figure/export prefix is evaluated.
    position = next(i for i,c in enumerate(nb['cells']) if 'prefixo = output_prefix' in ''.join(c['source']))
    nb['cells'].insert(position, {"cell_type":"code", "execution_count":None, "metadata":{}, "outputs":[], "source":contract.splitlines(keepends=True), "id":"report-evidence-contract"})
if not any('def calcular_score_hierarquico(' in ''.join(c['source']) for c in nb['cells']):
    position = next(i for i,c in enumerate(nb['cells']) if 'prefixo = output_prefix' in ''.join(c['source']))
    nb['cells'].insert(position, {"cell_type":"code", "execution_count":None, "metadata":{}, "outputs":[], "source":hierarchical.splitlines(keepends=True), "id":"hierarchical-score-proposal"})
path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding="utf-8")
