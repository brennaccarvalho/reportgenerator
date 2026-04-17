# Funil de Conversão — Quando usar este framework

## Qual pergunta ele responde

> "Onde estou perdendo clientes? Em qual etapa meu funil é mais ineficiente?"

Use o Funil quando seus dados representam **etapas sequenciais de uma jornada** — onde cada coluna é um passo que reduz o volume em relação ao anterior. O relatório calcula automaticamente as taxas de conversão entre etapas e identifica os gargalos.

---

## Escolha este framework se…

| Situação | Funil é a escolha certa? |
|----------|--------------------------|
| Quer saber em qual canal de marketing a conversão é melhor | ✅ Sim |
| Tem dados de visitas, leads, oportunidades e clientes | ✅ Sim |
| Quer comparar eficiência entre fontes de aquisição | ✅ Sim |
| Tem pipeline de vendas com etapas (proposta → negociação → fechamento) | ✅ Sim |
| Quer análise geral sem etapas definidas | ❌ Use OODA |
| Quer ver evolução ao longo do tempo | ❌ Use Temporal |
| Quer comparar performance de equipes internas | ❌ Use Performance |

---

## O que o relatório vai mostrar

1. **Topo do funil** — volume total de entrada por categoria (qual canal traz mais)
2. **Meio do funil** — taxa de conversão entre a primeira e segunda etapa com diagnóstico automático (abaixo de 30% = perda significativa)
3. **Fundo do funil** — taxa de conversão global do início ao fim
4. **Gargalos** — as 3 categorias com menor volume, sinalizadas como oportunidade de melhoria

---

## Que dados você precisa ter

Seu arquivo precisa ter:

- **Colunas numéricas em ordem decrescente de volume** — a primeira coluna deve ter os maiores valores (topo) e a última os menores (fundo). O framework lê a ordem das colunas como sequência do funil.
- **Pelo menos 2 colunas numéricas** para ativar a análise de meio e fundo
- **1 coluna de texto** (recomendado) para agrupar por canal, fonte ou segmento

### Regra crítica: a ordem das colunas define as etapas do funil

```
canal | visitas (topo) | leads (meio) | clientes (fundo) | receita (resultado)
```

Se você inverter a ordem — colocar `clientes` antes de `visitas` — o relatório vai calcular taxas erradas.

### Exemplo válido

```
canal,visitas,leads,oportunidades,clientes,receita
Google Ads,32450,1820,610,87,348000
Meta Ads,18700,980,290,52,187200
LinkedIn,8200,640,310,95,428000
Organico,25300,2100,840,198,712800
Email,12400,1560,890,312,936000
```

### Arquivo de exemplo pronto para usar

`data/exemplos/funil_marketing_vendas.csv` — 80 registros por canal com visitas, leads, oportunidades, clientes e receita. Mostra claramente que indicação tem a melhor taxa de conversão apesar do menor volume.

---

## O que evitar

- **Colunas fora de ordem** — não coloque receita antes de visitas
- **Etapas que não são sequenciais** — o framework assume que coluna 1 → coluna 2 é sempre uma redução de volume
- **Uma única coluna numérica** — sem pelo menos 2 colunas numéricas, só o topo é gerado
