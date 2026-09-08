"""LTFT screening: explicit heuristic priors, not calibrated kinetics."""
import hashlib
import html
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from asf import distribution, tail_fraction
from report_contract import output_prefix

MODEL_VERSION = 'ltft-heuristic-3'
ALPHA_ASSUMPTIONS = {'temperature_per_C': -.001, 'H2_CO_per_unit': -.04,
    'log_pressure': .008, 'K_Na_shift': .015, 'support_multiplier': .02,
    'reference_temperature_C':225, 'reference_pressure_bar':20,
    'reference_H2_CO':2, 'reference_support_index':.70, 'clip':[.50,.98]}
CHEMICAL_PROFILES = {
    'Co': {
        'activation': 'Avaliar redução dos precursores para Co metálico; confirmar fase e dispersão.',
        'wgs_status': 'Baixa atividade WGS como hipótese qualitativa; não assumir taxa zero.',
        'phase_warning': 'Água, reoxidação e interação com suporte não são resolvidas pelo modelo.',
    },
    'Fe': {
        'activation': 'Avaliar ativação e carburização; confirmar carbetos e óxidos coexistentes.',
        'wgs_status': 'WGS relevante: CO + H2O ⇌ CO2 + H2. Extensão e taxas não calculadas.',
        'phase_warning': 'Distribuição de fases depende da ativação e do ambiente; não presumir um carbeto único.',
    },
    'Co-Fe exploratório': {
        'activation': 'Avaliar redução e carburização de forma conjunta; caracterizar as fases presentes.',
        'wgs_status': 'WGS possível pela presença de Fe; não interpolar taxas entre Co e Fe.',
        'phase_warning': 'Mistura exploratória: não comprova liga, sinergia ou fases ativas coexistentes.',
    },
}
# Engineering priors, not fitted parameters or measured catalyst properties.
PRIORS = {
    'Co': {'alpha': .86, 'activity': .75, 'phase': 'Co0 (hipótese)', 'phase_score': .75},
    'Fe': {'alpha': .82, 'activity': .65, 'phase': 'Carbetos de Fe (hipótese)', 'phase_score': .60},
}
SUPPORTS = {'SiO2': .75, 'Al2O3': .70, 'TiO2': .80, 'ZrO2': .70, 'C': .65}
PROMOTERS = ('K', 'Na', 'Mn', 'Cu', 'Ru', 'Re', 'La', 'Ce', 'Zr')
WEIGHTS = {'activity': .25, 'C5plus': .25, 'growth': .15, 'phase': .15, 'stability': .10, 'operation': .10}


def validate_config(metals, promoter, temperature, pressure, ratio):
    if not metals or len(set(metals)) != len(metals) or not set(metals) <= {'Co', 'Fe'}:
        raise ValueError('LTFT: selecione Co, Fe ou Co e Fe. Outros metais ativos ainda não têm modelo.')
    if promoter and promoter not in PROMOTERS:
        raise ValueError('Promotor LTFT não suportado: ' + promoter)
    for value, low, high, name in ((temperature, 200, 250, 'Temperatura'), (pressure, 10, 30, 'Pressão'), (ratio, 1.5, 2.2, 'H2/CO')):
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{name}: permitido {low} a {high}')


def generate_candidates(metals, promoter='', seed=42):
    validate_config(metals, promoter, 225, 20, 2)
    pool = []
    ratios = range(1, 100) if len(metals) == 2 else [100]
    for share in ratios:
        for loading in range(5, 26):
            for promoter_loading in (range(1, 6) if promoter else [0]):
                for support in SUPPORTS:
                    fractions = {metals[0]: share/100}
                    if len(metals) == 2:
                        fractions[metals[1]] = 1-share/100
                    formula = ''.join(f'{metal}{fraction:.2f}' for metal, fraction in fractions.items())
                    identity = f'{formula}|{loading}|{promoter}|{promoter_loading}|{support}'
                    pool.append({'candidate_id': hashlib.sha256(identity.encode()).hexdigest()[:12],
                        'formula': formula, 'fractions': fractions, 'support': support,
                        'metal_loading_wt_pct': loading, 'promoter': promoter,
                        'promoter_loading_wt_pct': promoter_loading, 'support_wt_pct': 100-loading-promoter_loading})
    # Without a promoter a single metal has only 105 distinct formulations.
    # Never duplicate candidates merely to claim 1000 generated materials.
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(pool), size=min(1000, len(pool)), replace=False)
    return [pool[int(i)] for i in indices]


