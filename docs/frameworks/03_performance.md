# Diagnóstico de Performance — Quando usar este framework

## Qual pergunta ele responde

> "Minha operação está saudável? Quem performa melhor e por que?"

Use Performance quando você quer **comparar unidades** (equipes, lojas, filiais, produtos) em três dimensões: quanto produzem, quão eficientes são, e quão consistentes são os resultados. É o framework certo quando a pergunta central é eficiência, não tendência.

---

## Escolha este framework se…

| Situação | Performance é a escolha certa? |
|----------|-------------------------------|
| Quer comparar equipes por volume e eficiência | ✅ Sim |
| Tem dados de custo e resultado por unidade | ✅ Sim |
| Quer identificar qual loja/filial tem melhor custo-benefício | ✅ Sim |
| Quer medir consistência dos resultados (quem é previsível?) | ✅ Sim |
| Quer ver evolução ao longo do tempo | ❌ Use Temporal |
| Quer mapear etapas de conversão | ❌ Use Funil |
| Quer um diagnóstico geral sem foco em eficiência | ❌ Use OODA |

---

## O que o relatório vai mostrar

1. **Volume** — quanta produção cada unidade entregou (quem mais faz)
2. **Eficiência** — relação entre insumo e resultado por unidade (quem faz mais com menos)
3. **Qualidade** — consistência dos resultados (coeficiente de variação — quem é previsível vs. volátil)

---

## Que dados você precisa ter

Seu arquivo precisa ter:

- **1 coluna de texto** — a unidade de comparação (equipe, loja, produto, processo)
- **1ª coluna numérica: produção** — o que foi entregue (atendimentos, pedidos, unidades, visitas)
- **2ª coluna numérica: custo ou insumo** — o que foi consumido (custo operacional, horas, investimento)

A eficiência é calculada dividindo a 2ª pela 1ª coluna numérica. Quanto maior, melhor.

### Exemplo válido

```
equipe,mes,atendimentos,custo_operacional,receita_gerada,satisfacao,sla_pct
Alpha,Jan,312,89456,156800,4.2,94.5
Beta,Jan,198,72340,98400,3.8,87.2
Gamma,Fev,445,98120,223400,4.6,97.8
Delta,Mar,156,61200,74200,3.5,82.1
Epsilon,Jan,389,84500,194500,4.4,95.3
```

Aqui, a eficiência calculada será `receita_gerada / atendimentos` — Gamma tem o maior volume, mas Epsilon pode ter a melhor eficiência dependendo da proporção.

### Arquivo de exemplo pronto para usar

`data/exemplos/performance_operacional.csv` — 100 registros de 5 equipes com atendimentos, custo operacional, receita gerada, satisfação e SLA.

---

## O que evitar

- **Misturar unidades incomparáveis** — comparar uma loja grande com uma pequena sem normalizar pode distorcer a análise de eficiência
- **Colocar custo antes de produção** — a 1ª coluna numérica é sempre interpretada como o output (produção). Se inverter, a eficiência será calculada ao contrário
- **Dados com muitos nulos** — se uma equipe não tem registros em certos meses, o CV de qualidade será distorcido
