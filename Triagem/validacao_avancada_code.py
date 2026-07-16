# Define colunas geradas pela validacao avancada.
colunas_validacao_avancada = [
    "formula",
    "score_validacao_avancada",
    "recomendacao_validacao_avancada",
    "nivel_evidencia",
    "score_evidencia_dados",
    "score_compatibilidade_suporte",
    "score_interface_metal_suporte",
    "risco_sinterizacao",
    "score_estabilidade_termica_operando",
    "temperatura_tammann_min_C",
    "risco_redox_operando",
    "score_redox_operando",
    "risco_adsorcao_extrema",
    "score_equilibrio_adsorcao",
    "risco_coque_avancado",
    "score_anti_coque_avancado",
    "score_correcao_temperatura",
    "temperatura_correcao_K",
    "deltaG_correcao_temperatura_eV",
    "energia_adsorcao_corrigida_temperatura_eV",
    "score_volcano_corrigido_temperatura",
    "score_robustez_vies_sistematico",
    "score_cenario_pessimista",
    "acao_validacao_avancada",
    "justificativa_validacao_avancada",
]

# Define pontos de fusao aproximados em Kelvin para estimar temperatura de Tammann.
ponto_fusao_metais_K = {
    "Ni": 1728.0,
    "Co": 1768.0,
    "Fe": 1811.0,
    "Cu": 1358.0,
    "Mo": 2896.0,
    "W": 3695.0,
    "Ru": 2607.0,
    "Rh": 2237.0,
    "Pt": 2041.0,
    "Pd": 1828.0,
    "Ce": 1068.0,
    "Zr": 2128.0,
    "La": 1193.0,
    "Mg": 923.0,
    "Y": 1799.0,
    "Ti": 1941.0,
}

# Define leitura numerica robusta de uma coluna de uma linha.
def valor_float_avancado(row, coluna, padrao=0.0):
    # Le o valor bruto da coluna quando ela existe.
    valor = row.get(coluna, padrao)
    # Retorna o padrao quando o valor esta ausente.
    if pd.isna(valor):
        return float(padrao)
    # Converte para float quando possivel.
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float(padrao)

# Define leitura booleana robusta para campos exportados como texto ou booleano.
def valor_bool_avancado(row, coluna):
    # Le o valor bruto.
    valor = row.get(coluna, False)
    # Retorna booleano diretamente quando ja for booleano.
    if isinstance(valor, bool):
        return valor
    # Normaliza representacoes textuais.
    texto = str(valor).strip().lower()
    # Interpreta valores comuns como verdadeiro.
    return texto in {"true", "1", "sim", "yes", "verdadeiro"}

# Classifica risco a partir de um score em que valores altos sao melhores.
def classificar_risco_por_score(score, nao_aplicavel=False):
    # Retorna classe especifica quando o risco nao se aplica a reacao.
    if nao_aplicavel:
        return "nao aplicavel"
    # Risco alto indica score baixo.
    if score < 0.45:
        return "alto"
    # Risco medio indica zona de atencao.
    if score < 0.65:
        return "medio"
    # Risco baixo indica boa margem.
    return "baixo"

# Caracteriza propriedades aproximadas do suporte sugerido.
def caracterizar_suporte_avancado(suporte):
    # Converte suporte para texto minusculo.
    texto = str(suporte).lower()
    # Inicia score redox do suporte.
    redox = 0.0
    # Valoriza ceria e sistemas Ce-Zr por vacancias de oxigenio.
    if "ceo2" in texto or "ce-zr" in texto or "ceo2-zro2" in texto:
        redox = max(redox, 1.0)
    # Valoriza zirconia como suporte redox/termicamente estavel.
    if "zro2" in texto or "zro" in texto:
        redox = max(redox, 0.75)
    # Valoriza titania por interacao metal-suporte.
    if "tio2" in texto:
        redox = max(redox, 0.70)
    # Inicia score de basicidade do suporte.
    basicidade = 0.0
    # Valoriza MgO e MgAlOx para reforma e controle de coque.
    if "mgo" in texto or "mgal" in texto or "mgal2o4" in texto or "mgalox" in texto:
        basicidade = max(basicidade, 0.95)
    # Valoriza La2O3 por basicidade e ativacao de CO2.
    if "la2o3" in texto or "la2o3-al2o3" in texto:
        basicidade = max(basicidade, 0.88)
    # Valoriza CaO/BaO quando aparecerem no suporte.
    if "cao" in texto or "bao" in texto:
        basicidade = max(basicidade, 0.85)
    # Inicia score de dispersao.
    dispersao = 0.45
    # Valoriza alumina e silica como suportes de alta area.
    if "al2o3" in texto or "sio2" in texto:
        dispersao = max(dispersao, 0.90)
    # Valoriza oxidos redox tambem como suportes de dispersao intermediaria.
    if "ceo2" in texto or "zro2" in texto or "tio2" in texto:
        dispersao = max(dispersao, 0.70)
    # Inicia score de estabilidade termica.
    estabilidade_termica = 0.55
    # Valoriza suportes estaveis em alta temperatura.
    if "zro2" in texto or "mgal2o4" in texto or "mgalox" in texto or "mgo" in texto:
        estabilidade_termica = max(estabilidade_termica, 0.90)
    # Valoriza alumina e lantana como estabilidade intermediaria/alta.
    if "al2o3" in texto or "la2o3" in texto:
        estabilidade_termica = max(estabilidade_termica, 0.78)
    # Retorna os subdescritores do suporte.
    return {
        "redox": float(np.clip(redox, 0, 1)),
        "basicidade": float(np.clip(basicidade, 0, 1)),
        "dispersao": float(np.clip(dispersao, 0, 1)),
        "estabilidade_termica": float(np.clip(estabilidade_termica, 0, 1)),
    }

