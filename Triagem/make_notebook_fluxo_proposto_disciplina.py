import json
from pathlib import Path

import nbformat as nbf


# Define a pasta em que este gerador está salvo.
SCRIPT_DIR = Path(__file__).resolve().parent

# Define o notebook de saída dentro da mesma pasta do gerador.
NOTEBOOK = SCRIPT_DIR / "notebook_disciplina_triagem_virtual_fluxo_proposto.ipynb"


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "pygments_lexer": "ipython3"},
}

nb["cells"] = [
    md(
        """
# FLUXO DO PROJETO ATUALIZADO

1. Preparacao do ambiente: importa bibliotecas essenciais, localiza a pasta do projeto, separa a pasta de dados locais da pasta de saida e pergunta ao usuario onde salvar os documentos gerados. Tambem instala ou importa dependencias opcionais sob demanda, como `matminer`, `pymatgen`, `matplotlib` e `scipy`, quando disponiveis no ambiente.

2. Entrada do usuario: pergunta a reacao-alvo, o numero de metais ativos, o(s) metal(is) de fase ativa e o promotor quimico. As perguntas nao exibem respostas previas; em execucao automatizada, os scripts de teste podem preencher as respostas por variaveis de ambiente.

3. Perfis quimicos por reacao: seleciona entre metanacao de CO2, reforma de CH4 ou RWGS e carrega automaticamente descritores, intermediarios DFT esperados, pesos do ranking e limites de estabilidade adequados para a rota escolhida.

4. Geracao automatica de candidatos: cria 1000 candidatos puros, promovidos, bimetalicos e multimetalicos de forma controlada, balanceando metais ativos quando houver mais de um metal informado.

5. Busca e atualizacao de propriedades de materiais: consulta a base local multi-fonte; quando um candidato nao existe na base, tenta buscar dados no Materials Project usando a chave configurada no notebook ou em `MP_API_KEY` e tambem tenta consultar o OQMD; anexa os novos registros ao banco local e evita baixar novamente sistemas quimicos ja consultados com sucesso.
   Quando a execucao ocorre no Streamlit Cloud com token GitHub configurado, o notebook baixa primeiro os CSVs incrementais persistidos no repositorio e envia de volta os novos dados obtidos.

6. Calculo de descritores quimicos especificos da reacao: calcula atividade, seletividade, basicidade, redox, resistencia a coque, proxy DFT e incerteza conforme a reacao escolhida. Para reforma de CH4, adiciona penalidade de tendencia a coque, taxa proxy de desativacao por coque e atividade corrigida por coque.

6.1. Descritores composicionais obrigatorios com matminer: instala/importa `matminer`, calcula descritores Magpie e incorpora um score composicional por reacao ao ranking.

6.2. Descritores quimicos diretos com pymatgen: extrai massa molar, numero de elementos, eletronegatividade media, desvio de eletronegatividade e raio atomico medio quando o `pymatgen` esta disponivel.

6.3. Proxy DFT local com GNN: quando `CHGNet` ou `matgl/M3GNet` estiver disponivel, constroi uma estrutura cristalina aproximada para candidatos sem suporte estrutural completo, estima energia localmente, salva o cache em CSV e usa o resultado apenas como evidencia auxiliar com incerteza aumentada.

7. Filtro de viabilidade: aplica estabilidade termodinâmica, score de estabilidade, limite principal/exploratorio por reacao e penalizacao por incerteza.

8. Triagem preliminar com normalizacao robusta: aplica filtro de viabilidade e mantém apenas 100 candidatos viáveis para seguir no funil, agregando estabilidade, atividade, seletividade, proxy DFT e incerteza em um score multicriterio inicial.

9. Busca catalitica incremental no Catalysis-Hub e refinamento DFT: refina apenas os 10 melhores candidatos preliminares, busca energias de reacao/adsorcao associadas aos intermediarios da rota, salva os resultados em cache local e usa esses dados no score DFT quando disponiveis.

9.1. Peso termodinamico de Boltzmann: penaliza candidatos mais metaestaveis usando estabilidade termodinâmica e temperatura de referência.

9.2. Volcano simplificado por descritor catalitico: transforma energia de adsorcao real ou proxy em uma taxa relativa tipo Sabatier, favorecendo adsorcao moderada e penalizando adsorcao fraca ou forte demais.

9.3. Correcao de desativacao por coque para reforma: usa energia/proxy de adsorcao de C, score redox, resistencia composicional a coque e razao CH4/CO2 para penalizar candidatos com maior tendencia a formar carbono superficial.

10. Suporte e condicoes desejaveis de sintese/teste: sugere suporte, rota de sintese e faixas de temperatura, pressao, razao reacional e GHSV de acordo com a reacao e a composicao. Em reforma, a razao CH4/CO2 tambem ajusta a penalidade de coque por condicao operacional.

11. Ranking catalisador-condicao: combina score do material com desempenho previsto em diferentes condicoes operacionais e mantém apenas os 2 melhores candidatos no ranking final. Para reforma, a conversao prevista usa atividade corrigida por coque e o score final recebe penalizacao adicional quando a condicao favorece desativacao.

12. Controle de incerteza e recomendacao para sintese: executa validacoes estatisticas e operacionais, incluindo:

- Calcula analise de sensibilidade dos descritores.
- Executa simulacao de Monte Carlo fisicamente propagada, perturbando estabilidade, atividade, seletividade, DFT/proxy, volcano, penalidade de coque em reforma e condicoes antes de recalcular o ranking.
- Calcula intervalo de confianca de 95% da probabilidade de permanencia no top 5 usando `scipy`.
- Projeta desempenho em diferentes condicoes operacionais.

13. Visualizacao cientifica dos resultados: salva figuras do funil de triagem, ranking, estabilidade versus score, Monte Carlo, desempenho por condicao e sensibilidade dos descritores.

14. Metricas da triagem virtual: calcula metricas de viabilidade, ranking, confianca, DFT/proxy DFT, descritores, diversidade e metricas especificas da reacao.

15. Salvar resultados: grava todos os arquivos na pasta escolhida pelo usuario e gera automaticamente um relatório HTML autocontido com resumo, tabelas principais e figuras da triagem.

- `disciplina_fluxo_<reacao>_resultados.xlsx`
- `disciplina_fluxo_<reacao>_relatorio.html`
- `disciplina_fluxo_<reacao>_metricas_triagem.csv`
- `disciplina_fluxo_<reacao>_ranking_condicoes.csv`
- `disciplina_fluxo_<reacao>_melhor_condicao_por_candidato.csv`
- `disciplina_fluxo_<reacao>_prioritarios_sintese.csv`
- `disciplina_fluxo_<reacao>_desempenho_faixa_condicoes.csv`
- `disciplina_fluxo_<reacao>_sensibilidade_descritores.csv`
- `disciplina_fluxo_<reacao>_monte_carlo_ranking.csv`
- `disciplina_fluxo_<reacao>_descritores_matminer.csv`
- `disciplina_fluxo_<reacao>_descritores_pymatgen.csv`
- `disciplina_fluxo_<reacao>_proxy_gnn_local.csv`
- `disciplina_fluxo_<reacao>_figuras_geradas.csv`
- `disciplina_fluxo_<reacao>_resumo.json`
- `consultas_bases_externas.csv`, com o histórico de consultas incrementais ao Materials Project, OQMD e Catalysis-Hub
"""
    ),
    md(
        """
# Projeto da disciplina: triagem virtual de catalisadores para síntese

## Objetivo

Construir um fluxo independente de triagem virtual para sugerir catalisadores candidatos à síntese, partindo da lógica do notebook base de Materials Project: gerar candidatos, buscar propriedades de materiais, calcular descritores, ranquear catalisadores e refinar a seleção com dados ou proxies DFT.

## Roteiro

1. Escolher a reação: metanação de CO2, reforma de CH4 ou RWGS.
2. Informar quantos metais de fase ativa serão testados.
3. Informar o(s) metal(is) ativo(s) e o promotor.
4. Gerar candidatos automaticamente.
5. Buscar propriedades disponíveis em bases locais derivadas de MP/OQMD/Catalysis-Hub.
6. Calcular descritores químicos específicos para a reação.
7. Aplicar filtro de viabilidade.
8. Fazer triagem preliminar.
9. Refinar o ranking com dados/proxies DFT.
10. Gerar a tabela final com candidatos, suporte sugerido, condições desejáveis e nível de confiabilidade.

## Resultados esperados

- Ranking preliminar de catalisadores.
- Ranking final refinado por reação.
- Top candidatos para síntese.
- Condições desejáveis de teste catalítico.
- Justificativas químicas e classificação de incerteza.

> Este notebook é independente do Projeto Doutorado: não usa PlanML, artigo1 ou o modelo expandido.
"""
    ),
    md(
        """
## Etapa 1 - Preparação do ambiente

Esta célula importa bibliotecas, localiza a pasta do projeto e define onde os resultados serão salvos.
"""
    ),
    code(
        """
# Importa json para salvar resumos estruturados da execução.
import json

# Importa os para ler variaveis de ambiente em execucoes automatizadas.
import os

# Importa sys para instalar dependências opcionais no mesmo ambiente do notebook.
import sys

# Importa subprocess para instalação controlada de pacotes opcionais.
import subprocess

# Importa time para pequenas pausas entre chamadas a bases externas.
import time

# Importa getpass para solicitar chave do Materials Project sem exibi-la.
from getpass import getpass

# Importa math para funções matemáticas usadas nos fatores de condição reacional.
import math

# Importa re para extrair símbolos químicos das fórmulas.
import re

# Importa html para escapar textos no relatório HTML.
import html

# Importa base64 para embutir figuras no relatório HTML.
import base64

# Importa requests para consultar OQMD via API REST.
import requests

# Importa Path para trabalhar com caminhos de arquivos de forma robusta.
from pathlib import Path

# Importa numpy para cálculos numéricos e limites de valores.
import numpy as np

# Importa pandas para manipular tabelas de candidatos, descritores e rankings.
import pandas as pd

# Define funcao para instalar e importar dependencias obrigatorias da triagem.
def garantir_dependencia_obrigatoria(pacote, modulo=None):
    # Usa o nome do pacote como modulo quando nenhum modulo especifico foi informado.
    modulo = modulo or pacote
    # Tenta importar o modulo antes de instalar para evitar downloads desnecessarios.
    try:
        __import__(modulo)
    # Instala o pacote quando ele ainda nao esta disponivel no ambiente.
    except ModuleNotFoundError:
        # Instala no mesmo Python que executa o notebook.
        subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
        # Tenta importar novamente depois da instalacao.
        __import__(modulo)
    # Captura falhas de importacao diferentes de pacote ausente.
    except Exception as erro_dependencia:
        # Interrompe com mensagem direta para evitar fallback silencioso em descritores obrigatorios.
        raise RuntimeError(f"Falha ao importar dependencia obrigatoria {pacote}: {erro_dependencia}") from erro_dependencia

# Garante o matminer para calcular descritores Magpie na etapa 6.1.
garantir_dependencia_obrigatoria("matminer", "matminer")

# Garante o pymatgen para interpretar composicoes quimicas e apoiar descritores estruturais.
garantir_dependencia_obrigatoria("pymatgen", "pymatgen")

# Define a pasta em que o notebook está sendo executado.
CWD = Path.cwd()

# Define a raiz do projeto mesmo quando o notebook é aberto dentro da pasta Triagem.
PROJECT_ROOT = CWD.parent if CWD.name.lower() == "triagem" else CWD

# Define a pasta local do projeto onde ficam bases auxiliares usadas pela triagem.
PROJECT_DATA_DIR = PROJECT_ROOT / "outputs"

# Le a chave do Materials Project por variavel de ambiente/secrets, sem grava-la no notebook.
MP_API_KEY_SALVA = os.environ.get("MP_API_KEY", "").strip()

# Define a pasta de salvamento usada apenas em execucao automatica ou resposta vazia.
DEFAULT_OUTPUT_DIR = PROJECT_DATA_DIR

# Pergunta a pasta onde o usuario deseja salvar os documentos gerados.
try:
    # Mostra a pergunta sem resposta previa sugerida.
    pasta_saida_usuario = input("Em qual pasta deseja salvar os documentos gerados?: ").strip()
# Captura execucao automatica ou ambiente sem entrada interativa.
except Exception:
        # Usa variavel de ambiente apenas quando nao existe entrada interativa.
    pasta_saida_usuario = ""

# Usa a pasta digitada pelo usuario ou a pasta padrao quando nada foi informado.
OUTPUT_DIR = Path(pasta_saida_usuario).expanduser() if pasta_saida_usuario else DEFAULT_OUTPUT_DIR

# Resolve o caminho absoluto para evitar ambiguidade entre Windows, Colab e Linux.
OUTPUT_DIR = OUTPUT_DIR.resolve()

# Cria a pasta de saída caso ela ainda não exista.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define o arquivo local com ranking/propriedades já derivadas do notebook base.
RANKING_FILE = PROJECT_DATA_DIR / "ranking_multicriterio_v2_incerteza_explicabilidade.csv"

# Mostra as pastas principais para conferência.
print("Raiz do projeto:", PROJECT_ROOT)
print("Pasta de dados locais:", PROJECT_DATA_DIR)
print("Pasta de saída:", OUTPUT_DIR)
print("Base local de triagem existe?", RANKING_FILE.exists())
"""
    ),
    md(
        """
## Etapa 2 - Entrada do usuário

O notebook pergunta qual reação será avaliada, quantos metais ativos serão testados, quais são esses metais e qual promotor será considerado.

As perguntas não exibem respostas prévias. Em execução automatizada, os scripts de teste podem preencher as respostas por variáveis de ambiente, sem alterar a experiência interativa do notebook.
"""
    ),
    code(
        """
# Define uma funcao auxiliar para perguntar ao usuario sem mostrar resposta previa.
VARIAVEIS_ENTRADA = {
    "reacao": "TRIAGEM_REACAO",
    "n_metais": "TRIAGEM_N_METAIS",
    "metal_unico": "TRIAGEM_METAL_UNICO",
    "metais_multiplos": "TRIAGEM_METAIS_MULTIPLOS",
    "promotor": "TRIAGEM_PROMOTOR",
}

# Define uma funÃ§Ã£o auxiliar para perguntar ao usuÃ¡rio sem mostrar resposta prÃ©via.
def perguntar(texto, chave_auto):
    # Tenta ler uma resposta digitada pelo usuário.
    try:
        # Mostra a pergunta sem valor sugerido entre colchetes.
        resposta = input(f"{texto}: ").strip()
        # MantÃ©m a pergunta obrigatÃ³ria quando o usuÃ¡rio estÃ¡ interagindo.
        while not resposta:
            # Solicita novamente sem sugerir resposta pronta.
            resposta = input(f"{texto}: ").strip()
    # Captura falhas comuns quando o notebook é executado sem interação.
    except Exception:
        # Usa variavel de ambiente apenas quando nao existe entrada interativa.
        # Busca resposta em variavel de ambiente quando nao existe entrada interativa.
        resposta = os.environ.get(VARIAVEIS_ENTRADA[chave_auto], "").strip()
        # Interrompe a execucao se nao houver resposta do usuario nem variavel de ambiente.
        if not resposta:
            raise RuntimeError(f"Informe uma resposta para: {texto}")
    # Retorna a resposta digitada pelo usuario ou recebida por variavel de ambiente.
    return resposta

# Pergunta qual reação será avaliada.
reacao_usuario = perguntar("Qual reação deseja avaliar? Use metanacao, reforma ou rwgs", "reacao")

# Pergunta quantos metais de fase ativa serão usados.
n_metais_usuario = int(perguntar("Quantos metais de fase ativa quer testar?", "n_metais"))

# Pergunta um metal ativo se o usuário escolheu apenas um.
if n_metais_usuario == 1:
    # Lê o símbolo do único metal ativo.
    metais_usuario = [perguntar("Qual é o metal de fase ativa?", "metal_unico")]
# Pergunta uma lista de metais ativos quando o usuário escolheu mais de um.
else:
    # Lê os metais separados por vírgula.
    metais_usuario = perguntar("Quais metais de fase ativa? Separe por vírgula", "metais_multiplos").split(",")

# Limpa espaços extras dos símbolos informados.
metais_usuario = [m.strip() for m in metais_usuario if m.strip()]

# Pergunta qual promotor será usado.
promotor_usuario = perguntar("Qual será o promotor?", "promotor").strip()

# Mostra as escolhas do usuário.
print("Reação:", reacao_usuario)
print("Metais ativos:", metais_usuario)
print("Promotor:", promotor_usuario)
"""
    ),
    md(
        """
## Etapa 3 - Perfis químicos por reação

Cada reação usa princípios químicos diferentes. Por isso, o notebook define condições, intermediários DFT relevantes, limites de estabilidade e pesos de score específicos para metanação, reforma e RWGS.
"""
    ),
    code(
        """
# Define os perfis químicos usados para controlar a triagem.
PERFIS_REACAO = {
    # Perfil para metanação de CO2, cujo produto desejado é CH4.
    "metanacao": {
        "nome": "Metanação de CO2",
        "produto": "CH4",
        "limite_hull_principal": 0.10,
        "limite_hull_exploratorio": 0.15,
        "intermediarios_dft": ["CO2*", "COOH*", "OCHO*", "CO*", "C*", "H*"],
        "descritores": ["ativacao_CO2", "hidrogenacao", "seletividade_CH4", "vacancia_oxigenio", "basicidade"],
        "pesos": {"estabilidade": 0.22, "atividade": 0.20, "seletividade": 0.18, "dft": 0.20, "incerteza": 0.10, "condicao": 0.10},
        "condicoes": [
            {"regime": "baixa_temperatura", "temperatura_C": 300, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 4.0, "ghsv_h-1": 30000},
            {"regime": "equilibrado", "temperatura_C": 350, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 4.0, "ghsv_h-1": 30000},
            {"regime": "alta_conversao", "temperatura_C": 400, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 4.0, "ghsv_h-1": 30000},
            {"regime": "alta_pressao", "temperatura_C": 350, "pressao_bar": 5, "razao_nome": "H2/CO2", "razao": 4.0, "ghsv_h-1": 30000},
        ],
    },
    # Perfil para reforma de CH4, cujo objetivo é formar syngas/H2 e resistir a coque.
    "reforma": {
        "nome": "Reforma de CH4",
        "produto": "syngas/H2",
        "limite_hull_principal": 0.08,
        "limite_hull_exploratorio": 0.12,
        "intermediarios_dft": ["CH4*", "CH3*", "CHx*", "C*", "O*", "OH*", "CO*"],
        "descritores": ["ativacao_CH4", "quebra_C_H", "resistencia_coque", "mobilidade_oxigenio", "estabilidade_termica"],
        "pesos": {"estabilidade": 0.24, "atividade": 0.18, "seletividade": 0.12, "dft": 0.22, "incerteza": 0.14, "condicao": 0.10},
        "condicoes": [
            {"regime": "reforma_moderada", "temperatura_C": 650, "pressao_bar": 1, "razao_nome": "CH4/CO2", "razao": 1.0, "ghsv_h-1": 30000},
            {"regime": "reforma_padrao", "temperatura_C": 750, "pressao_bar": 1, "razao_nome": "CH4/CO2", "razao": 1.0, "ghsv_h-1": 30000},
            {"regime": "alta_temperatura", "temperatura_C": 850, "pressao_bar": 1, "razao_nome": "CH4/CO2", "razao": 1.0, "ghsv_h-1": 30000},
            {"regime": "maior_tempo_contato", "temperatura_C": 750, "pressao_bar": 1, "razao_nome": "CH4/CO2", "razao": 1.0, "ghsv_h-1": 15000},
        ],
    },
    # Perfil para RWGS, cujo produto desejado é CO e não CH4.
    "rwgs": {
        "nome": "RWGS",
        "produto": "CO",
        "limite_hull_principal": 0.10,
        "limite_hull_exploratorio": 0.15,
        "intermediarios_dft": ["CO2*", "COOH*", "OCHO*", "CO*", "O*", "H*"],
        "descritores": ["ativacao_CO2", "seletividade_CO", "supressao_CH4", "adsorcao_CO_moderada", "mobilidade_oxigenio"],
        "pesos": {"estabilidade": 0.22, "atividade": 0.22, "seletividade": 0.16, "dft": 0.22, "incerteza": 0.10, "condicao": 0.08},
        "condicoes": [
            {"regime": "rwgs_moderada", "temperatura_C": 500, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 2.0, "ghsv_h-1": 30000},
            {"regime": "rwgs_padrao", "temperatura_C": 600, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 2.0, "ghsv_h-1": 30000},
            {"regime": "rwgs_alta_temperatura", "temperatura_C": 700, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 2.0, "ghsv_h-1": 30000},
            {"regime": "rwgs_menor_H2", "temperatura_C": 650, "pressao_bar": 1, "razao_nome": "H2/CO2", "razao": 1.0, "ghsv_h-1": 30000},
        ],
    },
}

# Importa unicodedata para remover acentos e cedilha das respostas digitadas.
import unicodedata

# Normaliza nomes alternativos para a reação escolhida.
def normalizar_reacao(texto):
    # Converte a resposta para texto, remove espaços laterais e deixa em minúsculas.
    bruto = str(texto).strip().lower()
    # Remove acentos e cedilha para aceitar metanacao, metanação e metanaçao como equivalentes.
    sem_acentos = unicodedata.normalize("NFKD", bruto)
    # Mantém apenas caracteres base, descartando marcas de acentuação.
    sem_acentos = "".join(caractere for caractere in sem_acentos if not unicodedata.combining(caractere))
    # Padroniza separadores comuns usados em respostas textuais.
    t = sem_acentos.replace("-", "_").replace("/", "_").replace(" ", "_")
    # Remove duplicações de separador geradas pela padronização.
    while "__" in t:
        t = t.replace("__", "_")
    # Remove separadores sobrando no início ou no fim.
    t = t.strip("_")
    # Aceita variações de escrita para metanação.
    if t in ["metanacao", "metanacao_de_co2", "metanacao_co2", "co2_methanation", "methanation"]:
        return "metanacao"
    # Aceita variações de escrita para reforma.
    if t in ["reforma", "reforming", "dry_reforming", "drm", "reforma_ch4", "reforma_de_ch4", "reforma_seca"]:
        return "reforma"
    # Aceita variações de escrita para RWGS.
    if t in ["rwgs", "r_wgs", "reverse_water_gas_shift", "reverse_wgs"]:
        return "rwgs"
    # Interrompe a execução se a reação não for reconhecida, mostrando a entrada normalizada.
    raise ValueError(f"Reação inválida: {texto!r}. Use metanacao, reforma ou rwgs.")

# Aplica a normalização à reação informada pelo usuário.
reacao = normalizar_reacao(reacao_usuario)

# Seleciona o perfil químico correspondente.
perfil = PERFIS_REACAO[reacao]

# Mostra o perfil escolhido.
print("Perfil selecionado:", perfil["nome"])
print("Produto alvo:", perfil["produto"])
print("Descritores usados:", perfil["descritores"])
print("Intermediários DFT relevantes:", perfil["intermediarios_dft"])
"""
    ),
    md(
        """
## Etapa 4 - Geração automática de candidatos

O modelo gera candidatos a partir dos metais ativos e do promotor. Quando mais de um metal ativo é informado, o funil inclui ligas entre metais ativos, ligas multimetálicas e versões promovidas antes de aplicar o corte de 1000 candidatos. Depois disso, passa para 100 candidatos viáveis após o filtro, refina 10 candidatos e apresenta 2 candidatos no ranking final.
"""
    ),
    code(
        """
# Importa combinations para montar pares de metais ativos sem repetir a ordem.
from itertools import combinations

# Importa re para identificar os metais ativos presentes em cada fórmula gerada.
import re

# Define a quantidade de candidatos gerados no início do funil.
N_CANDIDATOS_GERADOS_FUNIL = 1000

# Define quantos candidatos viáveis seguem após o filtro de estabilidade.
N_CANDIDATOS_VIAVEIS_FUNIL = 100

# Define quantos candidatos seguem para refinamento DFT/proxy DFT.
N_CANDIDATOS_REFINADOS_FUNIL = 10

# Define quantos candidatos aparecem como prioritarios finais para sintese.
N_CANDIDATOS_RANKING_FINAL = 2

# Define proporções em grade de 0,01 para combinar um metal ativo com o promotor.
PROPORCOES_PROMOTOR = [round(i / 100, 2) for i in range(1, 100)]

# Define frações relativas em grade de 0,01 para variar a composição entre dois metais ativos.
PROPORCOES_LIGA_ATIVA = [round(i / 100, 2) for i in range(1, 100)]

# Define frações adicionais em grade de 0,01 para completar o funil quando ainda houver combinações únicas.
PROPORCOES_LIGA_ATIVA_FINA = [round(i / 100, 2) for i in range(1, 100)]

# Define frações moderadas de promotor em grade de 0,01, evitando excesso de casas decimais nas fórmulas.
PROPORCOES_PROMOTOR_MULTIMETAL = [round(i / 100, 2) for i in range(1, 31)]

# Remove metais ativos repetidos preservando a ordem informada pelo usuário.
metais_usuario = list(dict.fromkeys([m for m in metais_usuario if m]))

# Interrompe a execução se nenhum metal ativo válido tiver sido informado.
if not metais_usuario:
    # Explica que a geração depende de pelo menos um elemento de fase ativa.
    raise ValueError("Informe pelo menos um metal ativo para gerar candidatos catalíticos.")

# Define uma função para formatar frações estequiométricas com duas casas decimais.
def texto_fracao(valor):
    # Converte o valor para float para evitar problemas com inteiros ou strings numéricas.
    valor = float(valor)
    # Retorna a fração no padrão compacto usado nas fórmulas de triagem.
    return f"{valor:.2f}"

# Define uma função para montar fórmulas simplificadas a partir de pares elemento-fração.
def formula_por_composicao(componentes):
    # Cria um dicionário para somar frações quando o mesmo elemento aparece mais de uma vez.
    composicao = {}
    # Cria uma lista para preservar a ordem química em que os elementos foram inseridos.
    ordem_elementos = []
    # Percorre cada componente químico informado.
    for elemento, fracao in componentes:
        # Ignora componentes vazios ou com fração nula.
        if not elemento or fracao <= 0:
            # Continua para o próximo componente sem alterar a fórmula.
            continue
        # Registra a ordem do elemento na primeira vez em que ele aparece.
        if elemento not in composicao:
            # Guarda o elemento na ordem de montagem da fórmula.
            ordem_elementos.append(elemento)
            # Inicializa a fração acumulada do elemento.
            composicao[elemento] = 0.0
        # Soma a fração do componente à fração total do elemento.
        composicao[elemento] += float(fracao)
    # Junta elementos e frações em uma fórmula textual lida pelo pymatgen.
    return "".join([f"{elemento}{texto_fracao(composicao[elemento])}" for elemento in ordem_elementos])

# Define uma função para montar fórmulas metal-promotor no caso monometálico.
def formula_binaria(metal, promotor, fracao_promotor):
    # Calcula a fração restante do metal ativo.
    fracao_metal = 1.0 - fracao_promotor
    # Retorna a fórmula binária usando a função geral de composição.
    return formula_por_composicao([(metal, fracao_metal), (promotor, fracao_promotor)])

# Define uma função auxiliar para adicionar candidatos com fórmula e tipo.
def adicionar_candidato(formula, tipo):
    # Adiciona apenas fórmulas não vazias, inéditas e dentro do limite inicial do funil.
    if formula and formula not in candidatos_registrados and len(candidatos) < N_CANDIDATOS_GERADOS_FUNIL:
        # Marca a fórmula como já registrada para evitar duplicatas.
        candidatos_registrados.add(formula)
        # Registra a fórmula e o tipo para manter rastreabilidade no funil.
        candidatos.append({"formula": formula, "tipo": tipo})

# Inicia a lista que receberá todos os candidatos antes do corte do funil.
candidatos = []

# Inicia o conjunto usado para controlar duplicatas durante a geração combinatória.
candidatos_registrados = set()

# Define uma função para verificar se a biblioteca inicial já chegou a 1000 candidatos.
def funil_inicial_completo():
    # Retorna True quando a geração já atingiu o limite desejado.
    return len(candidatos) >= N_CANDIDATOS_GERADOS_FUNIL

# Adiciona os metais puros informados como referências de fase ativa.
for metal in metais_usuario:
    # Mantém o metal puro no funil para comparação com ligas e promovidos.
    adicionar_candidato(metal, "metal_ativo_puro")

# Define todos os pares de metais ativos informados pelo usuário.
pares_ativos = list(combinations(metais_usuario, 2))

# Adiciona ligas binárias entre metais ativos quando o usuário informa mais de um metal.
for fracao_a in PROPORCOES_LIGA_ATIVA:
    # Interrompe a camada se o funil inicial já estiver completo.
    if funil_inicial_completo():
        # Sai do laço de frações de liga ativa.
        break
    # Percorre todos os pares para distribuir a diversidade entre os metais informados.
    for metal_a, metal_b in pares_ativos:
        # Interrompe a camada se o funil inicial já estiver completo.
        if funil_inicial_completo():
            # Sai do laço de pares de metais ativos.
            break
        # Calcula a fração complementar do segundo metal ativo.
        fracao_b = 1.0 - fracao_a
        # Monta uma fórmula de liga ativa sem promotor.
        formula_liga = formula_por_composicao([(metal_a, fracao_a), (metal_b, fracao_b)])
        # Adiciona a liga ativa ao conjunto de candidatos.
        adicionar_candidato(formula_liga, "liga_binaria_ativa")

# Adiciona ligas com todos os metais ativos quando há três ou mais metais informados.
if len(metais_usuario) > 2:
    # Calcula a fração equimolar de cada metal ativo.
    fracao_equimolar = 1.0 / len(metais_usuario)
    # Monta a composição equimolar sem promotor.
    formula_multimetalica = formula_por_composicao([(metal, fracao_equimolar) for metal in metais_usuario])
    # Adiciona a liga multimetálica ao funil.
    adicionar_candidato(formula_multimetalica, "liga_multimetalica_ativa")
    # Adiciona versões promovidas da liga multimetálica quando o promotor é diferente da fase ativa.
    if promotor_usuario not in metais_usuario:
        # Percorre frações moderadas de promotor para manter diversidade química.
        for fracao_promotor in PROPORCOES_PROMOTOR_MULTIMETAL:
            # Calcula a fração total restante para os metais ativos.
            fracao_ativa_total = 1.0 - fracao_promotor
            # Divide a fração ativa igualmente entre os metais informados.
            componentes_ativos = [(metal, fracao_ativa_total / len(metais_usuario)) for metal in metais_usuario]
            # Acrescenta o promotor à composição multimetálica.
            formula_promovida = formula_por_composicao(componentes_ativos + [(promotor_usuario, fracao_promotor)])
            # Adiciona a versão promovida da liga multimetálica.
            adicionar_candidato(formula_promovida, "liga_multimetalica_ativa_promovida")

# Define a lista de frações para candidatos monometálicos promovidos.
fracs_promotor_mono = PROPORCOES_PROMOTOR if len(metais_usuario) == 1 else PROPORCOES_PROMOTOR_MULTIMETAL

# Adiciona candidatos metal-promotor para manter comparação com o comportamento monometálico.
for frac in fracs_promotor_mono:
    # Interrompe a camada se o funil inicial já estiver completo.
    if funil_inicial_completo():
        # Sai do laço de frações de promotor.
        break
    # Percorre os metais ativos alternadamente para evitar privilegiar apenas o primeiro metal informado.
    for metal in metais_usuario:
        # Interrompe a camada se o funil inicial já estiver completo.
        if funil_inicial_completo():
            # Sai do laço de metais ativos.
            break
        # Evita criar uma composição promovida quando metal ativo e promotor são o mesmo elemento.
        if metal != promotor_usuario:
            # Monta a fórmula metal-promotor.
            formula_promovida = formula_binaria(metal, promotor_usuario, frac)
            # Adiciona o candidato monometálico promovido.
            adicionar_candidato(formula_promovida, "metal_promovido")

# Adiciona ligas binárias promovidas quando há mais de um metal ativo e promotor distinto.
if len(metais_usuario) > 1 and promotor_usuario not in metais_usuario:
    # Percorre frações moderadas de promotor.
    for fracao_promotor in PROPORCOES_PROMOTOR_MULTIMETAL:
        # Interrompe a camada se o funil inicial já estiver completo.
        if funil_inicial_completo():
            # Sai do laço de frações de promotor.
            break
        # Varia a razão interna entre os dois metais ativos.
        for fracao_a_relativa in PROPORCOES_LIGA_ATIVA:
            # Interrompe a camada se o funil inicial já estiver completo.
            if funil_inicial_completo():
                # Sai do laço de frações relativas da liga.
                break
            # Percorre todos os pares de metais ativos para distribuir a biblioteca entre pares distintos.
            for metal_a, metal_b in pares_ativos:
                # Interrompe a camada se o funil inicial já estiver completo.
                if funil_inicial_completo():
                    # Sai do laço de pares de metais.
                    break
                # Calcula a fração total disponível para a fase ativa bimetálica.
                fracao_ativa_total = 1.0 - fracao_promotor
                # Calcula a fração absoluta do primeiro metal ativo.
                fracao_a = fracao_ativa_total * fracao_a_relativa
                # Calcula a fração absoluta do segundo metal ativo.
                fracao_b = fracao_ativa_total * (1.0 - fracao_a_relativa)
                # Monta a fórmula da liga ativa promovida.
                formula_liga_promovida = formula_por_composicao([(metal_a, fracao_a), (metal_b, fracao_b), (promotor_usuario, fracao_promotor)])
                # Adiciona a liga bimetálica promovida ao funil.
                adicionar_candidato(formula_liga_promovida, "liga_binaria_ativa_promovida")

# Completa o funil com ligas ativas finas quando ainda faltam candidatos, especialmente se o promotor já é um metal ativo.
if len(candidatos) < N_CANDIDATOS_GERADOS_FUNIL and len(metais_usuario) > 1:
    # Percorre frações finas para preencher a biblioteca inicial sem depender de promotor distinto.
    for fracao_a in PROPORCOES_LIGA_ATIVA_FINA:
        # Interrompe a camada se o funil inicial já estiver completo.
        if funil_inicial_completo():
            # Sai do laço de frações finas.
            break
        # Percorre os pares de metais ativos de forma balanceada.
        for metal_a, metal_b in pares_ativos:
            # Interrompe a camada se o funil inicial já estiver completo.
            if funil_inicial_completo():
                # Sai do laço de pares.
                break
            # Calcula a fração complementar do segundo metal ativo.
            fracao_b = 1.0 - fracao_a
            # Monta a fórmula fina da liga ativa.
            formula_liga_fina = formula_por_composicao([(metal_a, fracao_a), (metal_b, fracao_b)])
            # Adiciona a liga fina apenas se ela ainda não apareceu.
            adicionar_candidato(formula_liga_fina, "liga_binaria_ativa_fina")

# Converte a lista de candidatos em tabela.
candidatos_df = pd.DataFrame(candidatos)

# Remove duplicatas de fórmula.
candidatos_df = candidatos_df.drop_duplicates("formula").reset_index(drop=True)

# Limita a lista inicial ao tamanho definido para o funil.
candidatos_df = candidatos_df.head(N_CANDIDATOS_GERADOS_FUNIL).copy()

# Define uma função para listar quais metais ativos informados aparecem na fórmula.
def metais_ativos_presentes_na_formula(formula):
    # Extrai os símbolos químicos presentes na fórmula candidata.
    elementos = set(re.findall(r"[A-Z][a-z]?", str(formula)))
    # Mantém apenas os metais ativos escolhidos pelo usuário.
    return [metal for metal in metais_usuario if metal in elementos]

# Registra textualmente os metais ativos do usuário presentes em cada candidato.
candidatos_df["metais_ativos_presentes"] = candidatos_df["formula"].apply(lambda formula: ", ".join(metais_ativos_presentes_na_formula(formula)))

# Conta quantos metais ativos do usuário aparecem em cada candidato.
candidatos_df["n_metais_ativos_presentes"] = candidatos_df["formula"].apply(lambda formula: len(metais_ativos_presentes_na_formula(formula)))

# Marca candidatos que contêm dois ou mais metais ativos escolhidos pelo usuário.
candidatos_df["candidato_multimetal_ativo"] = candidatos_df["n_metais_ativos_presentes"] >= 2

# Separa uma tabela apenas com candidatos que preservam mais de um metal ativo.
candidatos_multimetal_ativo_df = candidatos_df[candidatos_df["candidato_multimetal_ativo"]].copy()

# Avisa quando a grade com duas casas decimais não permite atingir 1000 fórmulas únicas.
if len(candidatos_df) < N_CANDIDATOS_GERADOS_FUNIL:
    # Explica que a limitação vem da combinação entre duas casas decimais e espaço químico pequeno.
    print(
        f"Aviso: foram gerados {len(candidatos_df)} candidatos únicos. "
        f"Com duas casas decimais, sistemas com poucos elementos podem não atingir {N_CANDIDATOS_GERADOS_FUNIL} fórmulas únicas."
    )

# Mostra a quantidade e os primeiros candidatos.
print("Candidatos gerados:", len(candidatos_df))

# Mostra a distribuição por tipo para confirmar se ligas multimetálicas entraram no funil.
print("Distribuição por tipo de candidato:")
print(candidatos_df["tipo"].value_counts())

# Mostra quantos candidatos realmente contêm dois ou mais metais ativos informados.
print("Candidatos com dois ou mais metais ativos:", len(candidatos_multimetal_ativo_df))

# Mostra candidatos gerais e, quando houver mais de um metal ativo, mostra também a tabela multimetálica.
try:
    # Exibe os primeiros candidatos gerais no ambiente Jupyter/Colab.
    display(candidatos_df.head(20))
    # Exibe candidatos com mais de um metal ativo quando o usuário informou múltiplos metais.
    if len(metais_usuario) > 1:
        # Mostra os primeiros candidatos que contêm o segundo metal ativo.
        display(candidatos_multimetal_ativo_df[["formula", "tipo", "metais_ativos_presentes", "n_metais_ativos_presentes"]].head(20))
except NameError:
    # Usa impressão textual quando display não está disponível.
    print(candidatos_df.head(20))
    # Mostra a tabela textual multimetálica quando aplicável.
    if len(metais_usuario) > 1:
        # Imprime os primeiros candidatos com dois ou mais metais ativos.
        print(candidatos_multimetal_ativo_df[["formula", "tipo", "metais_ativos_presentes", "n_metais_ativos_presentes"]].head(20))

# Retorna a tabela multimetálica quando houver mais de um metal ativo, facilitando a conferência visual.
candidatos_multimetal_ativo_df.head(20) if len(metais_usuario) > 1 else candidatos_df.head(20)
"""
    ),
    md(
        """
## Etapa 5 - Busca de propriedades de materiais

Esta etapa procura candidatos iguais ou relacionados na base local derivada do notebook base. Quando um candidato não tem correspondência exata, o notebook identifica o sistema químico correspondente e tenta buscar novos dados de estabilidade e propriedades bulk no Materials Project e no OQMD. Os dados obtidos são anexados ao banco local em `outputs/` para reutilização em execuções futuras. O notebook não depende de GitHub: todo incremento de dados é feito em arquivos CSV locais. Se o sistema químico já foi consultado com sucesso antes, o notebook não baixa novamente.
"""
    ),
    code(
        """
# Define dono do reposit?rio usado como armazenamento incremental persistente.
GITHUB_INCREMENTAL_OWNER = os.environ.get("TRIAGEM_GITHUB_OWNER", "").strip()

# Define nome do reposit?rio usado como armazenamento incremental persistente.
GITHUB_INCREMENTAL_REPO = os.environ.get("TRIAGEM_GITHUB_REPO", "").strip()

# Define branch usado para ler e gravar os CSVs incrementais.
GITHUB_INCREMENTAL_BRANCH = os.environ.get("TRIAGEM_GITHUB_BRANCH", "main").strip() or "main"

# L? token GitHub dos secrets/ambiente; quando ausente, a sincroniza??o externa ? apenas ignorada.
GITHUB_INCREMENTAL_TOKEN = os.environ.get("TRIAGEM_GITHUB_TOKEN", "").strip()

# Define caminho do banco principal no reposit?rio.
GITHUB_RANKING_PATH = os.environ.get("TRIAGEM_GITHUB_RANKING_PATH", "outputs/ranking_multicriterio_v2_incerteza_explicabilidade.csv").strip()

# Define caminho do hist?rico de consultas externas no reposit?rio.
GITHUB_CONSULTAS_PATH = os.environ.get("TRIAGEM_GITHUB_CONSULTAS_PATH", "outputs/consultas_bases_externas.csv").strip()

# Define caminho do cache Catalysis-Hub no reposit?rio.
GITHUB_CATHUB_PATH = os.environ.get("TRIAGEM_GITHUB_CATHUB_PATH", "outputs/catalysis_hub_incremental.csv").strip()

# Define caminho do cache GNN local no reposit?rio.
GITHUB_GNN_PATH = os.environ.get("TRIAGEM_GITHUB_GNN_PATH", "outputs/proxy_gnn_local.csv").strip()

# Define fun??o que informa se a sincroniza??o GitHub est? dispon?vel.
def github_incremental_configurado():
    # Exige dono, reposit?rio e token para permitir escrita persistente.
    return bool(GITHUB_INCREMENTAL_OWNER and GITHUB_INCREMENTAL_REPO and GITHUB_INCREMENTAL_TOKEN)

# Define fun??o para montar cabe?alhos autenticados da API GitHub.
def github_incremental_headers():
    # Retorna cabe?alhos com token sem expor seu conte?do no notebook.
    return {
        "Authorization": f"Bearer {GITHUB_INCREMENTAL_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

# Define fun??o para obter metadados de um arquivo no GitHub.
def github_obter_arquivo(caminho_repo):
    # Retorna vazio quando n?o h? configura??o de persist?ncia.
    if not github_incremental_configurado():
        return None
    # Monta endpoint da API Contents do GitHub.
    url = f"https://api.github.com/repos/{GITHUB_INCREMENTAL_OWNER}/{GITHUB_INCREMENTAL_REPO}/contents/{caminho_repo}"
    try:
        # Busca o arquivo no branch configurado.
        resposta = requests.get(url, headers=github_incremental_headers(), params={"ref": GITHUB_INCREMENTAL_BRANCH}, timeout=20)
        # Arquivo ausente n?o ? erro; ele ser? criado no primeiro envio.
        if resposta.status_code == 404:
            return None
        # Interrompe para outros erros HTTP.
        resposta.raise_for_status()
        # Retorna metadados do arquivo.
        return resposta.json()
    except Exception as erro_github:
        # Registra o problema sem interromper a triagem.
        print(f"Sincronizacao GitHub indisponivel para {caminho_repo}: {erro_github}")
        return None

# Define fun??o para baixar um CSV persistido no GitHub antes da triagem.
def baixar_csv_incremental_github(caminho_repo, destino_local):
    # Ignora quando GitHub persistente n?o foi configurado.
    if not github_incremental_configurado():
        return False
    # Obt?m metadados e conte?do codificado do arquivo.
    payload = github_obter_arquivo(caminho_repo)
    # Retorna falso se o arquivo ainda n?o existe no reposit?rio.
    if not payload or "content" not in payload:
        return False
    try:
        # Garante que a pasta local existe.
        destino_local.parent.mkdir(parents=True, exist_ok=True)
        # Decodifica o conte?do base64 retornado pela API.
        conteudo = base64.b64decode(str(payload["content"]).replace(chr(10), ""))
        # Grava o CSV localmente para o restante do notebook ler normalmente.
        destino_local.write_bytes(conteudo)
        # Retorna verdadeiro quando houve sincroniza??o.
        return True
    except Exception as erro_github:
        # Registra falha sem interromper o fluxo.
        print(f"Nao foi possivel baixar {caminho_repo} do GitHub: {erro_github}")
        return False

# Define fun??o para enviar CSV incremental atualizado de volta ao GitHub.
def enviar_csv_incremental_github(caminho_repo, origem_local, mensagem):
    # Ignora quando GitHub persistente n?o foi configurado ou arquivo local n?o existe.
    if not github_incremental_configurado() or not origem_local.exists():
        return False
    # Obt?m metadados atuais para recuperar o SHA quando o arquivo j? existe.
    payload_atual = github_obter_arquivo(caminho_repo)
    # Monta endpoint da API Contents do GitHub.
    url = f"https://api.github.com/repos/{GITHUB_INCREMENTAL_OWNER}/{GITHUB_INCREMENTAL_REPO}/contents/{caminho_repo}"
    try:
        # Codifica o conte?do local em base64 para envio ? API.
        conteudo_b64 = base64.b64encode(origem_local.read_bytes()).decode("ascii")
        # Monta corpo da requisi??o com branch e mensagem de commit.
        corpo = {"message": mensagem, "content": conteudo_b64, "branch": GITHUB_INCREMENTAL_BRANCH}
        # Inclui SHA quando o arquivo j? existe, evitando criar duplicata.
        if payload_atual and payload_atual.get("sha"):
            corpo["sha"] = payload_atual["sha"]
        # Envia cria??o ou atualiza??o do arquivo.
        resposta = requests.put(url, headers=github_incremental_headers(), json=corpo, timeout=30)
        # Interrompe se o GitHub retornar erro.
        resposta.raise_for_status()
        # Retorna verdadeiro quando o commit foi aceito.
        return True
    except Exception as erro_github:
        # Registra falha sem interromper a triagem.
        print(f"Nao foi possivel enviar {caminho_repo} ao GitHub: {erro_github}")
        return False

# Baixa a vers?o mais recente do banco principal antes de carregar os dados.
baixar_csv_incremental_github(GITHUB_RANKING_PATH, RANKING_FILE)

# Carrega a base local de triagem se ela existir.
if RANKING_FILE.exists():
    # Lê a tabela com dados de estabilidade, descritores e evidências externas.
    base_local = pd.read_csv(RANKING_FILE)
else:
    # Cria uma tabela vazia se a base local não estiver disponível.
    base_local = pd.DataFrame()

# Define uma função para extrair elementos químicos de uma fórmula.
def elementos_formula(formula):
    # Usa expressão regular para capturar símbolos químicos.
    return set(re.findall(r"[A-Z][a-z]?", str(formula)))

# Define o arquivo que registra sistemas químicos já consultados externamente.
CONSULTAS_EXTERNAS_FILE = PROJECT_DATA_DIR / "consultas_bases_externas.csv"

# Prepara o histórico local de consultas externas antes de decidir o que consultar.
baixar_csv_incremental_github(GITHUB_CONSULTAS_PATH, CONSULTAS_EXTERNAS_FILE)

# Carrega o histórico de consultas externas para evitar baixar o mesmo sistema novamente.
consultas_externas_df = pd.read_csv(CONSULTAS_EXTERNAS_FILE) if CONSULTAS_EXTERNAS_FILE.exists() else pd.DataFrame(columns=["fonte", "chemsys", "n_registros", "status", "data_consulta"])

# Define função para converter uma fórmula em sistema químico ordenado.
def chemsys_formula(formula):
    # Extrai elementos químicos e remove duplicatas.
    elementos = sorted(elementos_formula(formula))
    # Retorna sistema químico no formato usado por MP/OQMD.
    return "-".join(elementos)

# Define função para verificar se um sistema químico já foi consultado em uma fonte.
def consulta_ja_realizada(fonte, chemsys):
    # Retorna falso se ainda não houver histórico.
    if consultas_externas_df.empty:
        return False
    # Verifica fonte e sistema químico no histórico local.
    mask = (
        (consultas_externas_df["fonte"].astype(str) == fonte)
        & (consultas_externas_df["chemsys"].astype(str) == chemsys)
        & (consultas_externas_df["status"].astype(str) == "ok")
    )
    # Retorna verdadeiro se já existe registro de consulta.
    return bool(mask.any())

# Define função para registrar uma consulta externa no histórico local.
def registrar_consulta(fonte, chemsys, n_registros, status):
    # Usa a variável global para atualizar o histórico carregado.
    global consultas_externas_df
    # Cria uma linha de log da consulta.
    linha = pd.DataFrame([{
        "fonte": fonte,
        "chemsys": chemsys,
        "n_registros": int(n_registros),
        "status": status,
        "data_consulta": pd.Timestamp.now().isoformat(timespec="seconds"),
    }])
    # Adiciona a linha ao histórico.
    consultas_externas_df = pd.concat([consultas_externas_df, linha], ignore_index=True)
    # Salva o histórico atualizado.
    consultas_externas_df.to_csv(CONSULTAS_EXTERNAS_FILE, index=False, encoding="utf-8-sig")

# Define função para obter a chave do Materials Project usada nas consultas incrementais.
def obter_chave_mp():
    # Lê a chave de variável de ambiente quando disponível para permitir substituição sem editar o notebook.
    chave = os.environ.get("MP_API_KEY", "").strip()
    # Usa a chave salva no notebook quando não houver variável de ambiente configurada.
    if not chave:
        chave = MP_API_KEY_SALVA.strip()
    # Se ainda não houver chave, pergunta de forma oculta ao usuário.
    if not chave:
        try:
            # Solicita a chave sem eco visual.
            chave = getpass("Digite sua chave do Materials Project para buscar dados ausentes, ou deixe vazio para pular MP: ").strip()
        except Exception:
            # Usa string vazia em execução não interativa sem chave.
            chave = ""
    # Retorna a chave ou string vazia.
    return chave

# Define função para consultar Materials Project para um sistema químico ainda ausente.
def baixar_mp_chemsys(chemsys, limite=50):
    # Ignora consulta se o sistema já foi consultado antes no MP.
    if consulta_ja_realizada("Materials Project", chemsys):
        return pd.DataFrame()
    # Obtém a chave do Materials Project.
    api_key = obter_chave_mp()
    # Se não houver chave, registra que o MP foi pulado.
    if not api_key:
        registrar_consulta("Materials Project", chemsys, 0, "sem_chave")
        return pd.DataFrame()
    # Tenta importar o cliente oficial do Materials Project.
    try:
        # Importa MPRester para consulta ao Materials Project.
        from mp_api.client import MPRester
    except ModuleNotFoundError:
        try:
            # Instala mp-api no mesmo ambiente quando estiver ausente.
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mp-api"])
            # Importa novamente após instalação.
            from mp_api.client import MPRester
        except Exception as erro_instalacao:
            # Registra falha de instalação.
            registrar_consulta("Materials Project", chemsys, 0, f"erro_instalacao: {erro_instalacao}")
            return pd.DataFrame()
    # Define campos necessários para enriquecer a base local.
    campos = ["material_id", "formula_pretty", "elements", "energy_above_hull", "formation_energy_per_atom", "band_gap", "density", "volume", "nsites", "symmetry"]
    # Cria lista para armazenar registros retornados.
    registros = []
    try:
        # Abre conexão com o Materials Project.
        with MPRester(api_key) as mpr:
            # Consulta materiais do sistema químico.
            docs = mpr.materials.summary.search(chemsys=chemsys, fields=campos)
    except Exception as erro_mp:
        # Registra falha da chamada.
        registrar_consulta("Materials Project", chemsys, 0, f"erro: {erro_mp}")
        return pd.DataFrame()
    # Percorre documentos retornados, limitando o volume anexado.
    for doc in docs[:limite]:
        # Recupera simetria quando disponível.
        symmetry = getattr(doc, "symmetry", None)
        # Adiciona registro normalizado.
        registros.append({
            "material_id": str(doc.material_id),
            "formula": getattr(doc, "formula_pretty", np.nan),
            "chemsys_consultado": chemsys,
            "origem": "materials_project_incremental",
            "energy_above_hull": getattr(doc, "energy_above_hull", np.nan),
            "formation_energy_per_atom": getattr(doc, "formation_energy_per_atom", np.nan),
            "band_gap": getattr(doc, "band_gap", np.nan),
            "density": getattr(doc, "density", np.nan),
            "volume": getattr(doc, "volume", np.nan),
            "nsites": getattr(doc, "nsites", np.nan),
            "crystal_system": getattr(symmetry, "crystal_system", np.nan) if symmetry else np.nan,
            "symbol": getattr(symmetry, "symbol", np.nan) if symmetry else np.nan,
            "elements": ",".join([str(e) for e in getattr(doc, "elements", [])]) if getattr(doc, "elements", None) else np.nan,
            "fonte_estabilidade_v2": "MP",
            "energy_above_hull_screening_v2": getattr(doc, "energy_above_hull", np.nan),
            "estabilidade_real_disponivel": True,
        })
    # Converte registros em tabela.
    df_mp_novo = pd.DataFrame(registros)
    # Registra consulta concluída.
    registrar_consulta("Materials Project", chemsys, len(df_mp_novo), "ok")
    # Retorna dados coletados.
    return df_mp_novo

# Define função para consultar OQMD para um sistema químico ainda ausente.
def baixar_oqmd_chemsys(chemsys, limite=50):
    # Ignora consulta se o sistema já foi consultado antes no OQMD.
    if consulta_ja_realizada("OQMD", chemsys):
        return pd.DataFrame()
    # Define endpoint REST do OQMD.
    url = "https://oqmd.org/oqmdapi/formationenergy"
    # Define campos de interesse para estabilidade termodinâmica.
    campos = "name,entry_id,delta_e,stability,band_gap,ntypes,natoms,volume,spacegroup,prototype"
    # Define parâmetros da consulta.
    params = {
        "fields": campos,
        "filter": f"element_set=({chemsys})",
        "limit": limite,
        "format": "json",
        "noduplicate": "True",
        "sort_by": "stability",
    }
    try:
        # Executa chamada HTTP com timeout.
        resposta = requests.get(url, params=params, timeout=30)
        # Interrompe se o status HTTP indicar erro.
        resposta.raise_for_status()
        # Converte resposta em JSON.
        payload = resposta.json()
    except Exception as erro_oqmd:
        # Registra falha da chamada.
        registrar_consulta("OQMD", chemsys, 0, f"erro: {erro_oqmd}")
        return pd.DataFrame()
    # Cria lista para armazenar registros.
    registros = []
    # Percorre itens retornados pelo OQMD.
    for item in payload.get("data", []):
        # Lê estabilidade termodinâmica do OQMD.
        estabilidade = item.get("stability")
        # Ignora registros sem estabilidade.
        if estabilidade is None:
            continue
        # Adiciona registro normalizado.
        registros.append({
            "material_id": f"oqmd-{item.get('entry_id')}",
            "formula": item.get("name"),
            "chemsys_consultado": chemsys,
            "origem": "oqmd_incremental",
            "energy_above_hull": max(float(estabilidade), 0.0),
            "formation_energy_per_atom": item.get("delta_e"),
            "band_gap": item.get("band_gap"),
            "density": np.nan,
            "volume": item.get("volume"),
            "nsites": item.get("natoms"),
            "crystal_system": np.nan,
            "symbol": item.get("spacegroup"),
            "elements": ",".join(sorted(chemsys.split("-"))),
            "fonte_estabilidade_v2": "OQMD",
            "energy_above_hull_screening_v2": max(float(estabilidade), 0.0),
            "energy_above_hull_oqmd": max(float(estabilidade), 0.0),
            "formation_energy_oqmd": item.get("delta_e"),
            "band_gap_oqmd": item.get("band_gap"),
            "oqmd_material_id": f"oqmd-{item.get('entry_id')}",
            "estabilidade_real_disponivel": True,
        })
    # Converte registros em tabela.
    df_oqmd_novo = pd.DataFrame(registros)
    # Registra consulta concluída.
    registrar_consulta("OQMD", chemsys, len(df_oqmd_novo), "ok")
    # Pausa curta para reduzir agressividade da consulta.
    time.sleep(0.15)
    # Retorna dados coletados.
    return df_oqmd_novo

# Define função para anexar dados novos à base local mantendo o schema existente.
def anexar_dados_base_local(base, novos):
    # Retorna a base original se não houver dados novos.
    if not novos:
        return base
    # Junta tabelas novas não vazias.
    novos_df = pd.concat([df for df in novos if isinstance(df, pd.DataFrame) and not df.empty], ignore_index=True, sort=False) if any(isinstance(df, pd.DataFrame) and not df.empty for df in novos) else pd.DataFrame()
    # Retorna a base original se a concatenação ficou vazia.
    if novos_df.empty:
        return base
    # Une colunas da base antiga e dos dados novos.
    base_atualizada = pd.concat([base, novos_df], ignore_index=True, sort=False)
    # Remove duplicatas por material_id quando possível.
    if "material_id" in base_atualizada.columns:
        base_atualizada = base_atualizada.drop_duplicates(subset=["material_id"], keep="first")
    # Remove duplicatas por fórmula e origem como proteção adicional.
    if {"formula", "origem"}.issubset(base_atualizada.columns):
        base_atualizada = base_atualizada.drop_duplicates(subset=["formula", "origem"], keep="first")
    # Salva a base local atualizada.
    base_atualizada.to_csv(RANKING_FILE, index=False, encoding="utf-8-sig")
    # Registra a atualização da base principal local para rastreabilidade da execução.
    enviar_csv_incremental_github(GITHUB_RANKING_PATH, RANKING_FILE, "Atualiza banco incremental de triagem")
    # Retorna a base atualizada.
    return base_atualizada.reset_index(drop=True)

# Identifica fórmulas já existentes exatamente na base local.
formulas_base = set(base_local["formula"].dropna().astype(str)) if "formula" in base_local.columns else set()

# Identifica candidatos sem correspondência exata na base local.
candidatos_sem_dado_exato = candidatos_df[~candidatos_df["formula"].astype(str).isin(formulas_base)].copy()

# Monta sistemas químicos únicos para busca externa incremental.
chemsys_para_buscar = sorted({
    chemsys_formula(formula)
    for formula in candidatos_sem_dado_exato["formula"]
    if chemsys_formula(formula)
})

# Cria lista para armazenar novos registros baixados.
novos_registros_externos = []

# Consulta apenas sistemas químicos ainda não consultados.
for chemsys in chemsys_para_buscar:
    # Baixa dados do Materials Project quando necessário e possível.
    novos_registros_externos.append(baixar_mp_chemsys(chemsys))
    # Baixa dados do OQMD quando necessário.
    novos_registros_externos.append(baixar_oqmd_chemsys(chemsys))

# Anexa dados novos à base local e recarrega a base usada na triagem.
base_local = anexar_dados_base_local(base_local, novos_registros_externos)

# Registra o histórico de consultas externas para reutilização em execuções futuras.
enviar_csv_incremental_github(GITHUB_CONSULTAS_PATH, CONSULTAS_EXTERNAS_FILE, "Atualiza historico incremental de consultas externas")

# Mostra resumo da atualização incremental.
print("Candidatos sem correspondência exata:", len(candidatos_sem_dado_exato))
print("Sistemas químicos avaliados para atualização:", chemsys_para_buscar)
print("Tamanho atual da base local:", len(base_local))

# Define uma função para encontrar a melhor correspondência local de um candidato.
def buscar_propriedade_local(formula):
    # Retorna dados vazios se a base local estiver vazia.
    if base_local.empty:
        return {}
    # Procura correspondência exata de fórmula.
    exata = base_local[base_local["formula"].astype(str).eq(str(formula))]
    # Retorna a primeira correspondência exata se existir.
    if not exata.empty:
        return exata.iloc[0].to_dict()
    # Extrai elementos do candidato.
    elems = elementos_formula(formula)
    # Calcula sobreposição de elementos com cada fórmula da base local.
    base_local["_overlap_temp"] = base_local["formula"].astype(str).apply(lambda f: len(elems & elementos_formula(f)))
    # Seleciona linhas com alguma sobreposição.
    relacionadas = base_local[base_local["_overlap_temp"] > 0].sort_values(["_overlap_temp", "score_multicriterio_v2"], ascending=False)
    # Retorna a melhor linha relacionada se existir.
    if not relacionadas.empty:
        return relacionadas.iloc[0].to_dict()
    # Retorna vazio quando não há informação relacionada.
    return {}

# Aplica a busca de propriedades locais a cada candidato.
propriedades = [buscar_propriedade_local(f) for f in candidatos_df["formula"]]

# Converte as propriedades encontradas em tabela.
propriedades_df = pd.DataFrame(propriedades)

# Junta candidatos gerados e propriedades encontradas.
triagem_df = pd.concat([candidatos_df, propriedades_df.add_prefix("prop_")], axis=1)

# Mostra uma visão inicial das propriedades disponíveis.
triagem_df.head()
"""
    ),
    md(
        """
## Etapa 6 - Cálculo de descritores químicos específicos da reação

Os descritores são escolhidos conforme a reação. A mesma composição pode ser boa para metanação e ruim para RWGS, por isso os scores mudam conforme o objetivo catalítico.
"""
    ),
    code(
        """
# Define valores químicos simples usados quando a base local não traz descritores completos.
PROPRIEDADES_ELEMENTOS = {
    "Ni": {"ativo": 1.00, "redox": 0.30, "basicidade": 0.10, "nobre": 0.00, "coque": 0.55},
    "Co": {"ativo": 0.78, "redox": 0.35, "basicidade": 0.10, "nobre": 0.00, "coque": 0.45},
    "Fe": {"ativo": 0.55, "redox": 0.45, "basicidade": 0.10, "nobre": 0.00, "coque": 0.35},
    "Ru": {"ativo": 0.95, "redox": 0.40, "basicidade": 0.10, "nobre": 1.00, "coque": 0.70},
    "Rh": {"ativo": 0.92, "redox": 0.38, "basicidade": 0.10, "nobre": 1.00, "coque": 0.72},
    "Pt": {"ativo": 0.65, "redox": 0.25, "basicidade": 0.10, "nobre": 1.00, "coque": 0.65},
    "Pd": {"ativo": 0.58, "redox": 0.25, "basicidade": 0.10, "nobre": 1.00, "coque": 0.60},
    "Ce": {"ativo": 0.20, "redox": 1.00, "basicidade": 0.65, "nobre": 0.00, "coque": 0.85},
    "Zr": {"ativo": 0.18, "redox": 0.78, "basicidade": 0.45, "nobre": 0.00, "coque": 0.78},
    "Mg": {"ativo": 0.10, "redox": 0.20, "basicidade": 0.95, "nobre": 0.00, "coque": 0.70},
    "La": {"ativo": 0.10, "redox": 0.55, "basicidade": 0.88, "nobre": 0.00, "coque": 0.82},
    "Cu": {"ativo": 0.35, "redox": 0.40, "basicidade": 0.10, "nobre": 0.00, "coque": 0.45},
    "Mo": {"ativo": 0.35, "redox": 0.65, "basicidade": 0.20, "nobre": 0.00, "coque": 0.55},
}

# Define uma função para calcular média de uma propriedade elementar.
def media_elementar(formula, chave):
    # Extrai elementos presentes na fórmula.
    elems = elementos_formula(formula)
    # Busca a propriedade de cada elemento conhecido.
    valores = [PROPRIEDADES_ELEMENTOS.get(e, {}).get(chave, 0.25) for e in elems]
    # Retorna a média ou valor baixo quando a lista estiver vazia.
    return float(np.mean(valores)) if valores else 0.25

# Define uma funcao auxiliar para perguntar ao usuario sem mostrar resposta previa.
def obter(row, coluna, padrao):
    # Monta o nome da coluna prefixada.
    nome = "prop_" + coluna
    # Retorna o valor se ele existir e não for nulo.
    if nome in row and pd.notna(row[nome]):
        return row[nome]
    # Retorna o padrão se não houver dado local.
    return padrao

# Define uma função que calcula descritores de acordo com a reação.
def calcular_descritores(row):
    # Lê a fórmula do candidato.
    formula = row["formula"]
    # Calcula score de metal ativo.
    ativo = float(obter(row, "cat_active_metal_proxy", media_elementar(formula, "ativo")))
    # Calcula score redox associado a vacâncias/mobilidade de oxigênio.
    redox = float(obter(row, "cat_redox_proxy", media_elementar(formula, "redox")))
    # Calcula score de basicidade para ativação de CO2.
    basicidade = float(obter(row, "cat_basicity_proxy", media_elementar(formula, "basicidade")))
    # Calcula fração nobre aproximada.
    nobre = float(obter(row, "cat_noble_fraction", media_elementar(formula, "nobre")))
    # Calcula resistência a coque aproximada.
    coque = media_elementar(formula, "coque")
    # Define descritores para metanação.
    if reacao == "metanacao":
        atividade = np.mean([ativo, redox, basicidade])
        seletividade = float(obter(row, "score_seletividade_CH4", obter(row, "cat_ch4_selectivity_prior", 0.60)))
        dft_proxy = np.mean([redox, basicidade, seletividade])
    # Define descritores para reforma.
    elif reacao == "reforma":
        atividade = np.mean([ativo, redox])
        seletividade = np.mean([coque, redox])
        dft_proxy = np.mean([coque, redox, ativo])
    # Define descritores para RWGS.
    else:
        atividade = np.mean([ativo, redox])
        seletividade = np.mean([redox, 1.0 - 0.60 * float(obter(row, "cat_ch4_selectivity_prior", 0.50))])
        dft_proxy = np.mean([redox, seletividade, atividade])
    # Retorna os descritores em uma série.
    return pd.Series({
        "score_atividade": np.clip(atividade, 0, 1),
        "score_seletividade": np.clip(seletividade, 0, 1),
        "score_DFT_proxy": np.clip(dft_proxy, 0, 1),
        "score_basicidade": np.clip(basicidade, 0, 1),
        "score_redox": np.clip(redox, 0, 1),
        "score_resistencia_coque": np.clip(coque, 0, 1),
    })

# Calcula descritores para todos os candidatos.
descritores_df = triagem_df.apply(calcular_descritores, axis=1)

# Junta descritores à tabela principal.
triagem_df = pd.concat([triagem_df, descritores_df], axis=1)

# Define funcao auxiliar para normalizacao min-max robusta e reutilizavel.
def normalizar_minmax_global(serie, invertido=False, p_baixo=0.05, p_alto=0.95, neutro=0.5):
    # Converte a serie para numerica e preserva ausencias.
    valores = pd.to_numeric(serie, errors="coerce")
    # Cria uma serie neutra para preencher casos sem dados.
    resultado = pd.Series(neutro, index=serie.index, dtype=float)
    # Retorna score neutro quando a coluna nao tem dados suficientes.
    if valores.notna().sum() < 2:
        return resultado
    # Calcula limite inferior robusto por percentil.
    limite_baixo = valores.quantile(p_baixo)
    # Calcula limite superior robusto por percentil.
    limite_alto = valores.quantile(p_alto)
    # Retorna score neutro quando nao ha variacao util.
    if pd.isna(limite_baixo) or pd.isna(limite_alto) or limite_alto == limite_baixo:
        return resultado
    # Aplica winsorizacao antes da normalizacao.
    valores_clipados = valores.clip(limite_baixo, limite_alto)
    # Normaliza no intervalo zero a um.
    normalizado = (valores_clipados - limite_baixo) / (limite_alto - limite_baixo)
    # Inverte quando valores menores representam melhor desempenho.
    if invertido:
        normalizado = 1.0 - normalizado
    # Preserva neutro onde havia ausencia.
    resultado.loc[valores.notna()] = normalizado.loc[valores.notna()].clip(0, 1)
    # Retorna serie normalizada.
    return resultado

# Define normalizacao robusta por z-score para metricas que precisam de escala padronizada.
def normalizar_standard_robusto(serie, invertido=False, neutro=0.5):
    # Converte valores para numerico.
    valores = pd.to_numeric(serie, errors="coerce")
    # Cria resultado neutro.
    resultado = pd.Series(neutro, index=serie.index, dtype=float)
    # Retorna neutro quando nao ha dados suficientes.
    if valores.notna().sum() < 2:
        return resultado
    # Calcula mediana robusta.
    mediana = valores.median()
    # Calcula desvio absoluto mediano.
    mad = (valores - mediana).abs().median()
    # Retorna neutro quando nao ha dispersao.
    if pd.isna(mad) or mad == 0:
        return resultado
    # Calcula z-score robusto.
    z = (valores - mediana) / (1.4826 * mad)
    # Converte z-score em escala sigmoidal entre zero e um.
    normalizado = 1.0 / (1.0 + np.exp(-z.clip(-6, 6)))
    # Inverte quando menor e melhor.
    if invertido:
        normalizado = 1.0 - normalizado
    # Preserva neutro onde havia ausencia.
    resultado.loc[valores.notna()] = normalizado.loc[valores.notna()].clip(0, 1)
    # Retorna serie normalizada.
    return resultado

# Mostra os descritores calculados.
triagem_df[["formula", "score_atividade", "score_seletividade", "score_DFT_proxy", "score_basicidade", "score_redox"]].head(20)
"""
    ),
    md(
        """
### Subetapa 6.1 - Descritores composicionais obrigatorios com matminer

Esta subetapa usa `matminer` como parte obrigatoria da triagem. O pacote e instalado/importado na etapa 1; aqui o notebook calcula descritores Magpie a partir das formulas quimicas e interrompe a execucao se eles nao puderem ser gerados. O score composicional usa pesos diferentes para metanacao, reforma e RWGS, porque cada rota valoriza propriedades quimicas diferentes.
"""
    ),
    code(
        """
# Comeca assumindo que o matminer ainda nao foi ativado na etapa atual.
matminer_disponivel = False

# Cria lista vazia para guardar os nomes dos descritores Magpie calculados.
matminer_feature_cols = []

# Importa conversor de formula textual para objeto de composicao.
try:
    # Importa conversor de formula textual para objeto de composicao.
    from matminer.featurizers.conversions import StrToComposition
    # Importa gerador de descritores composicionais baseados no preset Magpie.
    from matminer.featurizers.composition import ElementProperty
    # Marca o matminer como disponivel quando as importacoes funcionam.
    matminer_disponivel = True
# Interrompe a etapa se o matminer nao estiver funcional, pois agora ele e obrigatorio.
except Exception as erro_matminer:
    # Gera erro claro em vez de seguir com fallback neutro.
    raise RuntimeError(f"Matminer e obrigatorio para a etapa 6.1, mas nao foi importado: {erro_matminer}") from erro_matminer

# Copia a coluna de formulas para uma tabela temporaria de featurizacao.
matminer_descritores_df = triagem_df[["formula"]].copy()

# Cria o conversor de formula para composicao.
conversor = StrToComposition(target_col_id="composition")

# Converte formulas em composicoes quimicas, ignorando erros pontuais de formula.
matminer_descritores_df = conversor.featurize_dataframe(matminer_descritores_df, "formula", ignore_errors=True)

# Cria o featurizer Magpie.
featurizer_magpie = ElementProperty.from_preset("magpie")

# Calcula descritores Magpie para cada composicao valida.
matminer_descritores_df = featurizer_magpie.featurize_dataframe(matminer_descritores_df, col_id="composition", ignore_errors=True)

# Identifica colunas numericas geradas pelo preset Magpie.
matminer_feature_cols = [col for col in matminer_descritores_df.columns if col.startswith("MagpieData")]

# Interrompe se nenhum descritor Magpie foi calculado.
if not matminer_feature_cols:
    # Evita que a etapa obrigatoria seja tratada como neutra sem perceber.
    raise RuntimeError("Nenhum descritor Magpie foi calculado pelo matminer na etapa 6.1.")

# Seleciona descritores uteis para criar um score composicional por reacao.
col_numero_medio = next((col for col in matminer_feature_cols if col.endswith("mean Number")), None)

# Seleciona dispersao de numero atomico quando existir.
col_numero_desvio = next((col for col in matminer_feature_cols if col.endswith("avg_dev Number")), None)

# Seleciona eletronegatividade media quando existir.
col_eletro_medio = next((col for col in matminer_feature_cols if "mean Electronegativity" in col), None)

# Seleciona dispersao de eletronegatividade quando existir.
col_eletro_desvio = next((col for col in matminer_feature_cols if "avg_dev Electronegativity" in col), None)

# Junta apenas os descritores Magpie a tabela principal pelo indice original.
triagem_df = pd.concat([triagem_df.reset_index(drop=True), matminer_descritores_df[matminer_feature_cols].reset_index(drop=True)], axis=1)

# Usa a normalizacao robusta centralizada para reduzir efeito de outliers.
def normalizar_minmax(serie):
    # Encaminha a serie para a funcao global robusta.
    return normalizar_minmax_global(serie, neutro=0.0)

# Define pesos Magpie especificos para cada rota catalitica.
# Justificativa MCDA: estes pesos sao heuristicas iniciais de especialista.
# Eles tornam explicita a importancia relativa de composicao, eletronegatividade
# e heterogeneidade eletronica em cada reacao; nao sao parametros ajustados por regressao.
PESOS_MAGPIE_REACAO = {
    # Metanacao valoriza ativacao de CO2 e interfaces com diferenca de eletronegatividade.
    "metanacao": {"numero_medio": 0.15, "numero_desvio": 0.20, "eletro_medio": 0.20, "eletro_desvio": 0.25},
    # Reforma valoriza heterogeneidade composicional e propriedades associadas a resistencia a coque.
    "reforma": {"numero_medio": 0.10, "numero_desvio": 0.20, "eletro_medio": 0.20, "eletro_desvio": 0.30},
    # RWGS valoriza ajuste eletronico para favorecer CO e evitar metanacao excessiva.
    "rwgs": {"numero_medio": 0.10, "numero_desvio": 0.15, "eletro_medio": 0.30, "eletro_desvio": 0.25},
}

# Seleciona os pesos da reacao atual.
pesos_magpie = PESOS_MAGPIE_REACAO.get(reacao, PESOS_MAGPIE_REACAO["metanacao"])

# Inicializa o score composicional Magpie com base baixa para depender dos descritores calculados.
triagem_df["score_matminer_composicional"] = 0.20

# Adiciona contribuicao de numero atomico medio quando disponivel.
if col_numero_medio:
    triagem_df["score_matminer_composicional"] += pesos_magpie["numero_medio"] * normalizar_minmax(triagem_df[col_numero_medio])

# Adiciona contribuicao de diversidade de numero atomico quando disponivel.
if col_numero_desvio:
    triagem_df["score_matminer_composicional"] += pesos_magpie["numero_desvio"] * normalizar_minmax(triagem_df[col_numero_desvio])

# Adiciona contribuicao de eletronegatividade media quando disponivel.
if col_eletro_medio:
    triagem_df["score_matminer_composicional"] += pesos_magpie["eletro_medio"] * normalizar_minmax(triagem_df[col_eletro_medio])

# Adiciona contribuicao de heterogeneidade de eletronegatividade quando disponivel.
if col_eletro_desvio:
    triagem_df["score_matminer_composicional"] += pesos_magpie["eletro_desvio"] * normalizar_minmax(triagem_df[col_eletro_desvio])

# Limita o score composicional ao intervalo de zero a um.
triagem_df["score_matminer_composicional"] = triagem_df["score_matminer_composicional"].clip(0, 1)

# Enriquece o proxy DFT com maior peso dos descritores Magpie obrigatorios.
triagem_df["score_DFT_proxy"] = (0.80 * triagem_df["score_DFT_proxy"] + 0.20 * triagem_df["score_matminer_composicional"]).clip(0, 1)

# Enriquece a atividade com contribuicao composicional Magpie mais relevante.
triagem_df["score_atividade"] = (0.90 * triagem_df["score_atividade"] + 0.10 * triagem_df["score_matminer_composicional"]).clip(0, 1)

# Exibe estado do enriquecimento por matminer.
print("Matminer obrigatorio disponivel:", matminer_disponivel)

# Exibe a quantidade de descritores Magpie calculados.
print("Descritores Magpie calculados:", len(matminer_feature_cols))

# Exibe o perfil de pesos Magpie usado para a reacao.
print("Pesos Magpie usados:", pesos_magpie)

# Mostra o score composicional junto aos scores usados na triagem.
triagem_df[["formula", "score_matminer_composicional", "score_atividade", "score_DFT_proxy"]].head(20)
"""
    ),
    md(
        """
### Subetapa 6.2 - Descritores quimicos obrigatorios com pymatgen

Esta subetapa usa `pymatgen` como dependencia obrigatoria para transformar a formula do candidato em uma composicao quimica, extrair propriedades elementares e criar um score quimico complementar. O objetivo e reforcar a triagem com informacoes de massa molar, diversidade elementar, eletronegatividade media e heterogeneidade composicional.
"""
    ),
    code(
        """
# Comeca assumindo que o pymatgen ainda nao foi ativado.
pymatgen_disponivel = False

# Cria lista vazia para registrar os descritores diretos gerados pelo pymatgen.
pymatgen_feature_cols = []

# Tenta importar as classes de composicao e elemento do pymatgen.
try:
    # Importa Composition para representar a composicao quimica de cada candidato.
    from pymatgen.core import Composition
    # Importa Element para acessar propriedades elementares como eletronegatividade.
    from pymatgen.core import Element
    # Marca o pymatgen como disponivel quando as importacoes funcionam.
    pymatgen_disponivel = True
# Captura ausencia ou falha de importacao do pymatgen.
except Exception as erro_pymatgen:
    # Interrompe com mensagem clara, pois o pymatgen agora e obrigatorio.
    raise RuntimeError(f"Pymatgen e obrigatorio para a etapa 6.2, mas nao foi importado: {erro_pymatgen}") from erro_pymatgen

# Define funcao para converter formula com separadores cataliticos em dicionario elementar.
def extrair_composicao_elementar(formula):
    # Converte a formula para texto para evitar falhas com valores ausentes.
    texto = str(formula)
    # Encontra simbolos elementares seguidos opcionalmente por numeros estequiometricos.
    tokens = re.findall(r"([A-Z][a-z]?)([0-9]*\\.?[0-9]*)", texto)
    # Cria dicionario vazio para acumular quantidades por elemento.
    composicao = {}
    # Percorre todos os tokens encontrados na formula.
    for elemento, quantidade_texto in tokens:
        # Interpreta quantidade ausente como uma unidade.
        quantidade = float(quantidade_texto) if quantidade_texto else 1.0
        # Soma a quantidade quando o elemento aparece em mais de uma parte do catalisador.
        composicao[elemento] = composicao.get(elemento, 0.0) + quantidade
    # Retorna o dicionario elementar agregado.
    return composicao

# Define normalizacao robusta por z-score para metricas que precisam de escala padronizada.
def normalizar_standard_robusto(serie, invertido=False, neutro=0.5):
    # Converte valores para numerico.
    valores = pd.to_numeric(serie, errors="coerce")
    # Cria resultado neutro.
    resultado = pd.Series(neutro, index=serie.index, dtype=float)
    # Retorna neutro quando nao ha dados suficientes.
    if valores.notna().sum() < 2:
        return resultado
    # Calcula mediana robusta.
    mediana = valores.median()
    # Calcula desvio absoluto mediano.
    mad = (valores - mediana).abs().median()
    # Retorna neutro quando nao ha dispersao.
    if pd.isna(mad) or mad == 0:
        return resultado
    # Calcula z-score robusto.
    z = (valores - mediana) / (1.4826 * mad)
    # Converte z-score em escala sigmoidal entre zero e um.
    normalizado = 1.0 / (1.0 + np.exp(-z.clip(-6, 6)))
    # Inverte quando menor e melhor.
    if invertido:
        normalizado = 1.0 - normalizado
    # Preserva neutro onde havia ausencia.
    resultado.loc[valores.notna()] = normalizado.loc[valores.notna()].clip(0, 1)
    # Retorna serie normalizada.
    return resultado

# Executa os descritores diretos apenas quando pymatgen estiver disponivel.
if pymatgen_disponivel:
    # Cria lista para guardar uma linha de descritores por candidato.
    linhas_pymatgen = []
    # Percorre os candidatos da triagem.
    for _, row in triagem_df.iterrows():
        # Extrai a composicao elementar tolerante a separadores como hifen e barra.
        composicao_dict = extrair_composicao_elementar(row["formula"])
        # Cria objeto Composition quando ha pelo menos um elemento valido.
        composicao = Composition(composicao_dict) if composicao_dict else None
        # Lista elementos reconhecidos pelo pymatgen.
        elementos_validos = [Element(el) for el in composicao_dict if Element.is_valid_symbol(el)]
        # Calcula a massa molar do candidato quando a composicao existe.
        massa_molar = float(composicao.weight) if composicao else np.nan
        # Calcula a quantidade de elementos diferentes na composicao.
        n_elementos_pymatgen = len(elementos_validos)
        # Calcula eletronegatividade media ignorando elementos sem valor definido.
        eletronegatividades = [float(el.X) for el in elementos_validos if el.X is not None]
        # Calcula media de eletronegatividade quando ha dados.
        eletronegatividade_media = float(np.mean(eletronegatividades)) if eletronegatividades else np.nan
        # Calcula desvio de eletronegatividade como proxy de heterogeneidade de ligacao.
        eletronegatividade_desvio = float(np.std(eletronegatividades)) if eletronegatividades else np.nan
        # Calcula raio atomico medio quando disponivel.
        raios = [float(el.atomic_radius) for el in elementos_validos if el.atomic_radius is not None]
        # Calcula media de raio atomico como proxy geometrico simples.
        raio_atomico_medio = float(np.mean(raios)) if raios else np.nan
        # Registra os descritores calculados para o candidato.
        linhas_pymatgen.append({
            "formula": row["formula"],
            "pymatgen_massa_molar": massa_molar,
            "pymatgen_n_elementos": n_elementos_pymatgen,
            "pymatgen_eletronegatividade_media": eletronegatividade_media,
            "pymatgen_eletronegatividade_desvio": eletronegatividade_desvio,
            "pymatgen_raio_atomico_medio": raio_atomico_medio,
        })
    # Converte a lista de descritores em tabela.
    pymatgen_descritores_df = pd.DataFrame(linhas_pymatgen)
    # Define as colunas numericas geradas pelo pymatgen.
    pymatgen_feature_cols = [col for col in pymatgen_descritores_df.columns if col.startswith("pymatgen_")]
    # Junta os descritores pymatgen ao dataframe principal.
    triagem_df = triagem_df.merge(pymatgen_descritores_df, on="formula", how="left")
    # Cria score quimico direto iniciado em valor neutro.
    # Justificativa MCDA: os pesos abaixo sao pesos iniciais de especialista.
    # A diversidade elementar representa interfaces metal-promotor; a dispersao de
    # eletronegatividade representa heterogeneidade eletronica; a eletronegatividade
    # media descreve o carater eletronico global; o raio atomico medio entra com
    # menor peso por ser apenas um proxy estrutural simples.
    triagem_df["score_pymatgen_quimico"] = 0.50
    # Valoriza diversidade elementar moderada, util para suportes e promotores.
    triagem_df["score_pymatgen_quimico"] += 0.20 * normalizar_minmax_global(triagem_df["pymatgen_n_elementos"])
    # Valoriza heterogeneidade de eletronegatividade como proxy de interfaces acido-base/redox.
    triagem_df["score_pymatgen_quimico"] += 0.15 * normalizar_minmax_global(triagem_df["pymatgen_eletronegatividade_desvio"])
    # Usa eletronegatividade media como contribuicao composicional leve.
    triagem_df["score_pymatgen_quimico"] += 0.10 * normalizar_minmax_global(triagem_df["pymatgen_eletronegatividade_media"])
    # Usa raio atomico medio como proxy estrutural leve.
    triagem_df["score_pymatgen_quimico"] += 0.05 * normalizar_minmax_global(triagem_df["pymatgen_raio_atomico_medio"])
    # Limita o score quimico direto ao intervalo de zero a um.
    triagem_df["score_pymatgen_quimico"] = triagem_df["score_pymatgen_quimico"].clip(0, 1)
    # Enriquece o proxy DFT com descritores elementares diretos obrigatorios.
    triagem_df["score_DFT_proxy"] = (0.90 * triagem_df["score_DFT_proxy"] + 0.10 * triagem_df["score_pymatgen_quimico"]).clip(0, 1)
    # Enriquece a seletividade com heterogeneidade composicional calculada pelo pymatgen.
    triagem_df["score_seletividade"] = (0.94 * triagem_df["score_seletividade"] + 0.06 * triagem_df["score_pymatgen_quimico"]).clip(0, 1)
# Interrompe se o pymatgen nao estiver disponivel, pois ele e obrigatorio.
else:
    # Evita seguir com score neutro silencioso em uma etapa obrigatoria.
    raise RuntimeError("Pymatgen obrigatorio indisponivel na etapa 6.2.")

# Exibe estado do enriquecimento por pymatgen.
print("Pymatgen disponivel:", pymatgen_disponivel)

# Exibe a quantidade de descritores diretos calculados.
print("Descritores pymatgen calculados:", len(pymatgen_feature_cols))

# Mostra os principais descritores diretos usados na triagem.
triagem_df[["formula", "score_pymatgen_quimico", "score_seletividade", "score_DFT_proxy"]].head(20)
"""
    ),
    md(
        """
### Subetapa 6.3 - Proxy DFT local com GNN

Esta subetapa avalia a possibilidade de usar modelos GNN pré-treinados como camada local de pré-DFT. Quando `CHGNet` ou `matgl/M3GNet` está disponível, o notebook constrói uma estrutura cristalina simples a partir da composição, estima energia localmente e salva os resultados em cache. Como a estrutura é aproximada, o resultado não substitui `Estabilidade termodinâmica` de MP/OQMD; ele entra apenas como evidência auxiliar e recebe incerteza maior.
"""
    ),
    code(
        """
# Define arquivo de cache para resultados locais de GNN.
GNN_LOCAL_CACHE_FILE = PROJECT_DATA_DIR / "proxy_gnn_local.csv"

# Prepara o cache GNN local quando disponível.
baixar_csv_incremental_github(GITHUB_GNN_PATH, GNN_LOCAL_CACHE_FILE)

# Carrega o cache local de avaliações GNN já realizadas.
gnn_local_cache_df = pd.read_csv(GNN_LOCAL_CACHE_FILE) if GNN_LOCAL_CACHE_FILE.exists() else pd.DataFrame()

# Começa assumindo que nenhum modelo GNN local foi ativado.
gnn_local_disponivel = False

# Registra qual modelo GNN foi usado na execução.
gnn_modelo_usado = "indisponivel"

# Guarda mensagem de erro ou limitação para rastreabilidade.
erro_gnn_local = ""

# Define limite de candidatos avaliados localmente para manter a execução leve.
MAX_CANDIDATOS_GNN_LOCAL = 12

# Tenta carregar CHGNet primeiro, pois fornece inferência direta em estruturas.
try:
    # Importa o modelo CHGNet pré-treinado.
    from chgnet.model.model import CHGNet
    # Carrega pesos pré-treinados do CHGNet.
    modelo_gnn_local = CHGNet.load()
    # Marca a camada GNN local como disponível.
    gnn_local_disponivel = True
    # Registra o modelo usado.
    gnn_modelo_usado = "CHGNet"
# Captura ausência ou falha do CHGNet.
except Exception as erro_chgnet:
    # Guarda a falha do CHGNet antes de tentar MatGL.
    erro_gnn_local = f"CHGNet indisponível: {erro_chgnet}"
    # Tenta carregar um modelo MatGL/M3GNet ou MEGNet de energia de formação.
    try:
        # Importa MatGL para carregar modelos pré-treinados.
        import matgl
        # Carrega um modelo de energia de formação treinado no Materials Project.
        modelo_gnn_local = matgl.load_model("MEGNet-Eform-MP-2018.6.1")
        # Marca a camada GNN local como disponível.
        gnn_local_disponivel = True
        # Registra o modelo usado.
        gnn_modelo_usado = "MatGL-MEGNet-Eform-MP"
    # Captura ausência ou falha do MatGL.
    except Exception as erro_matgl:
        # Guarda as falhas para documentação da execução.
        erro_gnn_local = f"{erro_gnn_local}; MatGL indisponível: {erro_matgl}"
        # Mantém a camada GNN local desativada.
        gnn_local_disponivel = False
        # Mantém o nome de modelo como indisponível.
        gnn_modelo_usado = "indisponivel"

# Define posições fracionárias simples para uma célula cúbica proxy.
POSICOES_PROXY = [
    [0.0, 0.0, 0.0],
    [0.5, 0.5, 0.5],
    [0.0, 0.5, 0.5],
    [0.5, 0.0, 0.5],
    [0.5, 0.5, 0.0],
    [0.25, 0.25, 0.25],
    [0.75, 0.75, 0.75],
    [0.25, 0.75, 0.75],
]

# Define função para construir uma estrutura cristalina proxy a partir da fórmula.
def construir_estrutura_proxy_gnn(formula):
    # Interrompe se pymatgen não estiver disponível, pois a GNN precisa de Structure.
    if not pymatgen_disponivel:
        return None, "pymatgen_indisponivel"
    # Importa Lattice e Structure apenas quando necessário.
    from pymatgen.core import Lattice, Structure
    # Extrai composição elementar tolerante às fórmulas simplificadas da triagem.
    composicao_dict = extrair_composicao_elementar(formula)
    # Mantém apenas símbolos válidos reconhecidos pelo pymatgen.
    composicao_dict = {el: qtd for el, qtd in composicao_dict.items() if Element.is_valid_symbol(el) and qtd > 0}
    # Retorna vazio quando não há composição válida.
    if not composicao_dict:
        return None, "composicao_invalida"
    # Calcula frações atômicas normalizadas.
    total = sum(composicao_dict.values())
    # Ordena elementos por fração decrescente.
    fracoes = sorted([(el, qtd / total) for el, qtd in composicao_dict.items()], key=lambda x: x[1], reverse=True)
    # Define até oito sítios para representar a composição.
    n_sites = min(8, max(1, int(round(total)) if total >= 1 else 4))
    # Garante mais sítios para misturas binárias e promovidas.
    if len(fracoes) > 1:
        n_sites = max(n_sites, 4)
    # Calcula contagens inteiras aproximadas por elemento.
    contagens = {el: max(1, int(round(frac * n_sites))) for el, frac in fracoes}
    # Ajusta o número total de sítios para não exceder o limite.
    while sum(contagens.values()) > n_sites:
        # Reduz o elemento mais abundante que ainda tem mais de um sítio.
        alvo = max((el for el in contagens if contagens[el] > 1), key=lambda el: contagens[el], default=None)
        if alvo is None:
            break
        contagens[alvo] -= 1
    # Completa sítios faltantes com o elemento majoritário.
    while sum(contagens.values()) < n_sites:
        contagens[fracoes[0][0]] += 1
    # Expande a lista de espécies por sítio.
    especies = []
    # Percorre elementos e contagens aproximadas.
    for el, n in contagens.items():
        especies.extend([el] * int(n))
    # Corta a lista no limite de posições disponíveis.
    especies = especies[:len(POSICOES_PROXY)]
    # Calcula raio atômico médio para estimar parâmetro de rede inicial.
    raios = [float(Element(el).atomic_radius) for el in especies if Element(el).atomic_radius is not None]
    # Usa parâmetro cúbico conservador quando não houver raio.
    a = 2.8 * float(np.mean(raios)) if raios else 4.0
    # Limita a célula para evitar geometrias absurdas.
    a = float(np.clip(a, 3.0, 7.0))
    # Cria rede cúbica proxy.
    lattice = Lattice.cubic(a)
    # Seleciona posições compatíveis com a quantidade de espécies.
    posicoes = POSICOES_PROXY[:len(especies)]
    # Cria a estrutura proxy.
    estrutura = Structure(lattice, especies, posicoes)
    # Retorna estrutura e descrição do método.
    return estrutura, "estrutura_cubica_proxy_por_composicao"

# Define função para extrair número escalar de objetos numpy/torch.
def valor_escalar_gnn(valor):
    # Tenta converter tensores e arrays para float.
    try:
        if hasattr(valor, "detach"):
            valor = valor.detach().cpu().numpy()
        if hasattr(valor, "numpy"):
            valor = valor.numpy()
        return float(np.array(valor).reshape(-1)[0])
    except Exception:
        return np.nan

# Define função para avaliar uma fórmula com GNN local.
def avaliar_formula_gnn_local(formula):
    # Reaproveita cache quando há registro anterior para fórmula e modelo.
    if not gnn_local_cache_df.empty and {"formula", "modelo_gnn_local"}.issubset(gnn_local_cache_df.columns):
        cache = gnn_local_cache_df[
            (gnn_local_cache_df["formula"].astype(str) == str(formula))
            & (gnn_local_cache_df["modelo_gnn_local"].astype(str) == str(gnn_modelo_usado))
        ]
        if not cache.empty:
            return cache.iloc[0].to_dict()
    # Retorna registro de indisponibilidade quando não há modelo.
    if not gnn_local_disponivel:
        return {
            "formula": formula,
            "modelo_gnn_local": gnn_modelo_usado,
            "gnn_local_usado": False,
            "energia_gnn_eV_atom": np.nan,
            "energia_formacao_gnn_eV_atom": np.nan,
            "score_gnn_local": np.nan,
            "estrutura_proxy_gnn": "modelo_indisponivel",
            "observacao_gnn_local": erro_gnn_local,
        }
    # Constrói estrutura cristalina proxy.
    estrutura, metodo_estrutura = construir_estrutura_proxy_gnn(formula)
    # Retorna registro de falha quando não foi possível criar estrutura.
    if estrutura is None:
        return {
            "formula": formula,
            "modelo_gnn_local": gnn_modelo_usado,
            "gnn_local_usado": False,
            "energia_gnn_eV_atom": np.nan,
            "energia_formacao_gnn_eV_atom": np.nan,
            "score_gnn_local": np.nan,
            "estrutura_proxy_gnn": metodo_estrutura,
            "observacao_gnn_local": "estrutura_proxy_nao_criada",
        }
    try:
        # Executa inferência CHGNet quando esse foi o modelo carregado.
        if gnn_modelo_usado == "CHGNet":
            # Prediz energia e demais propriedades da estrutura proxy.
            predicao = modelo_gnn_local.predict_structure(estrutura)
            # Lê energia por átomo usando as chaves usuais do CHGNet.
            energia = valor_escalar_gnn(predicao.get("e", predicao.get("energy", np.nan)))
            # CHGNet retorna energia total aproximada, não energia de formação.
            energia_formacao = np.nan
        # Executa inferência MatGL quando esse foi o modelo carregado.
        else:
            # Prediz energia de formação por átomo com modelo MatGL/MEGNet.
            energia_formacao = valor_escalar_gnn(modelo_gnn_local.predict_structure(estrutura))
            # Usa a energia de formação também como energia local reportada.
            energia = energia_formacao
        # Retorna registro bruto; o score será normalizado depois com o conjunto avaliado.
        return {
            "formula": formula,
            "modelo_gnn_local": gnn_modelo_usado,
            "gnn_local_usado": True,
            "energia_gnn_eV_atom": energia,
            "energia_formacao_gnn_eV_atom": energia_formacao,
            "score_gnn_local": np.nan,
            "estrutura_proxy_gnn": metodo_estrutura,
            "volume_proxy_gnn_A3": float(estrutura.volume),
            "n_sites_proxy_gnn": int(len(estrutura)),
            "observacao_gnn_local": "proxy_estrutural_nao_substitui_hull",
        }
    except Exception as erro_predicao:
        # Registra falha da predição sem interromper a triagem.
        return {
            "formula": formula,
            "modelo_gnn_local": gnn_modelo_usado,
            "gnn_local_usado": False,
            "energia_gnn_eV_atom": np.nan,
            "energia_formacao_gnn_eV_atom": np.nan,
            "score_gnn_local": np.nan,
            "estrutura_proxy_gnn": metodo_estrutura,
            "observacao_gnn_local": f"erro_predicao: {erro_predicao}",
        }

# Seleciona candidatos para avaliação local, priorizando os que não têm estabilidade real clara.
formulas_gnn = list(dict.fromkeys(triagem_df["formula"].astype(str).head(MAX_CANDIDATOS_GNN_LOCAL)))

# Avalia as fórmulas selecionadas.
gnn_resultados_df = pd.DataFrame([avaliar_formula_gnn_local(formula) for formula in formulas_gnn])

# Calcula score local a partir da energia relativa apenas entre candidatos avaliados.
if not gnn_resultados_df.empty and gnn_resultados_df["energia_gnn_eV_atom"].notna().sum() > 1:
    # Converte energia para número.
    energias = pd.to_numeric(gnn_resultados_df["energia_gnn_eV_atom"], errors="coerce")
    # Energia menor recebe score maior.
    gnn_resultados_df["score_gnn_local"] = 1.0 - normalizar_minmax_global(energias)
elif not gnn_resultados_df.empty and gnn_resultados_df["energia_gnn_eV_atom"].notna().sum() == 1:
    # Usa score moderado quando há apenas uma energia disponível.
    gnn_resultados_df.loc[gnn_resultados_df["energia_gnn_eV_atom"].notna(), "score_gnn_local"] = 0.60

# Atualiza cache quando há registros novos.
if not gnn_resultados_df.empty:
    # Junta cache antigo e registros da execução.
    gnn_local_cache_df = pd.concat([gnn_local_cache_df, gnn_resultados_df], ignore_index=True, sort=False)
    # Remove duplicatas por fórmula e modelo.
    if {"formula", "modelo_gnn_local"}.issubset(gnn_local_cache_df.columns):
        gnn_local_cache_df = gnn_local_cache_df.drop_duplicates(subset=["formula", "modelo_gnn_local"], keep="last")
    # Salva cache local para reutilização.
    gnn_local_cache_df.to_csv(GNN_LOCAL_CACHE_FILE, index=False, encoding="utf-8-sig")
    # Envia o cache GNN incremental ao GitHub quando a integra??o estiver configurada.
    enviar_csv_incremental_github(GITHUB_GNN_PATH, GNN_LOCAL_CACHE_FILE, "Atualiza cache GNN incremental")

# Junta resultados GNN ao dataframe principal.
triagem_df = triagem_df.merge(
    gnn_resultados_df.drop_duplicates("formula"),
    on="formula",
    how="left",
)

# Cria fallback neutro para o score GNN quando não houve avaliação.
triagem_df["score_gnn_local"] = pd.to_numeric(triagem_df["score_gnn_local"], errors="coerce")

# Enriquece levemente o proxy DFT quando há score GNN local.
triagem_df["score_DFT_proxy"] = np.where(
    triagem_df["score_gnn_local"].notna(),
    (0.85 * triagem_df["score_DFT_proxy"] + 0.15 * triagem_df["score_gnn_local"]).clip(0, 1),
    triagem_df["score_DFT_proxy"],
)

# Define tabela de saída mesmo quando não há modelo disponível.
gnn_local_descritores_df = gnn_resultados_df.copy() if not gnn_resultados_df.empty else pd.DataFrame(columns=[
    "formula",
    "modelo_gnn_local",
    "gnn_local_usado",
    "energia_gnn_eV_atom",
    "energia_formacao_gnn_eV_atom",
    "score_gnn_local",
    "estrutura_proxy_gnn",
    "observacao_gnn_local",
])

# Exibe estado da camada GNN local.
print("GNN local disponível:", gnn_local_disponivel)
print("Modelo GNN local:", gnn_modelo_usado)
print("Candidatos avaliados por GNN local:", int(gnn_local_descritores_df["gnn_local_usado"].fillna(False).sum()) if "gnn_local_usado" in gnn_local_descritores_df else 0)

# Mostra resultados GNN locais.
gnn_local_descritores_df.head(20)
"""
    ),
    md(
        """
## Etapa 7 - Filtro de viabilidade

O filtro remove candidatos com baixa estabilidade prevista e mantém candidatos exploratórios apenas quando há justificativa química.

Nesta etapa, a propriedade **Estabilidade termodinâmica (eV/átomo)** mede o quanto um material está acima da combinação de fases mais estáveis para a mesma composição. Valores próximos de `0 eV/átomo` indicam materiais termodinamicamente mais estáveis; valores entre `0,05` e `0,10 eV/átomo` indicam candidatos metaestáveis ainda plausíveis; valores mais altos aumentam o risco de decomposição em fases mais estáveis. Por isso, essa propriedade é usada como primeiro filtro de viabilidade antes do ranqueamento catalítico.
"""
    ),
    code(
        """
# Define uma função para obter estabilidade termodinâmica local ou estimada.
def obter_hull(row):
    # Usa a estabilidade termodinâmica v2 quando disponível.
    valor = obter(row, "energy_above_hull_screening_v2", np.nan)
    # Se não existir, usa a propriedade técnica energy_above_hull original.
    if pd.isna(valor):
        valor = obter(row, "energy_above_hull", np.nan)
    # Se ainda não existir, estima valor conservador para candidatos hipotéticos.
    if pd.isna(valor):
        valor = 0.08 if row["tipo"] != "metal_ativo_puro" else 0.04
    # Retorna o valor numérico.
    return float(valor)

# Calcula a estabilidade termodinâmica para cada candidato.
triagem_df["energy_above_hull_eV_atom"] = triagem_df.apply(obter_hull, axis=1)

# Calcula score de estabilidade normalizado.
triagem_df["score_estabilidade"] = (1.0 - triagem_df["energy_above_hull_eV_atom"] / perfil["limite_hull_exploratorio"]).clip(0, 1)

# Define função para registrar a fonte usada na estabilidade.
def fonte_estabilidade_triagem(row):
    # Lê fonte explícita da base local quando disponível.
    fonte = obter(row, "fonte_estabilidade_v2", "")
    # Usa a fonte explícita se existir.
    if isinstance(fonte, str) and fonte:
        return fonte
    # Usa rótulo GNN quando houve avaliação local, mas sem substituir MP/OQMD.
    if bool(row.get("gnn_local_usado", False)):
        return "GNN_local_proxy"
    # Usa rótulo conservador para valor estimado por regra química.
    return "proxy_quimico"

# Registra a fonte de estabilidade usada no filtro.
triagem_df["fonte_estabilidade_triagem"] = triagem_df.apply(fonte_estabilidade_triagem, axis=1)

# Define função para ajustar incerteza conforme a qualidade da evidência.
def calcular_incerteza_triagem(row):
    # Lê incerteza original da base local quando disponível.
    base = float(obter(row, "incerteza_ensemble_std", 0.10))
    # Mantém incerteza menor quando a estabilidade vem de base termodinâmica.
    if row["fonte_estabilidade_triagem"] in ["MP", "OQMD"]:
        return min(base, 0.10)
    # Usa incerteza intermediária quando há GNN local como evidência auxiliar.
    if row["fonte_estabilidade_triagem"] == "GNN_local_proxy":
        return max(base, 0.18)
    # Usa incerteza maior para candidatos avaliados apenas por proxy químico.
    return max(base, 0.22)

# Obtém a incerteza ajustada pela fonte da evidência.
triagem_df["incerteza"] = triagem_df.apply(calcular_incerteza_triagem, axis=1)

# Converte incerteza em score, penalizando incertezas altas.
triagem_df["score_incerteza"] = (1.0 - triagem_df["incerteza"] / 0.30).clip(0, 1)

# Mantém candidatos dentro do limite exploratório de estabilidade.
viaveis_df = triagem_df[triagem_df["energy_above_hull_eV_atom"] <= perfil["limite_hull_exploratorio"]].copy()

# Ordena candidatos viáveis priorizando estabilidade, confiança e proxy DFT.
viaveis_df = viaveis_df.sort_values(
    ["score_estabilidade", "score_incerteza", "score_DFT_proxy", "score_atividade", "score_seletividade"],
    ascending=False,
).reset_index(drop=True)

# Define uma função para selecionar candidatos sem deixar ligas multimetálicas desaparecerem do funil.
def selecionar_com_representacao_multimetal(df, n_candidatos, coluna_score, fracao_minima=0.30):
    # Ordena a tabela pelo score escolhido antes de aplicar a cota de diversidade.
    ordenado = df.sort_values(coluna_score, ascending=False).reset_index(drop=True)
    # Retorna apenas os melhores quando o usuário escolheu um único metal ativo.
    if len(metais_usuario) < 2:
        # Mantém o comportamento puramente baseado em score para sistemas monometálicos.
        return ordenado.head(n_candidatos).copy()
    # Retorna apenas os melhores se a coluna de marcação multimetálica não existir.
    if "candidato_multimetal_ativo" not in ordenado.columns:
        # Mantém o comportamento padrão quando a etapa não recebeu a marcação de diversidade.
        return ordenado.head(n_candidatos).copy()
    # Seleciona candidatos que contêm dois ou mais metais ativos informados pelo usuário.
    multimetal = ordenado[ordenado["candidato_multimetal_ativo"].fillna(False)].copy()
    # Retorna apenas os melhores se nenhum candidato multimetálico estiver disponível.
    if multimetal.empty:
        # Mantém o ranking por score sem inventar candidatos.
        return ordenado.head(n_candidatos).copy()
    # Calcula a quantidade mínima de candidatos multimetálicos na etapa.
    minimo_multimetal = min(len(multimetal), max(1, int(np.ceil(n_candidatos * fracao_minima))))
    # Seleciona os melhores candidatos multimetálicos disponíveis.
    selecionados_multimetal = multimetal.head(minimo_multimetal)
    # Seleciona os melhores candidatos restantes sem repetir os multimetálicos já reservados.
    restantes = ordenado.drop(index=selecionados_multimetal.index).head(n_candidatos - len(selecionados_multimetal))
    # Combina a cota multimetálica com os demais melhores candidatos.
    selecionados = pd.concat([selecionados_multimetal, restantes], ignore_index=True)
    # Reordena a seleção final pelo score, preservando a presença mínima dos multimetálicos.
    selecionados = selecionados.sort_values(coluna_score, ascending=False).reset_index(drop=True)
    # Retorna a quantidade solicitada para a etapa do funil.
    return selecionados.head(n_candidatos).copy()

# Interrompe se o filtro de viabilidade não entregar candidatos suficientes.
if len(viaveis_df) < N_CANDIDATOS_VIAVEIS_FUNIL:
    # Explica que o filtro químico foi mais restritivo que o necessário para a etapa seguinte.
    raise ValueError(
        f"O filtro gerou apenas {len(viaveis_df)} candidatos viáveis. "
        f"Ajuste metais/promotor ou revise o limite de estabilidade para seguir com {N_CANDIDATOS_VIAVEIS_FUNIL} candidatos viáveis."
    )

# Mantém apenas a quantidade definida para passar à próxima etapa com cota de multimetálicos.
viaveis_df = selecionar_com_representacao_multimetal(viaveis_df, N_CANDIDATOS_VIAVEIS_FUNIL, "score_estabilidade", fracao_minima=0.30)

# Mostra quantos candidatos sobreviveram ao filtro.
print("Candidatos antes do filtro:", len(triagem_df))
print("Candidatos viáveis:", len(viaveis_df))

# Mostra quantos viáveis preservam dois ou mais metais ativos informados.
print("Viáveis com dois ou mais metais ativos:", int(viaveis_df.get("candidato_multimetal_ativo", pd.Series(dtype=bool)).sum()))

# Exibe os candidatos viáveis.
viaveis_df[["formula", "tipo", "metais_ativos_presentes", "n_metais_ativos_presentes", "energy_above_hull_eV_atom", "fonte_estabilidade_triagem", "score_estabilidade", "score_incerteza"]].head(20)
"""
    ),
    md(
        """
## Etapa 8 - Triagem preliminar

O score preliminar combina estabilidade, atividade, seletividade, proxy DFT e incerteza. Os pesos mudam conforme a reação escolhida.
"""
    ),
    code(
        """
# Lê os pesos definidos no perfil da reação.
pesos = perfil["pesos"]

# Calcula o score preliminar multicritério.
viaveis_df["score_preliminar"] = (
    pesos["estabilidade"] * viaveis_df["score_estabilidade"]
    + pesos["atividade"] * viaveis_df["score_atividade"]
    + pesos["seletividade"] * viaveis_df["score_seletividade"]
    + pesos["dft"] * viaveis_df["score_DFT_proxy"]
    + pesos["incerteza"] * viaveis_df["score_incerteza"]
)

# Ordena os candidatos do melhor para o pior.
preliminar_df = viaveis_df.sort_values("score_preliminar", ascending=False).copy()

# Limita a quantidade de candidatos preliminares mantendo representação multimetálica mínima.
preliminar_df = selecionar_com_representacao_multimetal(preliminar_df, N_CANDIDATOS_VIAVEIS_FUNIL, "score_preliminar", fracao_minima=0.30)

# Mostra o ranking preliminar.
preliminar_df[["formula", "tipo", "metais_ativos_presentes", "n_metais_ativos_presentes", "score_preliminar", "score_estabilidade", "score_atividade", "score_seletividade", "score_DFT_proxy"]].head(20)
"""
    ),
    md(
        """
## Etapa 9 - Busca catalítica incremental no Catalysis-Hub e refinamento DFT

A busca catalítica é aplicada apenas aos melhores candidatos preliminares. O notebook consulta primeiro o cache local do Catalysis-Hub; quando não há dados para a fórmula e a reação, tenta buscar dados externos de reação/adsorção para os intermediários relevantes. Os dados obtidos são salvos em cache local para reutilização e entram no score DFT refinado. Quando não há resposta externa, o notebook usa o proxy químico calculado pelos descritores da reação.
"""
    ),
    code(
        """
# Seleciona apenas os melhores candidatos para refinamento DFT mantendo presença multimetálica.
dft_df = selecionar_com_representacao_multimetal(preliminar_df, N_CANDIDATOS_REFINADOS_FUNIL, "score_preliminar", fracao_minima=0.40)

# Define arquivo local para armazenar dados incrementais do Catalysis-Hub.
CATHUB_CACHE_FILE = PROJECT_DATA_DIR / "catalysis_hub_incremental.csv"

# Prepara o cache Catalysis-Hub local quando disponível.
baixar_csv_incremental_github(GITHUB_CATHUB_PATH, CATHUB_CACHE_FILE)

# Carrega o cache local de dados catalíticos já baixados.
cathub_cache_df = pd.read_csv(CATHUB_CACHE_FILE) if CATHUB_CACHE_FILE.exists() else pd.DataFrame()

# Define o endpoint GraphQL do Catalysis-Hub.
CATHUB_GRAPHQL_URL = "https://api.catalysis-hub.org/graphql"

# Define quantidade máxima de candidatos consultados para evitar excesso de chamadas.
MAX_CANDIDATOS_CATHUB = 5

# Define quantidade máxima de pares metal-adsorbato por candidato.
MAX_PARES_CATHUB_POR_CANDIDATO = 8

# Define alvos aproximados de energia por intermediário para transformar energia em score Sabatier.
ALVOS_ADSORCAO_EV = {
    "metanacao": {"CO2": 0.35, "CO": 0.85, "H": 0.35, "O": 1.20, "OH": 0.75, "COOH": 0.55, "OCHO": 0.55, "C": 1.10},
    "reforma": {"CH4": 0.30, "CH3": 0.65, "CHx": 0.80, "C": 1.35, "O": 1.05, "OH": 0.75, "CO": 0.85},
    "rwgs": {"CO2": 0.30, "COOH": 0.50, "OCHO": 0.50, "CO": 0.70, "O": 0.95, "H": 0.35},
}

# Define função para remover marcações de superfície dos intermediários DFT.
def normalizar_adsorbato(intermediario):
    # Remove o símbolo de adsorção para consultar a base de reações.
    return str(intermediario).replace("*", "").strip()

# Define função para calcular score catalítico a partir de energia de reação/adsorção.
def score_cathub_por_energia(adsorbato, energia):
    # Retorna vazio se a energia não estiver disponível.
    if pd.isna(energia):
        return np.nan
    # Seleciona o alvo químico da reação ou usa alvo moderado quando não há valor específico.
    alvo = ALVOS_ADSORCAO_EV.get(reacao, {}).get(str(adsorbato), 0.75)
    # Usa o módulo da energia porque a API pode representar adsorção como energia negativa.
    modulo = abs(float(energia))
    # Aplica uma penalização suave quando a adsorção fica fraca ou forte demais.
    return float(np.clip(np.exp(-abs(modulo - alvo) / max(alvo, 0.15)), 0, 1))

# Define função para verificar se já há consulta bem-sucedida do Catalysis-Hub para a fórmula.
def consulta_cathub_ja_realizada(formula):
    # Usa a reação e a fórmula como chave do cache de consulta.
    chave = f"cathub:{reacao}:{formula}"
    # Reaproveita a função geral de histórico usada por MP/OQMD.
    return consulta_ja_realizada("Catalysis-Hub", chave)

# Define função para consultar o Catalysis-Hub por metal de superfície e adsorbato.
def consultar_cathub_par(formula, metal, adsorbato, limite=3):
    # Define consulta GraphQL restrita a poucos registros.
    consulta = \"\"\"
    query BuscarReacoes($first: Int, $surface: String, $reactant: String) {
      reactions(first: $first, surfaceComposition: $surface, reactants: $reactant) {
        totalCount
        edges {
          node {
            id
            Equation
            chemicalComposition
            surfaceComposition
            facet
            reactants
            products
            reactionEnergy
            activationEnergy
            sites
            pubId
          }
        }
      }
    }
    \"\"\"
    # Monta variáveis de consulta para o par metal-adsorbato.
    variaveis = {"first": int(limite), "surface": str(metal), "reactant": f"{adsorbato}*"}
    try:
        # Executa a chamada HTTP com timeout de 15 segundos para tolerar lentidao moderada da API sem travar o notebook.
        resposta = requests.post(CATHUB_GRAPHQL_URL, json={"query": consulta, "variables": variaveis}, timeout=15)
        # Interrompe se o status HTTP indicar erro.
        resposta.raise_for_status()
        # Converte a resposta em JSON.
        payload = resposta.json()
    except Exception as erro_cathub:
        # Registra a falha do par metal-adsorbato sem interromper a triagem.
        registrar_consulta("Catalysis-Hub", f"cathub:{reacao}:{formula}:{metal}:{adsorbato}", 0, f"erro_par: {erro_cathub}")
        # Retorna tabela vazia para permitir que os demais pares sejam consultados.
        return pd.DataFrame()
    # Lê as arestas retornadas pela API.
    edges = payload.get("data", {}).get("reactions", {}).get("edges", [])
    # Cria lista de registros normalizados.
    registros = []
    # Percorre reações retornadas.
    for edge in edges:
        # Extrai o nó da reação.
        node = edge.get("node", {})
        # Lê energia de reação quando disponível.
        energia = node.get("reactionEnergy")
        # Calcula score local do intermediário.
        score_ads = score_cathub_por_energia(adsorbato, energia)
        # Adiciona linha normalizada ao cache local.
        registros.append({
            "formula": formula,
            "reacao": reacao,
            "metal_consultado": metal,
            "adsorbato": adsorbato,
            "cathub_id": node.get("id"),
            "equacao": node.get("Equation"),
            "composicao_quimica": node.get("chemicalComposition"),
            "composicao_superficie": node.get("surfaceComposition"),
            "facet": node.get("facet"),
            "reagentes": str(node.get("reactants")),
            "produtos": str(node.get("products")),
            "energia_reacao_eV": energia,
            "energia_ativacao_eV": node.get("activationEnergy"),
            "sitios": str(node.get("sites")),
            "pub_id": node.get("pubId"),
            "score_adsorcao_cathub": score_ads,
            "data_consulta": pd.Timestamp.now().isoformat(timespec="seconds"),
        })
    # Retorna tabela do par consultado.
    return pd.DataFrame(registros)

# Define função para buscar dados do Catalysis-Hub para uma fórmula candidata.
def baixar_cathub_formula(formula):
    # Ignora a busca se já houver consulta bem-sucedida para esta fórmula e reação.
    if consulta_cathub_ja_realizada(formula):
        return pd.DataFrame()
    # Extrai metais/elementos da fórmula candidata.
    metais = sorted(elementos_formula(formula))
    # Extrai adsorbatos relevantes do perfil da reação.
    adsorbatos = [normalizar_adsorbato(x) for x in perfil["intermediarios_dft"]]
    # Remove duplicatas preservando ordem.
    adsorbatos = list(dict.fromkeys([a for a in adsorbatos if a]))
    # Cria lista para registros retornados.
    registros_formula = []
    # Controla quantidade de pares consultados.
    n_pares = 0
    try:
        # Percorre metais e adsorbatos até o limite definido.
        for metal in metais:
            # Percorre adsorbatos relevantes da rota.
            for adsorbato in adsorbatos:
                # Interrompe quando atinge o limite de pares por candidato.
                if n_pares >= MAX_PARES_CATHUB_POR_CANDIDATO:
                    break
                # Consulta um par metal-adsorbato.
                df_par = consultar_cathub_par(formula, metal, adsorbato)
                # Adiciona dados se houver retorno.
                if not df_par.empty:
                    registros_formula.append(df_par)
                # Atualiza contador de pares consultados.
                n_pares += 1
                # Pausa curta para reduzir agressividade contra a API.
                time.sleep(0.2)
            # Interrompe o laço externo quando o limite já foi atingido.
            if n_pares >= MAX_PARES_CATHUB_POR_CANDIDATO:
                break
    except Exception as erro_cathub:
        # Registra falha sem interromper o notebook.
        registrar_consulta("Catalysis-Hub", f"cathub:{reacao}:{formula}", 0, f"erro: {erro_cathub}")
        return pd.DataFrame()
    # Junta registros coletados para a fórmula.
    df_formula = pd.concat(registros_formula, ignore_index=True, sort=False) if registros_formula else pd.DataFrame()
    # Registra consulta concluída, mesmo que sem resultados, para não repetir chamadas vazias.
    registrar_consulta("Catalysis-Hub", f"cathub:{reacao}:{formula}", len(df_formula), "ok")
    # Retorna dados coletados.
    return df_formula

# Identifica fórmulas do top preliminar que ainda não possuem cache Catalysis-Hub.
formulas_para_cathub = [
    formula
    for formula in dft_df["formula"].astype(str).head(MAX_CANDIDATOS_CATHUB)
    if not consulta_cathub_ja_realizada(formula)
]

# Cria lista para novos dados do Catalysis-Hub.
novos_cathub = []

# Consulta apenas fórmulas ainda não buscadas com sucesso.
for formula in formulas_para_cathub:
    # Baixa dados catalíticos incrementais da fórmula.
    novos_cathub.append(baixar_cathub_formula(formula))

# Junta novos dados válidos.
novos_cathub_df = pd.concat([df for df in novos_cathub if isinstance(df, pd.DataFrame) and not df.empty], ignore_index=True, sort=False) if any(isinstance(df, pd.DataFrame) and not df.empty for df in novos_cathub) else pd.DataFrame()

# Atualiza o cache local quando houver novos dados.
if not novos_cathub_df.empty:
    # Combina cache antigo e novos registros.
    cathub_cache_df = pd.concat([cathub_cache_df, novos_cathub_df], ignore_index=True, sort=False)
    # Remove duplicatas por reação, fórmula, metal, adsorbato e ID da reação.
    cathub_cache_df = cathub_cache_df.drop_duplicates(subset=["reacao", "formula", "metal_consultado", "adsorbato", "cathub_id"], keep="first")
    # Salva o cache local atualizado.
    cathub_cache_df.to_csv(CATHUB_CACHE_FILE, index=False, encoding="utf-8-sig")
    # Envia o cache Catalysis-Hub ao GitHub quando a integra??o estiver configurada.
    enviar_csv_incremental_github(GITHUB_CATHUB_PATH, CATHUB_CACHE_FILE, "Atualiza cache Catalysis-Hub incremental")

# Registra o histórico de consultas, incluindo as chamadas Catalysis-Hub.
enviar_csv_incremental_github(GITHUB_CONSULTAS_PATH, CONSULTAS_EXTERNAS_FILE, "Atualiza historico incremental Catalysis-Hub")

# Define função para agregar evidências Catalysis-Hub em nível de fórmula.
def agregar_cathub_formula(formula):
    # Retorna campos vazios quando o cache ainda não existe.
    if cathub_cache_df.empty:
        return {
            "formula": formula,
            "score_cathub_incremental": np.nan,
            "energia_cathub_media_eV": np.nan,
            "n_evidencias_cathub_incremental": 0,
            "adsorbatos_cathub_encontrados": "",
        }
    # Filtra dados da fórmula e da reação atual.
    dados = cathub_cache_df[
        (cathub_cache_df["formula"].astype(str) == str(formula))
        & (cathub_cache_df["reacao"].astype(str) == str(reacao))
    ].copy()
    # Retorna campos vazios quando não há dados.
    if dados.empty:
        return {
            "formula": formula,
            "score_cathub_incremental": np.nan,
            "energia_cathub_media_eV": np.nan,
            "n_evidencias_cathub_incremental": 0,
            "adsorbatos_cathub_encontrados": "",
        }
    # Calcula score médio dos intermediários disponíveis.
    score = dados["score_adsorcao_cathub"].dropna().mean()
    # Calcula energia média de reação/adsorção.
    energia = pd.to_numeric(dados["energia_reacao_eV"], errors="coerce").dropna().mean()
    # Lista adsorbatos encontrados.
    ads = ", ".join(sorted(dados["adsorbato"].dropna().astype(str).unique()))
    # Retorna resumo agregado.
    return {
        "formula": formula,
        "score_cathub_incremental": float(score) if pd.notna(score) else np.nan,
        "energia_cathub_media_eV": float(energia) if pd.notna(energia) else np.nan,
        "n_evidencias_cathub_incremental": int(len(dados)),
        "adsorbatos_cathub_encontrados": ads,
    }

# Agrega evidências Catalysis-Hub para os candidatos refinados.
cathub_agregado_df = pd.DataFrame([agregar_cathub_formula(f) for f in dft_df["formula"].astype(str)])

# Junta evidências incrementais ao conjunto refinado.
dft_df = dft_df.merge(cathub_agregado_df, on="formula", how="left")

# Define uma função para calcular score DFT refinado.
def refinar_dft(row):
    # Usa score incremental do Catalysis-Hub quando a busca externa retornou evidência.
    cathub_incremental = obter(row, "score_cathub_incremental", np.nan)
    # Usa score específico de Catalysis-Hub local quando disponível.
    cathub = obter(row, "score_cathub_especifico", obter(row, "prop_score_cathub_especifico", np.nan))
    # Usa score de caminho de reação local quando disponível.
    pathway = obter(row, "cat_cathub_pathway_score", obter(row, "prop_cat_cathub_pathway_score", np.nan))
    # Junta evidências DFT disponíveis.
    evidencias = [v for v in [cathub_incremental, cathub, pathway] if pd.notna(v)]
    # Se houver evidência local, usa a média dessas evidências.
    if evidencias:
        return float(np.clip(np.mean(evidencias), 0, 1))
    # Se não houver evidência local, usa proxy calculado pelos descritores.
    return float(row["score_DFT_proxy"])

# Calcula o score DFT refinado.
dft_df["score_DFT_refinado"] = dft_df.apply(refinar_dft, axis=1)

# Marca se o refinamento usou dados reais do Catalysis-Hub incremental.
dft_df["cathub_incremental_usado"] = dft_df["score_cathub_incremental"].notna()

# Marca os candidatos que passaram pelo refinamento DFT.
dft_df["dft_refinado"] = True

# Mantém apenas os candidatos que passaram pelo refinamento definido no funil.
refinado_df = dft_df.copy()

# Calcula o score final de material após refinamento DFT.
refinado_df["score_final_material"] = (
    0.75 * refinado_df["score_preliminar"]
    + 0.25 * refinado_df["score_DFT_refinado"]
)

# Mostra o ranking refinado.
refinado_df.sort_values("score_final_material", ascending=False)[["formula", "tipo", "dft_refinado", "score_DFT_refinado", "score_final_material"]].head(20)
"""
    ),
    md(
        """
### Subetapa 9.1 - Peso termodinâmico de Boltzmann

Esta subetapa usa a ideia da aula de distribuições de Boltzmann para penalizar candidatos metaestáveis. Candidatos com melhor estabilidade termodinâmica recebem maior peso termodinâmico.
"""
    ),
    code(
        """
# Define a constante de Boltzmann em eV/K para usar a mesma unidade da estabilidade termodinâmica.
K_B_EV = 8.617333262e-5

# Define uma função para calcular o peso de Boltzmann associado à estabilidade.
def peso_boltzmann_hull(energia_hull, temperatura_C):
    # Converte a temperatura de Celsius para Kelvin.
    temperatura_K = float(temperatura_C) + 273.15
    # Garante que a energia usada seja positiva ou nula.
    energia = max(float(energia_hull), 0.0)
    # Calcula o fator de Boltzmann para penalizar estados menos estáveis.
    peso = math.exp(-energia / (K_B_EV * temperatura_K))
    # Limita o peso entre zero e um para uso como score.
    return float(np.clip(peso, 0, 1))

# Calcula uma temperatura de referência a partir das condições desejáveis da reação.
temperatura_referencia_C = float(np.median([cond["temperatura_C"] for cond in perfil["condicoes"]]))

# Calcula o peso de Boltzmann para cada candidato refinado.
refinado_df["peso_boltzmann_estabilidade"] = refinado_df["energy_above_hull_eV_atom"].apply(
    lambda valor: peso_boltzmann_hull(valor, temperatura_referencia_C)
)

# Combina o DFT/proxy DFT com a penalização termodinâmica de Boltzmann.
refinado_df["score_DFT_boltzmann"] = (
    0.85 * refinado_df["score_DFT_refinado"]
    + 0.15 * refinado_df["peso_boltzmann_estabilidade"]
).clip(0, 1)

# Atualiza o score final do material para incorporar estabilidade termodinâmica probabilística.
refinado_df["score_final_material"] = (
    0.70 * refinado_df["score_preliminar"]
    + 0.20 * refinado_df["score_DFT_refinado"]
    + 0.10 * refinado_df["peso_boltzmann_estabilidade"]
)

# Mostra o impacto do peso de Boltzmann no ranking refinado.
refinado_df.sort_values("score_final_material", ascending=False)[[
    "formula",
    "energy_above_hull_eV_atom",
    "peso_boltzmann_estabilidade",
    "score_DFT_refinado",
    "score_DFT_boltzmann",
    "score_final_material",
]].head(20)
"""
    ),
    md(
        """
### Subetapa 9.2 - Volcano simplificado por descritor catalítico

Esta subetapa aplica uma forma simplificada do princípio de Sabatier: adsorção fraca demais reduz ativação, e adsorção forte demais dificulta dessorção/turnover. O score volcano usa energia real do Catalysis-Hub quando disponível; quando não há, usa um descritor proxy derivado de GNN local, DFT proxy e estabilidade. O resultado é uma taxa relativa adimensional, não uma microcinética completa.
"""
    ),
    code(
        """
# Define descritores principais do volcano por reação.
VOLCANO_CONFIG = {
    "metanacao": {"descritor": "CO", "energia_otima_eV": 0.85, "largura_eV": 0.35, "barreira_base_eV": 0.62},
    "reforma": {"descritor": "C", "energia_otima_eV": 1.25, "largura_eV": 0.45, "barreira_base_eV": 0.78},
    "rwgs": {"descritor": "CO", "energia_otima_eV": 0.70, "largura_eV": 0.32, "barreira_base_eV": 0.58},
}

# Seleciona configuração da reação atual.
volcano_cfg = VOLCANO_CONFIG[reacao]

# Define função para estimar energia de adsorção proxy quando não há Catalysis-Hub.
def energia_adsorcao_proxy_volcano(row):
    # Usa energia média Catalysis-Hub quando disponível.
    energia_cathub = row.get("energia_cathub_media_eV", np.nan)
    # Retorna módulo da energia real/proxy DFT de adsorção quando existe.
    if pd.notna(energia_cathub):
        return abs(float(energia_cathub)), "Catalysis-Hub"
    # Usa score GNN local como proxy de força de ligação quando disponível.
    score_gnn = row.get("score_gnn_local", np.nan)
    # Usa score DFT refinado como evidência catalítica geral.
    score_dft = row.get("score_DFT_refinado", np.nan)
    # Usa estabilidade como penalização indireta.
    score_estabilidade = row.get("score_estabilidade", np.nan)
    # Combina evidências disponíveis em score adimensional.
    evidencias = [v for v in [score_gnn, score_dft, score_estabilidade] if pd.notna(v)]
    # Retorna alvo da reação quando não há nenhuma evidência.
    if not evidencias:
        return float(volcano_cfg["energia_otima_eV"]), "proxy_neutro"
    # Calcula score médio das evidências.
    score_medio = float(np.clip(np.mean(evidencias), 0, 1))
    # Converte score em energia de adsorção ao redor do ótimo.
    energia = volcano_cfg["energia_otima_eV"] + (0.5 - score_medio) * 2.0 * volcano_cfg["largura_eV"]
    # Limita energia proxy a faixa fisicamente moderada para triagem.
    return float(np.clip(energia, 0.05, 2.50)), "proxy_GNN_DFT_estabilidade"

# Define função para calcular score volcano.
def calcular_volcano(row):
    # Obtém energia de adsorção ou proxy.
    energia_ads, fonte = energia_adsorcao_proxy_volcano(row)
    # Substitui energia ausente ou inválida pelo ótimo da reação.
    if pd.isna(energia_ads) or not np.isfinite(float(energia_ads)):
        energia_ads = float(volcano_cfg["energia_otima_eV"])
        fonte = "proxy_neutro"
    # Calcula distância ao ótimo do volcano.
    distancia = abs(float(energia_ads) - volcano_cfg["energia_otima_eV"])
    # Transforma distância em score Sabatier.
    score_volcano = math.exp(-distancia / max(volcano_cfg["largura_eV"], 0.05))
    # Calcula barreira aparente simplificada.
    barreira_aparente = volcano_cfg["barreira_base_eV"] + distancia
    # Usa temperatura de referência para uma taxa relativa tipo Arrhenius.
    temperatura_K = temperatura_referencia_C + 273.15
    # Calcula taxa relativa adimensional.
    taxa_relativa = math.exp(-barreira_aparente / (K_B_EV * temperatura_K))
    # Retorna campos do volcano.
    return pd.Series({
        "descritor_volcano": volcano_cfg["descritor"],
        "energia_adsorcao_volcano_eV": energia_ads,
        "fonte_volcano": fonte,
        "distancia_otimo_volcano_eV": distancia,
        "barreira_aparente_volcano_eV": barreira_aparente,
        "taxa_relativa_volcano": taxa_relativa,
        "score_volcano": float(np.clip(score_volcano, 0, 1)),
    })

# Calcula volcano simplificado para cada candidato refinado.
volcano_df = refinado_df.apply(calcular_volcano, axis=1)

# Junta os campos volcano ao dataframe refinado.
refinado_df = pd.concat([refinado_df.reset_index(drop=True), volcano_df.reset_index(drop=True)], axis=1)

# Define função para estimar penalização semiempírica por tendência a coque.
def calcular_penalidade_coque_reforma(row, razao_ch4_co2=1.0):
    # Mantém a penalização desligada para reações diferentes de reforma.
    if reacao != "reforma":
        return pd.Series({
            "penalidade_tendencia_coque": 0.0,
            "taxa_desativacao_coque_proxy": 0.0,
            "score_atividade_corrigida_coque": float(row.get("score_atividade", 0.5)),
        })
    # Usa a energia de adsorção de C do volcano como proxy de carbono superficial.
    energia_c = row.get("energia_adsorcao_volcano_eV", np.nan)
    # Converte ausência de energia em valor ótimo para evitar penalização artificial.
    if pd.isna(energia_c):
        energia_c = volcano_cfg["energia_otima_eV"]
    # Penaliza principalmente adsorção de C mais forte que o ótimo do volcano.
    excesso_adsorcao_c = max(float(energia_c) - volcano_cfg["energia_otima_eV"], 0.0)
    # Normaliza o excesso de adsorção de C pela largura do volcano.
    tendencia_c_superficial = np.clip(excesso_adsorcao_c / max(volcano_cfg["largura_eV"], 0.05), 0, 1)
    # Usa atividade alta de reforma/ativação de CH4 como fator de formação de carbono.
    fator_ativacao_ch4 = float(np.clip(row.get("score_atividade", 0.5), 0, 1))
    # Usa redox, mobilidade de oxigênio e resistência composicional como capacidade de remoção de carbono.
    capacidade_remocao_c = float(np.clip(np.mean([
        row.get("score_redox", 0.5),
        row.get("score_resistencia_coque", 0.5),
    ]), 0, 1))
    # Penaliza excesso relativo de CH4 quando a razão CH4/CO2 passa de 1.
    excesso_ch4 = np.clip(max(float(razao_ch4_co2) - 1.0, 0.0), 0, 1)
    # Combina formação de carbono, adsorção forte e baixa remoção oxidativa.
    penalidade = (
        0.34 * fator_ativacao_ch4
        + 0.32 * tendencia_c_superficial
        + 0.24 * (1.0 - capacidade_remocao_c)
        + 0.10 * excesso_ch4
    )
    # Limita a penalidade para manter o termo como correção, não como filtro absoluto.
    penalidade = float(np.clip(penalidade, 0, 1))
    # Estima uma constante adimensional de desativação por coque.
    taxa_desativacao = float(np.clip(0.03 + 0.32 * penalidade, 0, 0.40))
    # Corrige a atividade inicial por uma queda exponencial simples.
    atividade_corrigida = float(np.clip(fator_ativacao_ch4 * math.exp(-taxa_desativacao), 0, 1))
    # Retorna os novos descritores de desativação.
    return pd.Series({
        "penalidade_tendencia_coque": penalidade,
        "taxa_desativacao_coque_proxy": taxa_desativacao,
        "score_atividade_corrigida_coque": atividade_corrigida,
    })

# Calcula descritores de desativação por coque para os candidatos refinados.
coque_reforma_df = refinado_df.apply(calcular_penalidade_coque_reforma, axis=1)

# Junta os descritores de coque ao dataframe refinado.
refinado_df = pd.concat([refinado_df.reset_index(drop=True), coque_reforma_df.reset_index(drop=True)], axis=1)

# Atualiza o score final incorporando o volcano simplificado.
refinado_df["score_final_material"] = (
    0.62 * refinado_df["score_preliminar"]
    + 0.16 * refinado_df["score_DFT_refinado"]
    + 0.10 * refinado_df["peso_boltzmann_estabilidade"]
    + 0.12 * refinado_df["score_volcano"]
).clip(0, 1)

# Aplica penalização de desativação por coque apenas para reforma.
if reacao == "reforma":
    # Reduz o score do material quando a tendência a coque é alta.
    refinado_df["score_final_material"] = (
        refinado_df["score_final_material"] * (1.0 - 0.20 * refinado_df["penalidade_tendencia_coque"])
        + 0.08 * refinado_df["score_atividade_corrigida_coque"]
    ).clip(0, 1)

# Exibe impacto do volcano no ranking.
refinado_df.sort_values("score_final_material", ascending=False)[[
    "formula",
    "descritor_volcano",
    "energia_adsorcao_volcano_eV",
    "fonte_volcano",
    "score_volcano",
    "penalidade_tendencia_coque",
    "taxa_desativacao_coque_proxy",
    "taxa_relativa_volcano",
    "score_final_material",
]].head(20)
"""
    ),
    md(
        """
## Etapa 10 - Suporte e condições desejáveis de síntese/teste

O suporte e as condições são definidos pelo modelo com base na reação e na composição química do candidato.
"""
    ),
    code(
        """
# Define regras químicas para sugerir suporte, rota e pré-tratamento.
def recomendar_sintese(formula):
    # Extrai elementos presentes no candidato.
    elems = elementos_formula(formula)
    # Identifica metais ativos comuns em reações de CO2/CH4.
    ativos_transicao = elems & {"Ni", "Co", "Fe", "Cu", "Mo"}
    # Identifica metais nobres que normalmente pedem baixa carga e alta dispersão.
    nobres = elems & {"Ru", "Rh", "Pt", "Pd"}
    # Identifica modificadores redox importantes.
    redox_mod = elems & {"Ce", "Zr", "Mo", "Fe"}
    # Identifica modificadores básicos úteis para ativação de CO2 e mitigação de coque.
    basicos = elems & {"Mg", "La", "Ca", "Ba"}
    # Define valores padrão para composição sem regra específica.
    suporte = "Al2O3-ZrO2"
    rota = "impregnacao incipiente em suporte oxido"
    pretratamento = "calcinacao em ar entre 450 e 550 C seguida de reducao em H2 diluido"
    justificativa = "suporte oxido misto para estabilidade termica e dispersao da fase ativa"
    observacao = "confirmar carga metalica e pH de impregnacao conforme solubilidade dos precursores"
    # Ajusta regras para metanação.
    if reacao == "metanacao":
        if redox_mod & {"Ce", "Zr"}:
            suporte = "CeO2-ZrO2 ou Al2O3-CeO2-ZrO2"
            rota = "impregnacao incipiente da fase ativa sobre suporte Ce-Zr pre-calcinado"
            justificativa = "Ce/Zr favorece ativacao de CO2, vacancias de oxigenio e estabilidade da interface metal-suporte"
        elif basicos:
            suporte = "Al2O3 modificada com MgO ou La2O3"
            rota = "impregnacao sequencial do promotor basico seguida do metal ativo"
            justificativa = "promotores basicos aumentam adsorcao/ativacao de CO2 e podem melhorar seletividade a CH4"
        elif nobres:
            suporte = "Al2O3 de alta area ou CeO2-Al2O3"
            rota = "impregnacao umida com baixa carga metalica para maximizar dispersao"
            justificativa = "metais nobres devem ser bem dispersos para reduzir custo e evitar sinterizacao"
        else:
            suporte = "Al2O3 ou SiO2-Al2O3"
            rota = "impregnacao incipiente de Ni/Co/Fe seguida de calcinacao e reducao"
            justificativa = "suporte de alta area favorece dispersao da fase ativa em metanacao"
    # Ajusta regras para reforma de CH4.
    elif reacao == "reforma":
        if redox_mod & {"Ce", "Zr"} and basicos:
            suporte = "CeO2-ZrO2-MgAlOx ou CeO2-ZrO2-La2O3-Al2O3"
            rota = "coprecipitação do suporte redox-básico seguida de impregnação do metal ativo"
            justificativa = "combina mobilidade de oxigênio com basicidade para remover carbono superficial"
        elif redox_mod & {"Ce", "Zr"}:
            suporte = "CeO2-ZrO2 ou Al2O3-CeO2-ZrO2"
            rota = "sol-gel ou coprecipitação do suporte Ce-Zr, seguida de impregnação da fase ativa"
            justificativa = "suporte redox melhora transferência de oxigênio e reduz desativação por coque"
        elif basicos:
            suporte = "MgAlOx, La2O3-Al2O3 ou espinelio MgAl2O4"
            rota = "coprecipitacao ou metodo hidrotalcita-like para alta estabilidade termica"
            justificativa = "basicidade e estabilidade termica ajudam a reduzir deposicao de carbono"
        elif "Ni" in elems:
            suporte = "MgO-Al2O3, MgAl2O4 ou La2O3-Al2O3"
            rota = "impregnação incipiente de Ni sobre suporte básico previamente calcinado"
            justificativa = "Ni é ativo para reforma, mas requer suporte básico/redox para mitigar coque"
        elif nobres:
            suporte = "CeO2-ZrO2, MgO-Al2O3 ou La2O3-Al2O3"
            rota = "impregnacao sequencial com baixa carga de metal nobre"
            justificativa = "metal nobre melhora ativacao, mas o suporte deve controlar sinterizacao e custo"
        else:
            suporte = "MgO-Al2O3, MgAl2O4 ou La2O3-Al2O3"
            rota = "impregnacao incipiente ou coprecipitacao simples seguida de reducao"
            justificativa = "suporte estavel e basico e preferivel para alta temperatura de reforma"
        pretratamento = "calcinacao entre 650 e 800 C e reducao em H2 antes do teste catalitico"
        observacao = "avaliar razao CH4/CO2 e tempo de estabilidade para confirmar resistencia a coque"
    # Ajusta regras para RWGS.
    else:
        if "Cu" in elems and redox_mod & {"Ce", "Zr"}:
            suporte = "CeO2-ZrO2 com Cu altamente disperso"
            rota = "deposicao-precipitacao ou impregnacao de Cu sobre suporte Ce-Zr"
            justificativa = "Cu favorece seletividade a CO e Ce/Zr auxilia ativação de CO2"
        elif redox_mod & {"Ce", "Zr"}:
            suporte = "CeO2-ZrO2 ou ZrO2"
            rota = "coprecipitacao/sol-gel do suporte redox seguida de impregnacao metalica"
            justificativa = "suporte redox favorece RWGS por ativação de CO2 e adsorção moderada de CO"
        elif nobres:
            suporte = "ZrO2 ou Al2O3-ZrO2"
            rota = "impregnacao sequencial com controle de baixa carga metalica"
            justificativa = "ZrO2 ajuda a modular adsorcao de CO e estabilizar particulas metalicas"
        else:
            suporte = "Al2O3-ZrO2 ou ZrO2"
            rota = "impregnacao incipiente seguida de calcinacao e reducao"
            justificativa = "suporte moderadamente redox favorece seletividade a CO"
    # Ajusta a rota para metais ativos de transição sem promotor forte.
    if ativos_transicao and not (redox_mod or basicos or nobres):
        rota = "impregnacao incipiente do metal ativo em suporte de alta area"
    # Retorna recomendações organizadas.
    return pd.Series({
        "suporte_sugerido": suporte,
        "rota_sintese_sugerida": rota,
        "pretratamento_sugerido": pretratamento,
        "justificativa_suporte_sintese": justificativa,
        "observacao_sintese": observacao,
    })

# Calcula recomendações de síntese e suporte.
sintese_df = refinado_df["formula"].apply(recomendar_sintese)

# Junta recomendações ao dataframe refinado.
refinado_df = pd.concat([refinado_df.reset_index(drop=True), sintese_df.reset_index(drop=True)], axis=1)

# Mostra suporte, rota e justificativa para os principais candidatos.
refinado_df.sort_values("score_final_material", ascending=False)[[
    "formula",
    "suporte_sugerido",
    "rota_sintese_sugerida",
    "pretratamento_sugerido",
    "justificativa_suporte_sintese",
]].head(20)
"""
    ),
    md(
        """
## Etapa 11 - Ranking catalisador-condição

Cada candidato é avaliado nas condições desejáveis da reação. O score final combina qualidade do material e adequação da condição.
"""
    ),
    code(
        """
# Define uma função para limitar valores entre 0 e 100.
def limitar_0_100(valor):
    # Usa numpy.clip para restringir o valor.
    return float(np.clip(valor, 0, 100))

# Define fatores de condição para cada reação.
def fator_condicao(condicao, reacao_alvo):
    # Lê temperatura da condição.
    temp = condicao["temperatura_C"]
    # Lê pressão da condição.
    pressao = condicao["pressao_bar"]
    # Lê razão reacional da condição.
    razao = condicao["razao"]
    # Define fatores para metanação.
    if reacao_alvo == "metanacao":
        conv = 0.74 + 0.34 / (1.0 + math.exp(-(temp - 345.0) / 32.0))
        sel = 1.02 - 0.000018 * (temp - 360.0) ** 2
        razao_fator = 1.0 - 0.035 * abs(razao - 4.0)
    # Define fatores para reforma.
    elif reacao_alvo == "reforma":
        conv = 0.45 + 0.60 / (1.0 + math.exp(-(temp - 720.0) / 55.0))
        sel = 0.86 + 0.12 / (1.0 + math.exp(-(temp - 700.0) / 70.0))
        razao_fator = 1.0 - 0.04 * abs(razao - 1.0)
    # Define fatores para RWGS.
    else:
        conv = 0.55 + 0.48 / (1.0 + math.exp(-(temp - 570.0) / 50.0))
        sel = 0.92 + 0.10 / (1.0 + math.exp(-(temp - 590.0) / 55.0))
        razao_fator = 1.0 - 0.035 * abs(razao - 2.0)
    # Calcula efeito de pressão.
    pressao_fator = 1.0 + 0.03 * math.log(max(pressao, 1.0))
    # Retorna fatores de conversão e seletividade.
    return conv * pressao_fator * razao_fator, sel * razao_fator

# Cria lista para armazenar combinações catalisador-condição.
linhas = []

# Percorre cada candidato refinado.
for _, row in refinado_df.iterrows():
    # Percorre cada condição definida no perfil da reação.
    for condicao in perfil["condicoes"]:
        # Calcula fatores de condição.
        fator_conv, fator_sel = fator_condicao(condicao, reacao)
        # Calcula penalização de coque específica da condição operacional.
        coque_condicao = calcular_penalidade_coque_reforma(row, condicao.get("razao", 1.0))
        # Extrai a penalidade de coque dependente da condição.
        penalidade_coque_condicao = float(coque_condicao["penalidade_tendencia_coque"])
        # Extrai a taxa proxy de desativação dependente da condição.
        taxa_desativacao_coque_condicao = float(coque_condicao["taxa_desativacao_coque_proxy"])
        # Usa atividade corrigida por coque para reforma e atividade original para as demais reações.
        atividade_operacional = float(coque_condicao["score_atividade_corrigida_coque"]) if reacao == "reforma" else float(row["score_atividade"])
        # Estima conversão a partir do score de atividade operacional.
        conversao = limitar_0_100((35 + 45 * atividade_operacional) * fator_conv)
        # Estima seletividade a partir do score de seletividade.
        seletividade = limitar_0_100((45 + 50 * row["score_seletividade"]) * fator_sel)
        # Calcula rendimento/produtividade relativa.
        rendimento = limitar_0_100(conversao * seletividade / 100.0)
        # Calcula score de condição.
        score_condicao = 0.40 * conversao/100 + 0.30 * seletividade/100 + 0.30 * rendimento/100
        # Combina score do material e score da condição.
        score_final = 0.60 * row["score_final_material"] + 0.40 * score_condicao
        # Penaliza levemente a combinação quando a condição favorece coque em reforma.
        if reacao == "reforma":
            score_final = float(np.clip(score_final * (1.0 - 0.10 * penalidade_coque_condicao), 0, 1))
        # Armazena a linha final.
        linhas.append({
            "reacao": reacao,
            "formula": row["formula"],
            "tipo": row["tipo"],
            "metais_ativos_presentes": row.get("metais_ativos_presentes", ""),
            "n_metais_ativos_presentes": row.get("n_metais_ativos_presentes", 0),
            "candidato_multimetal_ativo": row.get("candidato_multimetal_ativo", False),
            "suporte_sugerido": row["suporte_sugerido"],
            "rota_sintese_sugerida": row["rota_sintese_sugerida"],
            "pretratamento_sugerido": row["pretratamento_sugerido"],
            "justificativa_suporte_sintese": row["justificativa_suporte_sintese"],
            "observacao_sintese": row["observacao_sintese"],
            "energy_above_hull_eV_atom": row["energy_above_hull_eV_atom"],
            "score_estabilidade": row["score_estabilidade"],
            "score_atividade": row["score_atividade"],
            "score_seletividade": row["score_seletividade"],
            "score_DFT": row["score_DFT_refinado"],
            "score_incerteza": row["score_incerteza"],
            "score_basicidade": row["score_basicidade"],
            "score_redox": row["score_redox"],
            "score_resistencia_coque": row["score_resistencia_coque"],
            "penalidade_tendencia_coque": row.get("penalidade_tendencia_coque", np.nan),
            "taxa_desativacao_coque_proxy": row.get("taxa_desativacao_coque_proxy", np.nan),
            "score_atividade_corrigida_coque": row.get("score_atividade_corrigida_coque", np.nan),
            "penalidade_coque_condicao": penalidade_coque_condicao,
            "taxa_desativacao_coque_condicao": taxa_desativacao_coque_condicao,
            "score_matminer_composicional": row["score_matminer_composicional"],
            "score_pymatgen_quimico": row["score_pymatgen_quimico"],
            "score_gnn_local": row.get("score_gnn_local", np.nan),
            "energia_gnn_eV_atom": row.get("energia_gnn_eV_atom", np.nan),
            "energia_formacao_gnn_eV_atom": row.get("energia_formacao_gnn_eV_atom", np.nan),
            "modelo_gnn_local": row.get("modelo_gnn_local", "indisponivel"),
            "gnn_local_usado": row.get("gnn_local_usado", False),
            "estrutura_proxy_gnn": row.get("estrutura_proxy_gnn", ""),
            "fonte_estabilidade_triagem": row.get("fonte_estabilidade_triagem", ""),
            "peso_boltzmann_estabilidade": row["peso_boltzmann_estabilidade"],
            "score_DFT_boltzmann": row["score_DFT_boltzmann"],
            "descritor_volcano": row.get("descritor_volcano", ""),
            "energia_adsorcao_volcano_eV": row.get("energia_adsorcao_volcano_eV", np.nan),
            "fonte_volcano": row.get("fonte_volcano", ""),
            "distancia_otimo_volcano_eV": row.get("distancia_otimo_volcano_eV", np.nan),
            "barreira_aparente_volcano_eV": row.get("barreira_aparente_volcano_eV", np.nan),
            "taxa_relativa_volcano": row.get("taxa_relativa_volcano", np.nan),
            "score_volcano": row.get("score_volcano", np.nan),
            "score_final_material": row["score_final_material"],
            "score_cathub_incremental": row.get("score_cathub_incremental", np.nan),
            "energia_cathub_media_eV": row.get("energia_cathub_media_eV", np.nan),
            "n_evidencias_cathub_incremental": row.get("n_evidencias_cathub_incremental", 0),
            "adsorbatos_cathub_encontrados": row.get("adsorbatos_cathub_encontrados", ""),
            "cathub_incremental_usado": row.get("cathub_incremental_usado", False),
            **condicao,
            "conversao_prevista_pct": conversao,
            "seletividade_produto_prevista_pct": seletividade,
            "rendimento_ou_produtividade_prevista_pct": rendimento,
            "score_final": score_final,
        })

# Converte as combinações finais em tabela.
ranking_final_df = pd.DataFrame(linhas)

# Ordena a tabela pelo score final.
ranking_final_df = ranking_final_df.sort_values("score_final", ascending=False).reset_index(drop=True)

# Cria lista para armazenar o desempenho médio nas vizinhanças de condição.
linhas_faixa = []

# Percorre cada candidato para avaliar robustez em uma faixa de temperatura, pressão e razão.
for _, row in refinado_df.iterrows():
    # Percorre cada condição nominal definida no perfil da reação.
    for condicao in perfil["condicoes"]:
        # Cria lista temporária para guardar simulações locais ao redor da condição nominal.
        simulacoes = []
        # Varia temperatura em uma faixa curta para estimar desempenho médio.
        for temperatura_C in np.linspace(condicao["temperatura_C"] - 25, condicao["temperatura_C"] + 25, 5):
            # Varia pressão em torno da condição nominal.
            for pressao_bar in [condicao["pressao_bar"] * 0.8, condicao["pressao_bar"], condicao["pressao_bar"] * 1.2]:
                # Varia razão molar em torno da condição nominal.
                for razao in [condicao["razao"] * 0.9, condicao["razao"], condicao["razao"] * 1.1]:
                    # Copia a condição nominal para preservar o dicionário original.
                    condicao_variada = dict(condicao)
                    # Atualiza a temperatura da condição variada.
                    condicao_variada["temperatura_C"] = float(temperatura_C)
                    # Atualiza a pressão da condição variada.
                    condicao_variada["pressao_bar"] = float(pressao_bar)
                    # Atualiza a razão gasosa da condição variada.
                    condicao_variada["razao"] = float(razao)
                    # Calcula fatores de conversão e seletividade para a condição variada.
                    fator_conv, fator_sel = fator_condicao(condicao_variada, reacao)
                    # Calcula penalização de coque para a condição variada.
                    coque_condicao_variada = calcular_penalidade_coque_reforma(row, condicao_variada.get("razao", 1.0))
                    # Usa atividade corrigida por coque em reforma também na análise de robustez por faixa.
                    atividade_operacional_faixa = float(coque_condicao_variada["score_atividade_corrigida_coque"]) if reacao == "reforma" else float(row["score_atividade"])
                    # Estima conversão para a condição variada.
                    conversao = limitar_0_100((35 + 45 * atividade_operacional_faixa) * fator_conv)
                    # Estima seletividade para a condição variada.
                    seletividade = limitar_0_100((45 + 50 * row["score_seletividade"]) * fator_sel)
                    # Calcula rendimento ou produtividade para a condição variada.
                    rendimento = limitar_0_100(conversao * seletividade / 100.0)
                    # Calcula score de condição para a simulação local.
                    score_condicao = 0.40 * conversao/100 + 0.30 * seletividade/100 + 0.30 * rendimento/100
                    # Aplica a mesma penalizacao explicita de coque usada no score nominal para nao diluir o efeito no re-ranking por faixa.
                    if reacao == "reforma":
                        score_condicao = float(np.clip(score_condicao * (1.0 - 0.10 * float(coque_condicao_variada["penalidade_tendencia_coque"])), 0, 1))
                    # Guarda a simulação local para cálculo das médias.
                    simulacoes.append((conversao, seletividade, rendimento, score_condicao))
        # Converte as simulações locais em matriz numérica.
        simulacoes = np.array(simulacoes, dtype=float)
        # Armazena estatísticas médias da faixa avaliada.
        linhas_faixa.append({
            "formula": row["formula"],
            "regime": condicao["regime"],
            "temperatura_C": float(condicao["temperatura_C"]),
            "pressao_bar": float(condicao["pressao_bar"]),
            "razao_nome": condicao["razao_nome"],
            "razao": float(condicao["razao"]),
            "ghsv_h-1": float(condicao["ghsv_h-1"]),
            "conversao_media_faixa_pct": float(simulacoes[:, 0].mean()),
            "seletividade_media_faixa_pct": float(simulacoes[:, 1].mean()),
            "rendimento_medio_faixa_pct": float(simulacoes[:, 2].mean()),
            "score_faixa_condicao": float(simulacoes[:, 3].mean()),
        })

# Converte a avaliação por faixa em tabela.
desempenho_faixa_df = pd.DataFrame(linhas_faixa)

# Define chaves univocas de catalisador-condicao para evitar produto cartesiano no merge.
chaves_desempenho_merge = [
    "formula",
    "regime",
    "temperatura_C",
    "pressao_bar",
    "razao_nome",
    "razao",
    "ghsv_h-1",
]

# Define as metricas de desempenho por faixa que devem ser anexadas ao ranking.
metricas_desempenho_merge = [
    "conversao_media_faixa_pct",
    "seletividade_media_faixa_pct",
    "rendimento_medio_faixa_pct",
    "score_faixa_condicao",
]

# Monta tabela de desempenho por faixa com chaves completas e metricas.
desempenho_merge_df = desempenho_faixa_df[chaves_desempenho_merge + metricas_desempenho_merge].copy()

# Agrupa eventuais duplicatas de chave antes do merge para impedir multiplicacao silenciosa de linhas.
if desempenho_merge_df.duplicated(subset=chaves_desempenho_merge).any():
    desempenho_merge_df = desempenho_merge_df.groupby(chaves_desempenho_merge, as_index=False)[metricas_desempenho_merge].mean()

# Junta o desempenho médio por faixa ao ranking final nominal sem duplicar temperatura, pressão e razão.
ranking_final_df = ranking_final_df.merge(
    desempenho_merge_df,
    on=chaves_desempenho_merge,
    how="left",
    validate="many_to_one",
)

# Recalcula o score final favorecendo candidatos robustos em uma faixa de condição.
ranking_final_df["score_final"] = (
    0.80 * ranking_final_df["score_final"]
    + 0.20 * ranking_final_df["score_faixa_condicao"]
)

# Ordena novamente a tabela após incluir desempenho médio por faixa.
ranking_final_df = ranking_final_df.sort_values("score_final", ascending=False).reset_index(drop=True)

# Mostra as melhores combinações.
ranking_final_df.head(20)
"""
    ),
    md(
        """
## Etapa 12 - Controle de incerteza e recomendação para síntese

O notebook classifica a confiabilidade e recomenda apenas os melhores candidatos para síntese, deixando os demais como exploratórios.
"""
    ),
code(
        """
# Define os descritores que serão avaliados na análise de sensibilidade.
descritores_sensibilidade = ["score_estabilidade", "score_atividade", "score_seletividade", "score_DFT_refinado", "score_incerteza"]

# Cria lista para armazenar a sensibilidade do score a cada descritor.
linhas_sensibilidade = []

# Percorre cada candidato refinado para estimar sensibilidade local.
for _, row in refinado_df.iterrows():
    # Guarda o score de referência antes da perturbação.
    score_base = float(row["score_final_material"])
    # Percorre cada descritor selecionado.
    for descritor in descritores_sensibilidade:
        # Cria uma cópia da linha para perturbar apenas um descritor.
        perturbado = row.copy()
        # Aumenta o descritor em 0,05 unidade de score.
        perturbado[descritor] = float(np.clip(perturbado[descritor] + 0.05, 0, 1))
        # Recalcula o score preliminar após a perturbação.
        score_preliminar_perturbado = (
            pesos["estabilidade"] * perturbado["score_estabilidade"]
            + pesos["atividade"] * perturbado["score_atividade"]
            + pesos["seletividade"] * perturbado["score_seletividade"]
            + pesos["dft"] * perturbado["score_DFT_proxy"]
            + pesos["incerteza"] * perturbado["score_incerteza"]
        )
        # Recalcula o score final do material após a perturbação.
        score_perturbado = (
            0.70 * score_preliminar_perturbado
            + 0.20 * perturbado["score_DFT_refinado"]
            + 0.10 * perturbado["peso_boltzmann_estabilidade"]
        )
        # Calcula sensibilidade como variação do score dividida pela perturbação.
        sensibilidade = (float(score_perturbado) - score_base) / 0.05
        # Armazena a sensibilidade calculada.
        linhas_sensibilidade.append({
            "formula": row["formula"],
            "descritor": descritor,
            "sensibilidade_score": sensibilidade,
        })

# Converte a análise de sensibilidade em tabela.
sensibilidade_descritores_df = pd.DataFrame(linhas_sensibilidade)

# Cria gerador aleatório reprodutível para simulação Monte Carlo.
rng = np.random.default_rng(42)

# Define quantas simulações Monte Carlo serão realizadas.
n_simulacoes_mc = 300

# Seleciona um conjunto controlado de candidatos-condição para estimar incerteza no ranking.
base_mc = ranking_final_df.head(30).copy()

# Define limite mínimo para evitar divisão por zero no score de estabilidade.
limite_hull_mc = max(float(perfil["limite_hull_exploratorio"]), 1e-6)

# Cria contador para frequência de permanência no top 5.
contagem_top5 = {formula: 0 for formula in base_mc["formula"].unique()}

# Cria acumulador dos melhores scores simulados por fórmula.
scores_mc_por_formula = {formula: [] for formula in base_mc["formula"].unique()}

# Define função para estimar o desvio da estabilidade conforme a fonte dos dados.
def sigma_estabilidade_mc(row):
    # Lê a fonte de estabilidade usada na triagem.
    fonte = str(row.get("fonte_estabilidade_triagem", "")).lower()
    # Usa menor incerteza quando a estabilidade veio de base DFT estruturada.
    if "materials project" in fonte or "mp" == fonte or "oqmd" in fonte:
        return 0.015
    # Usa incerteza intermediária quando a estabilidade veio de GNN local.
    if bool(row.get("gnn_local_usado", False)):
        return 0.035
    # Usa maior incerteza quando a estabilidade veio de proxy químico ou fonte indefinida.
    return 0.050

# Define função para estimar o desvio do descritor DFT/proxy.
def sigma_dft_mc(row):
    # Usa menor incerteza quando houve evidência incremental do Catalysis-Hub.
    if bool(row.get("cathub_incremental_usado", False)):
        return 0.040
    # Usa incerteza intermediária quando há proxy GNN local.
    if bool(row.get("gnn_local_usado", False)):
        return 0.080
    # Usa maior incerteza quando o DFT é apenas proxy químico.
    return 0.120

# Define função para estimar o desvio do volcano conforme a origem da energia de adsorção.
def sigma_volcano_mc(row):
    # Usa menor incerteza quando a energia do volcano veio do Catalysis-Hub.
    if str(row.get("fonte_volcano", "")).lower() == "catalysis-hub":
        return 0.050
    # Usa maior incerteza quando o volcano é derivado de proxy.
    return 0.120

# Executa simulações Monte Carlo propagando ruído nos descritores fundamentais.
for _ in range(n_simulacoes_mc):
    # Copia o ranking base para não alterar a tabela original.
    simulado = base_mc.copy()
    # Calcula desvio de estabilidade por candidato.
    sigma_hull = simulado.apply(sigma_estabilidade_mc, axis=1).to_numpy(dtype=float)
    # Perturba a estabilidade termodinâmica em eV/atom.
    simulado["energy_above_hull_mc"] = np.clip(
        simulado["energy_above_hull_eV_atom"].to_numpy(dtype=float) + rng.normal(0, sigma_hull, len(simulado)),
        0,
        limite_hull_mc * 1.5,
    )
    # Recalcula o score de estabilidade a partir da estabilidade perturbada.
    simulado["score_estabilidade_mc"] = (1.0 - simulado["energy_above_hull_mc"] / limite_hull_mc).clip(0, 1)
    # Calcula desvio dos scores catalíticos a partir do nível de confiança.
    sigma_score = 0.035 + 0.070 * (1.0 - simulado["score_incerteza"].clip(0, 1).to_numpy(dtype=float))
    # Perturba o score de atividade.
    simulado["score_atividade_mc"] = np.clip(simulado["score_atividade"].to_numpy(dtype=float) + rng.normal(0, sigma_score, len(simulado)), 0, 1)
    # Perturba o score de seletividade.
    simulado["score_seletividade_mc"] = np.clip(simulado["score_seletividade"].to_numpy(dtype=float) + rng.normal(0, sigma_score, len(simulado)), 0, 1)
    # Calcula desvio específico para DFT/proxy.
    sigma_dft = simulado.apply(sigma_dft_mc, axis=1).to_numpy(dtype=float)
    # Perturba o score DFT/proxy.
    simulado["score_DFT_mc"] = np.clip(simulado["score_DFT"].to_numpy(dtype=float) + rng.normal(0, sigma_dft, len(simulado)), 0, 1)
    # Calcula desvio específico para o score volcano.
    sigma_volcano = simulado.apply(sigma_volcano_mc, axis=1).to_numpy(dtype=float)
    # Perturba o score volcano.
    simulado["score_volcano_mc"] = np.clip(simulado["score_volcano"].fillna(0.5).to_numpy(dtype=float) + rng.normal(0, sigma_volcano, len(simulado)), 0, 1)
    # Perturba a penalidade de coque quando ela existe no ranking.
    simulado["penalidade_coque_mc"] = np.clip(
        simulado.get("penalidade_coque_condicao", pd.Series(0.0, index=simulado.index)).fillna(0.0).to_numpy(dtype=float)
        + rng.normal(0, 0.060, len(simulado)),
        0,
        1,
    )
    # Recalcula atividade corrigida por coque em reforma.
    simulado["score_atividade_corrigida_coque_mc"] = np.where(
        reacao == "reforma",
        np.clip(simulado["score_atividade_mc"] * np.exp(-(0.03 + 0.32 * simulado["penalidade_coque_mc"])), 0, 1),
        simulado["score_atividade_mc"],
    )
    # Perturba o score de confiança mantendo a interpretação de confiabilidade.
    simulado["score_incerteza_mc"] = np.clip(simulado["score_incerteza"].to_numpy(dtype=float) + rng.normal(0, 0.050, len(simulado)), 0, 1)
    # Recalcula o score preliminar com os descritores perturbados.
    simulado["score_preliminar_mc"] = (
        pesos["estabilidade"] * simulado["score_estabilidade_mc"]
        + pesos["atividade"] * simulado["score_atividade_mc"]
        + pesos["seletividade"] * simulado["score_seletividade_mc"]
        + pesos["dft"] * simulado["score_DFT_mc"]
        + pesos["incerteza"] * simulado["score_incerteza_mc"]
    ).clip(0, 1)
    # Recalcula o peso de Boltzmann a partir da estabilidade perturbada.
    simulado["peso_boltzmann_mc"] = simulado["energy_above_hull_mc"].apply(
        lambda valor: peso_boltzmann_hull(valor, temperatura_referencia_C)
    )
    # Recalcula o score final do material com a mesma equação nominal.
    simulado["score_final_material_mc"] = (
        0.62 * simulado["score_preliminar_mc"]
        + 0.16 * simulado["score_DFT_mc"]
        + 0.10 * simulado["peso_boltzmann_mc"]
        + 0.12 * simulado["score_volcano_mc"]
    ).clip(0, 1)
    # Aplica desativação por coque no score de material simulado para reforma.
    if reacao == "reforma":
        simulado["score_final_material_mc"] = (
            simulado["score_final_material_mc"] * (1.0 - 0.20 * simulado["penalidade_coque_mc"])
            + 0.08 * simulado["score_atividade_corrigida_coque_mc"]
        ).clip(0, 1)
    # Recalcula conversão prevista a partir da atividade perturbada.
    conversao_mc = np.clip(simulado["conversao_prevista_pct"].to_numpy(dtype=float) * (0.80 + 0.40 * simulado["score_atividade_corrigida_coque_mc"].to_numpy(dtype=float)), 0, 100)
    # Recalcula seletividade prevista a partir da seletividade perturbada.
    seletividade_mc = np.clip(simulado["seletividade_produto_prevista_pct"].to_numpy(dtype=float) * (0.80 + 0.40 * simulado["score_seletividade_mc"].to_numpy(dtype=float)), 0, 100)
    # Recalcula rendimento/produtividade a partir de conversão e seletividade perturbadas.
    rendimento_mc = np.clip(conversao_mc * seletividade_mc / 100.0, 0, 100)
    # Recalcula o score da condição nominal perturbada.
    score_condicao_mc = 0.40 * conversao_mc / 100 + 0.30 * seletividade_mc / 100 + 0.30 * rendimento_mc / 100
    # Perturba o score médio da faixa de condições para representar incerteza operacional.
    score_faixa_mc = np.clip(simulado["score_faixa_condicao"].to_numpy(dtype=float) + rng.normal(0, 0.035, len(simulado)), 0, 1)
    # Recalcula a combinação catalisador-condição nominal.
    score_material_condicao_mc = 0.60 * simulado["score_final_material_mc"] + 0.40 * score_condicao_mc
    # Penaliza a combinação simulada quando a tendência a coque é alta em reforma.
    if reacao == "reforma":
        score_material_condicao_mc = np.clip(score_material_condicao_mc * (1.0 - 0.10 * simulado["penalidade_coque_mc"]), 0, 1)
    # Recalcula o score final propagando a incerteza até a etapa de ranking.
    simulado["score_final_mc"] = np.clip(0.80 * score_material_condicao_mc + 0.20 * score_faixa_mc, 0, 1)
    # Ordena a simulação pelo score recalculado.
    simulado = simulado.sort_values("score_final_mc", ascending=False)
    # Identifica as fórmulas que ficaram entre as cinco primeiras na simulação.
    top5_simulado = simulado.head(5)["formula"].unique()
    # Atualiza a contagem de permanência no top 5.
    for formula in top5_simulado:
        contagem_top5[formula] += 1
    # Guarda o melhor score simulado de cada fórmula nesta rodada.
    for formula, score in simulado.groupby("formula")["score_final_mc"].max().items():
        scores_mc_por_formula[formula].append(float(score))

# Organiza probabilidades e estatísticas Monte Carlo por fórmula.
monte_carlo_ranking_df = pd.DataFrame([
    {
        "formula": formula,
        "probabilidade_top5_mc": contagem / n_simulacoes_mc,
        "score_final_mc_media": float(np.mean(scores_mc_por_formula.get(formula, [np.nan]))),
        "score_final_mc_desvio": float(np.std(scores_mc_por_formula.get(formula, [np.nan]), ddof=1)) if len(scores_mc_por_formula.get(formula, [])) > 1 else 0.0,
    }
    for formula, contagem in contagem_top5.items()
])

# Comeca assumindo que scipy ainda nao foi ativado para estatistica.
scipy_disponivel = False

# Tenta importar scipy.stats para calcular intervalo de confianca da simulacao.
try:
    # Importa scipy.stats para usar a distribuicao beta.
    from scipy import stats
    # Marca scipy como disponivel quando a importacao funciona.
    scipy_disponivel = True
# Captura ausencia ou falha de importacao do scipy.
except Exception as erro_scipy:
    # Guarda a mensagem de erro para consulta posterior.
    erro_scipy = str(erro_scipy)
    # Mantem scipy como indisponivel e usa aproximacao normal.
    scipy_disponivel = False

# Cria lista para guardar intervalos de confianca da probabilidade Monte Carlo.
linhas_ic_mc = []

# Percorre cada formula e sua contagem de permanencia no top 5.
for formula, contagem in contagem_top5.items():
    # Calcula a probabilidade observada na simulacao.
    probabilidade = contagem / n_simulacoes_mc
    # Usa intervalo beta quando scipy esta disponivel.
    if scipy_disponivel:
        # Calcula intervalo de 95 por cento com suavizacao beta-binomial.
        limite_inferior, limite_superior = stats.beta.interval(0.95, contagem + 1, n_simulacoes_mc - contagem + 1)
    # Usa aproximacao normal quando scipy nao esta disponivel.
    else:
        # Calcula erro padrao binomial simples.
        erro_padrao = math.sqrt(max(probabilidade * (1 - probabilidade), 0) / n_simulacoes_mc)
        # Calcula limite inferior aproximado.
        limite_inferior = max(0.0, probabilidade - 1.96 * erro_padrao)
        # Calcula limite superior aproximado.
        limite_superior = min(1.0, probabilidade + 1.96 * erro_padrao)
    # Armazena intervalo e largura para a formula.
    linhas_ic_mc.append({
        "formula": formula,
        "probabilidade_top5_mc_ic95_inf": float(limite_inferior),
        "probabilidade_top5_mc_ic95_sup": float(limite_superior),
        "largura_ic95_top5_mc": float(limite_superior - limite_inferior),
    })

# Converte os intervalos Monte Carlo em tabela.
intervalos_mc_df = pd.DataFrame(linhas_ic_mc)

# Junta os intervalos de confianca a tabela Monte Carlo.
monte_carlo_ranking_df = monte_carlo_ranking_df.merge(intervalos_mc_df, on="formula", how="left")

# Incorpora a probabilidade Monte Carlo ao ranking final.
ranking_final_df = ranking_final_df.merge(monte_carlo_ranking_df, on="formula", how="left")

# Preenche probabilidade nula para candidatos fora da base Monte Carlo.
ranking_final_df["probabilidade_top5_mc"] = ranking_final_df["probabilidade_top5_mc"].fillna(0.0)

# Preenche limite inferior nulo para candidatos fora da base Monte Carlo.
ranking_final_df["probabilidade_top5_mc_ic95_inf"] = ranking_final_df["probabilidade_top5_mc_ic95_inf"].fillna(0.0)

# Preenche limite superior nulo para candidatos fora da base Monte Carlo.
ranking_final_df["probabilidade_top5_mc_ic95_sup"] = ranking_final_df["probabilidade_top5_mc_ic95_sup"].fillna(0.0)

# Preenche largura nula para candidatos fora da base Monte Carlo.
ranking_final_df["largura_ic95_top5_mc"] = ranking_final_df["largura_ic95_top5_mc"].fillna(0.0)

# Preenche média Monte Carlo com o score nominal quando a fórmula ficou fora da base simulada.
ranking_final_df["score_final_mc_media"] = ranking_final_df["score_final_mc_media"].fillna(ranking_final_df["score_final"])

# Preenche desvio Monte Carlo nulo para candidatos fora da base simulada.
ranking_final_df["score_final_mc_desvio"] = ranking_final_df["score_final_mc_desvio"].fillna(0.0)

# Define função para classificar confiabilidade.
def classificar_confiabilidade(row):
    # Alta confiabilidade exige estabilidade boa, baixa incerteza e bom DFT.
    if row["energy_above_hull_eV_atom"] <= perfil["limite_hull_principal"] and row["score_incerteza"] >= 0.65 and row["score_DFT"] >= 0.60 and row["probabilidade_top5_mc"] >= 0.30:
        return "alta"
    # Média confiabilidade aceita candidato metaestável com bom score geral.
    if row["energy_above_hull_eV_atom"] <= perfil["limite_hull_exploratorio"] and row["score_final"] >= 0.65:
        return "media"
    # Caso contrário, classifica como baixa.
    return "baixa"

# Aplica classificação de confiabilidade.
ranking_final_df["confiabilidade"] = ranking_final_df.apply(classificar_confiabilidade, axis=1)

# Seleciona a melhor condição por fórmula preservando a ordenação real por score final.
melhor_por_candidato_df = ranking_final_df.sort_values("score_final", ascending=False).drop_duplicates("formula", keep="first").reset_index(drop=True)

# Mantem os melhores candidatos refinados para classificacao top 10 com representação multimetálica.
melhor_por_candidato_df = selecionar_com_representacao_multimetal(melhor_por_candidato_df, N_CANDIDATOS_REFINADOS_FUNIL, "score_final", fracao_minima=0.40)

# Mantem a tabela de ranking final com os candidatos prioritarios finais e ao menos um multimetalico quando aplicavel.
ranking_final_df = selecionar_com_representacao_multimetal(melhor_por_candidato_df, N_CANDIDATOS_RANKING_FINAL, "score_final", fracao_minima=0.50)

# Seleciona top candidatos prioritários para síntese.
prioritarios_df = ranking_final_df.copy()

# Mostra quantos candidatos finais preservam dois ou mais metais ativos.
print("Prioritários finais com dois ou mais metais ativos:", int(prioritarios_df.get("candidato_multimetal_ativo", pd.Series(dtype=bool)).sum()))

# Exibe a tabela de síntese recomendada.
prioritarios_df[[
    "formula",
    "metais_ativos_presentes",
    "n_metais_ativos_presentes",
    "suporte_sugerido",
    "rota_sintese_sugerida",
    "regime",
    "temperatura_C",
    "pressao_bar",
    "razao_nome",
    "razao",
    "conversao_prevista_pct",
    "seletividade_produto_prevista_pct",
    "rendimento_ou_produtividade_prevista_pct",
    "score_cathub_incremental",
    "energia_cathub_media_eV",
    "n_evidencias_cathub_incremental",
    "adsorbatos_cathub_encontrados",
    "cathub_incremental_usado",
    "descritor_volcano",
    "energia_adsorcao_volcano_eV",
    "score_volcano",
    "score_final",
    "probabilidade_top5_mc",
    "confiabilidade",
]]
"""
    ),
    md(
        """
## Etapa 13 - Visualização científica dos resultados

Esta etapa aplica os princípios da aula de gráficos científicos com Matplotlib para transformar as tabelas finais em figuras interpretáveis. As imagens são salvas em PNG e PDF para uso no relatório ou apresentação.
"""
    ),
    code(
        """
# Importa sys para chamar o instalador usando o mesmo Python do notebook.
import sys

# Importa subprocess para instalar Matplotlib quando ele não estiver disponível localmente.
import subprocess

# Tenta importar Matplotlib para construir gráficos científicos.
try:
    # Importa o módulo de gráficos do Matplotlib.
    import matplotlib.pyplot as plt
# Captura ambiente local sem Matplotlib instalado.
except ModuleNotFoundError:
    # Instala Matplotlib no mesmo ambiente Python usado pelo notebook.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    # Importa Matplotlib novamente após a instalação.
    import matplotlib.pyplot as plt

# Define prefixo dos arquivos de saída com o nome da reação.
prefixo = f"disciplina_fluxo_{reacao}"

# Define a pasta em que as figuras serão salvas.
FIGURE_DIR = OUTPUT_DIR / f"{prefixo}_figuras"

# Cria a pasta de figuras caso ela ainda não exista.
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# Define um estilo visual limpo para todos os gráficos.
plt.style.use("seaborn-v0_8-whitegrid")

# Define um mapa de cores para representar a confiabilidade dos candidatos.
cores_confiabilidade = {"alta": "#2E7D32", "media": "#F9A825", "baixa": "#C62828"}

# Cria lista para registrar os arquivos de figura gerados.
figuras_geradas = []

# Define uma função auxiliar para salvar a figura em PNG e PDF.
def salvar_figura(nome_base):
    # Monta o caminho do arquivo PNG.
    caminho_png = FIGURE_DIR / f"{nome_base}.png"
    # Monta o caminho do arquivo PDF.
    caminho_pdf = FIGURE_DIR / f"{nome_base}.pdf"
    # Salva a figura em PNG com resolução adequada para apresentação.
    plt.savefig(caminho_png, dpi=300, bbox_inches="tight")
    # Salva a mesma figura em PDF para relatório.
    plt.savefig(caminho_pdf, bbox_inches="tight")
    # Registra os caminhos gerados em uma lista estruturada.
    figuras_geradas.append({"figura": nome_base, "arquivo_png": str(caminho_png), "arquivo_pdf": str(caminho_pdf)})

# Cria dados do funil da triagem.
funil_labels = ["Gerados", "Viáveis", "Refinados", "Prioritários"]

# Calcula os valores do funil da triagem.
funil_valores = [len(candidatos_df), len(viaveis_df), len(refinado_df), len(prioritarios_df)]

# Cria figura para o funil da triagem.
plt.figure(figsize=(8, 4.5))

# Desenha as barras do funil.
plt.bar(funil_labels, funil_valores, color=["#455A64", "#1976D2", "#7B1FA2", "#2E7D32"])

# Adiciona rótulo do eixo y.
plt.ylabel("Número de candidatos")

# Adiciona título explicativo.
plt.title(f"Funil da triagem virtual - {perfil['nome']}")

# Escreve o valor acima de cada barra.
for indice, valor in enumerate(funil_valores):
    # Posiciona o texto acima da barra correspondente.
    plt.text(indice, valor + max(funil_valores) * 0.02, str(valor), ha="center", va="bottom")

# Salva o gráfico do funil.
salvar_figura("01_funil_triagem")

# Exibe o gráfico no notebook.
plt.show()

# Seleciona os melhores candidatos para gráfico de ranking.
top_plot = melhor_por_candidato_df.head(10).copy()

# Cria figura para o ranking final.
plt.figure(figsize=(10, 5))

# Define cores das barras conforme a confiabilidade.
bar_colors = top_plot["confiabilidade"].map(cores_confiabilidade).fillna("#616161")

# Desenha barras horizontais para facilitar leitura das fórmulas.
plt.barh(top_plot["formula"], top_plot["score_final"], color=bar_colors)

# Inverte o eixo y para deixar o melhor candidato no topo.
plt.gca().invert_yaxis()

# Define rótulo do eixo x.
plt.xlabel("Score final")

# Define título do gráfico.
plt.title("Top candidatos por score final")

# Limita o eixo x para a escala de score.
plt.xlim(0, max(1.0, float(top_plot["score_final"].max()) * 1.10))

# Salva o gráfico do ranking.
salvar_figura("02_ranking_score_final")

# Exibe o gráfico no notebook.
plt.show()

# Cria figura para estabilidade versus score.
plt.figure(figsize=(7.5, 5.5))

# Define cores dos pontos conforme a confiabilidade.
scatter_colors = melhor_por_candidato_df["confiabilidade"].map(cores_confiabilidade).fillna("#616161")

# Desenha dispersão entre estabilidade termodinâmica e score final.
plt.scatter(
    melhor_por_candidato_df["energy_above_hull_eV_atom"],
    melhor_por_candidato_df["score_final"],
    c=scatter_colors,
    s=80,
    alpha=0.85,
    edgecolor="black",
    linewidth=0.4,
)

# Marca o limite principal de estabilidade.
plt.axvline(perfil["limite_hull_principal"], color="#2E7D32", linestyle="--", linewidth=1.5, label="limite principal")

# Marca o limite exploratório de estabilidade.
plt.axvline(perfil["limite_hull_exploratorio"], color="#C62828", linestyle=":", linewidth=1.5, label="limite exploratório")

# Define rótulo do eixo x.
plt.xlabel("Estabilidade termodinâmica (eV/átomo)")

# Define rótulo do eixo y.
plt.ylabel("Score final")

# Define título do gráfico.
plt.title("Estabilidade termodinâmica versus score final")

# Adiciona legenda dos limites.
plt.legend()

# Salva o gráfico de estabilidade versus score.
salvar_figura("03_estabilidade_vs_score")

# Exibe o gráfico no notebook.
plt.show()

# Seleciona candidatos com dados do volcano simplificado.
volcano_plot = melhor_por_candidato_df[
    melhor_por_candidato_df["energia_adsorcao_volcano_eV"].notna()
    & melhor_por_candidato_df["score_volcano"].notna()
].copy()

# Cria figura para o gráfico de vulcão.
plt.figure(figsize=(10.5, 6.4))

# Define eixo x teórico ao redor das energias observadas e do ótimo.
energia_otima_plot = float(volcano_cfg["energia_otima_eV"])

# Define largura do volcano usada para desenhar a curva.
largura_volcano_plot = float(volcano_cfg["largura_eV"])

# Calcula limite inferior do eixo x.
x_min = min(float(volcano_plot["energia_adsorcao_volcano_eV"].min()), energia_otima_plot) - 1.2 * largura_volcano_plot if len(volcano_plot) else energia_otima_plot - 1.2 * largura_volcano_plot

# Calcula limite superior do eixo x.
x_max = max(float(volcano_plot["energia_adsorcao_volcano_eV"].max()), energia_otima_plot) + 1.2 * largura_volcano_plot if len(volcano_plot) else energia_otima_plot + 1.2 * largura_volcano_plot

# Cria pontos da curva teórica.
x_volcano = np.linspace(x_min, x_max, 250)

# Calcula score volcano teórico pela distância ao ótimo.
y_volcano = np.exp(-np.abs(x_volcano - energia_otima_plot) / max(largura_volcano_plot, 0.05))

# Desenha a curva de vulcão.
plt.plot(x_volcano, y_volcano, color="#424242", linewidth=2.0, label="curva volcano")

# Marca o ponto ótimo do descritor.
plt.axvline(energia_otima_plot, color="#2E7D32", linestyle="--", linewidth=1.6, label="ótimo")

# Define cores por fonte do volcano.
cores_fonte_volcano = {
    "Catalysis-Hub": "#1565C0",
    "proxy_GNN_DFT_estabilidade": "#EF6C00",
    "proxy_neutro": "#757575",
}

# Define cores dos pontos conforme a fonte do volcano.
cores_pontos_volcano = volcano_plot["fonte_volcano"].map(cores_fonte_volcano).fillna("#6A1B9A") if len(volcano_plot) else []

# Desenha candidatos sobre a curva.
if len(volcano_plot):
    plt.scatter(
        volcano_plot["energia_adsorcao_volcano_eV"],
        volcano_plot["score_volcano"],
        c=cores_pontos_volcano,
        s=95,
        alpha=0.88,
        edgecolor="black",
        linewidth=0.5,
        zorder=3,
    )
    # Define deslocamentos alternados para evitar sobreposição dos rótulos.
    deslocamentos_rotulos = [
        (14, 14), (14, -18), (-54, 16), (-58, -20), (26, 32),
        (-72, 34), (38, -34), (-86, -36), (54, 50), (-100, 52),
    ]
    # Ordena os rótulos por energia e score para distribuir visualmente.
    volcano_rotulos = volcano_plot.sort_values(["energia_adsorcao_volcano_eV", "score_volcano"]).head(10).reset_index(drop=True)
    # Adiciona rótulos compactos às fórmulas com caixa e seta.
    for idx, row in volcano_rotulos.iterrows():
        # Seleciona deslocamento cíclico.
        deslocamento = deslocamentos_rotulos[idx % len(deslocamentos_rotulos)]
        # Anota a fórmula do candidato.
        plt.annotate(
            row["formula"],
            (row["energia_adsorcao_volcano_eV"], row["score_volcano"]),
            textcoords="offset points",
            xytext=deslocamento,
            ha="left" if deslocamento[0] >= 0 else "right",
            va="bottom" if deslocamento[1] >= 0 else "top",
            fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": "#9E9E9E", "alpha": 0.88},
            arrowprops={"arrowstyle": "-", "color": "#616161", "lw": 0.7, "shrinkA": 0, "shrinkB": 4},
            zorder=4,
        )

# Define rótulo do eixo x.
plt.xlabel(f"Energia de adsorção proxy de {volcano_cfg['descritor']} (eV)")

# Define rótulo do eixo y.
plt.ylabel("Score volcano")

# Define título do gráfico.
plt.title("Gráfico de Vulcão simplificado")

# Expande o eixo x para dar espaço aos rótulos laterais.
plt.xlim(x_min - 0.25 * largura_volcano_plot, x_max + 0.25 * largura_volcano_plot)

# Limita eixo y com margem para rótulos superiores.
plt.ylim(0, 1.18)

# Ajusta margens da figura para preservar rótulos anotados.
plt.tight_layout()

# Adiciona legenda.
plt.legend()

# Salva o gráfico de vulcão.
salvar_figura("04_volcano_plot")

# Exibe o gráfico no notebook.
plt.show()

# Seleciona candidatos com probabilidade Monte Carlo calculada.
mc_plot = melhor_por_candidato_df.sort_values("probabilidade_top5_mc", ascending=False).head(10).copy()

# Cria figura para incerteza Monte Carlo.
plt.figure(figsize=(10, 5))

# Desenha barras com a probabilidade de permanência no top 5.
plt.barh(mc_plot["formula"], mc_plot["probabilidade_top5_mc"], color="#1565C0")

# Inverte o eixo y para mostrar a maior probabilidade no topo.
plt.gca().invert_yaxis()

# Define rótulo do eixo x.
plt.xlabel("Probabilidade de ficar no top 5")

# Define limite do eixo x como probabilidade.
plt.xlim(0, 1)

# Define título do gráfico.
plt.title("Robustez do ranking por Monte Carlo")

# Salva o gráfico de Monte Carlo.
salvar_figura("05_monte_carlo_top5")

# Exibe o gráfico no notebook.
plt.show()

# Seleciona as formulas do Top 10 refinado para avaliar desempenho por faixa de condicao.
formulas_top10_condicoes = melhor_por_candidato_df["formula"].astype(str).head(N_CANDIDATOS_REFINADOS_FUNIL).tolist()

# Filtra a matriz completa de desempenho por condicao usando apenas o Top 10 refinado.
desempenho_top10_df = desempenho_faixa_df[desempenho_faixa_df["formula"].astype(str).isin(formulas_top10_condicoes)].copy()

# Usa toda a matriz de desempenho como fallback caso o filtro do Top 10 esteja vazio.
if desempenho_top10_df.empty:
    desempenho_top10_df = desempenho_faixa_df.copy()

# Cria tabela resumida de desempenho medio por condicao usando o Top 10.
condicao_plot = desempenho_top10_df.groupby(["regime", "temperatura_C"], as_index=False)[
    ["conversao_media_faixa_pct", "seletividade_media_faixa_pct", "rendimento_medio_faixa_pct"]
].mean()

# Ordena as condições por temperatura para melhorar leitura.
condicao_plot = condicao_plot.sort_values(["temperatura_C", "regime"])

# Cria figura para desempenho médio por condição.
plt.figure(figsize=(10, 5.5))

# Desenha linha de conversão média.
plt.plot(condicao_plot["regime"], condicao_plot["conversao_media_faixa_pct"], marker="o", label="Conversão média")

# Desenha linha de seletividade média.
plt.plot(condicao_plot["regime"], condicao_plot["seletividade_media_faixa_pct"], marker="s", label="Seletividade média")

# Desenha linha de rendimento/produtividade média.
plt.plot(condicao_plot["regime"], condicao_plot["rendimento_medio_faixa_pct"], marker="^", label="Rendimento/produtividade média")

# Rotaciona os rótulos do eixo x para evitar sobreposição.
plt.xticks(rotation=25, ha="right")

# Define rótulo do eixo y.
plt.ylabel("Valor médio previsto (%)")

# Define título do gráfico.
plt.title("Desempenho médio em faixa de condição - Top 10")

# Adiciona legenda.
plt.legend()

# Salva o gráfico de desempenho por condição.
salvar_figura("06_desempenho_faixa_condicoes")

# Exibe o gráfico no notebook.
plt.show()

# Resume a sensibilidade média por descritor.
sens_plot = sensibilidade_descritores_df.groupby("descritor", as_index=False)["sensibilidade_score"].mean()

# Ordena os descritores por impacto absoluto médio.
sens_plot = sens_plot.reindex(sens_plot["sensibilidade_score"].abs().sort_values(ascending=False).index)

# Cria figura para sensibilidade dos descritores.
plt.figure(figsize=(8.5, 4.8))

# Desenha barras de sensibilidade média.
plt.bar(sens_plot["descritor"], sens_plot["sensibilidade_score"], color="#6A1B9A")

# Rotaciona rótulos dos descritores.
plt.xticks(rotation=25, ha="right")

# Define rótulo do eixo y.
plt.ylabel("Sensibilidade média do score")

# Define título do gráfico.
plt.title("Sensibilidade média dos descritores")

# Salva o gráfico de sensibilidade.
salvar_figura("07_sensibilidade_descritores")

# Exibe o gráfico no notebook.
plt.show()

# Converte a lista de figuras em tabela.
figuras_geradas_df = pd.DataFrame(figuras_geradas)

# Exibe a tabela com os arquivos de figura gerados.
figuras_geradas_df
"""
    ),
    md(
        """
## Etapa 14 - Salvar resultados

As tabelas finais são salvas em CSV e Excel para uso no relatório ou apresentação da disciplina.
"""
    ),
    code(
        """
# Define prefixo dos arquivos de saída com o nome da reação.
prefixo = f"disciplina_fluxo_{reacao}"

# Define nomes em português para as colunas exportadas nos resultados.
nomes_colunas_pt = {
    "reacao": "reação",
    "formula": "fórmula",
    "tipo": "tipo de candidato",
    "suporte_sugerido": "suporte sugerido",
    "rota_sintese_sugerida": "rota de sintese sugerida",
    "pretratamento_sugerido": "pre-tratamento sugerido",
    "justificativa_suporte_sintese": "justificativa quimica do suporte e sintese",
    "observacao_sintese": "observacao de sintese",
    "energy_above_hull_eV_atom": "Estabilidade termodinâmica (eV/átomo)",
    "score_estabilidade": "score de estabilidade",
    "score_atividade": "score de atividade",
    "score_seletividade": "score de seletividade",
    "score_DFT": "score DFT/proxy DFT",
    "score_DFT_proxy": "score proxy DFT",
    "score_DFT_refinado": "score DFT refinado",
    "score_cathub_incremental": "score Catalysis-Hub incremental",
    "energia_cathub_media_eV": "energia média Catalysis-Hub (eV)",
    "n_evidencias_cathub_incremental": "número de evidências Catalysis-Hub",
    "adsorbatos_cathub_encontrados": "adsorbatos encontrados no Catalysis-Hub",
    "cathub_incremental_usado": "usou Catalysis-Hub incremental",
    "score_incerteza": "score de confiança",
    "incerteza": "incerteza estimada",
    "score_basicidade": "score de basicidade",
    "score_redox": "score redox",
    "score_resistencia_coque": "score de resistência a coque",
    "penalidade_tendencia_coque": "penalidade de tendência a coque",
    "taxa_desativacao_coque_proxy": "taxa proxy de desativação por coque",
    "score_atividade_corrigida_coque": "score de atividade corrigida por coque",
    "penalidade_coque_condicao": "penalidade de coque na condição",
    "taxa_desativacao_coque_condicao": "taxa de desativação por coque na condição",
    "score_matminer_composicional": "score composicional matminer",
    "score_pymatgen_quimico": "score químico pymatgen",
    "score_gnn_local": "score GNN local",
    "energia_gnn_eV_atom": "energia GNN local (eV/átomo)",
    "energia_formacao_gnn_eV_atom": "energia de formação GNN local (eV/átomo)",
    "modelo_gnn_local": "modelo GNN local",
    "gnn_local_usado": "usou GNN local",
    "estrutura_proxy_gnn": "estrutura proxy GNN",
    "fonte_estabilidade_triagem": "fonte da estabilidade na triagem",
    "observacao_gnn_local": "observação GNN local",
    "volume_proxy_gnn_A3": "volume proxy GNN (A³)",
    "n_sites_proxy_gnn": "número de sítios proxy GNN",
    "peso_boltzmann_estabilidade": "peso de Boltzmann da estabilidade",
    "score_DFT_boltzmann": "score DFT ajustado por Boltzmann",
    "descritor_volcano": "descritor volcano",
    "energia_adsorcao_volcano_eV": "energia de adsorção volcano (eV)",
    "fonte_volcano": "fonte do volcano",
    "distancia_otimo_volcano_eV": "distância ao ótimo volcano (eV)",
    "barreira_aparente_volcano_eV": "barreira aparente volcano (eV)",
    "taxa_relativa_volcano": "taxa relativa volcano",
    "score_volcano": "score volcano",
    "score_final_material": "score final do material",
    "temperatura_C": "temperatura (°C)",
    "pressao_bar": "pressão (bar)",
    "razao_reacional": "razão reacional",
    "GHSV_h_1": "GHSV (h⁻¹)",
    "regime": "regime operacional",
    "conversao_prevista_pct": "conversão prevista (%)",
    "seletividade_produto_prevista_pct": "seletividade prevista (%)",
    "rendimento_ou_produtividade_prevista_pct": "rendimento ou produtividade prevista (%)",
    "score_final": "score final",
    "conversao_media_faixa_pct": "conversão média na faixa (%)",
    "seletividade_media_faixa_pct": "seletividade média na faixa (%)",
    "rendimento_medio_faixa_pct": "rendimento médio na faixa (%)",
    "score_faixa_condicao": "score da faixa de condição",
    "probabilidade_top5_mc": "probabilidade Monte Carlo de ficar no top 5",
    "probabilidade_top5_mc_ic95_inf": "limite inferior IC95 da probabilidade top 5",
    "probabilidade_top5_mc_ic95_sup": "limite superior IC95 da probabilidade top 5",
    "largura_ic95_top5_mc": "largura do IC95 da probabilidade top 5",
    "score_final_mc_media": "média Monte Carlo do score final",
    "score_final_mc_desvio": "desvio Monte Carlo do score final",
    "confiabilidade": "confiabilidade",
    "descritor": "descritor",
    "sensibilidade_score": "sensibilidade do score",
    "grupo": "grupo",
    "metrica": "métrica",
    "valor": "valor",
    "interpretacao": "interpretação",
    "arquivo_png": "arquivo PNG",
    "arquivo_pdf": "arquivo PDF",
    "pymatgen_massa_molar": "massa molar calculada pelo pymatgen",
    "pymatgen_n_elementos": "número de elementos calculado pelo pymatgen",
    "pymatgen_eletronegatividade_media": "eletronegatividade média calculada pelo pymatgen",
    "pymatgen_eletronegatividade_desvio": "desvio de eletronegatividade calculado pelo pymatgen",
    "pymatgen_raio_atomico_medio": "raio atômico médio calculado pelo pymatgen",
}

# Define função auxiliar para traduzir apenas os nomes das colunas exportadas.
def traduzir_colunas(df):
    # Renomeia colunas conhecidas e mantém as demais sem alteração.
    return df.rename(columns={col: nomes_colunas_pt.get(col, col) for col in df.columns})

# Salva o ranking completo catalisador-condição.
traduzir_colunas(ranking_final_df).to_csv(OUTPUT_DIR / f"{prefixo}_ranking_condicoes.csv", index=False, encoding="utf-8-sig")

# Salva a melhor condição por candidato.
traduzir_colunas(melhor_por_candidato_df).to_csv(OUTPUT_DIR / f"{prefixo}_melhor_condicao_por_candidato.csv", index=False, encoding="utf-8-sig")

# Salva os candidatos prioritários para síntese.
traduzir_colunas(prioritarios_df).to_csv(OUTPUT_DIR / f"{prefixo}_prioritarios_sintese.csv", index=False, encoding="utf-8-sig")

# Salva a avaliação média em faixa de condição.
traduzir_colunas(desempenho_faixa_df).to_csv(OUTPUT_DIR / f"{prefixo}_desempenho_faixa_condicoes.csv", index=False, encoding="utf-8-sig")

# Salva a análise de sensibilidade dos descritores.
traduzir_colunas(sensibilidade_descritores_df).to_csv(OUTPUT_DIR / f"{prefixo}_sensibilidade_descritores.csv", index=False, encoding="utf-8-sig")

# Salva a incerteza Monte Carlo do ranking.
traduzir_colunas(monte_carlo_ranking_df).to_csv(OUTPUT_DIR / f"{prefixo}_monte_carlo_ranking.csv", index=False, encoding="utf-8-sig")

# Salva os descritores opcionais calculados pelo matminer.
traduzir_colunas(matminer_descritores_df).to_csv(OUTPUT_DIR / f"{prefixo}_descritores_matminer.csv", index=False, encoding="utf-8-sig")

# Salva os descritores diretos calculados pelo pymatgen.
traduzir_colunas(pymatgen_descritores_df).to_csv(OUTPUT_DIR / f"{prefixo}_descritores_pymatgen.csv", index=False, encoding="utf-8-sig")

# Salva as avaliações locais por GNN quando disponíveis.
traduzir_colunas(gnn_local_descritores_df).to_csv(OUTPUT_DIR / f"{prefixo}_proxy_gnn_local.csv", index=False, encoding="utf-8-sig")

# Salva o índice das figuras geradas.
traduzir_colunas(figuras_geradas_df).to_csv(OUTPUT_DIR / f"{prefixo}_figuras_geradas.csv", index=False, encoding="utf-8-sig")

# Salva um arquivo Excel com abas organizadas.
with pd.ExcelWriter(OUTPUT_DIR / f"{prefixo}_resultados.xlsx", engine="openpyxl") as writer:
    # Aba com candidatos prioritários.
    traduzir_colunas(prioritarios_df).to_excel(writer, sheet_name="Prioritarios_sintese", index=False)
    # Aba com melhor condição por candidato.
    traduzir_colunas(melhor_por_candidato_df).to_excel(writer, sheet_name="Melhor_por_candidato", index=False)
    # Aba com ranking completo.
    traduzir_colunas(ranking_final_df.head(150)).to_excel(writer, sheet_name="Top_condicoes", index=False)
    # Aba com desempenho médio em faixa de condição.
    traduzir_colunas(desempenho_faixa_df).to_excel(writer, sheet_name="Desempenho_faixa", index=False)
    # Aba com sensibilidade dos descritores.
    traduzir_colunas(sensibilidade_descritores_df).to_excel(writer, sheet_name="Sensibilidade", index=False)
    # Aba com incerteza Monte Carlo.
    traduzir_colunas(monte_carlo_ranking_df).to_excel(writer, sheet_name="Monte_Carlo", index=False)
    # Aba com o índice das figuras salvas.
    traduzir_colunas(figuras_geradas_df).to_excel(writer, sheet_name="Figuras", index=False)
    # Aba com descritores opcionais do matminer.
    traduzir_colunas(matminer_descritores_df.head(150)).to_excel(writer, sheet_name="Matminer", index=False)
    # Aba com descritores diretos do pymatgen.
    traduzir_colunas(pymatgen_descritores_df.head(150)).to_excel(writer, sheet_name="Pymatgen", index=False)
    # Aba com proxy DFT local por GNN.
    traduzir_colunas(gnn_local_descritores_df.head(150)).to_excel(writer, sheet_name="GNN_local", index=False)

# Define caminho do relatório HTML automático.
relatorio_html_path = OUTPUT_DIR / f"{prefixo}_relatorio.html"

# Define função para converter tabelas pequenas em HTML.
def tabela_html(df, linhas=10):
    # Retorna mensagem simples quando a tabela está vazia.
    if df is None or df.empty:
        return "<p class='muted'>Tabela indisponível para esta execução.</p>"
    # Traduz colunas, limita linhas e converte para HTML.
    return traduzir_colunas(df.head(linhas)).to_html(index=False, border=0, classes="tabela", escape=True)

# Define função para embutir figuras PNG no relatório.
def figura_html(caminho, titulo):
    # Converte caminho para Path.
    caminho = Path(caminho)
    # Retorna vazio quando a figura não existe.
    if not caminho.exists():
        return ""
    # Lê a figura em base64 para o relatório ficar autocontido.
    imagem64 = base64.b64encode(caminho.read_bytes()).decode("utf-8")
    # Retorna bloco HTML da figura.
    return f'''
    <figure>
        <img src="data:image/png;base64,{imagem64}" alt="{html.escape(titulo)}" />
        <figcaption>{html.escape(titulo)}</figcaption>
    </figure>
    '''

# Seleciona figuras principais para o relatório.
figuras_relatorio = []
if not figuras_geradas_df.empty and "arquivo_png" in figuras_geradas_df.columns:
    # Percorre figuras geradas durante a triagem.
    for _, fig_row in figuras_geradas_df.iterrows():
        # Usa o nome da figura como título de apresentação.
        titulo_figura = str(fig_row.get("nome", Path(str(fig_row["arquivo_png"])).stem)).replace("_", " ")
        # Monta HTML da figura.
        bloco_figura = figura_html(fig_row["arquivo_png"], titulo_figura)
        # Guarda apenas figuras disponíveis.
        if bloco_figura:
            figuras_relatorio.append(bloco_figura)

# Monta cartões de resumo do relatório.
cartoes_html = f'''
<div class="cards">
  <div><span>Rea&ccedil;&atilde;o</span><strong>{html.escape(str(reacao))}</strong></div>
  <div><span>Candidatos gerados</span><strong>{len(candidatos_df)}</strong></div>
  <div><span>Candidatos vi&aacute;veis</span><strong>{len(viaveis_df)}</strong></div>
  <div><span>Ranking final</span><strong>{len(melhor_por_candidato_df)}</strong></div>
</div>
'''

# Monta o documento HTML completo.
relatorio_html = f'''
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>Relat&oacute;rio da triagem virtual - {html.escape(str(reacao))}</title>
<style>
body {{
    margin: 0;
    padding: 32px;
    font-family: Arial, Helvetica, sans-serif;
    color: #123044;
    background: #f4fbff;
}}
main {{
    max-width: 1180px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #d8eef8;
    border-radius: 14px;
    padding: 28px;
}}
h1 {{
    margin: 0 0 6px 0;
    color: #168ac8;
    font-size: 32px;
}}
h2 {{
    margin-top: 30px;
    color: #0b4f7a;
    font-size: 21px;
}}
.subtitulo {{
    color: #526f82;
    margin-bottom: 22px;
}}
.cards {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 20px 0;
}}
.cards div {{
    border: 1px solid #d8eef8;
    border-radius: 10px;
    padding: 14px;
    background: #f6fbfe;
    text-align: center;
}}
.cards span {{
    display: block;
    font-size: 13px;
    color: #526f82;
    margin-bottom: 8px;
}}
.cards strong {{
    font-size: 24px;
    color: #0b4f7a;
}}
.tabela {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    margin-top: 10px;
}}
.tabela th {{
    background: #eaf7fc;
    color: #0b4f7a;
    text-align: left;
    padding: 9px;
    border-bottom: 1px solid #cfe7f2;
}}
.tabela td {{
    padding: 8px 9px;
    border-bottom: 1px solid #edf4f8;
    vertical-align: top;
}}
figure {{
    margin: 18px 0;
    padding: 12px;
    border: 1px solid #e1eef5;
    border-radius: 10px;
    background: #ffffff;
}}
figure img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}}
figcaption {{
    text-align: center;
    color: #526f82;
    margin-top: 8px;
    font-size: 13px;
}}
.muted {{
    color: #6b7f8d;
}}
</style>
</head>
<body>
<main>
<h1>Relat&oacute;rio da Triagem Virtual</h1>
<p class="subtitulo">Resumo autom&aacute;tico dos candidatos, condi&ccedil;&otilde;es operacionais, incerteza e recomenda&ccedil;&otilde;es de s&iacute;ntese.</p>
{cartoes_html}
<h2>Configura&ccedil;&atilde;o da execu&ccedil;&atilde;o</h2>
<p><strong>Metais ativos:</strong> {html.escape(', '.join(metais_usuario))}</p>
<p><strong>Promotor:</strong> {html.escape(str(promotor_usuario))}</p>
<p><strong>Perfil:</strong> {html.escape(str(perfil['nome']))}</p>
<h2>Top 2 candidatos recomendados</h2>
{tabela_html(prioritarios_df, linhas=2)}
<h2>Melhor condi&ccedil;&atilde;o por candidato</h2>
{tabela_html(melhor_por_candidato_df, linhas=10)}
<h2>Ranking catalisador-condi&ccedil;&atilde;o</h2>
{tabela_html(ranking_final_df, linhas=20)}
<h2>Incerteza Monte Carlo</h2>
{tabela_html(monte_carlo_ranking_df, linhas=20)}
<h2>Figuras principais</h2>
{''.join(figuras_relatorio) if figuras_relatorio else "<p class='muted'>Nenhuma figura foi encontrada para embutir no relat&oacute;rio.</p>"}
</main>
</body>
</html>
'''

# Salva o relatório HTML.
relatorio_html_path.write_text(relatorio_html, encoding="utf-8")

# Cria resumo da execução.
resumo = {
    "reacao": reacao,
    "perfil": perfil["nome"],
    "produto": perfil["produto"],
    "metais_ativos": metais_usuario,
    "promotor": promotor_usuario,
    "descritores": perfil["descritores"],
    "intermediarios_dft": perfil["intermediarios_dft"],
    "n_candidatos_gerados": int(len(candidatos_df)),
    "n_candidatos_viaveis": int(len(viaveis_df)),
    "n_candidatos_ranqueados": int(len(melhor_por_candidato_df)),
    "arquivo_excel": str(OUTPUT_DIR / f"{prefixo}_resultados.xlsx"),
    "arquivo_relatorio_html": str(relatorio_html_path),
    "arquivo_desempenho_faixa": str(OUTPUT_DIR / f"{prefixo}_desempenho_faixa_condicoes.csv"),
    "arquivo_sensibilidade": str(OUTPUT_DIR / f"{prefixo}_sensibilidade_descritores.csv"),
    "arquivo_monte_carlo": str(OUTPUT_DIR / f"{prefixo}_monte_carlo_ranking.csv"),
    "arquivo_descritores_matminer": str(OUTPUT_DIR / f"{prefixo}_descritores_matminer.csv"),
    "arquivo_descritores_pymatgen": str(OUTPUT_DIR / f"{prefixo}_descritores_pymatgen.csv"),
    "arquivo_proxy_gnn_local": str(OUTPUT_DIR / f"{prefixo}_proxy_gnn_local.csv"),
    "matminer_disponivel": bool(matminer_disponivel),
    "n_descritores_matminer": int(len(matminer_feature_cols)),
    "pymatgen_disponivel": bool(pymatgen_disponivel),
    "n_descritores_pymatgen": int(len(pymatgen_feature_cols)),
    "gnn_local_disponivel": bool(gnn_local_disponivel),
    "gnn_modelo_usado": gnn_modelo_usado,
    "n_candidatos_gnn_local": int(gnn_local_descritores_df["gnn_local_usado"].fillna(False).sum()) if "gnn_local_usado" in gnn_local_descritores_df else 0,
    "scipy_disponivel": bool(scipy_disponivel),
    "arquivo_figuras": str(OUTPUT_DIR / f"{prefixo}_figuras_geradas.csv"),
    "pasta_figuras": str(FIGURE_DIR),
}

# Salva o resumo em JSON.
(OUTPUT_DIR / f"{prefixo}_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

# Mostra o resumo final.
print(json.dumps(resumo, ensure_ascii=False, indent=2))
"""
    ),
]

nbf.write(nb, NOTEBOOK)
print(NOTEBOOK)





