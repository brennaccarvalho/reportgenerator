# Media Mix Modeling (Meridian) — Quando usar este framework

## Qual pergunta ele responde

> "Cada real que invisto em cada canal de marketing realmente traz retorno? E como redistribuir o budget para vender mais sem gastar mais?"

Use o Meridian quando você quer ir além da atribuição de último clique e entender o **impacto causal real** de cada canal de mídia nas suas vendas — incluindo canais offline como TV e rádio, que não aparecem no Google Analytics.

---

## Escolha este framework se…

| Situação | Meridian é a escolha certa? |
|----------|----------------------------|
| Tem budget mensal de mídia acima de R$ 30 mil | ✅ Sim |
| Investe em múltiplos canais (TV, digital, rádio, OOH) | ✅ Sim |
| Precisa justificar cortes ou aumentos de budget com dados | ✅ Sim |
| Quer saber o ROI real de cada canal, não só último clique | ✅ Sim |
| Quer otimizar a distribuição de verba entre canais | ✅ Sim |
| Seus dados têm menos de 1 ano de histórico semanal | ❌ Resultados não confiáveis |
| Investe em apenas 1 canal de mídia | ❌ MMM requer pelo menos 2 canais para comparação |
| Não tem registro histórico de investimento por canal | ❌ Framework não funciona sem dados de spend |

---

## O que o relatório vai mostrar

1. **ROI por canal** — quanto cada canal retorna por real investido, com intervalo de credibilidade de 90%
2. **Contribuição para as vendas** — percentual das vendas atribuído a cada canal + baseline (o que venderia sem mídia alguma)
3. **Diagnóstico de convergência** — R-hat por parâmetro, indicando se o modelo é confiável
4. **Otimização de budget** — dada uma verba total, qual a distribuição ótima entre canais para maximizar o KPI
5. **Relatório HTML completo** — exportável e publicável

---

## Que dados você precisa ter

Este framework tem os **requisitos mais específicos** de todos. Leia com atenção.

### Obrigatório

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Data | Texto/Data | Granularidade **semanal** recomendada. Formato `YYYY-MM-DD` |
| KPI | Numérica positiva | O resultado que você quer modelar: vendas, receita, conversões |
| Spend por canal (1+) | Numérica não-negativa | Investimento em R$ por canal de mídia. Mínimo 2 canais. |

### Opcional (melhora o modelo)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Impressões por canal | Numérica | Alcance, cliques, visualizações por canal |
| Variáveis de controle | Numérica | Fatores externos: temperatura, feriados, promoções |

### Regras de volume de dados

| Critério | Mínimo | Ideal |
|---|---|---|
| Semanas de histórico | 52 (1 ano) | 104+ (2 anos) |
| Canais de mídia | 2 | 4+ |
| Sem nulos no KPI e spend | Obrigatório | — |

### Exemplo válido

```
data,vendas,gasto_tv,gasto_digital,gasto_radio,gasto_ooh,impressoes_tv,cliques_digital,temperatura
2021-01-04,312450,45000,28000,12000,18000,1350000,1680,24.5
2021-01-11,298700,42000,31000,11500,16000,1260000,1860,25.1
2021-01-18,334200,48000,27500,13000,19500,1440000,1650,23.8
...
```

### Arquivo de exemplo pronto para usar

`data/exemplos/meridian_mmm_semanal.csv` — 156 semanas (3 anos) com vendas, investimento em TV, digital, rádio e OOH, impressões e cliques. O dataset tem ROI verdadeiro embutido: digital tem ROI 2.4, TV 1.8, OOH 1.1 e rádio 0.9 — o modelo deve recuperar esses valores.

---

## Requisito técnico importante

O Meridian usa TensorFlow internamente e **o treinamento pode demorar de 10 a 60 minutos**, dependendo do hardware.

- **Com GPU (NVIDIA + CUDA):** 10–20 minutos
- **Com CPU apenas:** 30–90 minutos (ou mais para bases grandes)

Se ainda não instalou as dependências:

```bash
pip install google-meridian[schema] tensorflow tensorflow-probability
```

---

## O que evitar

- **Dados diários** — o MMM funciona com granularidade semanal. Dados diários geram ruído excessivo no modelo
- **KPI com valores negativos ou zeros dominantes** — o modelo assume KPI positivo
- **Menos de 52 semanas** — abaixo disso, o modelo não tem histórico suficiente para separar o efeito de sazonalidade do efeito da mídia
- **Colunas de spend com nulos** — preencha com 0 nas semanas sem investimento naquele canal, nunca com NaN