# Calcula score de compatibilidade do suporte de acordo com a reacao.
def score_compatibilidade_suporte_avancado(row, caracteristicas):
    # Le carater redox do suporte.
    redox_suporte = caracteristicas["redox"]
    # Le basicidade do suporte.
    basicidade_suporte = caracteristicas["basicidade"]
    # Le capacidade de dispersao do suporte.
    dispersao_suporte = caracteristicas["dispersao"]
    # Le estabilidade termica do suporte.
    estabilidade_suporte = caracteristicas["estabilidade_termica"]
    # Reforma valoriza basicidade, estabilidade termica e mobilidade de oxigenio.
    if reacao == "reforma":
        return float(np.clip(0.35 * basicidade_suporte + 0.25 * redox_suporte + 0.25 * estabilidade_suporte + 0.15 * dispersao_suporte, 0, 1))
    # Metanacao valoriza dispersao e ativacao de CO2 sem excesso de severidade termica.
    if reacao == "metanacao":
        return float(np.clip(0.32 * dispersao_suporte + 0.28 * redox_suporte + 0.22 * basicidade_suporte + 0.18 * estabilidade_suporte, 0, 1))
    # RWGS valoriza suporte redox e estabilidade em temperatura moderada/alta.
    return float(np.clip(0.40 * redox_suporte + 0.25 * estabilidade_suporte + 0.20 * dispersao_suporte + 0.15 * (1.0 - 0.35 * basicidade_suporte), 0, 1))

# Calcula score aproximado de interface metal-suporte e risco SMSI excessivo.
def score_interface_avancado(row, caracteristicas, temperatura_C):
    # Le elementos da formula.
    elementos = elementos_formula(row.get("formula", ""))
    # Identifica metais que podem interagir fortemente com suporte redox.
    tem_metal_catalitico = bool(elementos & {"Ni", "Co", "Fe", "Cu", "Mo", "Ru", "Rh", "Pt", "Pd", "W"})
    # Le score redox do candidato.
    score_redox = valor_float_avancado(row, "score_redox", 0.5)
    # Le score de estabilidade do candidato.
    score_estabilidade = valor_float_avancado(row, "score_estabilidade", 0.5)
    # Estima penalidade de SMSI excessiva em alta temperatura sobre suporte muito redox.
    penalidade_smsi_excessiva = 0.12 if tem_metal_catalitico and caracteristicas["redox"] >= 0.85 and temperatura_C >= 700 else 0.0
    # Combina redox, basicidade, estabilidade e suporte para representar interface provavel.
    score_interface = (
        0.35 * caracteristicas["redox"]
        + 0.20 * caracteristicas["basicidade"]
        + 0.20 * caracteristicas["estabilidade_termica"]
        + 0.15 * score_redox
        + 0.10 * score_estabilidade
        - penalidade_smsi_excessiva
    )
    # Retorna score limitado entre 0 e 1.
    return float(np.clip(score_interface, 0, 1))

# Calcula nivel de evidencia dos dados usados no candidato.
def avaliar_evidencia_avancada(row):
    # Le fonte de estabilidade termodinamica ou proxy.
    fonte = str(row.get("fonte_estabilidade_triagem", row.get("fonte_estabilidade", ""))).lower()
    # Atribui score alto para Materials Project.
    if "materials" in fonte or fonte.strip() == "mp" or "mp_" in fonte:
        score_fonte = 0.90
    # Atribui score alto para OQMD.
    elif "oqmd" in fonte:
        score_fonte = 0.85
    # Atribui score intermediario para base local.
    elif "local" in fonte or "base" in fonte:
        score_fonte = 0.75
    # Atribui score auxiliar para GNN.
    elif "gnn" in fonte:
        score_fonte = 0.58
    # Atribui score menor para proxy puro.
    elif "proxy" in fonte:
        score_fonte = 0.42
    # Usa score neutro quando a fonte nao esta clara.
    else:
        score_fonte = 0.50
    # Le quantidade de evidencias do Catalysis-Hub.
    n_cathub = valor_float_avancado(row, "n_evidencias_cathub_incremental", 0.0)
    # Normaliza evidencias do Catalysis-Hub.
    score_cathub_evidencia = float(np.clip(n_cathub / 3.0, 0, 1))
    # Le score de incerteza calculado no funil.
    score_incerteza_local = valor_float_avancado(row, "score_incerteza", 0.5)
    # Le uso de GNN local.
    gnn_usado = valor_bool_avancado(row, "gnn_local_usado")
    # Atribui evidencia auxiliar para GNN quando usada.
    score_gnn_evidencia = 0.65 if gnn_usado else 0.45
    # Combina evidencias com maior peso para base termodinamica e Catalysis-Hub.
    score_evidencia = float(np.clip(
        0.38 * score_fonte
        + 0.28 * max(score_cathub_evidencia, valor_float_avancado(row, "score_cathub_incremental", 0.0))
        + 0.22 * score_incerteza_local
        + 0.12 * score_gnn_evidencia,
        0,
        1,
    ))
    # Classifica como evidencia forte quando ha bom score e dado catalitico.
    if score_evidencia >= 0.72 and n_cathub > 0:
        nivel = "forte"
    # Classifica como intermediaria para score razoavel.
    elif score_evidencia >= 0.52:
        nivel = "intermediario"
    # Classifica como exploratoria quando depende demais de proxy.
    else:
        nivel = "exploratorio"
    # Retorna score, classe e subscore Catalysis-Hub.
    return score_evidencia, nivel, score_cathub_evidencia

