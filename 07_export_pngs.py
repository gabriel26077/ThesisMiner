"""
07_export_pngs.py

Exporta todos os grafos gerados como imagens PNG de alta resolução:
  - area_cooccurrence.gml  → PNG colorido por área temática
  - graph_*_*.gml (NER)   → PNG com top-N nós por grau

Saída: data/graphs/png/
"""

import json
import networkx as nx
import matplotlib
matplotlib.use("Agg")  # backend sem janela (WSL-safe)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from pathlib import Path

# ── Caminhos ───────────────────────────────────────────────────────────────────
GRAPH_DIR = Path("data/graphs")
PNG_DIR   = GRAPH_DIR / "png"
PNG_DIR.mkdir(parents=True, exist_ok=True)

FREQ_PATH = GRAPH_DIR / "area_frequency.json"

# ── Configuração visual ────────────────────────────────────────────────────────
CORES_AREAS = {
    "Machine Learning / IA":              "#FF6B6B",
    "Ciência de Dados / Análise":         "#FF9F43",
    "IoT / Sistemas Embarcados":          "#48DBFB",
    "Redes de Computadores":              "#1DD1A1",
    "Segurança da Informação":            "#EE5A24",
    "Processamento de Sinais / Imagens":  "#A29BFE",
    "Cloud / Sistemas Distribuídos":      "#74B9FF",
    "Engenharia de Software":             "#FDCB6E",
    "Banco de Dados / Grafos":            "#6C5CE7",
    "Otimização / Alto Desempenho":       "#00B894",
    "Astronomia / Ciências Aplicadas":    "#FD79A8",
    "Sistemas de Recomendação":           "#E17055",
}
BG_COLOR  = "#0f0f1a"
TEXT_COLOR = "#f0f0f0"

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "text.color":       TEXT_COLOR,
    "axes.facecolor":   BG_COLOR,
    "figure.facecolor": BG_COLOR,
})


# ── Helpers ────────────────────────────────────────────────────────────────────

def salvar_png(fig, path: Path):
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print(f"  [✓] {path.name}")


def layout_com_seed(G, seed=42):
    """Spring layout com semente fixa para reprodutibilidade."""
    return nx.spring_layout(G, seed=seed, k=2.5 / (len(G.nodes()) ** 0.5 + 1))


# ── Grafo de Áreas ─────────────────────────────────────────────────────────────

def exportar_area_graph():
    path = GRAPH_DIR / "area_cooccurrence.gml"
    if not path.exists():
        print("[!] area_cooccurrence.gml não encontrado.")
        return

    G = nx.read_gml(path)

    # Frequências para tamanho dos nós
    freq_map = {}
    if FREQ_PATH.exists():
        with open(FREQ_PATH, encoding="utf-8") as f:
            freq_map = {d["area"]: d["frequencia"] for d in json.load(f)}

    pos    = layout_com_seed(G, seed=7)
    cores  = [CORES_AREAS.get(n, "#B2BEC3") for n in G.nodes()]
    sizes  = [300 + freq_map.get(n, 1) * 400 for n in G.nodes()]
    pesos  = [G[u][v].get("weight", 1) for u, v in G.edges()]
    max_p  = max(pesos) if pesos else 1
    widths = [0.5 + (p / max_p) * 5 for p in pesos]

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_facecolor(BG_COLOR)
    ax.set_title(
        "Grafo de Co-ocorrência — Grandes Áreas Temáticas (15 TCCs)\n"
        "Eng. Computação · UFRN · Algorithms & Data Structures",
        fontsize=14, color=TEXT_COLOR, pad=20, fontweight="bold"
    )

    nx.draw_networkx_edges(G, pos, ax=ax,
                           width=widths,
                           edge_color="white", alpha=0.2)

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=cores,
                           node_size=sizes,
                           linewidths=1.5, edgecolors="white", alpha=0.92)

    # Labels com quebra de linha para nomes longos
    labels = {n: n.replace(" / ", "\n").replace(" / ", "\n") for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=8, font_color=TEXT_COLOR,
                            font_weight="bold")

    # Edge weight labels
    edge_labels = {(u, v): G[u][v].get("weight", "") for u, v in G.edges()
                   if G[u][v].get("weight", 0) > 1}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_size=7, font_color="#aaaaaa",
                                 bbox=dict(alpha=0))

    # Legenda
    patches = [mpatches.Patch(color=c, label=n)
               for n, c in CORES_AREAS.items() if n in G.nodes()]
    ax.legend(handles=patches, loc="lower left", fontsize=7,
              facecolor="#1a1a2e", edgecolor="#444", labelcolor=TEXT_COLOR,
              framealpha=0.9, ncol=2)

    ax.axis("off")
    salvar_png(fig, PNG_DIR / "area_cooccurrence.png")


