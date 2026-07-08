# Screening Virtual

Aplicativo Streamlit para triagem virtual de catalisadores voltados à conversão de CO2.

## Como publicar no Streamlit Community Cloud

1. Crie um repositório no GitHub contendo o conteúdo desta pasta `publicacao_online`.
2. Acesse https://share.streamlit.io e selecione **Create app**.
3. Informe o repositório, a branch e o arquivo principal:

```text
Triagem/app.py
```

4. Em **Advanced settings > Secrets**, adicione:

```toml
MP_API_KEY = "sua_chave_do_materials_project"
```

5. Publique o app e compartilhe o link gerado com o professor.

## Observações

- A chave do Materials Project não fica salva no código.
- A pasta `outputs` contém resultados de demonstração para o painel abrir já com dados.
- Ao executar uma nova triagem, os novos arquivos são gerados na pasta de saída definida na interface.