# Calcula estabilidade termica operando por temperatura de Tammann aproximada.
def avaliar_sinterizacao_avancada(row):
    # Le formula como texto.
    formula = str(row.get("formula", ""))
    # Extrai elementos da formula.
    elementos = elementos_formula(formula)
    # Prioriza metais ativos informados pelo usuario.
    elementos_ativos = [metal for metal in metais_usuario if metal in elementos]
    # Usa qualquer metal conhecido como fallback.
    if not elementos_ativos:
        elementos_ativos = [el for el in elementos if el in ponto_fusao_metais_K]
    # Le temperatura operacional.
    temperatura_C = valor_float_avancado(row, "temperatura_C", perfil["condicoes"][0]["temperatura_C"] if perfil.get("condicoes") else 400)
    # Converte temperatura para Kelvin.
    temperatura_K = temperatura_C + 273.15
    # Calcula temperaturas de Tammann.
    tammann_K = [0.5 * ponto_fusao_metais_K[el] for el in elementos_ativos if el in ponto_fusao_metais_K]
    # Usa score neutro quando nao ha dado de fusao.
    if not tammann_K:
        return 0.50, "medio", np.nan
    # Usa a menor Tammann como ponto limitante.
    tammann_min_K = float(min(tammann_K))
    # Converte a menor Tammann para Celsius.
    tammann_min_C = tammann_min_K - 273.15
    # Score cai quando a temperatura de teste se aproxima ou supera Tammann.
    score_termico = float(np.clip((tammann_min_K - temperatura_K + 250.0) / 500.0, 0, 1))
    # Classifica risco de sinterizacao.
    risco = classificar_risco_por_score(score_termico)
    # Retorna score, risco e Tammann.
    return score_termico, risco, tammann_min_C

# Calcula score redox em condicao operando.
def avaliar_redox_operando_avancado(row, caracteristicas):
    # Define alvo redox por reacao.
    alvo_redox = {"metanacao": 0.55, "reforma": 0.75, "rwgs": 0.70}.get(reacao, 0.65)
    # Le score redox do candidato.
    score_redox = valor_float_avancado(row, "score_redox", 0.5)
    # Mede proximidade do alvo redox.
    alinhamento = float(np.clip(1.0 - abs(score_redox - alvo_redox) / 0.75, 0, 1))
    # Combina redox do candidato e do suporte.
    score_operando = float(np.clip(0.45 * alinhamento + 0.25 * score_redox + 0.30 * caracteristicas["redox"], 0, 1))
    # Retorna score e risco.
    return score_operando, classificar_risco_por_score(score_operando)

# Calcula equilibrio de adsorcao por volcano, DFT/proxy e Catalysis-Hub.
def avaliar_adsorcao_avancada(row):
    # Le score do volcano com fallback para score DFT.
    score_volcano_local = valor_float_avancado(row, "score_volcano", valor_float_avancado(row, "score_DFT", 0.5))
    # Le score DFT refinado ou proxy.
    score_dft_local = valor_float_avancado(row, "score_DFT", valor_float_avancado(row, "score_DFT_proxy", 0.5))
    # Le score Catalysis-Hub.
    score_cathub_local = valor_float_avancado(row, "score_cathub_incremental", 0.0)
    # Le configuracao do volcano quando ela existir no notebook.
    volcano_cfg_local = globals().get("volcano_cfg", {})
    # Le largura do volcano com fallback para execucoes parciais.
    largura_volcano = float(volcano_cfg_local.get("largura_eV", 0.35)) if isinstance(volcano_cfg_local, dict) else 0.35
    # Le distancia ao ponto otimo do volcano.
    distancia = abs(valor_float_avancado(row, "distancia_otimo_volcano_eV", largura_volcano))
    # Penaliza adsorcao muito longe do otimo.
    penalidade_extrema = float(np.clip((distancia - largura_volcano) / max(2.0 * largura_volcano, 0.10), 0, 1))
    # Combina os sinais de adsorcao.
    score_adsorcao = float(np.clip(
        0.45 * score_volcano_local
        + 0.25 * score_dft_local
        + 0.20 * score_cathub_local
        + 0.10 * (1.0 - penalidade_extrema),
        0,
        1,
    ))
    # Aplica penalidade suave para adsorcao extrema.
    score_adsorcao = float(np.clip(score_adsorcao * (1.0 - 0.25 * penalidade_extrema), 0, 1))
    # Retorna score, risco e penalidade.
    return score_adsorcao, classificar_risco_por_score(score_adsorcao), penalidade_extrema

# Calcula validacao avancada de tendencia a coque.
def avaliar_coque_avancado(row):
    # Fora de reforma, coque nao entra como risco principal do funil.
    if reacao != "reforma":
        return 1.0, "nao aplicavel"
    # Le resistencia composicional a coque.
    resistencia = valor_float_avancado(row, "score_resistencia_coque", 0.5)
    # Le score redox.
    redox = valor_float_avancado(row, "score_redox", 0.5)
    # Le basicidade.
    basicidade = valor_float_avancado(row, "score_basicidade", 0.5)
    # Usa a maior penalidade de coque disponivel.
    penalidade_coque = max(
        valor_float_avancado(row, "penalidade_tendencia_coque", 0.5),
        valor_float_avancado(row, "penalidade_coque_condicao", 0.5),
    )
    # Usa a maior taxa proxy de desativacao disponivel.
    taxa_desativacao = max(
        valor_float_avancado(row, "taxa_desativacao_coque_proxy", 0.0),
        valor_float_avancado(row, "taxa_desativacao_coque_condicao", 0.0),
    )
    # Normaliza taxa proxy como penalidade adicional.
    penalidade_taxa = float(np.clip(taxa_desativacao / 0.25, 0, 1))
    # Combina resistencia, redox, basicidade e penalidades.
    score_anti_coque = float(np.clip(
        0.25 * resistencia
        + 0.25 * redox
        + 0.20 * basicidade
        + 0.20 * (1.0 - penalidade_coque)
        + 0.10 * (1.0 - penalidade_taxa),
        0,
        1,
    ))
    # Retorna score e risco.
    return score_anti_coque, classificar_risco_por_score(score_anti_coque)

