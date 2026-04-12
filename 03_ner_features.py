"""
03_ner_features.py
Performs Named Entity Recognition (NER) across different segmentation strategies.
Compares performance (time and entity count) for 3 and 6 PDF scenarios.
"""

import json
import time
import spacy
from pathlib import Path

# Configuration
# Loading the 'Large' Portuguese model for better vector accuracy
NLP = spacy.load("pt_core_news_lg") 
INTERIM_DIR = Path("data/interim")
PROCESSED_BASE_DIR = Path("data/processed")

# Experiment Scenarios and Variants
SCENARIOS = {"3_pdfs": 3, "6_pdfs": 6, "9_pdfs":9, "12_pdfs":12}
VARIANTS = ["sentence", "paragraph", "window_k500", "window_k1000", "window_k1500"]

def get_segments(text, variant):
    """Divides text into segments based on the chosen strategy."""
    if variant == "sentence":
        # Uses spaCy's dependency parser to find sentence boundaries
        doc = NLP(text)
        return [sent.text for sent in doc.sents]
    
    elif variant == "paragraph":
        # Simple split by double newlines for paragraphs
        return [p.strip() for p in text.split('\n\n') if p.strip()]
    
    elif variant.startswith("window_k"):
        # Dynamic window size extraction (k500, k1000, etc.)
        try:
            k = int(variant.split('_k')[-1])
            return [text[i:i+k] for i in range(0, len(text), k)]
        except ValueError:
            return [text]
            
    return [text]

def run_experiment():
    performance_report = []
    txt_files = sorted(list(INTERIM_DIR.glob("*.txt")))

    if not txt_files:
        print("[!] No text files found in data/interim. Please run the PDF extraction first.")
        return

    for sc_name, limit in SCENARIOS.items():
        subset = txt_files[:limit]
        if len(subset) < limit:
            print(f"[!] Not enough files for scenario {sc_name}. Skipping.")
            continue

        print(f"\n>>> Starting Scenario: {sc_name} ({limit} files)")

        for variant in VARIANTS:
            # Organizing output by scenario and variant folders
            out_dir = PROCESSED_BASE_DIR / sc_name / variant
            out_dir.mkdir(parents=True, exist_ok=True)
            
            start_time = time.time()
            total_entities = 0

            for txt_path in subset:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                segments = get_segments(text, variant)
                document_data = []

                # Processing each segment for entities
                # We use nlp.pipe or disable unneeded components for speed
                for seg in segments:
                    # Disable parser and lemmatizer for faster NER during windowing
                    doc_seg = NLP(seg)
                    for ent in doc_seg.ents:
                        document_data.append({
                            "text": ent.text.strip(),
                            "label": ent.label_
                        })
                
                total_entities += len(document_data)
                
                # Save individual document features
                output_file = out_dir / f"{txt_path.stem}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(document_data, f, ensure_ascii=False, indent=4)

            elapsed = time.time() - start_time
            performance_report.append({
                "scenario": sc_name,
                "variant": variant,
                "total_time_sec": round(elapsed, 4),
                "entities_count": total_entities,
                "avg_time_per_file": round(elapsed / limit, 4)
            })
            print(f"  - Finished variant: {variant} in {elapsed:.2f}s")

    # Saving final comparison report
    report_path = "performance_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(performance_report, f, indent=4)
    
    print(f"\n[v] Experiment complete. Report saved to {report_path}")

if __name__ == "__main__":
    run_experiment()