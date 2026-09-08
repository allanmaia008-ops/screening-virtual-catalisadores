"""Dedicated FT results so unrelated reaction models cannot be used silently."""
from pathlib import Path
from uuid import uuid4
import streamlit as st
import plotly.express as px
from asf import distribution
from ltft import run
from ltft_cards import recommendations_html
from ltft_panels import candidates_view, chemistry_view
from ltft_synthesis import render_synthesis


def render(metals, promoter, output_dir, execute, configured):
    st.subheader('Fischer–Tropsch de baixa temperatura | C₅₊')
    st.caption('Triagem heurística. α e fase ativa são estimativas não calibradas. ASF descreve carbono nos hidrocarbonetos; não prevê conversão de CO.')
    a,b,c = st.columns(3)
    temperature = a.slider('Temperatura (°C)', 200, 250, 225, key='ltft_T')
    pressure = b.slider('Pressão (bar)', 10, 30, 20, key='ltft_P')
    ratio = c.slider('Razão H₂/CO (mol/mol)', 1.5, 2.2, 2.0, .05, key='ltft_ratio')
    manual = st.checkbox('Informar α para comparar cenários', key='ltft_manual')
    alpha = st.number_input('α informado', min_value=0.0, max_value=.999, value=.85, step=.01, key='ltft_alpha') if manual else None
    signature = (tuple(metals), promoter, temperature, pressure, ratio, alpha, str(output_dir))
    if execute:
        st.session_state.pop('ltft_result', None)
        if not configured:
            st.error('Complete a seleção de metais e de promotor na barra lateral.')
        else:
            try:
                with st.spinner('Gerando formulações, descritores Magpie e distribuição ASF...'):
                    result = run(metals, promoter, Path(output_dir)/('ltft_'+uuid4().hex), temperature, pressure, ratio, alpha_override=alpha)
                st.session_state['ltft_result'] = (signature, result)
            except Exception as exc:
                st.error('Falha na triagem LTFT: '+str(exc))
    stored = st.session_state.get('ltft_result')
    if not stored or stored[0] != signature:
        st.info('Defina as condições e execute a triagem. Alterações exigem uma nova execução.')
        return
    result = stored[1]
    tables = result['tables']
    metrics = st.columns(4)
    for col, key, title in zip(metrics, ['gerados','selecionados_100','refinados_10','prioritarios_2'], ['Gerados','Selecionados','Refinados','Prioritários']):
        col.metric(title, len(tables[key]))
    tabs = st.tabs(['Catalisadores recomendados', 'Candidatos', 'Distribuição ASF', 'Química', 'Síntese', 'Arquivos'])
    with tabs[0]:
        st.markdown(recommendations_html(tables['prioritarios_2']), unsafe_allow_html=True)
    with tabs[1]:
        candidates_view(result)
    with tabs[2]:
        ids = tables['refinados_10']['candidate_id'].tolist()
        selected = st.selectbox('Candidato', ids)
        row = tables['refinados_10'].set_index('candidate_id').loc[selected]
        data = tables['distribuicao_ASF'].query('candidate_id == @selected').copy()
        data['Carbono (%)'] = 100*data['fraction']
        fig = px.bar(data, x='carbon_number', y='Carbono (%)', labels={'carbon_number':'Número de carbonos'}, color_discrete_sequence=['#16805c'])
        st.plotly_chart(fig, width='stretch')
        st.caption(f"Cauda C₆₁₊: {100*distribution(float(row['alpha']))['tail_fraction']:.6f}% do carbono. C₅₊ é subtotal.")
        groups = tables['grupos_produtos'].query('candidate_id == @selected')
        st.plotly_chart(px.bar(groups, x='group', y='carbon_pct',
            labels={'group':'Faixa de produtos', 'carbon_pct':'Carbono nos hidrocarbonetos (%)'},
            color_discrete_sequence=['#16805c']), width='stretch')
        st.caption(result['metadata']['product_basis'])
        st.write(f"Fechamento das cinco faixas: {groups['carbon_pct'].sum():.8f}%. Inclui a cauda infinita C₂₁₊.")
    with tabs[3]:
        chemistry_view(result)
    with tabs[4]:
        render_synthesis(result)
    with tabs[5]:
        for path in sorted(Path(result['output']).iterdir()):
            if path.is_file():
                st.download_button(path.name, path.read_bytes(), file_name=path.name, key='ltft_download_'+path.name)