# ── Grafos NER ─────────────────────────────────────────────────────────────────

def cor_por_densidade(densidade: float) -> str:
    """Mapeia densidade 0-1 para uma cor numa paleta viridis."""
    cmap = plt.cm.plasma
    return mcolors.to_hex(cmap(min(densidade * 2, 1.0)))


def exportar_ner_graph(gml_path: Path, top_n: int = 60):
    """
    Exporta um grafo NER como PNG.
    Como os grafos NER têm centenas/milhares de nós, exibimos apenas os
    top_n nós por grau (mais conectados = mais relevantes na rede).
    """
    G_full = nx.read_gml(gml_path)
    n_total = G_full.number_of_nodes()
    e_total = G_full.number_of_edges()

    # Sub-grafo com os top_n nós por grau
    graus  = sorted(G_full.degree(), key=lambda x: x[1], reverse=True)
    top    = [n for n, _ in graus[:top_n]]
    G      = G_full.subgraph(top).copy()

    # Metadados do nome do arquivo (ex: graph_3_pdfs_sentence.gml)
    nome   = gml_path.stem  # graph_3_pdfs_sentence
    partes = nome.replace("graph_", "").split("_")
    # Monta cenário e variante do nome
    # Padrão: graph_{n}_pdfs_{variante}
    cenario = "_".join(partes[:2])   # ex: 3_pdfs
    variante = "_".join(partes[2:])  # ex: sentence

    densidade = nx.density(G_full)
    titulo = (
        f"Grafo NER · Cenário: {cenario.replace('_', ' ')} · "
        f"Variante: {variante}\n"
        f"Total: {n_total} nós / {e_total:,} arestas  —  "
        f"Exibindo top {min(top_n, n_total)} por grau  —  "
        f"Densidade: {densidade:.5f}"
    )

    pos   = layout_com_seed(G, seed=42)
    graus_sub = dict(G.degree())
    max_g = max(graus_sub.values()) if graus_sub else 1

    node_sizes  = [50 + (graus_sub[n] / max_g) * 600 for n in G.nodes()]
    node_colors = [cor_por_densidade(graus_sub[n] / max_g)  for n in G.nodes()]

    pesos  = [G[u][v].get("weight", 1) for u, v in G.edges()]
    max_p  = max(pesos) if pesos else 1
    widths = [0.2 + (p / max_p) * 2.5 for p in pesos]

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_facecolor(BG_COLOR)
    ax.set_title(titulo, fontsize=11, color=TEXT_COLOR, pad=16)

    nx.draw_networkx_edges(G, pos, ax=ax,
                           width=widths,
                           edge_color="white", alpha=0.15)

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=node_colors,
                           node_size=node_sizes,
                           linewidths=0.8, edgecolors="white", alpha=0.9)

    # Labels só para os top 20 (evita poluição visual)
    top20 = {n for n, _ in graus[:20]}
    labels = {n: n for n in G.nodes() if n in top20}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=7, font_color=TEXT_COLOR)

    # Barra de cor (grau normalizado)
    sm = plt.cm.ScalarMappable(cmap=plt.cm.plasma,
                               norm=plt.Normalize(vmin=0, vmax=max_g))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01)
    cbar.set_label("Grau do nó", color=TEXT_COLOR, fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_COLOR)

    ax.axis("off")
    out_name = f"{nome}.png"
    salvar_png(fig, PNG_DIR / out_name)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print("  Exportando todos os grafos para PNG")
    print(f"{'='*60}\n")

    # 1. Grafo de áreas temáticas
    print("[*] Grafo de áreas temáticas:")
    exportar_area_graph()

    # 2. Todos os grafos NER
    ner_files = sorted(GRAPH_DIR.glob("graph_*.gml"))
    print(f"\n[*] {len(ner_files)} grafos NER encontrados:")
    for gml in ner_files:
        exportar_ner_graph(gml, top_n=60)

    total = 1 + len(ner_files)
    print(f"\n{'='*60}")
    print(f"[✓] {total} PNGs salvos em: {PNG_DIR.resolve()}")
    print(f"    Windows (WSL): \\\\wsl$\\Ubuntu\\home\\sara\\ThesisMiner\\data\\graphs\\png\\")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
