"""LTFT views using the dashboard's restrained green scientific layout."""
import base64
import html
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ltft_cards import chemical, number


STYLE = """<style>
.ft-title{text-align:center;color:#17263e;font-size:1.45rem;font-weight:750;margin:18px 0}
.ft-podium{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;align-items:end;margin:18px 0 24px}
.ft-place{min-width:0;border:1px solid #d3ddd8;border-bottom:6px solid var(--medal);border-radius:8px;background:white;padding:16px;text-align:center;color:#243651}
.ft-place.winner{padding-top:30px}.ft-place b{display:block;font-size:1rem;overflow-wrap:anywhere}.ft-place small{display:block;color:#637285;font-size:.82rem;margin:6px 0;overflow-wrap:anywhere}
.ft-medal{display:grid;place-items:center;width:32px;height:32px;background:var(--medal);border-radius:50%;color:#fff;font-weight:800}
.ft-place img{width:100%;height:128px;object-fit:contain}.ft-place strong{display:block;color:#087a46;font-size:1.55rem;margin-top:5px}
.ft-scroll{overflow-x:auto;border:1px solid #dbe4df;border-radius:8px}
.ft-table{width:100%;border-collapse:collapse;color:#283b52;font-size:.94rem}.ft-table th{background:#f3f8f5;color:#173b2b;font-weight:700}.ft-table th,.ft-table td{padding:12px 10px;text-align:center;border-bottom:1px solid #e4ebe7;vertical-align:middle}.ft-table td{overflow-wrap:anywhere}.ft-table tbody tr:nth-child(even){background:#fbfdfc}.ft-table td.score{color:#146ac0;font-weight:750}.ft-table small{display:block;font-size:.76rem;color:#69778a;margin-top:5px}
.ft-badge{display:inline-block;padding:4px 8px;border:1px solid #ddc080;border-radius:5px;color:#805b14;font-size:.82rem;background:#fffaf0}
.ft-profile{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:20px;align-items:center;margin:12px 0 22px;color:#33465a}
.ft-profile h4{font-size:1.05rem!important;color:#17412d!important;margin:12px 0 5px!important}.ft-profile p{font-size:.98rem;line-height:1.55;margin:0 0 14px;overflow-wrap:anywhere}
.ft-profile figure{margin:0;text-align:center}.ft-profile img{width:100%;height:210px;object-fit:contain}.ft-profile figcaption{font-size:.92rem;font-weight:700;overflow-wrap:anywhere}.ft-profile small{display:block;color:#637285;font-size:.8rem;margin-top:6px}
.ft-supports{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0}.ft-support{border:1px solid #d4e1d9;border-radius:8px;padding:16px;background:white;color:#364c60;text-align:center;min-width:0}.ft-support.best{border:2px solid #16843c}.ft-support h4{color:#126d40!important;font-size:1.05rem!important;margin:6px 0!important}.ft-support p{font-size:.92rem;margin:8px 0;line-height:1.5}.ft-support strong{display:block;color:#126d40;font-size:1.35rem}.ft-support small{display:block;color:#64748b;font-size:.81rem}
@media(max-width:850px){.ft-podium,.ft-profile{grid-template-columns:1fr}.ft-place.winner{padding-top:16px}.ft-podium .winner{order:-1}.ft-supports{grid-template-columns:1fr}}
</style>"""


def picture(index):
    path = Path(__file__).with_name('assets') / f'estrutura_catalitica_padrao_{index % 5 + 1}.png'
    if not path.is_file():
        return ''
    return '<img alt="Ilustração esquemática, não estrutura calculada" src="data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii') + '">'


def podium_html(top):
    entries = []
    for index in ([1,0,2] if len(top) >= 3 else range(len(top))):
        row = top.iloc[index]
        color = ['#c39219','#8a949d','#af693f'][index]
        entries.append(f'<article class="ft-place {"winner" if index == 0 else ""}" style="--medal:{color}"><span class="ft-medal">{index+1}</span>{picture(index)}<b>{chemical(row.formula)} / {chemical(row.support)}</b><small>{html.escape(str(row.candidate_id))}</small><small>Pontuação LTFT</small><strong>{number(row.score_LTFT,3)}</strong></article>')
    return '<div class="ft-podium">'+''.join(entries)+'</div>'


def table_html(top):
    rows = []
    for position, (_, row) in enumerate(top.head(10).iterrows(),1):
        rows.append(f'<tr><td>{position}</td><td>{chemical(row.formula)}<small>{html.escape(str(row.candidate_id))}</small></td><td>{chemical(row.support)}</td><td>{chemical(row.promoter or "Sem promotor")}</td><td class="score">{number(row.score_LTFT,3)}</td><td>{number(row.alpha,3)}</td><td>{number(row.C5plus_carbon_pct,1)}%</td><td><span class="ft-badge">Não calibrado</span></td></tr>')
    headers = ['#','Fórmula atômica','Suporte da formulação','Promotor','Pontuação (0–1)','α','C₅₊ (% carbono)','Evidência']
    return '<div class="ft-scroll"><table class="ft-table"><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def candidates_view(result):
    top = result['tables']['refinados_10']
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('<div class="ft-title">Candidatos prioritários para síntese</div>', unsafe_allow_html=True)
    st.markdown(podium_html(top), unsafe_allow_html=True)
    st.caption('Ilustrações esquemáticas. A ordem representa priorização heurística, não validação experimental.')
    table, weights = st.columns([3,1])
    with table:
        st.markdown(table_html(top), unsafe_allow_html=True)
    with weights:
        st.markdown('#### Composição da pontuação')
        labels = {'activity':'Atividade', 'C5plus':'Fração C₅₊', 'growth':'Crescimento de cadeia',
                  'phase':'Fase ativa', 'stability':'Índice de suporte', 'operation':'Condição operacional'}
        fig = go.Figure(go.Pie(labels=[labels[k] for k in result['metadata']['weights']],
            values=list(result['metadata']['weights'].values()), hole=.65,
            marker_colors=['#146ac0','#16843c','#53a7c6','#91bf66','#e2b345','#ad82b2']))
        fig.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation='h',y=-.1), font=dict(size=13))
        st.plotly_chart(fig, width='stretch')
        st.caption('Pesos da soma bruta. A pontuação final também desconta as penalidades declaradas; não é probabilidade.')
    with st.expander('Detalhamento dos candidatos e componentes da pontuação'):
        st.dataframe(top, hide_index=True, width='stretch')
    st.caption('Os selecionados passaram por priorização composicional; estabilidade termodinâmica e viabilidade de síntese não estão comprovadas.')