# Calcula score aproximado de correcao de temperatura para DFT/proxies estaticos.
def avaliar_correcao_temperatura_avancada(row, score_evidencia, score_cathub_evidencia):
    # Le temperatura operacional.
    temperatura_C = valor_float_avancado(row, "temperatura_C", perfil["condicoes"][0]["temperatura_C"] if perfil.get("condicoes") else 400)
    # Define base de severidade por reacao.
    temperatura_base = {"metanacao": 300.0, "reforma": 650.0, "rwgs": 500.0}.get(reacao, 400.0)
    # Mede o quanto a condicao se afasta da faixa menos severa.
    severidade = float(np.clip((temperatura_C - temperatura_base) / 300.0, 0, 1))
    # Catalysis-Hub e evidencia mais forte reduzem a penalidade de usar energia estatica.
    cobertura_evidencia = max(score_evidencia, score_cathub_evidencia)
    # Retorna score de confianca termica aproximada.
    return float(np.clip(1.0 - 0.35 * severidade * (1.0 - cobertura_evidencia), 0, 1))

# Define correcoes aproximadas para converter energia estatica de adsorcao em energia livre efetiva.
correcoes_termicas_adsorbatos = {
    "CO": {"zpe_eV": 0.13, "cp_eV_K": 0.000035, "s_perdida_eV_K": 0.00022},
    "C": {"zpe_eV": 0.04, "cp_eV_K": 0.000020, "s_perdida_eV_K": 0.00005},
    "O": {"zpe_eV": 0.05, "cp_eV_K": 0.000022, "s_perdida_eV_K": 0.00006},
    "H": {"zpe_eV": 0.16, "cp_eV_K": 0.000018, "s_perdida_eV_K": 0.00008},
    "CH": {"zpe_eV": 0.19, "cp_eV_K": 0.000040, "s_perdida_eV_K": 0.00013},
    "CH2": {"zpe_eV": 0.25, "cp_eV_K": 0.000048, "s_perdida_eV_K": 0.00016},
    "CH3": {"zpe_eV": 0.32, "cp_eV_K": 0.000055, "s_perdida_eV_K": 0.00018},
    "HCOO": {"zpe_eV": 0.30, "cp_eV_K": 0.000075, "s_perdida_eV_K": 0.00025},
    "COOH": {"zpe_eV": 0.28, "cp_eV_K": 0.000070, "s_perdida_eV_K": 0.00024},
}

# Normaliza o descritor do volcano para escolher a correcao termica aproximada.
def normalizar_descritor_correcao_temperatura(row):
    # Le descritor do volcano quando existir.
    descritor = str(row.get("descritor_volcano", "")).upper().replace("*", "").strip()
    # Usa descritor do perfil do volcano como fallback.
    if not descritor:
        volcano_cfg_local = globals().get("volcano_cfg", {})
        descritor = str(volcano_cfg_local.get("descritor", "CO")).upper() if isinstance(volcano_cfg_local, dict) else "CO"
    # Mapeia descritores compostos para chaves tabeladas.
    if "HCOO" in descritor or "FORM" in descritor:
        return "HCOO"
    if "COOH" in descritor:
        return "COOH"
    if "CH3" in descritor:
        return "CH3"
    if "CH2" in descritor:
        return "CH2"
    if "CH" in descritor:
        return "CH"
    if "CO" in descritor:
        return "CO"
    if "O" == descritor or "O_" in descritor:
        return "O"
    if "H" == descritor:
        return "H"
    if "C" in descritor:
        return "C"
    return "CO"

# Calcula energia de adsorcao corrigida por temperatura e novo score volcano.
def calcular_correcao_temperatura_adsorcao(row):
    # Le configuracao do volcano definida na etapa catalitica.
    volcano_cfg_local = globals().get("volcano_cfg", {})
    # Define energia otima da reacao.
    energia_otima = float(volcano_cfg_local.get("energia_otima_eV", 0.85)) if isinstance(volcano_cfg_local, dict) else 0.85
    # Define largura da curva volcano.
    largura = float(volcano_cfg_local.get("largura_eV", 0.35)) if isinstance(volcano_cfg_local, dict) else 0.35
    # Define barreira base para taxa relativa.
    barreira_base = float(volcano_cfg_local.get("barreira_base_eV", 0.62)) if isinstance(volcano_cfg_local, dict) else 0.62
    # Le energia de adsorcao estatica/proxy.
    energia_ads = valor_float_avancado(row, "energia_adsorcao_volcano_eV", energia_otima)
    # Corrige energia invalida pelo alvo otimo.
    if not np.isfinite(energia_ads):
        energia_ads = energia_otima
    # Le temperatura operacional em Celsius.
    temperatura_C = valor_float_avancado(row, "temperatura_C", perfil["condicoes"][0]["temperatura_C"] if perfil.get("condicoes") else 400)
    # Converte temperatura para Kelvin.
    temperatura_K = float(temperatura_C + 273.15)
    # Define temperatura de referencia termodinamica.
    temperatura_ref_K = 298.15
    # Escolhe parametros aproximados do adsorbato guia.
    descritor_corr = normalizar_descritor_correcao_temperatura(row)
    # Recupera parametros tabelados.
    params = correcoes_termicas_adsorbatos.get(descritor_corr, correcoes_termicas_adsorbatos["CO"])
    # Calcula contribuicao de energia de ponto zero aproximada.
    zpe = float(params["zpe_eV"])
    # Calcula contribuicao entalpica vibracional aproximada.
    termo_entalpico = float(params["cp_eV_K"]) * max(temperatura_K - temperatura_ref_K, 0.0)
    # Calcula penalizacao entropica associada a perda de graus de liberdade na adsorcao.
    termo_entropico = float(params["s_perdida_eV_K"]) * temperatura_K
    # Converte as contribuicoes em enfraquecimento efetivo da adsorcao em alta temperatura.
    enfraquecimento_adsorcao = float(np.clip(termo_entropico - zpe - termo_entalpico, -0.15, 0.45))
    # Corrige a energia de adsorcao efetiva; temperatura alta tende a reduzir a forca efetiva de ligacao.
    energia_corrigida = float(np.clip(energia_ads - enfraquecimento_adsorcao, 0.05, 2.50))
    # Calcula distancia ao otimo apos correcao.
    distancia_corrigida = abs(energia_corrigida - energia_otima)
    # Recalcula score volcano com a energia corrigida.
    score_volcano_corrigido = float(np.clip(math.exp(-distancia_corrigida / max(largura, 0.05)), 0, 1))
    # Recalcula barreira aparente corrigida.
    barreira_corrigida = barreira_base + distancia_corrigida
    # Usa constante de Boltzmann do notebook quando disponivel.
    k_b_ev_local = float(globals().get("K_B_EV", 8.617333262e-5))
    # Calcula taxa relativa corrigida pela temperatura operacional.
    taxa_corrigida = float(math.exp(-barreira_corrigida / (k_b_ev_local * temperatura_K))) if temperatura_K > 0 else 0.0
    # Le score volcano nominal.
    score_volcano_nominal = valor_float_avancado(row, "score_volcano", 0.5)
    # Le score final nominal.
    score_final_nominal = valor_float_avancado(row, "score_final", valor_float_avancado(row, "score_final_material", 0.0))
    # Recalcula score final alterando apenas a parcela do volcano.
    score_final_corrigido = float(np.clip(score_final_nominal + 0.12 * (score_volcano_corrigido - score_volcano_nominal), 0, 1))
    # Retorna campos de auditoria.
    return pd.Series({
        "descritor_correcao_temperatura": descritor_corr,
        "temperatura_correcao_K": temperatura_K,
        "energia_adsorcao_estatica_eV": energia_ads,
        "deltaG_correcao_temperatura_eV": enfraquecimento_adsorcao,
        "energia_adsorcao_corrigida_temperatura_eV": energia_corrigida,
        "distancia_otimo_corrigida_temperatura_eV": distancia_corrigida,
        "score_volcano_corrigido_temperatura": score_volcano_corrigido,
        "taxa_relativa_corrigida_temperatura": taxa_corrigida,
        "score_final_corrigido_temperatura": score_final_corrigido,
    })

