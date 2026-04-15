"""
08_area_pngs.py

Gera 4 PNGs do grafo de co-ocorrência de áreas temáticas,
um para cada cenário: 3, 6, 9 e 12 TCCs.

Saída: data/graphs/png/areas_N_tccs.png
"""

import re
import json
import itertools
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from collections import Counter

# ── Configuração ───────────────────────────────────────────────────────────────
INTERIM_DIR = Path("data/interim")
PNG_DIR     = Path("data/graphs/png")
PNG_DIR.mkdir(parents=True, exist_ok=True)

CENARIOS = [3, 6, 9, 12]

AREAS = {
    "Machine Learning / IA": [
        "machine learning", "aprendizado de máquina", "deep learning",
        "redes neurais", "neural", "inteligência artificial",
        "random forest", "xgboost", "svm", "modelo preditivo",
        "predição", "churn", "feature importance", "classificação supervisionada",
    ],
    "Ciência de Dados": [
        "ciência de dados", "data science", "análise de dados", "data analytics",
        "visualização de dados", "dashboard", "dataset", "dataframe",
        "pré-processamento", "pipeline de dados", "indicador",
        "exploratória", "estatística descritiva",
    ],
    "IoT / Embarcados": [
        "iot", "internet das coisas", "raspberry", "arduino",
        "embarcado", "microcontrolador", "sensor", "atuador",
        "firmware", "automação residencial",
    ],
    "Redes": [
        "rede de computadores", "protocolo", "tcp", "udp",
        "wi-fi", "wireless", "roteamento", "vlan", "firewall",
        "latência", "throughput", "monitoramento de redes",
    ],
    "Segurança": [
        "segurança", "criptografia", "autenticação", "spoofing",
        "vulnerabilidade", "biométrico", "reconhecimento facial",
        "liveness detection", "privacidade",
    ],
    "Sinais / Imagens": [
        "processamento de sinal", "processamento de imagem",
        "visão computacional", "áudio", "acústica", "ultrassom",
        "fft", "opencv", "compressão de sinal",
    ],
    "Cloud / Distribuído": [
        "cloud", "nuvem", "sistemas distribuídos", "microsserviços",
        "container", "docker", "kubernetes", "baas", "mlops",
        "wandb", "mlflow", "escalabilidade",
    ],
    "Engenharia de Software": [
        "engenharia de software", "metodologia ágil", "scrum",
        "testes automatizados", "qualidade de software", "api rest",
        "requisitos",
    ],
    "Banco de Dados / Grafos": [
        "banco de dados", "sql", "nosql", "mongodb", "neo4j",
        "grafo", "graph database", "modelagem de dados",
    ],
    "Otimização / Desempenho": [
        "otimização", "eficiência energética", "benchmark", "profiling",
        "compressão de rede neural", "poda", "quantização", "pruning",
        "complexidade computacional", "paralelismo",
    ],
    "Astronomia": [
        "astronomia", "estrela", "fotometria", "kepler",
        "período de rotação", "telescópio",
    ],
    "Sistemas de Recomendação": [
        "sistema de recomendação", "recommender system",
        "filtragem colaborativa", "preferências do usuário",
    ],
}

# Paleta de cores harmoniosa
CORES = {
    "Machine Learning / IA":    "#FF6B6B",
    "Ciência de Dados":         "#FF9F43",
    "IoT / Embarcados":         "#48DBFB",
    "Redes":                    "#1DD1A1",
    "Segurança":                "#EE5A24",
    "Sinais / Imagens":         "#A29BFE",
    "Cloud / Distribuído":      "#74B9FF",
    "Engenharia de Software":   "#FDCB6E",
    "Banco de Dados / Grafos":  "#6C5CE7",
    "Otimização / Desempenho":  "#00B894",
    "Astronomia":               "#FD79A8",
    "Sistemas de Recomendação": "#E17055",
}

BG  = "#0d0d1a"
FG  = "#f0f0f0"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG})


def detectar_areas(texto: str) -> list[str]:
    texto_lower = texto.lower()
    return [
        area for area, kws in AREAS.items()
        if any(re.search(r'\b' + re.escape(kw) + r'\b', texto_lower) for kw in kws)
    ]


def carregar_secoes() -> list[dict]:
    path = INTERIM_DIR / "all_sections.json"
    with open(path, encoding="utf-8") as f:
        dados = json.load(f)
    return [d for d in dados if d.get("resumo") or d.get("conclusao")]


