"""
09_plot_histogram.py

Gera DOIS histogramas (gráfico de barras empilhadas) demonstrando a evolução
dos tópicos descobertos pela IA ao longo dos anos:
1. Absoluto (Mostra o total bruto gerado em cada ano)
2. Proporcional (Normaliza em 100% para entendermos as tendências independente do volume de alunos)
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import random
from pathlib import Path

GRAPH_DIR = Path("data/graphs")
PNG_DIR = GRAPH_DIR / "png"
PNG_DIR.mkdir(parents=True, exist_ok=True)

BG_COLOR = "#0d0d1a"
TEXT_COLOR = "#f0f0f0"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": TEXT_COLOR,
    "axes.facecolor": BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "axes.edgecolor": "#444444",
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
})

def generate_color(seed_str: str) -> str:
    random.seed(seed_str)
    return f"#{random.randint(50, 255):02x}{random.randint(50, 255):02x}{random.randint(50, 255):02x}"

def criar_grafico(anos, freq_matrix, areas_ordenadas, out_name, title, ylabel, proporcional=False):
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_title(title, fontsize=15, color=TEXT_COLOR, pad=20, fontweight="bold")

    bottom = np.zeros(len(anos))
    
    # Calcular totais por ano se for proporcional
    totais = np.zeros(len(anos))
    if proporcional:
        for area in areas_ordenadas:
            totais += np.array(freq_matrix[area])
        totais[totais == 0] = 1 # Evitar divisao por zero

    for area in areas_ordenadas:
        frequencias = np.array(freq_matrix[area])
        if proporcional:
            frequencias = (frequencias / totais) * 100

        cor = generate_color(area)
        ax.bar(anos, frequencias, bottom=bottom, label=area, color=cor, edgecolor=BG_COLOR, linewidth=1.5)
        bottom += frequencias

    ax.set_ylabel(ylabel, fontsize=12, labelpad=10)
    ax.set_xlabel("Ano de Lançamento do TCC", fontsize=12, labelpad=10)
    
    ax.yaxis.grid(True, linestyle="--", alpha=0.15, color="#ffffff")
    ax.set_axisbelow(True)
    
    # Adicionando um limite superior de 100 se for %
    if proporcional:
        ax.set_ylim(0, 100)
    
    handles, labels = ax.get_legend_handles_labels()
    short_labels = [l.replace(" / ", "\n") for l in labels]
    
    ax.legend(
        reversed(handles), reversed(short_labels),
        title="Tópicos NMF da Estatística", loc="center left", bbox_to_anchor=(1.02, 0.5),
        fontsize=9, title_fontsize=11,
        facecolor="#1a1a2e", edgecolor="#444", labelcolor=TEXT_COLOR
    )

    plt.tight_layout()
    out_path = PNG_DIR / out_name
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [✓] {out_path.name} gerado!")

def main():
    anos = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
    todas_areas = set()
    dados_por_ano = {}

    for ano in anos:
        path = GRAPH_DIR / f"area_frequency_{ano}.json"
        dados_por_ano[ano] = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                dados = json.load(f)
                for d in dados:
                    area = d["area"]
                    freq = d["frequencia"]
                    dados_por_ano[ano][area] = freq
                    todas_areas.add(area)

    if not todas_areas:
        return

    areas_ordenadas = sorted(list(todas_areas))
    freq_matrix = {area: [] for area in areas_ordenadas}
    
    for ano in anos:
        for area in areas_ordenadas:
            freq_matrix[area].append(dados_por_ano[ano].get(area, 0))

    print("\n[*] Gerando histogramas...")
    
    criar_grafico(anos, freq_matrix, areas_ordenadas, 
                  "histograma_absoluto.png",
                  "Mudança de Foco nos TCCs (2019 a 2025)\nEvolução Temática por Ano (Em Unidades Absolutas)",
                  "Quantidade de TCCs / Ocorrências", 
                  proporcional=False)
                  
    criar_grafico(anos, freq_matrix, areas_ordenadas, 
                  "histograma_proporcional.png",
                  "Comparativo Proporcional Temático (2019 a 2025)\nDistribuição de Foco Acadêmico Independentemente do Total de Alunos em 100%",
                  "Porcentagem de Distribuição Temática (%)", 
                  proporcional=True)

if __name__ == "__main__":
    main()
