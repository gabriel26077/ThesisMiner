"""
04_graph_builder.py
Constructs co-occurrence networks (graphs) from the extracted NER features.
Applies distance metrics (sentence, paragraph, and k-characters) using NetworkX and exports the final graphs for analysis.
"""

import json
import itertools
import networkx as nx
from pathlib import Path

# Configuration
PROCESSED_BASE_DIR = Path("data/processed")
GRAPH_OUTPUT_DIR = Path("data/graphs")
GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Experiment Scenarios and Variants defined in Step 03
SCENARIOS = ["3_pdfs", "6_pdfs", "9_pdfs", "12_pdfs"]
VARIANTS = ["sentence", "paragraph", "window_k500", "window_k1000", "window_k1500"]

def build_graph(scenario, variant):
    """Reads NER JSON files and builds a NetworkX graph based on co-occurrence."""
    G = nx.Graph()
    input_dir = PROCESSED_BASE_DIR / scenario / variant
    
    if not input_dir.exists():
        print(f"  [!] Directory not found: {input_dir}")
        return None

    json_files = list(input_dir.glob("*.json"))
    print(f"  [*] Building graph for {scenario}/{variant} ({len(json_files)} files)...")

    for json_path in json_files:
        with open(json_path, "r", encoding="utf-8") as f:
            # entities is a list of {"text": "...", "label": "..."}
            entities = json.load(f)
        
        # Extract unique entity names to avoid self-loops and overcounting in the same segment
        # In a real co-occurrence graph, we look at entities appearing TOGETHER
        # Strategy: Each file represents a set of segments processed in Step 03
        entity_names = [ent["text"] for ent in entities if len(ent["text"]) > 2]
        
        # Add nodes with labels as attributes
        for ent in entities:
            if ent["text"] not in G:
                G.add_node(ent["text"], label=ent["label"])

        # Create co-occurrence edges (Combinations of 2)
        # Note: Step 03 already split the data into segments. 
        # For a more granular graph, Step 03 should have saved entities PER SEGMENT.
        # Assuming current JSONs are per-document:
        combinations = itertools.combinations(set(entity_names), 2)
        
        for u, v in combinations:
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)

    return G

def main():
    report = []

    for scenario in SCENARIOS:
        for variant in VARIANTS:
            graph = build_graph(scenario, variant)
            
            if graph:
                # Calculate basic graph metrics for the performance report
                num_nodes = graph.number_of_nodes()
                num_edges = graph.number_of_edges()
                density = nx.density(graph)

                # Save Graph in GML format (best for Gephi)
                output_name = f"graph_{scenario}_{variant}.gml"
                nx.write_gml(graph, GRAPH_OUTPUT_DIR / output_name)
                
                report.append({
                    "scenario": scenario,
                    "variant": variant,
                    "nodes": num_nodes,
                    "edges": num_edges,
                    "density": round(density, 5)
                })

    # Save summary report
    with open("graph_metrics_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\n--- Graph Construction Complete ---")
    for r in report:
        print(f"Scenario: {r['scenario']} | Variant: {r['variant']} | Nodes: {r['nodes']} | Edges: {r['edges']}")

if __name__ == "__main__":
    main()