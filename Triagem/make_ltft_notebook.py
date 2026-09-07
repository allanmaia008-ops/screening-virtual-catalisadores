"""Build a self-contained LTFT notebook from the tested source modules."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent

def cell(kind, source):
    item = {'cell_type':kind, 'metadata':{}, 'source':source.splitlines(keepends=True)}
    if kind == 'code': item.update(execution_count=None, outputs=[])
    return item

asf = (root/'asf.py').read_text(encoding='utf-8')
contract = (root/'report_contract.py').read_text(encoding='utf-8')
ltft = (root/'ltft.py').read_text(encoding='utf-8').replace('from asf import distribution, tail_fraction\n','').replace('from report_contract import output_prefix\n','').replace('        from asf import validate_alpha\n','')
nb = {'nbformat':4, 'nbformat_minor':5, 'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}}, 'cells':[
    cell('markdown', '# Fischer–Tropsch LTFT\n\nTriagem heurística não calibrada. Requer numpy, pandas, openpyxl, matminer e pymatgen. Alpha pode ser estimado pelos priors auditáveis ou informado. Não calcula conversão de CO nem produtividade.\n'),
    cell('code', 'metais = ["Co", "Fe"]\npromotor = "K"\ntemperatura_C = 225\npressao_bar = 20\nrazao_H2_CO = 2.0\nalpha_informado = None\npasta_saida = "resultados_ltft"\n'),
    cell('code', asf), cell('code',contract), cell('code',ltft),
    cell('code','resultado = run(metais, promotor, pasta_saida, temperatura_C, pressao_bar, razao_H2_CO, alpha_override=alpha_informado)\ndisplay(resultado["tables"]["refinados_10"])\nprint(resultado["metadata"])\n')
]}
for i,c in enumerate(nb['cells']): c['id']=f'ltft-{i}'
(root/'notebook_fischer_tropsch_ltft.ipynb').write_text(json.dumps(nb, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
