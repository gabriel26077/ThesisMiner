# ThesisMiner — NER e Análise de Áreas Temáticas em TCCs

Repositório dedicado à extração de entidades nomeadas (NLP) e à identificação de **grandes áreas temáticas** em Trabalhos de Conclusão de Curso de Engenharia de Computação da UFRN, com construção de redes de co-ocorrência e visualização em grafos.

Desenvolvido por **Gabriel Neto, Sara Gabrielly e Ícaro Cortês** como artefato de avaliação e análise de desempenho para a disciplina de **Algoritmos e Estrutura de Dados II – Unidade 01**.

---

## 📂 Estrutura do Projeto

```text
.
├── 01_scraper.py            # Etapa 1: Coleta de TCCs via API REST do DSpace (UFRN)
├── 02_extractor.py          # Etapa 2: Extração de texto completo dos PDFs
├── 02_section_extractor.py  # Etapa 2b: Extração de Resumo e Conclusão por seção
├── 03_ner_features.py       # Etapa 3: NER com spaCy (cenários × variantes)
├── 04_graph_builder.py      # Etapa 4: Grafos de co-ocorrência de entidades (NetworkX)
├── 05_area_analyzer.py      # Etapa 5: Identificação de grandes áreas temáticas
├── 06_visualizer.py         # Etapa 6: Visualização interativa em HTML (pyvis)
├── 07_export_pngs.py        # Etapa 7: Exporta todos os grafos NER como PNG
├── 08_area_pngs.py          # Etapa 8: Exporta grafos de áreas por cenário (3/6/9/12 TCCs)
├── README.md
├── requirements.txt
├── performance_report.json  # Relatório de desempenho do NER (tempo × entidades)
├── graph_metrics_report.json # Métricas dos grafos (nós, arestas, densidade)
└── data/
    ├── raw/                 # PDFs baixados (gitignored)
    ├── interim/             # Textos limpos (.txt) e JSONs de seções (gitignored)
    ├── processed/           # JSONs de entidades NER por cenário/variante (gitignored)
    ├── graphs/              # Grafos exportados (.gml) e PNGs
    │   └── png/             # Imagens estáticas dos grafos
    └── features/            # (reservado)
```

---

## 🔄 Pipeline de Execução

```
01_scraper → 02_section_extractor → 05_area_analyzer → 08_area_pngs
                    ↓
             02_extractor → 03_ner_features → 04_graph_builder → 07_export_pngs
                                                        ↓
                                                 06_visualizer (HTML interativo)
```

### Descrição das Etapas

| Script | Entrada | Saída | Descrição |
|---|---|---|---|
| `01_scraper.py` | API DSpace | `data/raw/*.pdf` + `data/interim/resumos_api.json` | Baixa TCCs e extrai resumos via API REST (sem navegador) |
| `02_extractor.py` | `data/raw/*.pdf` | `data/interim/*.txt` | Extrai e limpa o texto completo dos PDFs |
| `02_section_extractor.py` | `data/raw/*.pdf` | `data/interim/all_sections.json` | Extrai apenas Resumo e Conclusão de cada TCC |
| `03_ner_features.py` | `data/interim/*.txt` | `data/processed/` | NER com spaCy em 4 cenários × 5 variantes de segmentação |
| `04_graph_builder.py` | `data/processed/` | `data/graphs/*.gml` | Constrói grafos de co-ocorrência de entidades |
| `05_area_analyzer.py` | `data/interim/all_sections.json` | `data/graphs/area_*.json + .gml` | Detecta grandes áreas por palavras-chave e gera grafo temático |
| `06_visualizer.py` | `data/graphs/area_cooccurrence.gml` | `data/graphs/visualizacao_areas.html` | Visualização interativa (abre no navegador) |
| `07_export_pngs.py` | `data/graphs/*.gml` | `data/graphs/png/` | Exporta todos os grafos NER como PNG |
| `08_area_pngs.py` | `data/interim/all_sections.json` | `data/graphs/png/areas_N_tccs.png` | 4 PNGs comparativos do grafo de áreas (3, 6, 9, 12 TCCs) |

---

## ⚙️ Configuração do Ambiente

### 1. Criar ambiente virtual e instalar dependências

```bash
python3 -m venv venv
source venv/bin/activate          # Linux/Mac/WSL
# venv\Scripts\activate           # Windows

pip install selenium webdriver-manager pymupdf spacy \
            networkx matplotlib pyvis requests
```

### 2. Baixar o modelo de linguagem português (spaCy)

```bash
python -m spacy download pt_core_news_lg
```

---

## 🚀 Execução

```bash
# 1. Baixar 15 TCCs do repositório da UFRN
python 01_scraper.py

# 2a. Extrair Resumo + Conclusão (para análise temática)
python 02_section_extractor.py

# 2b. Extrair texto completo (para NER)
python 02_extractor.py

# 3. Rodar NER (cenários: 3, 6, 9, 12 PDFs × 5 variantes de segmentação)
python 03_ner_features.py

# 4. Construir grafos de co-ocorrência de entidades
python 04_graph_builder.py

# 5. Analisar grandes áreas temáticas (padrão: todos os TCCs)
python 05_area_analyzer.py

# 6. Gerar visualização interativa HTML
python 06_visualizer.py

# 7. Exportar grafos NER como PNG
python 07_export_pngs.py

# 8. Exportar grafos de áreas (3/6/9/12 TCCs) para comparação
python 08_area_pngs.py
```

---

## 📊 Variantes de Segmentação (Etapa 3)

O NER é avaliado em **5 estratégias de segmentação** do texto:

| Variante | Descrição |
|---|---|
| `sentence` | Segmenta por sentenças (maior precisão, mais lento) |
| `paragraph` | Segmenta por parágrafos |
| `window_k500` | Janelas deslizantes de 500 caracteres |
| `window_k1000` | Janelas deslizantes de 1000 caracteres |
| `window_k1500` | Janelas deslizantes de 1500 caracteres |

---

## 🗺️ Grandes Áreas Temáticas Identificadas

A análise de palavras-chave cobre **12 grandes áreas** da Engenharia de Computação:

`Machine Learning / IA` · `Ciência de Dados` · `IoT / Embarcados` · `Redes` · `Segurança` · `Sinais / Imagens` · `Cloud / Distribuído` · `Engenharia de Software` · `Banco de Dados / Grafos` · `Otimização / Desempenho` · `Astronomia` · `Sistemas de Recomendação`

---

## 👥 Autores

Gabriel Neto · Sara Gabrielly · Ícaro Cortês  
UFRN — Departamento de Engenharia de Computação e Automação  
Disciplina: Algoritmos e Estrutura de Dados II