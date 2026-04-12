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

def clean_text(text):
    return text

    
    
    if not text:
        return ""

    # 1. REMOVER REFERÊNCIAS (Preservamos essa parte que funciona bem)
    ref_pattern = re.compile(r'\n\s*(?:REFERÊNCIAS|REFERÊNCIAS BIBLIOGRÁFICAS).*\n', re.IGNORECASE | re.DOTALL)
    match = ref_pattern.search(text)
    if match:
        text = text[:match.start()]

    # 2. LIMPEZA DE LINHAS DE SUMÁRIO (O pulo do gato)
    # Remove qualquer linha que tenha sequências de pontos (característica de sumário/listas)
    # Isso limpa o sumário sem precisar saber onde ele termina.
    text = re.sub(r'.*?[\.\s]{5,}\d+.*?\n', '', text)

    # 3. REMOVER CABEÇALHOS/RODAPÉS COMUNS
    # Remove linhas que são apenas números isolados (prováveis números de página do PDF)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # 4. FIX HYPHENATION (Engenha-\nria -> Engenharia)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 5. REMOVER ELEMENTOS PRÉ-TEXTUAIS GENÉRICOS
    # Se ainda houver muita "sujeira" inicial, podemos cortar as primeiras ~2000 caracteres
    # mas só se encontrarmos a Introdução de forma segura depois.
    intro_match = list(re.finditer(r'\n(?:1\s+)?INTRODUÇÃO', text, re.IGNORECASE))
    if intro_match:
        # Pegamos a ÚLTIMA ocorrência de Introdução que sobrou após limpar os pontos do sumário
        text = text[intro_match[-1].start():]

    # 6. NORMALIZAÇÃO DE ESPAÇOS
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()
    
    
    if not text:
        return ""

    # 1. REMOVER REFERÊNCIAS (Corta o final)
    ref_pattern = re.compile(r'\n\s*(?:REFERÊNCIAS|REFERÊNCIAS BIBLIOGRÁFICAS).*\n', re.IGNORECASE | re.DOTALL)
    match = ref_pattern.search(text)
    if match:
        text = text[:match.start()]

    # 2. REMOVER PRÉ-TEXTUAIS (Corta o início)
    # Procuramos pela INTRODUÇÃO que NÃO tenha os pontinhos de sumário (. . . .)
    # E que esteja preferencialmente no início de uma linha
    # O [^.\n]{2,} garante que não há uma sequência de pontos logo após a palavra
    intro_pattern = re.compile(r'\n(?:1\s+)?INTRODUÇÃO(?!\s*[\.\s]{5,})', re.IGNORECASE)
    
    # Pegamos todas as ocorrências e escolhemos a última (que geralmente é o capítulo real)
    matches = list(intro_pattern.finditer(text))
    if matches:
        last_match = matches[-1]
        text = text[last_match.start():]

    # 3. FIX HYPHENATION (Engenha-\nria -> Engenharia)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 4. REMOVER LINHAS DE SUMÁRIO RESIDUAIS
    # Remove linhas que só tenham títulos e números de página (ex: "Contextualização . . . 13")
    text = re.sub(r'.*?\. \. \. \. .*?\n', '', text)

    # 5. LIMPEZA FINAL
    text = re.sub(r'\n\s*\n', '\n', text)
    
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