# Calcula robustez frente a vies sistematico dos proxies.
def avaliar_vies_sistematico_avancado(row, score_evidencia):
    # Le probabilidade Monte Carlo.
    prob_mc = valor_float_avancado(row, "probabilidade_top5_mc", 0.0)
    # Le score de incerteza.
    score_incerteza_local = valor_float_avancado(row, "score_incerteza", 0.5)
    # Le dominio de aplicabilidade.
    score_dominio = valor_float_avancado(row, "score_dominio_aplicabilidade", 0.5)
    # Verifica se GNN foi usada.
    gnn_usado = valor_bool_avancado(row, "gnn_local_usado")
    # Le quantidade de evidencias Catalysis-Hub.
    n_cathub = valor_float_avancado(row, "n_evidencias_cathub_incremental", 0.0)
    # Penaliza quando a GNN/proxy e usada sem evidencia Catalysis-Hub.
    penalidade_proxy_unico = 0.35 if gnn_usado and n_cathub <= 0 else 0.0
    # Combina sinais de robustez.
    return float(np.clip(
        0.30 * score_evidencia
        + 0.25 * prob_mc
        + 0.20 * score_incerteza_local
        + 0.15 * score_dominio
        + 0.10 * (1.0 - penalidade_proxy_unico),
        0,
        1,
    ))

# Gera uma justificativa textual curta para a validacao avancada.
def justificar_validacao_avancada(nivel_evidencia, risco_sinterizacao, risco_redox, risco_adsorcao, risco_coque, recomendacao):
    # Junta os principais alertas em uma frase de leitura direta.
    return (
        f"Evidencia {nivel_evidencia}; risco de sinterizacao {risco_sinterizacao}; "
        f"risco redox {risco_redox}; risco de adsorcao extrema {risco_adsorcao}; "
        f"risco de coque {risco_coque}. Recomendacao: {recomendacao}."
    )

# Cria linhas da validacao avancada.
linhas_validacao_avancada = []