def descriptors(candidates):
    from pymatgen.core import Composition
    from matminer.featurizers.composition import ElementProperty
    featurizer = ElementProperty.from_preset('magpie')
    labels = featurizer.feature_labels()
    cache = {}
    for candidate in candidates:
        formula = candidate['formula']
        if formula not in cache:
            comp = Composition(formula)
            features = featurizer.featurize(comp)
            # Magpie includes missing properties for some elements: retain NaN explicitly.
            cache[formula] = {**dict(zip(labels, features)), 'mean_atomic_mass': float(comp.weight/comp.num_atoms)}
    return pd.DataFrame([{'candidate_id': c['candidate_id'], **cache[c['formula']]} for c in candidates])


def alpha_terms(candidate, temperature=225, pressure=20, ratio=2, alpha_override=None):
    validate_config(list(candidate['fractions']), candidate['promoter'], temperature, pressure, ratio)
    p = ALPHA_ASSUMPTIONS
    terms = {
        'base':sum(PRIORS[m]['alpha']*x for m,x in candidate['fractions'].items()),
        'temperature':p['temperature_per_C']*(temperature-p['reference_temperature_C']),
        'ratio':p['H2_CO_per_unit']*(ratio-p['reference_H2_CO']),
        'pressure':p['log_pressure']*math.log(pressure/p['reference_pressure_bar']),
        'promoter':p['K_Na_shift'] if candidate['promoter'] in ('K','Na') else 0.0,
        'support':p['support_multiplier']*(SUPPORTS[candidate['support']]-p['reference_support_index']),
    }
    raw = sum(terms.values())
    clipped = float(np.clip(raw, *p['clip']))
    used = clipped
    if alpha_override is not None:
        from asf import validate_alpha
        used = validate_alpha(alpha_override)
    return {**terms, 'raw':raw, 'clipping_adjustment':clipped-raw,
            'manual_adjustment':used-clipped, 'used':used}


def evaluate(candidate, temperature=225, pressure=20, ratio=2, alpha_override=None):
    fractions = candidate['fractions']
    validate_config(list(fractions), candidate['promoter'], temperature, pressure, ratio)
    terms = alpha_terms(candidate, temperature, pressure, ratio, alpha_override)
    alpha = terms['used']
    c5 = tail_fraction(alpha, 5)
    methane = (1-alpha)**2
    activity = sum(PRIORS[m]['activity']*x for m, x in fractions.items())
    phase = sum(PRIORS[m]['phase_score']*x for m, x in fractions.items())
    if len(fractions) == 2:
        phase *= .8  # Mixed-phase uncertainty, not claimed alloy synergy.
    sintering = (temperature-200)/100
    operation = 1-abs(temperature-225)/100
    stability = SUPPORTS[candidate['support']]
    components = dict(activity=activity, C5plus=c5, growth=alpha, phase=phase, stability=stability, operation=operation)
    # Coke/oxidation remain unestimated; do not fabricate a quantitative rate.
    penalty = .10*methane+.07*sintering
    score = max(0.0, sum(WEIGHTS[k]*v for k,v in components.items())-penalty)
    family = next(iter(fractions)) if len(fractions)==1 else 'Co-Fe exploratório'
    product_distribution = distribution(alpha)
    return {**{k:v for k,v in candidate.items() if k!='fractions'}, 'family': family,
        **CHEMICAL_PROFILES[family], 'WGS_extent': None,
        'phase_hypothesis': ' + '.join(PRIORS[m]['phase'] for m in fractions),
        'temperature_C': temperature, 'pressure_bar': pressure, 'H2_CO': ratio,
        'alpha': alpha, 'alpha_origin': 'informado' if alpha_override is not None else 'heurística não calibrada',
        **{'alpha_term_'+k:v for k,v in terms.items()},
        'C5plus_carbon_pct':100*c5, 'CH4_carbon_pct':100*methane,
        **{name+'_carbon_pct':100*fraction for name,fraction in product_distribution['exclusive_groups'].items()},
        'carbon_closure_error':product_distribution['closure_error'],
        'score_LTFT':score, **{'component_'+k:v for k,v in components.items()},
        'penalty_total':penalty, 'CO_conversion_pct':None, 'CO2_selectivity_pct':None,
        'coke_rate':None, 'validation':'Sem calibração experimental',
        'synthesis_route':'Rota proposta: impregnação; definir precursores e tratamentos. '+CHEMICAL_PROFILES[family]['activation'],
        'model_version':MODEL_VERSION}