def chemistry_view(result):
    tables = result['tables']
    top = tables['refinados_10'].set_index('candidate_id')
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('<div class="ft-title">Química do catalisador e distribuição de produtos</div>', unsafe_allow_html=True)
    selected = st.selectbox('Candidato para análise de α e suporte', top.index.tolist(),
        format_func=lambda key:f'{top.loc[key,"formula"]} / {top.loc[key,"support"]} · {key}')
    row = top.loc[selected]
    def safe(key): return html.escape(str(row.get(key,'Não informado')))
    st.markdown(f'<div class="ft-profile"><div><h4>Fase ativa e ativação</h4><p>{safe("phase_hypothesis")}<br>{safe("activation")}</p><h4>Química da reação</h4><p>{safe("wgs_status")}</p><h4>Ponto de atenção</h4><p>{safe("phase_warning")}</p></div><figure>{picture(top.index.tolist().index(selected))}<figcaption>{chemical(row.formula)} / {chemical(row.support)}</figcaption><small>Representação ilustrativa, sem inferência de estrutura atômica</small></figure></div>', unsafe_allow_html=True)
    st.markdown('#### Racional do suporte')
    comparison = tables['comparacao_suportes'].query('candidate_id == @selected')
    cards = []
    for _, support in comparison.head(3).iterrows():
        rank = int(support.recommendation_rank)
        cards.append(f'<article class="ft-support {"best" if rank == 1 else ""}"><small>{"Recomendação heurística" if rank == 1 else "Alternativa " + str(rank)}</small><h4>{chemical(support.support)}</h4><p>Índice de suporte: {number(support.support_index)}<br>α: {number(support.alpha,3)}</p><small>Pontuação no cenário</small><strong>{number(support.score_LTFT,3)}</strong><p>Diferença para o primeiro: {number(support.score_delta_to_best,4)}</p><small>{"Suporte da formulação atual" if support.selected_formulation else "Cenário alternativo; formulação original preservada"}</small></article>')
    st.markdown('<div class="ft-supports">'+''.join(cards)+'</div>', unsafe_allow_html=True)
    st.caption(result['metadata']['support_limits'])
    with st.expander('Comparação completa dos cinco suportes'):
        st.dataframe(comparison, hide_index=True, width='stretch')
    sensitivity = tables['sensibilidade_alpha'].query('candidate_id == @selected')
    left, right = st.columns(2)
    with left:
        st.markdown('#### Sensibilidade de α')
        axis = st.selectbox('Parâmetro', sensitivity.parameter.unique().tolist())
        view = sensitivity[sensitivity.parameter == axis].copy()
        if axis != 'Promotor':
            view['value'] = view['value'].astype(float)
            fig = px.line(view,x='value',y='alpha',markers=True,labels={'value':axis,'alpha':'α'},color_discrete_sequence=['#16843c'])
        else:
            fig = px.bar(view,x='value',y='delta_alpha',labels={'value':axis,'delta_alpha':'Variação de α'},color_discrete_sequence=['#16843c'])
        fig.update_layout(height=350,margin=dict(l=20,r=20,t=10,b=30))
        st.plotly_chart(fig,width='stretch')
    with right:
        st.markdown('#### Formação do valor de α')
        keys = ['base','temperature','pressure','ratio','promoter','support','clipping_adjustment','manual_adjustment']
        fig = go.Figure(go.Waterfall(x=['Base','Temperatura','Pressão','H₂/CO','Promotor','Suporte','Limitação','Ajuste manual','α final'],
            y=[float(row['alpha_term_'+k]) for k in keys]+[0],measure=['absolute']+['relative']*7+['total'],
            increasing=dict(marker=dict(color='#16843c')),decreasing=dict(marker=dict(color='#c78929')),totals=dict(marker=dict(color='#146ac0'))))
        fig.update_layout(height=350,margin=dict(l=20,r=20,t=10,b=30),yaxis_title='α (adimensional)')
        st.plotly_chart(fig,width='stretch')
    st.caption(result['metadata']['sensitivity_limits'])
    with st.expander('Rota de síntese e registro técnico'):
        st.write(row.synthesis_route)
        st.write('Cargas em equivalentes elementares; massas de sais, pureza e hidratação exigem cálculo próprio.')
        st.json({key:float(row[key]) for key in row.index if key.startswith('alpha_term_')})
        st.json(result['metadata'])
