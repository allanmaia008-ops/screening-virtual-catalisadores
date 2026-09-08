# LTFT: perfis e produtos

Versao: ltft-heuristic-2.

Os perfis de Co, Fe e Co-Fe apresentam separadamente as hipoteses de fase,
ativacao e participacao da WGS. Co-Fe continua exploratorio, sem comprovacao
de liga ou sinergia. A extensao da WGS permanece nula no sentido de ausente
(None), nunca zero numerico. Conversao e produtividade nao sao calculadas.
Os pesos e os priors numericos anteriores foram preservados, nao recalibrados.

A distribuicao ASF usa cinco faixas exclusivas: CH4, C2-C4, C5-C11,
C12-C20 e C21+. A soma e 100% do carbono nos hidrocarbonetos do modelo,
incluindo a cauda infinita. C5+ e um subtotal, nao uma sexta faixa exclusiva.
Este fechamento nao e um balanco global do reator: CO, CO2, oxigenados
e coque nao estao incluidos. As faixas nao qualificam combustivel SAF.

Os resultados aparecem na interface, CSV, Excel, HTML e no notebook
independente. A tabela grupos_produtos conserva o identificador do candidato.
O JSON registra os perfis e a base de interpretacao.

Contexto bibliografico, nao fonte de calibracao dos coeficientes:
- https://doi.org/10.1016/j.cattod.2015.11.005
- https://www.sciencedirect.com/science/article/pii/S0021951718302550

Verificacao: testes de Co, Fe e mistura; fechamento em alpha de zero a
0.999999; subtotal C5+; exportacao de 50 linhas para os dez candidatos;
execucao com descritores reais e teste da interface Streamlit.
