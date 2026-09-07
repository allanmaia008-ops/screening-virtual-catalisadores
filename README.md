# Screening Virtual

Aplicativo Streamlit para triagem virtual de catalisadores voltados a conversao de CO2.

## Como publicar no Streamlit Community Cloud

1. Crie um repositorio no GitHub contendo o conteudo desta pasta `publicacao_online`.
2. Acesse `https://share.streamlit.io` e selecione **Create app**.
3. Informe o repositorio, a branch e o arquivo principal:

```text
Triagem/app.py
```

4. Em **Advanced settings**, selecione **Python 3.12**.
5. Em **Advanced settings > Secrets**, adicione:

```toml
MP_API_KEY = "sua_chave_do_materials_project"
TRIAGEM_GITHUB_TOKEN = "token_github_com_permissao_contents_write"
```

6. Publique o app e compartilhe o link gerado.

## Dependencias cientificas obrigatorias

- `matminer==0.10.1` calcula os descritores composicionais Magpie da etapa 6.1.
- `pymatgen==2026.5.4` e `pymatgen-core==2026.5.18` interpretam formulas, composicoes e estruturas quimicas usadas nas etapas 6.2 e posteriores.
- Se `matminer` ou `pymatgen` nao importarem corretamente, a triagem deve parar com erro claro, porque esses descritores fazem parte obrigatoria do fluxo.

## Observacoes

- A pasta `outputs` contem resultados de demonstracao para o painel abrir ja com dados.
- Ao executar uma nova triagem, os novos arquivos sao gerados na pasta de saida definida na interface.
- Se `TRIAGEM_GITHUB_TOKEN` estiver configurado, o app baixa e atualiza os bancos incrementais em `outputs/ranking_multicriterio_v2_incerteza_explicabilidade.csv`, `outputs/consultas_bases_externas.csv`, `outputs/catalysis_hub_incremental.csv` e `outputs/proxy_gnn_local.csv`.
- O token GitHub deve ter permissao de leitura e escrita em **Contents** no repositorio do app.
# Expansão planejada: Fischer–Tropsch

O núcleo `Triagem/asf.py` calcula a distribuição ideal a partir de alpha informado,
com bases molar, de carbono e de massa de parafinas e cauda infinita explícita.
Exemplo local: `python Triagem/demo_asf.py --alpha 0.85 --output outputs/asf_demo`.
O perfil FT para aviação está detalhado em `Triagem/FT_SAF_PERFIL.md`.
O núcleo não estima alpha nem conversão a partir do catalisador.

O primeiro escopo científico para a expansão foi definido em
`Triagem/fischer_tropsch_scope.py`. O alvo inicial é Fischer–Tropsch de baixa
temperatura para hidrocarbonetos `C5+`, com janela inicial de 200–250 °C,
10–30 bar e razão H₂/CO de 1,5–2,2. Co e Fe serão tratados como famílias
catalíticas distintas, pois exigem representações diferentes da fase ativa.

O perfil LTFT está disponível no seletor e no notebook
`Triagem/notebook_fischer_tropsch_ltft.ipynb`, para Co, Fe e Co-Fe exploratório.
O módulo `ltft.py` calcula alpha por priors declarados de família, suporte,
promotor e condições, ou aceita alpha informado. Isso não é uma regressão
calibrada. Magpie/pymatgen são obrigatórios e registrados para auditoria;
o score não afirma uma contribuição aprendida desses descritores.

A triagem seleciona até 1000 formulações únicas, 100 selecionadas, 10 refinadas
e 2 prioritárias; a grade monometálica sem promotor contém 105 formulações.
As cargas variam de 5 a 25% de metais ativos e de 1 a 5% de promotor, em massa,
como grade de estudo, não como faixa experimental validada. As misturas de
metais têm passo atômico de 1%. Carga, preço e precursor não modificam o score
nesta versão. Empates têm desempate determinístico pelo identificador.

Exporta CSV, Excel, HTML e configuração JSON; conversão, WGS, produtividade,
coque e oxidação continuam não quantificados. A fase ativa é uma hipótese.
Referência para dependência qualitativa do crescimento com condições:
https://pubs.acs.org/doi/10.1021/acscatal.7b02758 . Os coeficientes numéricos
do módulo são escolhas heurísticas do projeto, não valores extraídos do artigo.
