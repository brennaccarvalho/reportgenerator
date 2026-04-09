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
3. Conecte o repositório, aponte para `app/main.py`
4. Adicione as variáveis de ambiente necessárias em **Settings → Secrets**
5. Use o arquivo `DATASET_TESTE.csv` para testar o upload

---

*Desenvolvido com Streamlit, Pandas, Plotly e Python 3.11+*
