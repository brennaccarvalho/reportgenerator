# Comparação Temporal — Quando usar este framework

## Qual pergunta ele responde

> "Estou crescendo? Qual é o meu padrão ao longo do tempo e o que é sazonalidade?"

Use Temporal quando seus dados têm **uma dimensão de tempo** e você quer entender a evolução — tendência de crescimento, variação mês a mês e padrões que se repetem todo ano.

---

## Escolha este framework se…

| Situação | Temporal é a escolha certa? |
|----------|----------------------------|
| Quer ver se receita/pedidos estão crescendo | ✅ Sim |
| Quer identificar os meses mais fortes e mais fracos do ano | ✅ Sim |
| Quer calcular crescimento % mês a mês ou semana a semana | ✅ Sim |
| Quer saber se uma queda recente é sazonalidade ou tendência real | ✅ Sim |
| Seus dados não têm coluna de data | ❌ Framework não funciona sem data |
| Quer comparar performance entre equipes ou produtos | ❌ Use Performance ou OODA |
| Quer mapear etapas de conversão | ❌ Use Funil |

---

## O que o relatório vai mostrar

1. **Tendência** — evolução da métrica do primeiro ao último período, com variação total em %
2. **Crescimento mês a mês** — qual período teve o maior crescimento e qual o maior recuo
3. **Sazonalidade** — média por mês do ano para identificar padrões cíclicos (precisa de pelo menos 12 meses de dados)

---

## Que dados você precisa ter

Este é o único framework com um **requisito obrigatório**: uma coluna de data.

- **Coluna de data** — em qualquer formato reconhecível: `YYYY-MM-DD`, `DD/MM/YYYY`, `2024-01`, etc. O sistema converte automaticamente e agrupa por mês.
- **Pelo menos 1 coluna numérica** — a métrica que vai ser analisada no tempo
- Não precisa de coluna categórica (mas pode ter)

### Atenção: granularidade dos dados

O framework **agrupa automaticamente por mês**, independente da granularidade original:

| Granularidade do CSV | O que acontece |
|---|---|
| Dados diários (1 linha por dia) | Agrupados em meses — funciona perfeitamente |
| Dados semanais (1 linha por semana) | Agrupados em meses — funciona |
| Dados mensais (1 linha por mês) | Já no formato correto — ideal |
| Dados anuais (1 linha por ano) | Gera só 1 ponto por período — análise limitada |

Para análise de sazonalidade, o mínimo é **12 meses de histórico**. Para tendência confiável, recomenda-se **24 meses ou mais**.

### Exemplo válido (dados diários)

```
data,receita,pedidos,custo,ticket_medio
2022-01-01,9240.50,42,3820.00,220.01
2022-01-02,7810.20,35,3180.00,223.15
2022-01-03,11200.00,51,4650.00,219.61
...
2024-12-31,14320.00,63,5840.00,227.30
```

### Arquivo de exemplo pronto para usar

`data/exemplos/temporal_receita_diaria.csv` — 1096 dias (3 anos completos: 2022, 2023 e 2024) com receita, pedidos, custo e ticket médio. Tem tendência de crescimento embutida e sazonalidade com pico no final do ano.

---

## O que evitar

- **Menos de 2 meses de dados** — o framework não consegue calcular crescimento com apenas 1 período
- **Datas em formato numérico** (ex: `20240101` como inteiro) — converta para string antes de carregar
- **Misturar granularidades** — não misture linhas mensais com linhas diárias no mesmo arquivo
- **Usar Temporal para comparar categorias** — se quiser saber qual produto cresceu mais, combine com OODA após ver a tendência geral
