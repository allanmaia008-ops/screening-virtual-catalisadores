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
