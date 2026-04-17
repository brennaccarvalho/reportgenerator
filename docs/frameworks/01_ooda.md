# OODA Loop — Quando usar este framework

## Qual pergunta ele responde

> "O que está acontecendo no meu negócio e onde devo focar?"

Use o OODA quando você precisa de um **diagnóstico geral rápido** — sem uma hipótese específica ainda. É o framework de partida quando você tem um novo dataset e quer entender o panorama antes de ir fundo.

---

## Escolha este framework se…

| Situação | OODA é a escolha certa? |
|----------|------------------------|
| Precisa de um relatório executivo mensal | ✅ Sim |
| Quer saber quais canais / produtos / regiões lideram | ✅ Sim |
| Precisa de um diagnóstico rápido para reunião de board | ✅ Sim |
| Quer entender se duas métricas estão relacionadas | ✅ Sim |
| Precisa analisar uma série histórica com datas | ❌ Use Temporal |
| Quer mapear etapas de um funil de marketing | ❌ Use Funil |
| Quer medir eficiência operacional por equipe/loja | ❌ Use Performance |

---

## O que o relatório vai mostrar

1. **Panorama geral** — distribuição total e por categoria, com interpretação automática
2. **Contexto comparativo** — ranking das categorias, quem lidera, quem está abaixo
3. **Ponto de decisão** — relação entre duas métricas (ex: custo e receita se movem juntos?)
4. **Recomendações acionáveis** — top 3 categorias para priorizar e a mais fraca para investigar

---

## Que dados você precisa ter

Seu arquivo precisa ter:

- **Pelo menos 1 coluna de texto** (categoria) — ex: canal, produto, região, equipe
- **Pelo menos 1 coluna numérica** (métrica) — ex: receita, vendas, quantidade
- **Recomendado: 2 colunas numéricas** para ativar a análise de correlação

Não precisa de coluna de data.

### Exemplo mínimo válido

```
produto,receita
Produto A,45200
Produto B,28700
Produto C,61400
```

### Exemplo rico (recomendado)

```
canal,produto,regiao,receita,custo,margem
Organico,Produto A,Sudeste,12450,5632,6818
Pago,Produto C,Sul,8900,4100,4800
Email,Produto B,Nordeste,6200,2900,3300
```

### Arquivo de exemplo pronto para usar

`data/exemplos/ooda_estrategia_comercial.csv` — 120 registros de vendas por canal, produto e região com receita, custo e margem.

---

## O que evitar

- **Colunas com IDs numéricos** (1, 2, 3…) — serão interpretadas como métricas
- **Poucas linhas** — abaixo de 5 registros o relatório não gera análise útil
- **Datas no arquivo** — se tiver data e quiser análise temporal, escolha o framework Temporal
