"""
05_area_analyzer.py

Identifica as grandes áreas temáticas da Engenharia de Computação nos TCCs
usando ML (Topic Modeling com NMF e TF-IDF) sobre resumo + conclusão.

Constrói grafos de co-ocorrência agrupados por ANO e um GLOBAL:
  - Nós  = temas descobertos pelo algoritmo (ex: "Machine / Dados")
  - Arestas = co-ocorrência em um mesmo TCC

Saídas em data/graphs/:
  - area_cooccurrence_{ano|global}.gml
  - area_frequency_{ano|global}.json
  - area_cooccurrence_{ano|global}.json
"""

import json
import itertools
import networkx as nx
from pathlib import Path
from collections import Counter, defaultdict

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

# ── Configuração ───────────────────────────────────────────────────────────────
INTERIM_DIR = Path("data/interim")
GRAPH_DIR   = Path("data/graphs")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

MAX_TCCS = None
NUM_TOPICS = 12
TOP_WORDS_PER_TOPIC = 3

print("[*] Carregando modelo SpaCy para stopwords em português...")
# carrega só as dependências mais leves
nlp = spacy.load("pt_core_news_lg", disable=["ner", "parser"])
STOP_WORDS = list(nlp.Defaults.stop_words) + [
    "este", "trabalho", "como", "através", "deste", "sistema", "desenvolvimento", 
    "uso", "aplicação", "base", "estudo", "resultados", "foi", "foram", "forma", 
    "objetivo", "tcc", "análise", "técnicas", "utilização", "proposta", "the", 
    "and", "of", "to", "in", "for", "is", "on", "that", "with", "by", "this", 
    "as", "it", "an", "be", "are", "which", "from", "or", "can", "https", "http",
    "disponível", "acesso", "2019", "2020", "2021", "2022", "2023", "2024", "2025",
    "www", "acessado", "figura", "fonte", "tabela", "gráfico", "capítulo", 
    "seção", "universidade", "federal", "ufrn", "com", "em", "um", "uma", "ser",
    "fazer", "pode", "podem", "bem", "são", "sobre", "tem", "ainda", "assim"
]

def carregar_secoes(limite: int | None = None) -> list[dict]:
    path = INTERIM_DIR / "all_sections.json"
    if not path.exists():
        raise FileNotFoundError(f"[!] {path} não encontrado. Rode o 02_section_extractor.py primeiro.")

    with open(path, encoding="utf-8") as f:
        dados = json.load(f)

    uteis = [d for d in dados if d.get("resumo") or d.get("conclusao")]
    if limite:
        uteis = uteis[:limite]

    print(f"[+] {len(uteis)} TCCs carregados.")
    return uteis

def classificar_documentos_nmf(textos: list[str]) -> tuple[list[list[str]], list[str]]:
    """Aplica NMF para extração de tópicos nos textos de entrada."""
    vectorizer = TfidfVectorizer(max_df=0.85, min_df=2, stop_words=STOP_WORDS)
    tfidf = vectorizer.fit_transform(textos)
    
    nmf = NMF(n_components=NUM_TOPICS, random_state=42)
    W = nmf.fit_transform(tfidf)
    feature_names = vectorizer.get_feature_names_out()

    topics = []
    for topic_idx, topic in enumerate(nmf.components_):
        top_features_ind = topic.argsort()[:-TOP_WORDS_PER_TOPIC - 1:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        topics.append(" / ".join(top_features).title())

    doc_topics = []
    for doc_weights in W:
        # Pega top 2 tópicos do documento
        top_indices = doc_weights.argsort()[-2:][::-1]
        
        assigned = []
        for i in top_indices:
            # limiar de pertinência empírico
            if doc_weights[i] > 0.05:
                assigned.append(topics[i])
                
        # Se nenhum bater o threshold, atribui pelo menos o primário
        if not assigned and len(top_indices) > 0:
            assigned = [topics[top_indices[0]]]
            
        doc_topics.append(assigned)

    return doc_topics, topics

def construir_grafo(analise: list[dict]) -> nx.Graph:
    G = nx.Graph()
    freq_global = Counter()
    for item in analise:
        freq_global.update(item["areas_detectadas"])

    for area, freq in freq_global.items():
        G.add_node(area, frequencia=freq, label=area)

    for item in analise:
        areas = item["areas_detectadas"]
        for a, b in itertools.combinations(sorted(set(areas)), 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)

    return G

def exportar_grafo(G: nx.Graph, freq_por_area: Counter, prefixo: str):
    gml_path = GRAPH_DIR / f"area_cooccurrence_{prefixo}.gml"
    nx.write_gml(G, gml_path)

    freq_path = GRAPH_DIR / f"area_frequency_{prefixo}.json"
    with open(freq_path, "w", encoding="utf-8") as f:
        json.dump([{"area": a, "frequencia": c} for a, c in freq_por_area.most_common()], f, ensure_ascii=False, indent=4)

    cooc_path = GRAPH_DIR / f"area_cooccurrence_{prefixo}.json"
    cooc_data = [{"area_a": u, "area_b": v, "peso": d["weight"]} for u, v, d in G.edges(data=True)]
    cooc_data.sort(key=lambda x: -x["peso"])
    with open(cooc_path, "w", encoding="utf-8") as f:
        json.dump(cooc_data, f, ensure_ascii=False, indent=4)
        
    print(f"  [✓] Salvo {prefixo}!")

def main():
    print(f"\n{'='*60}")
    print(f"  Análise de Áreas Temáticas c/ Tópicos NMF — ThesisMiner")
    print(f"{'='*60}\n")

    secoes = carregar_secoes(limite=MAX_TCCS)
    
    # 1. Topic Modeling em todo o Corpus
    textos = [f"{item.get('resumo', '')} {item.get('conclusao', '')}" for item in secoes]
    doc_topics, topics_list = classificar_documentos_nmf(textos)
    
    # Adiciona a predição no dicionário
    for i, item in enumerate(secoes):
        item["areas_detectadas"] = doc_topics[i]
        
    print("\n[*] Tópicos Gerados Mestre:")
    for t in topics_list:
        print(f"    - {t}")
        
    # 2. Gerar Global
    print("\n[*] GERANDO GRAFO GLOBAL...")
    analise_global = [{"arquivo": s["arquivo"], "areas_detectadas": s["areas_detectadas"]} for s in secoes]
    G_global = construir_grafo(analise_global)
    
    freq_global = Counter()
    for s in secoes:
        freq_global.update(s["areas_detectadas"])
        
    exportar_grafo(G_global, freq_global, "global")

    # 3. Agrupar por ano
    secoes_por_ano = defaultdict(list)
    for item in secoes:
        ano = item.get("ano", "unknown")
        secoes_por_ano[ano].append(item)

    for ano, itens_ano in secoes_por_ano.items():
        print(f"\n[*] GERANDO GRAFO ANO: {ano} ({len(itens_ano)} TCCs)...")
        analise_ano = [{"arquivo": s["arquivo"], "areas_detectadas": s["areas_detectadas"]} for s in itens_ano]
        G_ano = construir_grafo(analise_ano)
        
        freq_ano = Counter()
        for s in itens_ano:
            freq_ano.update(s["areas_detectadas"])
            
        exportar_grafo(G_ano, freq_ano, ano)

if __name__ == "__main__":
    main()
