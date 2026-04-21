"""
02_section_extractor.py

Extrai apenas as seções de RESUMO e CONCLUSÃO de cada PDF de TCC.
Salva os resultados como arquivos JSON estruturados em data/interim/.

Estratégia:
  - RESUMO: localizado entre a palavra "RESUMO" e a próxima seção
    (ABSTRACT, palavras-chave, introdução, ou lista de figuras).
  - CONCLUSÃO: localizado entre "CONCLUS" e "REFERÊNCIAS" (ou fim do doc).
  - Ambas as seções são limpas de ruídos comuns (cabeçalhos, hifenização, etc).
"""

import re
import json
import pymupdf  # fitz
from pathlib import Path

# ── Configuração de caminhos ──────────────────────────────────────────────────
RAW_DIR    = Path("data/raw")
INTERIM_DIR = Path("data/interim")
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

# ── Padrões regex das seções ──────────────────────────────────────────────────
# Padrão de início de RESUMO (ignorar caixa)
_RESUMO_START = re.compile(
    r'\n\s*RESUMO\s*\n',
    re.IGNORECASE
)

# Padrão que sinaliza o FIM do resumo (próxima seção pré-textual)
_RESUMO_END = re.compile(
    r'\n\s*(?:ABSTRACT|PALAVRAS[- ]CHAVE|LISTA\s+DE|SUM[ÁA]RIO|'
    r'AGR[AE]DE[CS]IMENTOS?|1\s+INTRODU|INTRODU[CÇ][AÃ]O)\s*\n',
    re.IGNORECASE
)

# Padrão de início de CONCLUSÃO — aceita variações comuns em TCCs da UFRN:
#   "5 CONCLUSÃO", "5. Conclusão", "Conclusão e trabalhos futuros", etc.
_CONCLUSAO_START = re.compile(
    r'\n\s*(?:\d+[\s.]*)?CONCLUS[AÃÕ][OÕE][ES]?(?:\s+E\s+\w+(?:\s+\w+)*)?\.?\s*\n',
    re.IGNORECASE
)

# Padrão que sinaliza o FIM da conclusão
_CONCLUSAO_END = re.compile(
    r'\n\s*(?:REFERÊNCIAS|REFER[EÊ]NCIAS\s+BIBLIOGR[ÁA]FICAS|BIBLIOGRAFIA|APÊNDICE|ANEXO|AP[EÊ]NDICE)\s*\n',
    re.IGNORECASE
)


def _clean_section(text: str) -> str:
    """Aplica limpeza básica num trecho de texto extraído do PDF."""
    if not text:
        return ""

    # 1. Corrigir hifenização quebrada entre linhas (Engenha-\nria → Engenharia)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 2. Remover linhas que são apenas números (números de página)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # 3. Remover linhas de sumário com reticências (ex: "Contextualização . . . 13")
    text = re.sub(r'^.*?[\.]{3,}.*$', '', text, flags=re.MULTILINE)

    # 4. Colapsar múltiplas linhas em branco
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _extract_section(full_text: str, start_pattern: re.Pattern,
                     end_pattern: re.Pattern,
                     pick_last: bool = False) -> str:
    """
    Localiza a seção delimitada por start_pattern e end_pattern no texto.
    - pick_last: se True, usa a ÚLTIMA ocorrência do padrão de início
      (ignora entradas no sumário e pega o capítulo real).
    Retorna o conteúdo entre eles (já limpo), ou string vazia se não encontrar.
    """
    matches = list(start_pattern.finditer(full_text))
    if not matches:
        return ""

    start_match = matches[-1] if pick_last else matches[0]
    content_start = start_match.end()

    # Fim: próxima seção reconhecida, ou fim do documento
    end_match = end_pattern.search(full_text, content_start)
    content_end = end_match.start() if end_match else len(full_text)

    raw_section = full_text[content_start:content_end]
    return _clean_section(raw_section)


def extract_sections(pdf_path: Path) -> dict | None:
    """
    Extrai RESUMO e CONCLUSÃO de um PDF de TCC.
    Retorna um dicionário com as seções ou None em caso de falha.
    """
    full_text = ""
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                full_text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"  [!] Erro ao abrir {pdf_path.name}: {e}")
        return None

    if not full_text.strip():
        print(f"  [!] PDF sem texto extraível: {pdf_path.name}")
        return None

    # pick_last=True: ignora a ocorrência no sumário e pega o capítulo de fato
    resumo    = _extract_section(full_text, _RESUMO_START,    _RESUMO_END,    pick_last=False)
    conclusao = _extract_section(full_text, _CONCLUSAO_START, _CONCLUSAO_END, pick_last=True)

    # Aviso se alguma seção não foi localizada
    if not resumo:
        print(f"  [~] RESUMO não encontrado em: {pdf_path.name}")
    if not conclusao:
        print(f"  [~] CONCLUSÃO não encontrada em: {pdf_path.name}")

    year_match = re.search(r'tcc_(\d{4})_', pdf_path.name)
    year = year_match.group(1) if year_match else "unknown"

    return {
        "arquivo": pdf_path.name,
        "ano": year,
        "resumo": resumo,
        "conclusao": conclusao,
        "chars_resumo": len(resumo),
        "chars_conclusao": len(conclusao)
    }


def main():
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    print(f"[+] {len(pdf_files)} PDFs encontrados em '{RAW_DIR}'")

    if not pdf_files:
        print("[!] Nenhum PDF disponível. Execute o 01_scraper.py primeiro.")
        return

    resultados = []
    falhas = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n  [{i}/{len(pdf_files)}] Processando: {pdf_path.name}")
        secoes = extract_sections(pdf_path)

        if secoes:
            # Salva JSON individual por TCC
            out_path = INTERIM_DIR / f"{pdf_path.stem}_sections.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(secoes, f, ensure_ascii=False, indent=4)
            print(f"  [✓] Salvo → {out_path.name}  "
                  f"(resumo: {secoes['chars_resumo']} chars | "
                  f"conclusão: {secoes['chars_conclusao']} chars)")
            resultados.append(secoes)
        else:
            falhas.append(pdf_path.name)

    # Salva consolidado com todos os TCCs num único arquivo
    consolidado_path = INTERIM_DIR / "all_sections.json"
    with open(consolidado_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)

    print(f"\n{'='*60}")
    print(f"[✓] Processamento concluído!")
    print(f"    Sucesso : {len(resultados)} arquivo(s)")
    print(f"    Falhas  : {len(falhas)} arquivo(s)  → {falhas}")
    print(f"    Consolidado salvo em: {consolidado_path}")


if __name__ == "__main__":
    main()
