"""Recommendation cards with LTFT-specific evidence and existing visual assets."""
import base64
import html
import math
import re
from pathlib import Path


STYLE = """<style>
.ltft-recommendations{font-family:Arial,sans-serif;color:#17263e;letter-spacing:0}
.ltft-recommendations h3{text-align:center;font-size:1.3rem!important;margin:12px 0 6px!important}
.ltft-lead{text-align:center;color:#536378;margin:0 0 20px;font-size:1rem}
.ltft-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
.ltft-card{min-width:0;background:#fff;border:1px solid #cbd9d3;border-left:4px solid var(--accent);border-radius:8px;overflow:hidden;box-shadow:0 4px 14px #14213d0a}
.ltft-card header{display:flex;align-items:center;gap:12px;padding:20px}
.ltft-rank{display:grid;place-items:center;flex:0 0 36px;height:36px;border-radius:50%;background:var(--accent);color:#fff;font-weight:700;font-size:1.2rem}
.ltft-card h4{font-size:1.02rem!important;line-height:1.4;margin:0!important;color:#17263e!important;overflow-wrap:anywhere}
.ltft-id{display:block;color:#657489;font-size:.8rem;margin-top:3px;font-weight:400}
.ltft-dot{margin-left:auto;flex:0 0 12px;height:12px;border-radius:50%;background:var(--accent)}
.ltft-visual{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:16px;padding:0 20px 18px}
.ltft-visual figure{margin:0;min-width:0;text-align:center;background:#f8fafb;border-radius:6px;padding:8px}
.ltft-visual img{display:block;width:100%;height:155px;object-fit:contain;mix-blend-mode:multiply}
.ltft-visual figcaption{font-size:.94rem;font-weight:700;overflow-wrap:anywhere;color:#243651}
.ltft-schematic{display:block;font-size:.75rem;font-weight:400;color:#667587;margin-top:5px}
.ltft-score{display:flex;flex-direction:column;justify-content:center;min-width:0;border-left:1px solid #e1e8e4;padding-left:16px}
.ltft-score span{font-size:.94rem;color:#536378}.ltft-score strong{color:var(--accent);font-size:1.8rem;line-height:1.35;margin:5px 0}
.ltft-score small{font-size:.83rem;font-weight:400;color:#536378}.ltft-score hr{width:100%;border:0;border-top:1px solid #e1e8e4;margin:10px 0}
.ltft-facts{margin:0 20px;padding:0}.ltft-fact{display:grid;grid-template-columns:minmax(110px,.8fr) minmax(0,1.2fr);gap:12px;padding:12px 0;border-top:1px solid #e3ebe6;font-size:.95rem;line-height:1.45}
.ltft-fact dt{font-weight:700;color:#233950}.ltft-fact dd{margin:0;overflow-wrap:anywhere;color:#46586d}
.ltft-details{padding:0 20px}.ltft-details section{padding:14px 0;border-top:1px solid #e3ebe6}
.ltft-details b{font-size:.96rem;color:#196641}.ltft-details p{font-size:.94rem;line-height:1.55;color:#46586d;margin:7px 0 0;overflow-wrap:anywhere}
.ltft-caution{margin:4px 20px 20px;padding:12px;background:#fff7e8;border-left:3px solid #dbac46;font-size:.9rem;line-height:1.5;color:#674d1c}
@media(max-width:1000px){.ltft-cards{grid-template-columns:1fr}}
@media(max-width:480px){.ltft-visual{grid-template-columns:1fr}.ltft-score{border-left:0;border-top:1px solid #e1e8e4;padding:12px 0 0}.ltft-fact{grid-template-columns:1fr;gap:5px}.ltft-card header{padding:16px}.ltft-visual{padding-inline:16px}}
</style>"""


def chemical(value):
    escaped = html.escape(str(value))
    return re.sub(r'(?<=[A-Za-z)])(\d+(?:\.\d+)?)', r'<sub>\1</sub>', escaped)


def number(value, decimals=2):
    try:
        value = float(value)
        return f'{value:.{decimals}f}'.replace('.', ',') if math.isfinite(value) else 'Não calculado'
    except (TypeError, ValueError):
        return 'Não calculado'


def recommendations_html(frame):
    cards = []
    for rank, (_, row) in enumerate(frame.head(2).iterrows(), 1):
        def text(key, default='Não informado'):
            value = row.get(key)
            return html.escape(str(value)) if value is not None and str(value) not in ('', 'nan') else default
        path = Path(__file__).with_name('assets') / f'estrutura_catalitica_padrao_{rank}.png'
        picture = ''
        if path.is_file():
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
            picture = f'<img src="data:image/png;base64,{encoded}" alt="Ilustração esquemática de um catalisador suportado; não representa estrutura calculada">'
        formula = chemical(row.get('formula','Não informado'))
        support = chemical(row.get('support','Não informado'))
        promoter = chemical(row.get('promoter') or 'Sem promotor')
        facts = [
            ('Suporte da formulação', support),
            ('Suporte recomendado', chemical(row.get('recommended_support', row.get('support','Não informado')))),
            ('Promotor', promoter),
            ('Condições', f"{number(row.get('temperature_C'),0)} °C · {number(row.get('pressure_bar'),0)} bar · H₂/CO = {number(row.get('H2_CO'))}"),
            ('Cargas nominais', f"Metais: {number(row.get('metal_loading_wt_pct'),0)}% m/m; promotor: {number(row.get('promoter_loading_wt_pct'),0)}% m/m"),
            ('Fase ativa proposta', text('phase_hypothesis')),
            ('Crescimento de cadeia', f"α = {number(row.get('alpha'),3)} · {text('alpha_origin')}"),
        ]
        facts_html = ''.join(f'<div class="ltft-fact"><dt>{label}</dt><dd>{value}</dd></div>' for label,value in facts)
        accent = '#16843c' if rank == 1 else '#c58a00'
        cards.append(f'''<article class="ltft-card" style="--accent:{accent}">
<header><span class="ltft-rank">{rank}</span><h4>{text('family')}<span class="ltft-id">Candidato {text('candidate_id')}</span></h4><span class="ltft-dot" aria-hidden="true"></span></header>
<div class="ltft-visual"><figure>{picture}<figcaption>{formula} / {support}<span class="ltft-schematic">Ilustração, não estrutura calculada</span></figcaption></figure>
<div class="ltft-score"><span>Pontuação LTFT</span><strong>{number(row.get('score_LTFT'))} <small>/ 1,00</small></strong><small>Índice heurístico de priorização</small><hr><span>Fração C₅₊ (ASF)</span><strong>{number(row.get('C5plus_carbon_pct'),1)}%</strong><small>Do carbono nos hidrocarbonetos</small></div></div>
<dl class="ltft-facts">{facts_html}</dl><div class="ltft-details">
<section><b>Justificativa do suporte</b><p>{text('support_rationale')}</p></section>
<section><b>Rota de síntese e ativação</b><p>{text('synthesis_route')}</p></section>
<section><b>Química da reação</b><p>{text('wgs_status')}</p></section></div>
<div class="ltft-caution"><b>Ponto de atenção</b><br>{text('phase_warning')} O modelo não calcula conversão de CO, produtividade ou confiança experimental. As cargas são equivalentes elementares, não massas de sais precursores.</div></article>''')
    return STYLE + '<div class="ltft-recommendations"><h3>Principais recomendações</h3><p class="ltft-lead">Triagem virtual orientada por IA para sua reação</p><div class="ltft-cards">' + ''.join(cards) + '</div></div>'