# Avalia apenas os candidatos prioritarios finais.
for _, row in prioritarios_df.head(N_CANDIDATOS_RANKING_FINAL).copy().iterrows():
    # Caracteriza suporte sugerido.
    suporte_caracteristicas = caracterizar_suporte_avancado(row.get("suporte_sugerido", ""))
    # Le temperatura operacional para scores de interface.
    temperatura_linha_C = valor_float_avancado(row, "temperatura_C", perfil["condicoes"][0]["temperatura_C"] if perfil.get("condicoes") else 400)
    # Calcula evidencia dos dados.
    score_evidencia, nivel_evidencia, score_cathub_evidencia = avaliar_evidencia_avancada(row)
    # Calcula compatibilidade do suporte.
    score_suporte = score_compatibilidade_suporte_avancado(row, suporte_caracteristicas)
    # Calcula score de interface metal-suporte.
    score_interface = score_interface_avancado(row, suporte_caracteristicas, temperatura_linha_C)
    # Calcula risco de sinterizacao.
    score_termico, risco_sinterizacao, tammann_min_C = avaliar_sinterizacao_avancada(row)
    # Calcula risco redox em operando.
    score_redox_operando, risco_redox_operando = avaliar_redox_operando_avancado(row, suporte_caracteristicas)
    # Calcula equilibrio de adsorcao.
    score_adsorcao, risco_adsorcao_extrema, penalidade_adsorcao_extrema = avaliar_adsorcao_avancada(row)
    # Calcula risco de coque quando aplicavel.
    score_anti_coque, risco_coque = avaliar_coque_avancado(row)
    # Calcula correcao aproximada de temperatura.
    score_temperatura = avaliar_correcao_temperatura_avancada(row, score_evidencia, score_cathub_evidencia)
    # Recalcula energia de adsorcao e volcano em temperatura operacional.
    correcao_adsorcao_temperatura = calcular_correcao_temperatura_adsorcao(row)
    # Calcula robustez contra vies sistematico.
    score_vies = avaliar_vies_sistematico_avancado(row, score_evidencia)
    # Le score final nominal.
    score_final_nominal = valor_float_avancado(row, "score_final", 0.0)
    # Calcula cenario pessimista reduzindo scores sensiveis a proxy.
    score_cenario_pessimista = float(np.clip(
        score_final_nominal
        - 0.08 * (1.0 - score_evidencia)
        - 0.06 * (1.0 - score_adsorcao)
        - 0.05 * (1.0 - score_redox_operando)
        - (0.07 * (1.0 - score_anti_coque) if reacao == "reforma" else 0.0),
        0,
        1,
    ))
    # Combina pesos especificos para reforma.
    if reacao == "reforma":
        score_validacao = float(np.clip(
            0.18 * score_evidencia
            + 0.14 * score_suporte
            + 0.12 * score_interface
            + 0.12 * score_termico
            + 0.12 * score_redox_operando
            + 0.12 * score_adsorcao
            + 0.12 * score_anti_coque
            + 0.05 * score_temperatura
            + 0.03 * score_vies,
            0,
            1,
        ))
    # Combina pesos gerais para metanacao e RWGS.
    else:
        score_validacao = float(np.clip(
            0.22 * score_evidencia
            + 0.18 * score_suporte
            + 0.12 * score_interface
            + 0.13 * score_termico
            + 0.13 * score_redox_operando
            + 0.12 * score_adsorcao
            + 0.05 * score_temperatura
            + 0.05 * score_vies,
            0,
            1,
        ))
    # Lista riscos avaliados.
    riscos = [risco_sinterizacao, risco_redox_operando, risco_adsorcao_extrema]
    # Inclui coque apenas na reforma.
    if reacao == "reforma":
        riscos.append(risco_coque)
    # Conta riscos altos.
    n_riscos_altos = sum(1 for risco in riscos if risco == "alto")
    # Define recomendacao forte.
    if score_validacao >= 0.72 and n_riscos_altos == 0 and nivel_evidencia != "exploratorio":
        recomendacao = "Prioritario para sintese"
        acao = "seguir para sintese/teste com DOE central e caracterizacao inicial"
    # Define recomendacao intermediaria.
    elif score_validacao >= 0.58 and n_riscos_altos <= 1:
        recomendacao = "Promissor com validacao adicional"
        acao = "realizar DFT de superficie/interface ou teste exploratorio antes de ampliar sintese"
    # Define recomendacao exploratoria.
    else:
        recomendacao = "Exploratorio"
        acao = "nao usar como unico candidato; obter evidencia experimental ou DFT adicional antes da sintese"
    # Adiciona linha consolidada.
    linhas_validacao_avancada.append({
        "formula": row.get("formula", ""),
        "score_validacao_avancada": score_validacao,
        "recomendacao_validacao_avancada": recomendacao,
        "nivel_evidencia": nivel_evidencia,
        "score_evidencia_dados": score_evidencia,
        "score_compatibilidade_suporte": score_suporte,
        "score_interface_metal_suporte": score_interface,
        "risco_sinterizacao": risco_sinterizacao,
        "score_estabilidade_termica_operando": score_termico,
        "temperatura_tammann_min_C": tammann_min_C,
        "risco_redox_operando": risco_redox_operando,
        "score_redox_operando": score_redox_operando,
        "risco_adsorcao_extrema": risco_adsorcao_extrema,
        "score_equilibrio_adsorcao": score_adsorcao,
        "penalidade_adsorcao_extrema": penalidade_adsorcao_extrema,
        "risco_coque_avancado": risco_coque,
        "score_anti_coque_avancado": score_anti_coque,
        "score_correcao_temperatura": score_temperatura,
        "temperatura_correcao_K": correcao_adsorcao_temperatura.get("temperatura_correcao_K", np.nan),
        "deltaG_correcao_temperatura_eV": correcao_adsorcao_temperatura.get("deltaG_correcao_temperatura_eV", np.nan),
        "energia_adsorcao_corrigida_temperatura_eV": correcao_adsorcao_temperatura.get("energia_adsorcao_corrigida_temperatura_eV", np.nan),
        "score_volcano_corrigido_temperatura": correcao_adsorcao_temperatura.get("score_volcano_corrigido_temperatura", np.nan),
        "score_robustez_vies_sistematico": score_vies,
        "score_cenario_pessimista": score_cenario_pessimista,
        "acao_validacao_avancada": acao,
        "justificativa_validacao_avancada": justificar_validacao_avancada(
            nivel_evidencia,
            risco_sinterizacao,
            risco_redox_operando,
            risco_adsorcao_extrema,
            risco_coque,
            recomendacao,
        ),
    })

# Cria tabela de validacao avancada com colunas estaveis.
validacao_avancada_df = pd.DataFrame(linhas_validacao_avancada)

# Garante colunas mesmo quando nao ha candidato final.
for coluna in colunas_validacao_avancada:
    # Cria coluna ausente com serie vazia.
    if coluna not in validacao_avancada_df.columns:
        validacao_avancada_df[coluna] = pd.Series(dtype=float if coluna.startswith("score") else object)

# Ordena candidatos por score de validacao avancada.
validacao_avancada_df = validacao_avancada_df[colunas_validacao_avancada + [c for c in validacao_avancada_df.columns if c not in colunas_validacao_avancada]]
validacao_avancada_df = validacao_avancada_df.sort_values("score_validacao_avancada", ascending=False, na_position="last").reset_index(drop=True)

