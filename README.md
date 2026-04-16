# Report Generator

Transforme planilhas brutas em relatórios analíticos estruturados com visualizações interativas e insights automáticos — sem nenhum conhecimento técnico necessário.

---

## O que é

O **Report Generator** é uma aplicação Streamlit que permite a qualquer pessoa:

1. Fazer upload de `.csv` ou `.xlsx`, ou conectar um Google Sheets
2. Processar e sanear os dados automaticamente
3. Escolher um framework analítico estratégico
4. Visualizar gráficos interativos com interpretação analítica
5. Exportar o relatório em PDF, HTML ou CSV
6. Publicar relatórios para consulta posterior

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd reportgenerator

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Instale as dependências
pip install -r requirements.txt
```

O `requirements.txt` tambem instala o proprio projeto em modo editavel (`-e .`).
Isso garante que o pacote `app` seja importavel corretamente em ambientes como o
Streamlit Cloud.

---

## Configuração do .env

Copie o arquivo de exemplo e edite conforme necessário:

```bash
cp .env.example .env
```

Variáveis disponíveis:

| Variável | Descrição | Padrão |
|---|---|---|
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | Caminho para o JSON da Service Account | `credentials/service_account.json` |
| `DATABASE_PATH` | Caminho do banco SQLite | `data/reports.db` |
| `PUBLISHED_REPORTS_DIR` | Diretório de relatórios publicados | `data/published_reports` |
| `MAX_UPLOAD_SIZE_MB` | Tamanho máximo de upload | `50` |
| `APP_NAME` | Nome da aplicação | `Report Generator` |

---

## Configurar Google Sheets (Service Account)

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto e ative a **Google Sheets API** e **Google Drive API**
3. Crie uma **Service Account** e baixe o JSON de credenciais
4. Salve o JSON em `credentials/service_account.json`
5. Compartilhe a planilha com o e-mail da Service Account

---

## Como rodar

```bash
streamlit run app/main.py
```

A aplicação abrirá em `http://localhost:8501`

---

## Dataset de teste

O arquivo `DATASET_TESTE.csv` na raiz do projeto contém 240 registros simulados com as colunas:

- `data` — data da transação (2024)
- `canal` — canal de aquisição (organico, pago, email, direto, afiliado)
- `produto` — produto vendido (5 tipos)
- `regiao` — região do Brasil (5 regiões)
- `sessoes` — número de sessões
- `conversoes` — número de conversões
- `receita` — receita em R$
- `custo` — custo em R$

**Use este arquivo para testar todos os frameworks diretamente no Streamlit Cloud.**

---

## Frameworks Analíticos

### OODA Loop
**Observe → Orient → Decide → Act**
Analisa dados em 4 fases estratégicas. Ideal para tomada de decisão executiva.

### Funil de Conversão
**Topo → Meio → Fundo → Conversão → Gargalos**
Mapeia o fluxo de volume e identifica gargalos. Ideal para marketing e vendas.

### Diagnóstico de Performance
**Volume → Eficiência → Qualidade**
Avalia produção, eficiência operacional e consistência dos resultados.

### Análise Exploratória (EDA)
**Distribuições → Correlações → Outliers**
Exploração estatística abrangente. Ideal para primeiro contato com dados novos.

### Comparação Temporal
**Tendência → Crescimento → Sazonalidade**
Analisa evolução ao longo do tempo. Requer coluna de data no dataset.

---

## Media Mix Modeling (Meridian)

### O que é e quando usar

O **Google Meridian** é uma biblioteca de Media Mix Modeling (MMM) que usa inferência Bayesiana (MCMC) para quantificar o impacto de cada canal de marketing (TV, digital, rádio, etc.) nas vendas ou conversões. Use quando precisar:

- Medir o ROI real por canal de mídia
- Entender a contribuição de cada canal para o KPI principal
- Otimizar a distribuição de budget entre canais

### Pré-requisitos de hardware

- Python 3.10+
- TensorFlow 2.16+
- GPU recomendada (NVIDIA com CUDA) para treino em tempo razoável
- Sem GPU: treino pode levar horas; CPU é suportado mas lento

### Instalação das dependências opcionais

```bash
pip install google-meridian[schema]>=1.3.0 tensorflow>=2.16.0 tensorflow-probability>=0.24.0
```

### Estrutura de CSV esperada

```
data,vendas,gasto_tv,gasto_digital,custo_radio,impressoes_tv,alcance_digital
2023-01-01,15420,12000,8500,3200,450000,180000
2023-01-08,16800,11500,9000,3000,480000,195000
...
```

Colunas:

- `data` — data da semana (formato `YYYY-MM-DD`; granularidade semanal recomendada)
- `vendas` — KPI principal (receita, conversões, etc.)
- `gasto_tv`, `gasto_digital`, `custo_radio` — investimento por canal de mídia
- `impressoes_tv`, `alcance_digital` — impressões/alcance (opcional)
- Variáveis de controle como `temperatura` ou `feriado` são opcionais

Recomendações de volume de dados:

- Mínimo de 52 semanas (1 ano)
- Ideal: 104+ semanas (2 anos)
- Pelo menos 3 canais de mídia

### Documentação oficial

- Documentação: https://google.github.io/meridian
- PyPI: https://pypi.org/project/google-meridian/

---

## Estrutura de pastas

```
reportgenerator/
├── app/
│   ├── main.py                    # Entrypoint Streamlit
│   ├── pages/                     # 6 páginas do fluxo
│   ├── components/                # Componentes visuais reutilizáveis
│   ├── services/                  # Lógica de negócio
│   ├── analysis_frameworks/       # 5 frameworks analíticos
│   ├── models/                    # Dataclasses
│   ├── utils/                     # Utilitários
│   └── config/                    # Settings e banco de dados
├── data/
│   ├── example_dataset.csv        # Dataset de exemplo
│   └── published_reports/         # Relatórios publicados
├── templates/                     # Templates Jinja2
├── static/                        # CSS global
├── tests/                         # Testes pytest
├── DATASET_TESTE.csv              # Arquivo de teste na raiz (fácil acesso)
├── requirements.txt
└── .env.example
```

---

## Rodar os testes

```bash
pytest tests/ -v
```

---

## Deploy no Streamlit Cloud

1. Faça push do repositório para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório e aponte para `app/main.py`
4. Adicione as variáveis de ambiente necessárias em **Settings → Secrets**
5. Use o arquivo `DATASET_TESTE.csv` para testar o upload

---

*Desenvolvido com Streamlit, Pandas, Plotly e Python 3.11+*
