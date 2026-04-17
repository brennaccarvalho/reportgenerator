# Análise Exploratória (EDA) — Quando usar este framework

## Qual pergunta ele responde

> "O que esses dados revelam que eu ainda não sei?"

Use EDA quando você está **começando do zero** com um dataset — sem hipótese formada, sem pergunta específica. É o framework de descoberta: ele vai atrás de padrões escondidos, relações entre variáveis e anomalias que nenhum relatório pré-formatado consegue capturar.

---

## Escolha este framework se…

| Situação | EDA é a escolha certa? |
|----------|------------------------|
| Está vendo esse dataset pela primeira vez | ✅ Sim |
| Quer descobrir quais variáveis se influenciam mutuamente | ✅ Sim |
| Precisa auditoria de qualidade (outliers, nulos, distribuições estranhas) | ✅ Sim |
| Quer entender o perfil de clientes antes de segmentar | ✅ Sim |
| Já sabe qual pergunta quer responder | ❌ Escolha o framework específico |
| Quer ver tendência no tempo | ❌ Use Temporal |
| Quer comparar etapas de um funil | ❌ Use Funil |

---

## O que o relatório vai mostrar

1. **Distribuições** — média, mediana e assimetria de cada métrica numérica (distribuição simétrica? concentrada? com cauda longa?)
2. **Correlações** — pares de variáveis com correlação acima de 0.5 (positiva ou negativa), com o scatter do par mais correlacionado
3. **Outliers** — quantidade de valores atípicos em cada coluna pelo método IQR, com os limites calculados

---

## Que dados você precisa ter

EDA é o framework mais flexível — funciona com praticamente qualquer estrutura. Mas quanto mais variáveis numéricas, mais rico o relatório.

- **Mínimo:** 1 coluna numérica (só mostra distribuição)
- **Ideal:** 3+ colunas numéricas + 1-2 categóricas
- Não precisa de coluna de data (mas pode ter)

### Onde a EDA brilha

O relatório fica mais útil quando há variáveis que podem se relacionar entre si. Exemplos:

- `renda` e `ticket_medio` — clientes mais ricos gastam mais?
- `frequencia_compra` e `churn` — clientes que compram mais ficam mais tempo?
- `nps` e `ltv` — promotores geram mais receita?

### Exemplo válido

```
segmento,faixa_etaria,renda_mensal,ticket_medio,frequencia_anual,ltv,nps,dias_ate_churn
Premium,36-45,18500,1240.50,18,22329,9,680
Standard,26-35,8200,420.00,8,3360,7,290
Basico,18-25,2800,85.00,3,255,5,95
Trial,26-35,12000,0.00,1,0,6,45
```

### Arquivo de exemplo pronto para usar

`data/exemplos/eda_clientes.csv` — 200 registros de clientes com renda, ticket, frequência, LTV, NPS e dias até churn. Contém correlações propositais (renda↔ticket) e outliers intencionais para demonstrar a detecção.

---

## O que evitar

- **Datasets muito pequenos** — com menos de 20 registros, a detecção de outliers e correlações não é estatisticamente confiável
- **Colunas com IDs ou códigos sequenciais** — retire-as antes de carregar (ex: `id_cliente`, `cod_pedido`) pois distorcem as correlações
- **Usar EDA quando você já tem uma pergunta clara** — se sabe que quer analisar um funil ou ver tendência, escolha o framework específico. EDA é para descoberta, não confirmação
