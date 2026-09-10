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
from ltft_experimental import (BEZERRA_2010_REFERENCE, MELLO_2017_REFERENCE,
    PI012_REFERENCE, kinetic_readiness, mello_selectivity_table, observed_totals,
    thesis_evidence_readiness)


def render_experimental_anchor(result):
    """Show the institutional observation without presenting it as calibrated kinetics."""
    reference = PI012_REFERENCE
    st.markdown('### Âncora experimental LABPROBIO/NUPPRAR')
    st.info('Dado experimental publicado para uma condição específica. Não é uma lei cinética e não deve ser extrapolado para outros catalisadores ou condições.')
    cols = st.columns(4)
    cols[0].markdown(f"**Catalisador**  \n{reference['catalyst']}")
    cols[1].markdown(f"**Temperatura**  \n{reference['temperature_C']:.0f} °C")
    cols[2].markdown(f"**Pressão**  \n{reference['pressure_bar']:.0f} bar")
    cols[3].markdown(f"**GHSV**  \n{reference['GHSV_h-1']:.0f} h⁻¹")
    st.caption(f"H₂/CO = {reference['H2_CO']:.0f}. Fonte integral: CBCAT 2023, PI.012.")
    # Limits the calculation to the duration explicitly reported by the authors.
    hours = st.slider('Período integrado dentro do ensaio publicado (h)', 1, int(reference['reported_operation_h']), 24)
    totals = observed_totals(hours)
    st.dataframe(totals.style.format({'Produção média reportada (g/h)': '{:.3f}', 'Massa no período (g)': '{:.2f}'}), hide_index=True, width='stretch')
    st.caption('Massa no período = produção média publicada × duração selecionada. O cálculo não estima conversão, produtividade normalizada ou comportamento fora das 192 h observadas.')
    readiness = kinetic_readiness()
    st.warning('Modelo cinético ainda bloqueado: o artigo não informa conversões, vazão absoluta, massa/volume do leito, balanço de carbono, equação de taxa ou parâmetros com incerteza.')
    with st.expander('Campos necessários para liberar a calibração'):
        st.code('\n'.join(readiness['missing_fields']), language=None)
    st.markdown(f"[Abrir a fonte institucional]({reference['source_url']})")

    st.divider()
    mello = MELLO_2017_REFERENCE
    st.markdown('### Série experimental LABPEMOL/UFRN — Mello (2017)')
    st.info('Dados medidos de Co–Ru suportado, não previsões. O promotor Ru e os óxidos de recobrimento impedem transferência direta para Co não promovido.')
    cols = st.columns(4)
    cols[0].markdown(f"**Catalisadores**  \n{mello['catalyst_family']}")
    cols[1].markdown(f"**Condição**  \n{mello['temperature_C']:.0f} °C; {mello['pressure_bar']:.0f} bar")
    cols[2].markdown(f"**Conversão-alvo de CO**  \n{mello['target_CO_conversion_pct']:.0f} ± {mello['target_CO_conversion_tolerance_pct_points']:.0f}%")
    cols[3].markdown(f"**Balanço de carbono**  \n{mello['carbon_balance_pct']:.0f} ± {mello['carbon_balance_tolerance_pct_points']:.0f}%")
    table = mello_selectivity_table()
    st.dataframe(table.style.format({c: '{:.1f}' for c in ['CO2_pct','C1_pct','C2_C4_pct','C5_C12_pct','C13plus_pct','fechamento_HC_pct']}), hide_index=True, width='stretch')
    plot = table.melt(id_vars='Catalisador', value_vars=['C1_pct','C2_C4_pct','C5_C12_pct','C13plus_pct'], var_name='Faixa', value_name='Seletividade de carbono (%)')
    st.plotly_chart(px.bar(plot, x='Catalisador', y='Seletividade de carbono (%)', color='Faixa', barmode='stack'), width='stretch')
    st.success('Maior C₁₃₊ medido: CoRu/TaOx@AO (40,8%). O texto reporta CTY de 0,23 mol CO gCo⁻¹ h⁻¹ e produtividade C₁₃₊ >0,09 mol C gCo⁻¹ h⁻¹ para CoRu/TiOx@AO.')
    st.caption('Seletividades de hidrocarbonetos em base carbono livre de CO₂; cada linha fecha em 100%. CO₂ medido: 0,4–0,8%, portanto WGS é baixa, mas não experimentalmente nula.')
    st.markdown(f"[Abrir a tese no Repositório UFRN]({mello['source_url']})")

    st.markdown('#### Comparação dos candidatos com a série experimental')
    comparison = result['tables']['comparacao_experimental']
    selected_id = st.selectbox(
        'Candidato para comparação experimental', comparison['candidate_id'].tolist(),
        format_func=lambda cid: f"{comparison.set_index('candidate_id').loc[cid, 'formula']} / {comparison.set_index('candidate_id').loc[cid, 'support']} · {cid}",
    )
    selected = comparison.set_index('candidate_id').loc[selected_id]
    cols = st.columns(4)
    cols[0].metric('Família ativa', selected['family_match'])
    cols[1].metric('Promotor', selected['promoter_match'])
    cols[2].metric('Suporte', selected['support_match'].replace('_', ' '))
    cols[3].metric('Aplicabilidade', selected['applicability'].replace('_', ' '))
    st.write(f"**Referência mais próxima:** {selected['reference_catalyst']}. {selected['support_relation']}.")
    if selected['reference_catalyst'] != 'Nenhum':
        st.info(f"Na referência: C5–C12 = {selected['reference_C5_C12_pct']:.1f}%, C13+ = {selected['reference_C13plus_pct']:.1f}% e CO2 = {selected['reference_CO2_pct']:.1f}%. Estes valores não são previsão para o candidato.")
    st.caption(f"Condições: {selected['condition_match']}. A carga experimental era 20% Co e 0,5% Ru; diferenças de carga permanecem explícitas na tabela.")
    with st.expander('Tabela auditável dos dez candidatos'):
        st.dataframe(comparison, hide_index=True, width='stretch')

    with st.expander('Equações da dissertação de Bezerra (2010): uso permitido e limites'):
        bez = BEZERRA_2010_REFERENCE
        st.code(bez['cobalt_rate_equation'], language=None)
        st.warning('A dissertação não estimou k para Co e descreve a comparação como qualitativa. A equação fica registrada como proveniência, não como modelo calibrado.')
        st.write('A hipótese R_WGS = 0 usada na simulação não é aplicada como fato experimental, pois a tese de Mello mediu pequena formação de CO₂.')
        st.markdown(f"[Abrir a dissertação no Repositório UFRN]({bez['source_url']})")
    gate = thesis_evidence_readiness()
    st.warning('Âncora experimental liberada; calibração cinética continua bloqueada: ' + '; '.join(gate['missing_fields']) + '.')


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
    tabs = st.tabs(['Catalisadores recomendados', 'Candidatos', 'Distribuição ASF', 'Química', 'Síntese', 'Dados experimentais', 'Arquivos'])
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
        render_experimental_anchor(result)
    with tabs[6]:
        for path in sorted(Path(result['output']).iterdir()):
            if path.is_file():
                st.download_button(path.name, path.read_bytes(), file_name=path.name, key='ltft_download_'+path.name)
