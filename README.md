# Graph Analysis and Named Entity Recognition in Undergraduate Theses

Repository dedicated to the extraction of Named Entities (NLP) and the construction of structured co-occurrence networks from academic works in Computer Engineering at UFRN.

Developed by Gabriel Neto, Sara Gabrielly, and Ícaro Cortês as an artifact for evaluation and performance analysis for Algorithms and Data Structures – Unit 01.

## 📂 Project Structure

```text
.
├── 01_scraper.py          # Step 1: Web scraping of UFRN repository
├── 02_extractor.py        # Step 2: PDF to clean text conversion
├── 03_ner_features.py     # Step 3: Named Entity Recognition (spaCy)
├── 04_graph_builder.py    # Step 4: Graph construction (NetworkX)
├── README.md              # Project documentation
├── data/                  # Data pipeline layers (Gitignored)
│   ├── features/          # Structured NER JSON objects
│   ├── interim/           # Cleaned plain text files
│   ├── processed/         # Final network graphs (.gml)
│   └── raw/               # Original downloaded PDFs
└── notebooks/             # Analysis and visualization report