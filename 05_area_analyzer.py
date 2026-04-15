"""
05_area_analyzer.py

Identifica as grandes áreas temáticas da Engenharia de Computação nos TCCs
usando matching de palavras-chave sobre resumo + conclusão.

Constrói um grafo de co-ocorrência onde:
  - Nós  = grandes áreas (ex: "Machine Learning", "IoT")
  - Arestas = duas áreas aparecem juntas no mesmo TCC
  - Peso   = número de TCCs em que co-ocorrem

Saídas:
  - data/graphs/area_cooccurrence.gml     → grafo exportável pro Gephi
  - data/graphs/area_frequency.json       → ranking de frequência das áreas
  - data/graphs/area_cooccurrence.json    → detalhamento das co-ocorrências
"""

import re
import json
import itertools
import networkx as nx
from pathlib import Path
from collections import Counter, defaultdict

# ── Configuração ───────────────────────────────────────────────────────────────
INTERIM_DIR = Path("data/interim")
GRAPH_DIR   = Path("data/graphs")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Número máximo de TCCs a processar (None = todos)
MAX_TCCS = 5

# ── Dicionário de Grandes Áreas ────────────────────────────────────────────────
# Cada área tem uma lista de palavras-chave (busca case-insensitive).
# Palavras mais específicas têm prioridade no diagnóstico.
AREAS = {
    "Machine Learning / IA": [
        "machine learning", "aprendizado de máquina", "aprendizado automático",
        "deep learning", "redes neurais", "neural", "inteligência artificial",
        "random forest", "xgboost", "svm", "classificação supervisionada",
        "regressão", "treinamento", "modelo preditivo", "predição", "churn",
        "feature importance", "overfitting", "underfitting",
    ],
    "Ciência de Dados / Análise": [
        "ciência de dados", "data science", "análise de dados", "data analytics",
        "visualização de dados", "dashboard", "dataset", "dataframe",
        "pré-processamento", "pipeline de dados", "indicador", "métrica",
        "exploratória", "estatística descritiva", "correlação",
    ],
    "IoT / Sistemas Embarcados": [
        "iot", "internet das coisas", "internet of things", "raspberry",
        "arduino", "embarcado", "microcontrolador", "microprocessador",
        "sensor", "atuador", "firmware", "rtos", "esp32", "esp8266",
        "automação residencial", "smart home",
    ],
    "Redes de Computadores": [
        "rede de computadores", "protocolo", "tcp", "udp", "http", "https",
        "wi-fi", "wireless", "roteamento", "switching", "vlan", "firewall",
        "latência", "throughput", "bandwidth", "topologia de rede", "lan", "wan",
        "rede de sensores", "monitoramento de redes",
    ],
    "Segurança da Informação": [
        "segurança", "criptografia", "autenticação", "spoofing", "anti-spoofing",
        "vulnerabilidade", "ataque", "defesa", "biométrico", "reconhecimento facial",
        "reconhecimento de voz", "liveness detection", "privacidade", "gdpr",
    ],
    "Processamento de Sinais / Imagens": [
        "processamento de sinal", "processamento de imagem", "visão computacional",
        "áudio", "som", "acústica", "ultrassom", "fft", "espectrograma",
        "reconhecimento de padrões", "opencv", "filtro digital", "compressão de sinal",
    ],
    "Cloud / Sistemas Distribuídos": [
        "cloud", "nuvem", "computação em nuvem", "sistemas distribuídos",
        "microsserviços", "container", "docker", "kubernetes", "baas",
        "serverless", "mlops", "wandb", "mlflow", "devops", "ci/cd",
        "escalabilidade", "disponibilidade",
    ],
    "Engenharia de Software": [
        "engenharia de software", "desenvolvimento de software", "metodologia ágil",
        "scrum", "kanban", "testes automatizados", "qualidade de software",
        "refatoração", "design pattern", "arquitetura de software", "api rest",
        "microsserviço", "requisitos", "uat",
    ],
    "Banco de Dados / Grafos": [
        "banco de dados", "sql", "nosql", "mongodb", "neo4j", "grafo",
        "graph database", "ontologia", "schema", "query", "indexação",
        "modelagem de dados", "entidade-relacionamento", "data engineering",
    ],
    "Otimização / Alto Desempenho": [
        "otimização", "performance", "eficiência energética", "consolidação de servidores",
        "virtualização", "conteinerização", "benchmark", "profiling",
        "compressão de rede neural", "poda", "quantização", "pruning",
        "complexidade computacional", "paralelismo",
    ],
    "Astronomia / Ciências Aplicadas": [
        "astronomia", "estrela", "fotometria", "kepler", "telescópio",
        "período de rotação", "espectroscopia", "exoplaneta",
    ],
    "Sistemas de Recomendação": [
        "sistema de recomendação", "recommender system", "filtragem colaborativa",
        "filtragem baseada em conteúdo", "preferências do usuário",
    ],
}


# ── Funções principais ─────────────────────────────────────────────────────────