# Monta validacao de temperatura para o Top 10 sem alterar a triagem inicial.
top10_correcao_temperatura_base_df = melhor_por_candidato_df.head(N_CANDIDATOS_REFINADOS_FUNIL).copy() if "melhor_por_candidato_df" in globals() else pd.DataFrame()

# Calcula a tabela dedicada quando ha candidatos no Top 10.
if not top10_correcao_temperatura_base_df.empty:
    # Aplica a correcao de temperatura para cada candidato do Top 10.
    correcao_top10_df = top10_correcao_temperatura_base_df.apply(calcular_correcao_temperatura_adsorcao, axis=1)
    # Junta dados originais e campos corrigidos.
    top10_correcao_temperatura_df = pd.concat(
        [top10_correcao_temperatura_base_df.reset_index(drop=True), correcao_top10_df.reset_index(drop=True)],
        axis=1,
    )
    # Registra a posicao original no ranking.
    top10_correcao_temperatura_df["posicao_original_temperatura"] = np.arange(1, len(top10_correcao_temperatura_df) + 1)
    # Ordena pela pontuacao corrigida por temperatura.
    ordem_corrigida_temperatura = top10_correcao_temperatura_df.sort_values("score_final_corrigido_temperatura", ascending=False).reset_index(drop=True)
    # Registra a nova posicao apos correcao.
    ordem_corrigida_temperatura["posicao_corrigida_temperatura"] = np.arange(1, len(ordem_corrigida_temperatura) + 1)
    # Recupera posicao corrigida por formula.
    posicao_corrigida_map = ordem_corrigida_temperatura.set_index("formula")["posicao_corrigida_temperatura"].to_dict()
    # Aplica posicao corrigida na tabela original.
    top10_correcao_temperatura_df["posicao_corrigida_temperatura"] = top10_correcao_temperatura_df["formula"].map(posicao_corrigida_map)
    # Calcula deslocamento de ranking.
    top10_correcao_temperatura_df["deslocamento_posicao_temperatura"] = (
        top10_correcao_temperatura_df["posicao_corrigida_temperatura"]
        - top10_correcao_temperatura_df["posicao_original_temperatura"]
    )
    # Mede diferenca entre score corrigido e nominal.
    top10_correcao_temperatura_df["delta_score_final_temperatura"] = (
        pd.to_numeric(top10_correcao_temperatura_df["score_final_corrigido_temperatura"], errors="coerce")
        - pd.to_numeric(top10_correcao_temperatura_df.get("score_final", pd.Series(np.zeros(len(top10_correcao_temperatura_df)))), errors="coerce")
    )
    # Classifica o impacto da correcao para facilitar a leitura.
    top10_correcao_temperatura_df["impacto_correcao_temperatura"] = np.select(
        [
            top10_correcao_temperatura_df["deslocamento_posicao_temperatura"].abs() <= 1,
            top10_correcao_temperatura_df["deslocamento_posicao_temperatura"].abs() <= 3,
        ],
        [
            "baixo",
            "moderado",
        ],
        default="alto",
    )
    # Mantem a tabela ordenada pela posicao original para comparacao direta.
    top10_correcao_temperatura_df = top10_correcao_temperatura_df.sort_values("posicao_original_temperatura").reset_index(drop=True)
else:
    # Cria tabela vazia com colunas esperadas.
    top10_correcao_temperatura_df = pd.DataFrame(columns=[
        "formula",
        "posicao_original_temperatura",
        "posicao_corrigida_temperatura",
        "deslocamento_posicao_temperatura",
        "descritor_correcao_temperatura",
        "temperatura_correcao_K",
        "energia_adsorcao_estatica_eV",
        "deltaG_correcao_temperatura_eV",
        "energia_adsorcao_corrigida_temperatura_eV",
        "score_volcano",
        "score_volcano_corrigido_temperatura",
        "score_final",
        "score_final_corrigido_temperatura",
        "impacto_correcao_temperatura",
    ])

# Define colunas que serao incorporadas aos rankings.
colunas_validacao_avancada_merge = [
    "formula",
    "score_validacao_avancada",
    "recomendacao_validacao_avancada",
    "nivel_evidencia",
    "score_evidencia_dados",
    "score_compatibilidade_suporte",
    "score_interface_metal_suporte",
    "risco_sinterizacao",
    "score_estabilidade_termica_operando",
    "temperatura_tammann_min_C",
    "risco_redox_operando",
    "score_redox_operando",
    "risco_adsorcao_extrema",
    "score_equilibrio_adsorcao",
    "risco_coque_avancado",
    "score_anti_coque_avancado",
    "score_correcao_temperatura",
    "temperatura_correcao_K",
    "deltaG_correcao_temperatura_eV",
    "energia_adsorcao_corrigida_temperatura_eV",
    "score_volcano_corrigido_temperatura",
    "score_robustez_vies_sistematico",
    "score_cenario_pessimista",
    "acao_validacao_avancada",
    "justificativa_validacao_avancada",
]

# Define funcao para incorporar a validacao avancada a tabelas existentes.
def incorporar_validacao_avancada(df):
    # Retorna a propria tabela quando nao ha formula.
    if df is None or df.empty or "formula" not in df.columns or validacao_avancada_df.empty:
        return df
    # Remove colunas antigas para evitar duplicacao.
    df_limpo = df.drop(columns=[c for c in colunas_validacao_avancada_merge if c in df.columns and c != "formula"], errors="ignore")
    # Mescla pela formula.
    return df_limpo.merge(validacao_avancada_df[colunas_validacao_avancada_merge].drop_duplicates("formula"), on="formula", how="left")

# Incorpora validacao avancada nos candidatos prioritarios.
prioritarios_df = incorporar_validacao_avancada(prioritarios_df)

# Incorpora validacao avancada no ranking final.
ranking_final_df = incorporar_validacao_avancada(ranking_final_df)

# Incorpora validacao avancada na melhor condicao por candidato.
melhor_por_candidato_df = incorporar_validacao_avancada(melhor_por_candidato_df)

