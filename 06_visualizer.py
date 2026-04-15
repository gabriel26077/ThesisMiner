"""
06_visualizer.py

Gera uma visualização interativa do grafo de co-ocorrência de áreas temáticas.
O resultado é um arquivo HTML que pode ser aberto diretamente no navegador.

Usa pyvis (wrapper do vis.js) para renderização interativa:
  - Nós  = grandes áreas (tamanho proporcional à frequência)
  - Arestas = co-ocorrências (espessura proporcional ao peso)
  - Cores  = agrupadas por cluster de afinidade

Saída: data/graphs/visualizacao_areas.html
"""

import json
import networkx as nx
from pathlib import Path
from pyvis.network import Network

# ── Caminhos ───────────────────────────────────────────────────────────────────
GRAPH_DIR    = Path("data/graphs")
GML_PATH     = GRAPH_DIR / "area_cooccurrence.gml"
FREQ_PATH    = GRAPH_DIR / "area_frequency.json"
OUTPUT_PATH  = GRAPH_DIR / "visualizacao_areas.html"

# ── Paleta de cores por cluster temático ──────────────────────────────────────
# Cores vibrantes para diferenciar os clusters visualmente
CORES = {
    "Machine Learning / IA":              "#FF6B6B",   # vermelho
    "Ciência de Dados / Análise":         "#FF9F43",   # laranja
    "IoT / Sistemas Embarcados":          "#48DBFB",   # ciano
    "Redes de Computadores":              "#1DD1A1",   # verde-água
    "Segurança da Informação":            "#EE5A24",   # vermelho-escuro
    "Processamento de Sinais / Imagens":  "#A29BFE",   # lilás
    "Cloud / Sistemas Distribuídos":      "#74B9FF",   # azul
    "Engenharia de Software":             "#FDCB6E",   # amarelo
    "Banco de Dados / Grafos":            "#6C5CE7",   # roxo
    "Otimização / Alto Desempenho":       "#00B894",   # verde
    "Astronomia / Ciências Aplicadas":    "#FD79A8",   # rosa
    "Sistemas de Recomendação":           "#E17055",   # salmão
}
COR_PADRAO = "#B2BEC3"  # cinza para áreas sem cor definida


def main():
    # 1. Carrega o grafo GML
    if not GML_PATH.exists():
        print(f"[!] Arquivo {GML_PATH} não encontrado.")
        print("    Execute o 05_area_analyzer.py primeiro.")
        return

    G = nx.read_gml(GML_PATH)

    # 2. Carrega frequências para dimensionar os nós
    freq_map = {}
    if FREQ_PATH.exists():
        with open(FREQ_PATH, encoding="utf-8") as f:
            freq_data = json.load(f)
        freq_map = {item["area"]: item["frequencia"] for item in freq_data}

    print(f"[+] Grafo carregado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    # 3. Configura a rede pyvis
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#0f0f1a",        # fundo escuro elegante
        font_color="#f0f0f0",
        notebook=False,
        directed=False,
    )

    # Física: spring layout dá boa separação para grafos de co-ocorrência
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 200,
          "springConstant": 0.08,
          "damping": 0.6
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "timestep": 0.5,
        "stabilization": { "iterations": 200 }
      },
      "nodes": {
        "font": { "size": 14, "face": "Inter, Arial, sans-serif" },
        "borderWidth": 2,
        "shadow": { "enabled": true, "size": 10, "x": 3, "y": 3 }
      },
      "edges": {
        "smooth": { "type": "continuous" },
        "shadow": { "enabled": true }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "hideEdgesOnDrag": false
      }
    }
    """)

    # 4. Adiciona nós
    for node in G.nodes():
        freq      = freq_map.get(node, 1)
        cor       = CORES.get(node, COR_PADRAO)
        tamanho   = 20 + freq * 15   # nós mais frequentes = maiores
        tooltip   = f"<b>{node}</b><br>Frequência: {freq} TCC(s)"

        net.add_node(
            node,
            label=node,
            title=tooltip,
            color={
                "background": cor,
                "border":     "#ffffff",
                "highlight":  {"background": "#ffffff", "border": cor},
                "hover":      {"background": "#ffffff", "border": cor},
            },
            size=tamanho,
            font={"color": "#ffffff", "size": 13},
        )

    # 5. Adiciona arestas
    max_peso = max((d.get("weight", 1) for _, _, d in G.edges(data=True)), default=1)

    for u, v, data in G.edges(data=True):
        peso    = data.get("weight", 1)
        espess  = 1 + (peso / max_peso) * 6   # espessura 1-7
        tooltip = f"Co-ocorrências: {peso} TCC(s)"

        net.add_edge(
            u, v,
            value=espess,
            title=tooltip,
            color={"color": "rgba(255,255,255,0.25)", "highlight": "#ffffff"},
        )

    # 6. Injeta cabeçalho HTML customizado e salva
    net.write_html(str(OUTPUT_PATH))

    # Adiciona título e legenda diretamente no HTML gerado
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    cabecalho = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
      body { margin: 0; font-family: 'Inter', sans-serif; background: #0f0f1a; }
      #titulo {
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #f0f0f0; padding: 12px 24px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 2px 20px rgba(0,0,0,0.5);
      }
      #titulo h1 { margin: 0; font-size: 18px; font-weight: 700; color: #74B9FF; }
      #titulo p  { margin: 0; font-size: 12px; color: #b2bec3; }
      #legenda {
        position: fixed; bottom: 20px; left: 20px; z-index: 999;
        background: rgba(15,15,26,0.9); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; padding: 12px 16px; color: #f0f0f0;
        font-size: 12px; line-height: 1.8; backdrop-filter: blur(10px);
      }
      #legenda b { font-size: 13px; color: #74B9FF; }
      .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
      #mynetwork { margin-top: 56px !important; }
    </style>
    <div id="titulo">
      <div>
        <h1>🎓 ThesisMiner — Grafo de Co-ocorrência de Áreas Temáticas</h1>
        <p>TCCs de Engenharia de Computação · UFRN · Algoritmos e Estrutura de Dados</p>
      </div>
      <p style="color:#b2bec3; font-size:12px;">Nó maior = área mais frequente &nbsp;|&nbsp; Aresta mais grossa = mais co-ocorrências</p>
    </div>
    <div id="legenda">
      <b>Legenda de Cores</b><br>
      <span class="dot" style="background:#FF6B6B"></span>Machine Learning / IA<br>
      <span class="dot" style="background:#FF9F43"></span>Ciência de Dados<br>
      <span class="dot" style="background:#48DBFB"></span>IoT / Embarcados<br>
      <span class="dot" style="background:#1DD1A1"></span>Redes de Computadores<br>
      <span class="dot" style="background:#74B9FF"></span>Cloud / Dist.<br>
      <span class="dot" style="background:#6C5CE7"></span>Banco de Dados / Grafos<br>
      <span class="dot" style="background:#FD79A8"></span>Astronomia / Ciências<br>
      <span class="dot" style="background:#E17055"></span>Sistemas de Recomendação<br>
    </div>
    """

    html = html.replace("<body>", f"<body>\n{cabecalho}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[✓] Visualização salva em: {OUTPUT_PATH}")
    print(f"\n    Abra o arquivo no navegador:")
    # Converte caminho WSL para Windows se aplicável
    path_abs = OUTPUT_PATH.resolve()
    wsl_win  = str(path_abs).replace("/home/", "\\\\wsl$\\Ubuntu\\home\\")
    print(f"    Linux : file://{path_abs}")
    print(f"    Windows (WSL): {wsl_win}")


if __name__ == "__main__":
    main()