def detectar_areas(texto: str) -> list[str]:
    """
    Retorna a lista de áreas detectadas num texto via matching de palavras-chave.
    Uma área é detectada se ao menos UMA das suas palavras-chave aparecer no texto.
    """
    texto_lower = texto.lower()
    detectadas = []
    for area, keywords in AREAS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', texto_lower):
                detectadas.append(area)
                break  # basta uma keyword para confirmar a área
    return detectadas


def carregar_secoes(limite: int | None = None) -> list[dict]:
    """Carrega os JSONs de seções e filtra apenas TCCs com conteúdo útil."""
    path = INTERIM_DIR / "all_sections.json"
    if not path.exists():
        raise FileNotFoundError(f"[!] {path} não encontrado. Rode o 02_section_extractor.py primeiro.")

    with open(path, encoding="utf-8") as f:
        dados = json.load(f)

    # Filtra somente TCCs com pelo menos resumo ou conclusão
    uteis = [d for d in dados if d.get("resumo") or d.get("conclusao")]

    if limite:
        uteis = uteis[:limite]

    print(f"[+] {len(uteis)} TCCs carregados (de {len(dados)} totais).")
    return uteis


def construir_grafo(analise: list[dict]) -> nx.Graph:
    """
    Constrói o grafo de co-ocorrência de áreas a partir da análise.
    """
    G = nx.Graph()

    # Adiciona nós (áreas) com atributo de frequência total
    freq_global = Counter()
    for item in analise:
        freq_global.update(item["areas_detectadas"])

    for area, freq in freq_global.items():
        G.add_node(area, frequencia=freq, label=area)

    # Adiciona arestas (co-ocorrência por TCC)
    for item in analise:
        areas = item["areas_detectadas"]
        for a, b in itertools.combinations(sorted(set(areas)), 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
                G[a][b]["tccs"].append(item["arquivo"])
            else:
                G.add_edge(a, b, weight=1, tccs=[item["arquivo"]])

    return G


# ── Pipeline principal ─────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"  Análise de Grandes Áreas Temáticas — ThesisMiner")
    print(f"  TCCs a processar: {MAX_TCCS if MAX_TCCS else 'todos'}")
    print(f"{'='*60}\n")

    # 1. Carrega seções
    secoes = carregar_secoes(limite=MAX_TCCS)

    # 2. Detecta áreas em cada TCC
    analise = []
    freq_por_area = Counter()

    for item in secoes:
        texto_completo = f"{item.get('resumo', '')} {item.get('conclusao', '')}"
        areas = detectar_areas(texto_completo)
        freq_por_area.update(areas)

        resultado = {
            "arquivo": item["arquivo"],
            "areas_detectadas": areas,
            "total_areas": len(areas),
        }
        analise.append(resultado)

        print(f"  [{item['arquivo'][:30]}]")
        if areas:
            for a in areas:
                print(f"    ✓ {a}")
        else:
            print(f"    ~ nenhuma área detectada")

    # 3. Relatório de frequência
    print(f"\n{'─'*60}")
    print(f"  RANKING DE GRANDES ÁREAS (pelos {MAX_TCCS} TCCs)")
    print(f"{'─'*60}")
    for area, count in freq_por_area.most_common():
        barra = "█" * count
        print(f"  {area:<35} {barra} ({count})")

    # 4. Constrói grafo de co-ocorrência
    G = construir_grafo(analise)
    print(f"\n[+] Grafo de co-ocorrência:")
    print(f"    Nós (áreas)  : {G.number_of_nodes()}")
    print(f"    Arestas      : {G.number_of_edges()}")
    if G.number_of_nodes() > 0:
        print(f"    Densidade    : {nx.density(G):.4f}")

    # 5. Exporta resultados
    # GML para Gephi
    gml_path = GRAPH_DIR / "area_cooccurrence.gml"
    # GML não suporta atributos de lista, remover 'tccs' antes de exportar
    G_export = G.copy()
    for u, v in G_export.edges():
        G_export[u][v].pop("tccs", None)
    nx.write_gml(G_export, gml_path)

    # JSON de frequência
    freq_path = GRAPH_DIR / "area_frequency.json"
    with open(freq_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"area": a, "frequencia": c} for a, c in freq_por_area.most_common()],
            f, ensure_ascii=False, indent=4
        )

    # JSON detalhado de co-ocorrências
    cooc_path = GRAPH_DIR / "area_cooccurrence.json"
    cooc_data = [
        {"area_a": u, "area_b": v, "peso": d["weight"], "tccs": d.get("tccs", [])}
        for u, v, d in G.edges(data=True)
    ]
    cooc_data.sort(key=lambda x: -x["peso"])
    with open(cooc_path, "w", encoding="utf-8") as f:
        json.dump(cooc_data, f, ensure_ascii=False, indent=4)

    print(f"\n[✓] Arquivos salvos:")
    print(f"    {gml_path}    → Gephi")
    print(f"    {freq_path}")
    print(f"    {cooc_path}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