def compare_supports(candidate, temperature=225, pressure=20, ratio=2, alpha_override=None):
    rows = []
    for support in SUPPORTS:
        result = evaluate({**candidate, 'support':support}, temperature, pressure, ratio, alpha_override)
        rows.append({'candidate_id':candidate['candidate_id'], 'support':support,
            'support_index':SUPPORTS[support], 'alpha':result['alpha'],
            'score_LTFT':result['score_LTFT'], 'C5plus_carbon_pct':result['C5plus_carbon_pct'],
            'selected_formulation':support == candidate['support']})
    table = pd.DataFrame(rows).sort_values(['score_LTFT','support'], ascending=[False,True]).reset_index(drop=True)
    table['recommendation_rank'] = np.arange(1, len(table)+1)
    table['score_delta_to_best'] = table['score_LTFT']-table['score_LTFT'].max()
    table['basis'] = 'Comparação controlada com índice de suporte heurístico; sem DFT de interface ou recalibração por família.'
    return table


def alpha_sensitivity(candidate, temperature=225, pressure=20, ratio=2, alpha_override=None):
    nominal = evaluate(candidate, temperature, pressure, ratio, alpha_override)
    rows = []
    grids = {'Temperatura (°C)':np.linspace(200,250,11), 'Pressão (bar)':np.linspace(10,30,11),
             'H2/CO':np.linspace(1.5,2.2,15), 'Promotor':['']+list(PROMOTERS)}
    for axis, values in grids.items():
        for value in values:
            varied = dict(candidate)
            t,p,r = temperature,pressure,ratio
            if axis == 'Temperatura (°C)': t = float(value)
            elif axis == 'Pressão (bar)': p = float(value)
            elif axis == 'H2/CO': r = float(value)
            else: varied['promoter'] = value
            result = evaluate(varied,t,p,r,alpha_override)
            rows.append({'candidate_id':candidate['candidate_id'], 'parameter':axis,
                'value':value if value != '' else 'Sem promotor', 'alpha':result['alpha'],
                'delta_alpha':result['alpha']-nominal['alpha'],
                'C5plus_carbon_pct':result['C5plus_carbon_pct'],
                'mode':'α fixo informado' if alpha_override is not None else 'Cenário heurístico, um fator por vez'})
    return pd.DataFrame(rows)


