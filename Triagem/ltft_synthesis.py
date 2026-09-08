"""Element-equivalent batch planning; not final oxide/carbide mass prediction."""
import math
import pandas as pd
from pymatgen.core import Composition, Element


def plan(formula, promoter, mass, loading, promoter_loading, reagents):
    values = (mass, loading, promoter_loading)
    if not all(math.isfinite(float(v)) for v in values) or mass <= 0 or loading <= 0 or promoter_loading < 0 or loading+promoter_loading >= 100:
        raise ValueError('Massa e cargas inválidas; reserve uma fração positiva para o suporte.')
    if bool(promoter) != (promoter_loading > 0):
        raise ValueError('Promotor e carga de promotor devem ser coerentes.')
    active = Composition(formula)
    if not set(active.as_dict()) <= {'Co','Fe'} or any(v <= 0 for v in active.as_dict().values()):
        raise ValueError('A fase ativa deve conter apenas Co e/ou Fe em proporções positivas.')
    if promoter in active.as_dict():
        raise ValueError('O promotor não pode duplicar um metal ativo neste cálculo.')
    targets = {e:mass*loading/100*active.get_wt_fraction(e) for e in active.as_dict()}
    if promoter:
        targets[promoter] = mass*promoter_loading/100
    rows = []
    for element, target in targets.items():
        data = reagents[element]
        purity = float(data['purity'])/100
        waters = int(data['waters'])
        if waters != data['waters'] or waters < 0 or not math.isfinite(purity) or not 0 < purity <= 1:
            raise ValueError('Confira a hidratação inteira e a pureza entre 0 e 100%.')
        precursor = Composition(data['formula'])
        if any(v <= 0 for v in precursor.as_dict().values()) or precursor[element] <= 0:
            raise ValueError(f'O precursor precisa conter {element}.')
        if (set(precursor.as_dict()) & set(targets)) - {element}:
            raise ValueError('Precursor com vários elementos-alvo exige balanço acoplado; não suportado aqui.')
        molar_mass = float(precursor.weight)+waters*float(Composition('H2O').weight)
        fraction = precursor[element]*float(Element(element).atomic_mass)/molar_mass
        rows.append({'Elemento':element, 'Massa elementar (g)':target,
            'Precursor anidro':data['formula'], 'Águas de hidratação':waters,
            'Pureza (%)':purity*100, 'Massa molar hidratada (g/mol)':molar_mass,
            'Massa a pesar (g)':target/fraction/purity})
    return pd.DataFrame(rows), mass*(1-(loading+promoter_loading)/100)


def render_synthesis(result):
    import json
    import streamlit as st
    from ltft import SUPPORTS
    st.markdown('### Planejamento de síntese LTFT')
    top = result['tables']['refinados_10'].set_index('candidate_id')
    selected = st.selectbox('Catalisador para planejar a síntese', top.index.tolist(),
        format_func=lambda key:f'{top.loc[key,"formula"]} / {top.loc[key,"support"]} · {key}')
    row = top.loc[selected]
    st.info('Base: massa nominal em equivalentes elementares + suporte seco. Não é previsão da massa final após calcinação ou carburização; oxigênio/carbono incorporados e perdas não estão calculados.')
    with st.form('ltft_synthesis_form'):
        support = st.selectbox('Suporte do planejamento', list(SUPPORTS), index=list(SUPPORTS).index(row.support))
        method = st.selectbox('Procedimento proposto', ['Impregnação úmida','Impregnação sequencial','Impregnação incipiente'])
        a,b,c = st.columns(3)
        mass = a.number_input('Massa nominal desejada (g)', min_value=.01, value=100.0)
        loading = b.number_input('Carga de metais (% m/m)', min_value=.01,max_value=99.0,value=float(row.metal_loading_wt_pct))
        prom_loading = c.number_input('Carga de promotor (% m/m)',min_value=0.0,max_value=99.0,value=float(row.promoter_loading_wt_pct))
        defaults = {'Co':('Co(NO3)2',6), 'Fe':('Fe(NO3)3',9), 'K':('KNO3',0)}
        inputs = {}
        elements = list(Composition(row.formula).as_dict())+([row.promoter] if row.promoter else [])
        for element in elements:
            st.markdown(f'**Precursor de {element}**')
            x,y,z = st.columns([2,1,1])
            default, waters = defaults.get(element, ('',0))
            inputs[element] = {'formula':x.text_input('Fórmula anidra',value=default,key=f'syn_formula_{selected}_{element}'),
                'waters':y.number_input('H₂O por fórmula',min_value=0,value=waters,step=1,key=f'syn_water_{selected}_{element}'),
                'purity':z.number_input('Pureza (%)',min_value=.01,max_value=100.0,value=100.0,key=f'syn_purity_{selected}_{element}')}
        st.caption('Os precursores preenchidos são exemplos editáveis. Confira fórmula, hidratação, pureza, solubilidade e compatibilidade no rótulo e na ficha de segurança. Informe a hidratação apenas no campo H₂O.')
        submitted = st.form_submit_button('Calcular quantidades')
    if submitted:
        try:
            table, support_mass = plan(row.formula,row.promoter,mass,loading,prom_loading,inputs)
        except (ValueError,KeyError,TypeError) as exc:
            st.error(f'Não foi possível calcular: {exc}')
            return
        st.dataframe(table.style.format(precision=4),hide_index=True,width='stretch')
        st.success(f'Suporte seco: {support_mass:.4f} g de {support}. Base nominal: {mass:.4f} g.')
        st.write('1. Confirmar certificado, segurança e compatibilidade dos reagentes e do suporte.')
        st.write('2. Preparar a solução com solvente compatível. Volume não calculado: requer solubilidade e, na impregnação incipiente, volume de poros medido.')
        st.write('3. Realizar a impregnação escolhida; para a sequencial, definir a ordem e os tratamentos entre deposições em protocolo específico.')
        st.write('4. Definir secagem e tratamento térmico com base em TGA, suporte e precursor. Não aplicar calcinação oxidante indiscriminadamente a suporte de carbono.')
        st.write('5. '+row.activation)
        st.warning('Temperaturas, rampas, tempos e vazões de ativação não foram dimensionados. Redução/carburização com gases exige protocolo aprovado, equipamentos adequados e avaliação de riscos. A mudança de suporte não recalcula o ranking.')
        config = {'candidate_id':selected,'formula':row.formula,'support':support,'method':method,
                  'nominal_mass_g':mass,'support_dry_mass_g':support_mass,'metal_loading_pct':loading,
                  'promoter_loading_pct':prom_loading,'reagents':inputs,
                  'basis':'Equivalentes elementares + suporte seco; retenção elementar teórica 100%; sem balanço de fases finais',
                  'activation':row.activation,'quantities':table.to_dict('records')}
        st.download_button('Baixar quantidades (CSV)',table.to_csv(index=False).encode('utf-8-sig'),file_name=f'ltft_{selected}_quantidades_sintese.csv',mime='text/csv')
        st.download_button('Baixar planejamento (JSON)',json.dumps(config,ensure_ascii=False,indent=2).encode('utf-8'),file_name=f'ltft_{selected}_plano_sintese.json',mime='application/json')