# Registra score medio de validacao avancada.
adicionar_metrica("validacao_avancada", "score medio validacao avancada Top 2", float(pd.to_numeric(validacao_avancada_df.get("score_validacao_avancada", pd.Series(dtype=float)), errors="coerce").mean()) if not validacao_avancada_df.empty else np.nan, "0-1", "Reavaliacao dos candidatos finais por evidencia, suporte, sinterizacao, redox, adsorcao, coque, temperatura e vies sistematico.")

# Registra candidatos com risco alto de sinterizacao.
adicionar_metrica("validacao_avancada", "candidatos com alto risco de sinterizacao", int((validacao_avancada_df.get("risco_sinterizacao", pd.Series(dtype=str)) == "alto").sum()) if not validacao_avancada_df.empty else 0, "n", "Candidatos finais cuja temperatura operacional se aproxima ou supera a temperatura de Tammann aproximada.")

# Registra candidatos recomendados diretamente para sintese.
adicionar_metrica("validacao_avancada", "prioritarios para sintese apos validacao avancada", int((validacao_avancada_df.get("recomendacao_validacao_avancada", pd.Series(dtype=str)) == "Prioritario para sintese").sum()) if not validacao_avancada_df.empty else 0, "n", "Candidatos finais que permaneceram fortes apos a checagem quimica avancada.")

# Registra variacao media do score final causada pela correcao de temperatura no Top 10.
adicionar_metrica("validacao_avancada", "delta medio score final apos correcao de temperatura Top 10", float(pd.to_numeric(top10_correcao_temperatura_df.get("delta_score_final_temperatura", pd.Series(dtype=float)), errors="coerce").mean()) if not top10_correcao_temperatura_df.empty else np.nan, "0-1", "Mudanca media do score final quando a energia de adsorcao e corrigida para a temperatura operacional.")

# Registra deslocamento medio absoluto do ranking corrigido por temperatura.
adicionar_metrica("validacao_avancada", "deslocamento medio absoluto por correcao de temperatura Top 10", float(pd.to_numeric(top10_correcao_temperatura_df.get("deslocamento_posicao_temperatura", pd.Series(dtype=float)), errors="coerce").abs().mean()) if not top10_correcao_temperatura_df.empty else np.nan, "posicoes", "Quanto menor, mais estavel e o Top 10 frente a correcao termodinamica aproximada.")

# Calcula se o Top 2 nominal permanece no Top 2 apos correcao.
top2_nominal_temperatura = set(top10_correcao_temperatura_df.sort_values("posicao_original_temperatura").head(2).get("formula", pd.Series(dtype=str)).astype(str)) if not top10_correcao_temperatura_df.empty else set()
top2_corrigido_temperatura = set(top10_correcao_temperatura_df.sort_values("posicao_corrigida_temperatura").head(2).get("formula", pd.Series(dtype=str)).astype(str)) if not top10_correcao_temperatura_df.empty else set()
adicionar_metrica("validacao_avancada", "candidatos Top 2 mantidos apos correcao de temperatura", int(len(top2_nominal_temperatura & top2_corrigido_temperatura)), "n", "Conta quantos candidatos do Top 2 original continuam no Top 2 apos corrigir energia de adsorcao para temperatura operacional.")

# Atualiza tabela consolidada de metricas apos acrescentar validacao avancada.
metricas_triagem_df = pd.DataFrame(linhas_metricas_triagem)

# Atualiza tabela compacta de validacao para incluir a validacao avancada.
validacao_quimiometrica_df = metricas_triagem_df[metricas_triagem_df["grupo"].isin(["quimiometria", "DOE", "ranking", "regressao_proxy", "validacao_avancada"])].copy()

# Calcula score medio da validacao avancada.
score_medio_validacao_avancada = float(pd.to_numeric(validacao_avancada_df.get("score_validacao_avancada", pd.Series(dtype=float)), errors="coerce").mean()) if not validacao_avancada_df.empty else np.nan

# Acrescenta a validacao avancada ao relatorio metodologico.
relatorio_validacao_metodo_df = pd.concat([
    relatorio_validacao_metodo_df,
    pd.DataFrame([{
        "criterio": "validacao avancada dos prioritarios",
        "status": "concluido" if not validacao_avancada_df.empty else "indisponivel",
        "evidencia": f"score medio = {score_medio_validacao_avancada:.3f}; {int((validacao_avancada_df.get('recomendacao_validacao_avancada', pd.Series(dtype=str)) == 'Prioritario para sintese').sum()) if not validacao_avancada_df.empty else 0} candidatos prioritarios para sintese.",
        "risco_residual": "a validacao avancada ainda usa regras e proxies; nao substitui DFT explicito de slab/interface nem teste catalitico.",
        "acao_recomendada": "usar a recomendacao avancada para decidir entre sintese direta, DFT de superficie/interface ou teste exploratorio.",
    }, {
        "criterio": "correcao de temperatura no Top 10",
        "status": "concluido" if not top10_correcao_temperatura_df.empty else "indisponivel",
        "evidencia": f"Top 2 mantidos = {len(top2_nominal_temperatura & top2_corrigido_temperatura)}; deslocamento medio absoluto = {pd.to_numeric(top10_correcao_temperatura_df.get('deslocamento_posicao_temperatura', pd.Series(dtype=float)), errors='coerce').abs().mean():.2f}" if not top10_correcao_temperatura_df.empty else "dados insuficientes para correcao de temperatura.",
        "risco_residual": "usa correcoes termodinamicas aproximadas por adsorbato guia; nao substitui frequencias vibracionais DFT explicitas.",
        "acao_recomendada": "usar a tabela de correcao de temperatura para verificar se o Top 10 permanece robusto nas temperaturas reais de operacao.",
    }]),
], ignore_index=True)

# Exibe tabela de validacao avancada.
validacao_avancada_df
