"""
02_extractor.py
Converts raw PDFs into clean plain text files.
Uses PyMuPDF to extract text while automatically removing the References section to prevent noise.
"""

import os
import re
import pymupdf  # fitz
from pathlib import Path

# Config de caminhos
RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    """Limpa o texto bruto extraído do PDF, removendo ruídos comuns."""
    if not text:
        return ""

    # 1. REMOVER REFERÊNCIAS — corta tudo após a seção de referências
    ref_pattern = re.compile(
        r'\n\s*(?:REFERÊNCIAS|REFERÊNCIAS BIBLIOGRÁFICAS).*',
        re.IGNORECASE | re.DOTALL
    )
    match = ref_pattern.search(text)
    if match:
        text = text[:match.start()]

    # 2. REMOVER PRÉ-TEXTUAIS — corta tudo antes da Introdução real
    # Usa a ÚLTIMA ocorrência (ignora a entrada do sumário)
    intro_pattern = re.compile(
        r'\n(?:1\s+)?INTRODUÇÃO(?!\s*[\.\s]{5,})', re.IGNORECASE
    )
    matches = list(intro_pattern.finditer(text))
    if matches:
        text = text[matches[-1].start():]

    # 3. FIX HYPHENATION — Engenha-\nria → Engenharia
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 4. REMOVER LINHAS DE SUMÁRIO COM RETICÊNCIAS
    text = re.sub(r'.*?\. \. \. \. .*?\n', '', text)

    # 5. REMOVER NÚMEROS DE PÁGINA ISOLADOS
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # 6. NORMALIZAÇÃO DE ESPAÇOS
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        
        # --- A MÁGICA ACONTECE AQUI ---
        cleaned_text = clean_text(text)
        return cleaned_text
        # ------------------------------

    except Exception as e:
        print(f"  [!] Error reading {pdf_path.name}: {e}")
        return None

def main():
    pdf_files = list(RAW_DIR.glob("*.pdf"))
    print(f"[+] Found {len(pdf_files)} PDFs in {RAW_DIR}")

    for i, pdf_path in enumerate(pdf_files, 1):
        txt_filename = pdf_path.stem + ".txt"
        output_path = INTERIM_DIR / txt_filename

        print(f"  [{i}/{len(pdf_files)}] Extracting & Cleaning: {pdf_path.name}...")
        
        # Agora o raw_text já vem limpo pela função interna
        processed_text = extract_text_from_pdf(pdf_path)
        
        if processed_text:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(processed_text)
            print(f"  [v] Saved clean text to: {output_path}")
        else:
            print(f"  [X] Failed to extract text from {pdf_path.name}")

if __name__ == "__main__":
    main()