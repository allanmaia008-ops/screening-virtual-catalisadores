"""Escopo científico aprovado para a futura triagem Fischer-Tropsch.

Este módulo define o alvo; ele não habilita a reação no pipeline. A execução só
deve ser liberada após a implementação e os testes do modelo ASF, dos
descritores específicos, das fases ativas e do score Fischer-Tropsch.
"""

FISCHER_TROPSCH_LTFT_SCOPE = {
    "id": "fischer_tropsch_ltft_c5plus",
    "status": "definido_nao_executavel",
    "nome": "Fischer-Tropsch de baixa temperatura para hidrocarbonetos C5+",
    "objetivo_primario": "maximizar_seletividade_C5plus",
    "objetivos_secundarios": [
        "maximizar_conversao_CO",
        "maximizar_probabilidade_crescimento_cadeia",
        "minimizar_seletividade_CH4",
        "minimizar_formacao_CO2",
        "minimizar_desativacao",
    ],
    "reacao_global_referencia": "nCO + (2n+1)H2 -> CnH(2n+2) + nH2O",
    "alimentacao": {"reagentes": ["CO", "H2"], "razao_H2_CO": [1.5, 2.2]},
    "janela_operacional_inicial": {
        "temperatura_C": [200, 250],
        "pressao_bar": [10, 30],
        "ghsv_h_1": None,
        "observacao_ghsv": "Definir somente com base física e unidades consistentes no modelo executável.",
    },
    "produtos": {
        "alvo": "C5+",
        "faixas_a_reportar": ["CH4", "C2-C4", "C5-C11", "C12+", "C5+"],
        "coprodutos_a_reportar": ["H2O", "CO2"],
    },
    "familias_ativas_iniciais": {
        "cobalto": {"metais": ["Co", "Ru"], "fase_ativa_referencia": "Co0"},
        "ferro": {"metais": ["Fe"], "fase_ativa_referencia": "carbetos_de_ferro"},
        "exploratoria": {"metais": ["Co", "Fe"], "fase_ativa_referencia": "definir_por_candidato"},
    },
    "promotores_iniciais": ["K", "Na", "Mn", "Cu", "Ru", "Re", "La", "Ce", "Zr"],
    "suportes_iniciais": ["Al2O3", "SiO2", "TiO2", "ZrO2", "C"],
    "restricoes_metodologicas": [
        "tratar_cobalto_e_ferro_com_modelos_de_fase_ativa_separados",
        "nao_representar_C5plus_com_seletividade_de_produto_unico",
        "identificar_distribuicao_ASF_como_proxy_quando_nao_calibrada",
        "distinguir_fracao_atomica_da_fase_ativa_e_carga_massica_no_catalisador",
        "nao_exibir_confianca_probabilistica_sem_calibracao",
    ],
    "criterios_para_habilitar_execucao": [
        "modelo_ASF_e_balanco_de_carbono_implementados",
        "descritores_de_CO_H2_CHx_carbono_e_oxigenio_implementados",
        "formacao_de_Co0_e_carbetos_de_ferro_tratada_separadamente",
        "score_FT_especifico_e_penalizacoes_auditaveis_implementados",
        "testes_de_unidades_limites_e_conservacao_aprovados",
    ],
}


def validar_escopo_fischer_tropsch(escopo=None):
    """Falha cedo se o contrato científico perder limites essenciais."""
    escopo = escopo or FISCHER_TROPSCH_LTFT_SCOPE
    temperatura = escopo["janela_operacional_inicial"]["temperatura_C"]
    pressao = escopo["janela_operacional_inicial"]["pressao_bar"]
    razao = escopo["alimentacao"]["razao_H2_CO"]
    assert escopo["status"] == "definido_nao_executavel"
    assert escopo["produtos"]["alvo"] == "C5+"
    assert temperatura[0] < temperatura[1]
    assert pressao[0] < pressao[1]
    assert razao[0] < razao[1]
    assert "Co0" == escopo["familias_ativas_iniciais"]["cobalto"]["fase_ativa_referencia"]
    assert "carbetos_de_ferro" == escopo["familias_ativas_iniciais"]["ferro"]["fase_ativa_referencia"]
    return True
