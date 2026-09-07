# Perfil Fischer-Tropsch direcionado a combustivel de aviacao

## Estado e objetivo

Este e um perfil de aplicacao da rota FT, identificado como `fischer_tropsch_saf`.
Nao e uma terceira reacao elementar. O nucleo ASF e executavel; a triagem de
catalisadores FT e a conversao posterior ainda exigem modelos proprios.
Nenhuma fracao calculada pelo ASF equivale a rendimento de SAF qualificado.

## Etapas da rota

1. Alimentacao de gas de sintese CO/H2: registrar origem, composicao, diluentes,
   impurezas, vazao e razao H2/CO. A sustentabilidade depende tambem dessa origem.
2. Sintese FT: usar inicialmente o escopo LTFT, 200-250 graus C e 10-30 bar,
   como janela de estudo proposta. Separar catalisadores de Co metalico e Fe
   carburizado. Ru como metal ativo exige uma familia propria; nao assumir Co0.
3. Separacao: registrar leves, corte de interesse e material pesado.
4. Hidrocraqueamento e hidroisomerizacao: avaliar funcao metalica de hidrogenacao,
   acidez e porosidade da funcao de craqueamento/isomerizacao, seletividade para
   ramificacao, formacao de gases, estabilidade e demanda de H2.
5. Fracionamento e avaliacao de propriedades do produto: curva de destilacao,
   congelamento, ponto de fulgor, densidade, viscosidade, composicao e impurezas.
   Numero de carbonos isolado nao determina essas propriedades.

## Saidas calculaveis agora

Com alpha informado, a distribuicao ideal molar e:

    y_n = (1-alpha)*alpha^(n-1), 0 <= alpha < 1

A fracao de carbono nos hidrocarbonetos e:

    c_n = n*(1-alpha)^2*alpha^(n-1)

O somatorio e sobre n=1 ate infinito. Para parafinas, a fracao massica exata
pondera y_n pela massa molar de CnH(2n+2), incluindo os hidrogenios terminais.
Essas distribuicoes sao condicionais aos hidrocarbonetos formados; nao incluem
CO nao convertido, CO2, agua ou oxigenados. Fe pode ter contribuicao importante
de WGS, que exigira balanco separado.

O corte C8-C16 e uma convencao inicial configuravel de triagem, nao uma
especificacao de combustivel. Seus grupos exclusivos sao C1-C7, C8-C16 e C17+.
C17+ significa alimentacao pesada potencial, nao necessariamente cera fisica:
estado fisico depende da estrutura molecular e da temperatura.

Nao somar C5+ aos grupos exclusivos C1, C2-C4, C5-C11 e C12+; C5+ e subtotal.
O modelo ideal pode apresentar desvios para metano e olefinas; alpha ainda
nao e estimado a partir de metal, promotor, temperatura ou pressao.

## Saidas futuras e dados necessarios

- Conversao de CO: modelo cinetico, alimentacao e tempo de contato definidos.
- Rendimento global de carbono no corte: conversao de CO, seletividade de
  carbono para hidrocarbonetos e distribuicao ASF compativeis entre si.
- Rendimento apos processamento: matriz de transferencia de carbono entre
  cortes, fracao convertida dos pesados, perdas para gases e reciclo.
- Demanda de H2: balancos estequiometricos de hidrogenacao/craqueamento;
  a fracao pesada sozinha nao determina esse consumo.
- Ramificacao e propriedades de combustivel: modelos independentes da ASF.
- Sustentabilidade e qualificacao: avaliacoes separadas; nao inferir de C8-C16.

## Priorizacao futura

Comparar duas alternativas: maximizar o corte direto ou produzir pesados para
processamento posterior. Maximizar alpha indefinidamente reduz o corte direto
e aumenta os pesados. Evitar premiar simultaneamente C5+, C8-C16 e C17+ como
se fossem beneficios independentes. Antes de fixar pesos, apresentar objetivos
separados: recuperacao de carbono no corte, gases, H2, estabilidade e severidade.
Nao definir uma temperatura de hidrotratamento universal neste perfil.

## Fontes e alcance

- van der Laan e Beenackers, Kinetic modelling of Fischer-Tropsch product
  distributions: https://www.sciencedirect.com/science/article/pii/S0926860X99001660
- The product distribution in Fischer-Tropsch synthesis: An extension of the
  ASF model to describe common deviations:
  https://www.sciencedirect.com/science/article/abs/pii/S0009250915004893
- DOE, Sustainable Aviation Fuel: Review of Technical Pathways (2020):
  https://www.energy.gov/sites/default/files/2020/09/f78/beto-sust-aviation-fuel-sep-2020.pdf

As fontes sustentam a arquitetura ASF e a necessidade de processamento da rota;
o corte C8-C16 e a janela inicial sao decisoes de escopo do projeto.
