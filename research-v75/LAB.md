# AdipoLab v100

Laboratório metodológico de dados sintéticos, sem dados clínicos ou pessoais. As dez etapas são tópicos de investigação, não protocolos de intervenção. 

- lab.mjs: gerador determinístico e testes de concordância, cobertura e confundimento.
- synthetic-results.json: snapshot reproduzível; 2.000 repetições de Monte Carlo, 10.000 observações sintéticas do cenário de confundimento.
- cycles.json: hipóteses, critérios de qualidade, lacunas e manifesto de fontes públicas sem importação.
- lab.html: painel estático de resultados e critérios.

Executar: node --test research-v75/*.test.mjs. O CI roda no push/PR. O snapshot não corresponde a eficácia clínica, nem pode servir de prescrição ou previsão. Intervalos de concordância são descritivos, não intervalos de confiança para o viés. Cobertura testada assume normalidade e variância conhecida. Não há validação externa, revisão integral das fontes ou ensaio biológico.
