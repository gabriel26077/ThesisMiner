"""
06_visualizer.py

Constrói uma UI interativa, responsiva e muito bonita (Glassmorphism + Dark Mode)
para exibição do Grafo Temático de todos os anos e global.
Injeta os dados diretamente no HTML para funcionar offline via duplo-clique (file://).
"""

import json
from pathlib import Path
import networkx as nx
import random

GRAPH_DIR = Path("data/graphs")

def generate_color(seed_str: str) -> str:
    random.seed(seed_str)
    # HSL color gen for vibrant nodes
    return f"hsl({random.randint(0, 360)}, 85%, 65%)"

def main():
    print(f"\n{'='*60}")
    print("  Gerando UI Premium Interativa — ThesisMiner")
    print(f"{'='*60}\n")

    grafos = sorted(GRAPH_DIR.glob("area_cooccurrence_*.gml"))
    
    # Vamos criar um grande dicionário de dados injetáveis no HTML
    dados_por_ano = {}
    
    for gml in grafos:
        cenario = gml.stem.split("_")[-1] # 2019, 2025, global
        G = nx.read_gml(gml)
        
        freq_path = GRAPH_DIR / f"area_frequency_{cenario}.json"
        freq_map = {}
        if freq_path.exists():
            with open(freq_path, encoding="utf-8") as f:
                freq_map = {d["area"]: d["frequencia"] for d in json.load(f)}

        nodes = []
        for n in G.nodes():
            freq = freq_map.get(n, 1)
            nodes.append({
                "id": n,
                "label": n.replace(" / ", "\n"),
                "value": freq,
                "title": f"<b>{n}</b><br>Quantidade: {freq} TCCs",
                "color": {"background": generate_color(n), "border": "#ffffff"},
                "font": {"color": "#eeeeee"}
            })

        edges = []
        for u, v in G.edges():
            w = G[u][v].get("weight", 1)
            edges.append({
                "from": u,
                "to": v,
                "value": w,
                "title": f"Co-ocorrência: {w}",
                "color": {"color": "rgba(255,255,255,0.2)", "highlight": "#ffcc00"}
            })
            
        dados_por_ano[cenario] = {"nodes": nodes, "edges": edges}

    # Gera HTML Premium
    html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>ThesisMiner Mapeamento de Tópicos (AI)</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body, html {
            height: 100%;
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at 10% 20%, #1a1a2e 0%, #0d0d1a 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #fff;
            overflow: hidden;
        }

        #mynetwork {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }

        .glass-panel {
            position: absolute;
            top: 30px;
            left: 30px;
            z-index: 10;
            background: rgba(20, 20, 35, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            width: 320px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        }

        h1 {
            margin: 0 0 10px 0;
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: -webkit-linear-gradient(45deg, #FF6B6B, #48DBFB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        h2 {
            font-size: 13px;
            color: #a0a0b5;
            margin: 0 0 20px 0;
            font-weight: 400;
            line-height: 1.5;
        }

        select {
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.2);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 15px;
            outline: none;
            transition: 0.3s;
            cursor: pointer;
        }

        select:focus {
            border-color: #48DBFB;
            box-shadow: 0 0 10px rgba(72, 219, 251, 0.3);
        }

        option {
            background:#1a1a2e;
            color:#fff;
        }

        .stats {
            margin-top: 20px;
            font-size: 13px;
            color: #dcdcdc;
            line-height: 1.6;
        }

        .badge {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-right: 5px;
            border: 1px solid rgba(255,255,255,0.05);
        }
    </style>
</head>
<body>

    <div class="glass-panel">
        <h1>ThesisMiner</h1>
        <h2>IA Não-Supervisionada (NMF) de TCCs de Eng. Computação.</h2>
        
        <label for="anoSelect" style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color:#888;">Escopo Temático</label>
        <select id="anoSelect" onchange="renderGraph()">
            <option value="global" selected>Visão Global (Todos os anos)</option>
            <!-- SERÃO INJETADOS AUTOMATICAMENTE -->
            %%OPCOES_HTML%%
        </select>

        <div class="stats" id="statsPanel">
            <!-- stats injetado JS -->
        </div>
        
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        // Inject database via Python
        const GRAPH_DB = %%INJECT_JSON%%;

        let network = null;

        function renderGraph() {
            const select = document.getElementById("anoSelect");
            const cenario = select.value;
            const data = GRAPH_DB[cenario];
            
            if(!data) return;

            const container = document.getElementById("mynetwork");
            
            // Stats Update
            const nodesCount = data.nodes.length;
            const edgesCount = data.edges.length;
            document.getElementById("statsPanel").innerHTML = `
                <div><span class="badge">Nós</span> ${nodesCount} Tópicos descobertos</div>
                <div style="margin-top:8px"><span class="badge">Arestas</span> ${edgesCount} co-ocorrências</div>
            `;

            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: {
                        min: 15,
                        max: 60,
                        label: { min: 11, max: 22, drawThreshold: 5, maxVisible: 40 }
                    },
                    font: { size: 14, face: 'Tahoma', strokeWidth: 2, strokeColor: '#1a1a2e' },
                    borderWidth: 2,
                    borderWidthSelected: 4
                },
                edges: {
                    width: 1,
                    hoverWidth: 3,
                    selectionWidth: 3,
                    smooth: { type: 'continuous' }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 100,
                    zoomView: true
                },
                physics: {
                    forceAtlas2Based: {
                        gravitationalConstant: -120,
                        centralGravity: 0.015,
                        springLength: 200,
                        springConstant: 0.04
                    },
                    maxVelocity: 50,
                    solver: 'forceAtlas2Based',
                    timestep: 0.4,
                    stabilization: { iterations: 150 }
                }
            };

            const visData = {
                nodes: new vis.DataSet(data.nodes),
                edges: new vis.DataSet(data.edges)
            };

            if (network !== null) {
                network.destroy();
            }
            network = new vis.Network(container, visData, options);
        }

        // Run initially
        window.onload = () => {
            renderGraph();
        };

    </script>
</body>
</html>
"""

    opcoes_html = ""
    for cenario in sorted(dados_por_ano.keys()):
        if cenario != "global":
            opcoes_html += f'<option value="{cenario}">Ano {cenario}</option>\n'

    html_final = html_template.replace("%%INJECT_JSON%%", json.dumps(dados_por_ano))
    html_final = html_final.replace("%%OPCOES_HTML%%", opcoes_html)

    out_path = GRAPH_DIR / "visualizacao_novo.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"[✓] Dashboard hiper-moderno gerado!")
    print(f"    Rode no navegador: file://{out_path.resolve()}")

if __name__ == "__main__":
    main()