def construir_grafo_cenario(secoes: list[dict], n: int):
    subset = secoes[:n]
    freq   = Counter()
    arestas: dict[tuple, int] = {}

    for item in subset:
        texto = f"{item.get('resumo','')} {item.get('conclusao','')}"
        areas = list(set(detectar_areas(texto)))
        freq.update(areas)
        for a, b in itertools.combinations(sorted(areas), 2):
            arestas[(a, b)] = arestas.get((a, b), 0) + 1

    G = nx.Graph()
    for area, f in freq.items():
        G.add_node(area, freq=f)
    for (a, b), w in arestas.items():
        G.add_edge(a, b, weight=w)
    return G, freq


def gerar_png(G: nx.Graph, freq: Counter, n: int):
    if G.number_of_nodes() == 0:
        print(f"  [!] Nenhuma área detectada para {n} TCCs. Pulando.")
        return

    # Layout
    pos = nx.spring_layout(G, seed=42, k=3.0 / (G.number_of_nodes() ** 0.5 + 1))

    node_list  = list(G.nodes())
    node_colors = [CORES.get(n_,  "#B2BEC3") for n_ in node_list]
    node_sizes  = [800 + freq.get(n_, 1) * 500 for n_ in node_list]

    edges      = list(G.edges(data=True))
    max_w      = max((d.get("weight", 1) for _, _, d in edges), default=1)
    edge_widths = [0.8 + (d.get("weight", 1) / max_w) * 6 for _, _, d in edges]
    edge_colors = ["rgba(255,255,255,0.18)" if False else "#ffffff" for _ in edges]

    fig, ax = plt.subplots(figsize=(14, 9), facecolor=BG)
    ax.set_facecolor(BG)

    # Título
    ax.set_title(
        f"Grafo de Co-ocorrência de Áreas Temáticas — {n} TCCs\n"
        f"Eng. Computação · UFRN  |  "
        f"{G.number_of_nodes()} áreas · {G.number_of_edges()} co-ocorrências",
        fontsize=13, color=FG, fontweight="bold", pad=18
    )

    # Arestas
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        width=edge_widths,
        edge_color="#ffffff",
        alpha=0.18,
        style="solid"
    )

    # Nós
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        nodelist=node_list,
        node_color=node_colors,
        node_size=node_sizes,
        linewidths=2,
        edgecolors="#ffffff",
        alpha=0.95
    )

    # Labels com quebra de linha nos nomes longos
    labels = {nd: nd.replace(" / ", "\n") for nd in node_list}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=9, font_color=FG, font_weight="bold")

    # Peso das arestas (só se > 1)
    ew_labels = {(u, v): str(d["weight"])
                 for u, v, d in edges if d.get("weight", 0) > 1}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=ew_labels, ax=ax,
                                 font_size=8, font_color="#aaaaaa",
                                 bbox=dict(alpha=0, pad=0))

    # Legenda lateral
    patches = [
        mpatches.Patch(color=CORES.get(nd, "#B2BEC3"),
                       label=f"{nd}  ({freq.get(nd,0)})")
        for nd in sorted(node_list, key=lambda x: -freq.get(x, 0))
    ]
    legend = ax.legend(
        handles=patches,
        loc="lower left",
        fontsize=8,
        facecolor="#12122a",
        edgecolor="#333355",
        labelcolor=FG,
        framealpha=0.92,
        ncol=1,
        title="Área  (frequência)",
        title_fontsize=8,
    )
    legend.get_title().set_color(FG)

    ax.axis("off")
    fig.tight_layout()

    out = PNG_DIR / f"areas_{n}_tccs.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  [✓] {out.name}")


def main():
    print(f"\n{'='*55}")
    print("  Gerando PNGs de Áreas Temáticas por Cenário")
    print(f"{'='*55}\n")

    secoes = carregar_secoes()
    print(f"[+] {len(secoes)} TCCs disponíveis\n")

    for n in CENARIOS:
        if n > len(secoes):
            print(f"  [!] Cenário {n} TCCs: só há {len(secoes)} disponíveis. Pulando.")
            continue
        print(f"[*] Gerando PNG — {n} TCCs...")
        G, freq = construir_grafo_cenario(secoes, n)
        gerar_png(G, freq, n)

    print(f"\n[✓] PNGs salvos em: {PNG_DIR.resolve()}")
    print(f"    Windows (WSL): \\\\wsl$\\Ubuntu\\home\\sara\\ThesisMiner\\data\\graphs\\png\\\n")


if __name__ == "__main__":
    main()