def run(metals, promoter, output, temperature=225, pressure=20, ratio=2, seed=42, alpha_override=None):
    validate_config(metals, promoter, temperature, pressure, ratio)
    candidates = generate_candidates(metals, promoter, seed)
    descriptor_table = descriptors(candidates)  # Required: failure aborts execution.
    generated = pd.DataFrame([evaluate(c, temperature, pressure, ratio, alpha_override) for c in candidates])
    # All satisfy compositional bounds; the cap is prioritization, not proven thermodynamic viability.
    selected = generated.sort_values(['score_LTFT','candidate_id'], ascending=[False,True]).head(100).copy()
    refined = selected.head(10).copy()
    by_id = {c['candidate_id']:c for c in candidates}
    supports = pd.concat([compare_supports(by_id[cid], temperature, pressure, ratio, alpha_override)
                          for cid in refined.candidate_id], ignore_index=True)
    sensitivity = pd.concat([alpha_sensitivity(by_id[cid], temperature, pressure, ratio, alpha_override)
                             for cid in refined.candidate_id], ignore_index=True)
    recommendations = supports[supports.recommendation_rank == 1].set_index('candidate_id').support
    refined['recommended_support'] = refined.candidate_id.map(recommendations)
    refined['support_rationale'] = 'Maior score no cenário de comparação controlada dos cinco suportes; depende dos índices heurísticos declarados. Não comprova superioridade experimental.'
    final = refined.head(2).copy()
    rows = []
    for _, c in refined.iterrows():
        for row in distribution(float(c['alpha']))['rows']:
            rows.append({'candidate_id':c['candidate_id'], **row})
    asf_table = pd.DataFrame(rows)
    product_rows = []
    for _, candidate in refined.iterrows():
        dist = distribution(float(candidate['alpha']))
        for group, fraction in dist['exclusive_groups'].items():
            product_rows.append({'candidate_id':candidate['candidate_id'], 'group':group,
                                 'carbon_pct':100*fraction, 'basis':'carbono nos hidrocarbonetos',
                                 'closure_error':dist['closure_error']})
    products = pd.DataFrame(product_rows)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    prefix = output_prefix('fischer_tropsch_LTFT', metals, promoter)
    tables = {'gerados':generated, 'selecionados_100':selected, 'refinados_10':refined,
              'prioritarios_2':final, 'descritores_magpie':descriptor_table, 'distribuicao_ASF':asf_table,
              'grupos_produtos':products, 'comparacao_suportes':supports, 'sensibilidade_alpha':sensitivity}
    for name, frame in tables.items():
        frame.to_csv(out/f'{prefix}_{name}.csv', index=False, encoding='utf-8-sig')
    with pd.ExcelWriter(out/f'{prefix}_resultados.xlsx') as writer:
        for name, frame in tables.items(): frame.to_excel(writer, sheet_name=name, index=False)
    metadata = {'version':MODEL_VERSION,'metals':metals,'promoter':promoter,'seed':seed,
        'temperature_C':temperature,'pressure_bar':pressure,'H2_CO':ratio,'alpha_override':alpha_override,
        'counts':{k:len(v) for k,v in tables.items()}, 'weights':WEIGHTS, 'priors':PRIORS,
        'chemical_profiles':CHEMICAL_PROFILES,
        'alpha_assumptions':ALPHA_ASSUMPTIONS, 'support_indices':SUPPORTS,
        'sensitivity_limits':'Um fator por vez, não intervalo de confiança. Promotores distintos de K/Na têm efeito não parametrizado (zero assumido, não comprovado). Carga do promotor não influencia alpha. Modo manual mantém alpha constante.',
        'support_limits':'Os índices atuais são comuns às famílias. A recomendação pode ser igual para Co, Fe e misturas; não modela interação química específica. O suporte original da formulação é preservado, e alternativas são cenários separados.',
        'product_basis':'Fração do carbono dos hidrocarbonetos; não inclui CO/CO2, oxigenados ou coque. C5+ é subtotal, não somar novamente.',
        'chemical_references':['https://doi.org/10.1016/j.cattod.2015.11.005', 'https://www.sciencedirect.com/science/article/pii/S0021951718302550'],
        'alpha_equation':'clip(weighted_alpha - .001*(T-225) - .04*(H2/CO-2) + .008*ln(P/20) + promoter_shift + support_shift, .50, .98)',
        'status':'Triagem heurística LTFT; sem conversão ou produtividade calibradas',
        'descriptor_role':'Magpie e massa atômica registrados para auditoria; sem contribuição aprendida no score',
        'limitations':'ASF condicional aos hidrocarbonetos; fases não calculadas; WGS, coque e oxidação não quantificados; misturas Co-Fe exploratórias'}
    (out/f'{prefix}_resumo.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    report = '<!doctype html><meta charset="utf-8"><title>LTFT</title><style>body{font-family:Arial;margin:32px}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ccc}</style><h1>Fischer–Tropsch LTFT</h1>'
    report += '<p>'+html.escape(metadata['status'])+'</p><p>'+html.escape(metadata['limitations'])+'</p>'
    report += '<h2>Distribuição de produtos</h2><p>'+html.escape(metadata['product_basis'])+'</p>'+products.to_html(index=False, escape=True)
    report += '<h2>Suportes: comparação controlada</h2><p>'+html.escape(metadata['support_limits'])+'</p>'+supports.to_html(index=False, escape=True)
    report += '<h2>Sensibilidade de alpha</h2><p>'+html.escape(metadata['sensitivity_limits'])+'</p>'+sensitivity.to_html(index=False, escape=True)
    report += '<h2>Top 10</h2>'+refined.to_html(index=False, escape=True)+'<h2>Configuração auditável</h2><pre>'+html.escape(json.dumps(metadata, indent=2, ensure_ascii=False))+'</pre>'
    (out/f'{prefix}_relatorio.html').write_text(report, encoding='utf-8')
    return {'tables':tables, 'metadata':metadata, 'output':str(out), 'prefix':prefix}
