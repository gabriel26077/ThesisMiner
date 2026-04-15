"""
01_scraper.py

Coleta metadados e PDFs dos TCCs de Engenharia de Computação da UFRN
usando a API REST do DSpace — sem necessidade de navegador (sem Selenium).

O repositório expõe o RESUMO diretamente via metadado `dc.description.resumo`,
então este script já salva o resumo em JSON junto com o link do PDF para download.

Saídas:
  - data/raw/*.pdf          → PDFs dos TCCs
  - data/interim/resumos.json → Resumos extraídos diretamente da API
"""

import os
import json
import time
import requests
from pathlib import Path

# ── Configuração ───────────────────────────────────────────────────────────────
COLLECTION_ID  = "a7202bae-5682-427c-b668-7289d877375b"
API_BASE       = "https://repositorio.ufrn.br/server/api"
SEARCH_URL     = f"{API_BASE}/discover/search/objects"
MAX_DOWNLOADS  = 15   # Número alvo de TCCs a baixar

RAW_DIR        = Path("data/raw")
INTERIM_DIR    = Path("data/interim")
RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "ThesisMiner/1.0 (UFRN - Algoritmos e Estrutura de Dados)",
    "Accept": "application/json",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_meta(metadata: dict, field: str) -> str:
    """Retorna o primeiro valor de um campo de metadado DSpace, ou string vazia."""
    entries = metadata.get(field, [])
    if entries:
        return entries[0].get("value", "").strip()
    return ""


def get_pdf_url(item_uuid: str) -> str | None:
    """
    Percorre bundles → bitstreams do item para achar o link direto de download do PDF.
    Retorna a URL de download ou None se não encontrar.
    """
    try:
        bundles_url = f"{API_BASE}/core/items/{item_uuid}/bundles"
        r = requests.get(bundles_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        bundles = r.json().get("_embedded", {}).get("bundles", [])

        for bundle in bundles:
            if bundle.get("name") != "ORIGINAL":
                continue
            bitstreams_url = bundle["_links"]["bitstreams"]["href"]
            r2 = requests.get(bitstreams_url, headers=HEADERS, timeout=20)
            r2.raise_for_status()
            bitstreams = r2.json().get("_embedded", {}).get("bitstreams", [])

            for bs in bitstreams:
                name = bs.get("name", "")
                if name.lower().endswith(".pdf"):
                    return bs["_links"]["content"]["href"]
    except Exception as e:
        print(f"    [!] Erro ao buscar PDF do item {item_uuid}: {e}")
    return None


def download_pdf(url: str, dest_path: Path) -> bool:
    """Faz o download de um PDF e salva em dest_path. Retorna True em sucesso."""
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"    [!] Erro no download: {e}")
        return False


# ── Pipeline principal ─────────────────────────────────────────────────────────

def main():
    print(f"[+] Iniciando coleta via API REST do DSpace — alvo: {MAX_DOWNLOADS} TCCs")

    resumos_coletados = []
    page = 0
    page_size = 20
    total_baixados = 0

    while total_baixados < MAX_DOWNLOADS:
        params = {
            "scope": COLLECTION_ID,
            "dsoType": "item",
            "page": page,
            "size": page_size,
        }
        print(f"\n[*] Buscando página {page} da API...")
        try:
            r = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[!] Erro na chamada à API: {e}")
            break

        objects = (data
                   .get("_embedded", {})
                   .get("searchResult", {})
                   .get("_embedded", {})
                   .get("objects", []))

        if not objects:
            print("[!] Sem mais resultados.")
            break

        for obj in objects:
            if total_baixados >= MAX_DOWNLOADS:
                break

            item = obj.get("_embedded", {}).get("indexableObject", {})
            uuid  = item.get("uuid", "")
            meta  = item.get("metadata", {})
            title = get_meta(meta, "dc.title")

            # Resumo já disponível na API — não precisa do PDF para isso!
            resumo   = get_meta(meta, "dc.description.resumo")
            abstract = get_meta(meta, "dc.description.abstract")
            subjects = [s["value"] for s in meta.get("dc.subject", [])]
            author   = get_meta(meta, "dc.contributor.author")
            year     = get_meta(meta, "dc.date.issued")[:4]

            print(f"\n  [{total_baixados + 1}] {title[:70]}...")
            print(f"      Autor: {author} | Ano: {year}")

            # -- Download do PDF --
            pdf_url = get_pdf_url(uuid)
            pdf_saved = False
            if pdf_url:
                safe_name = f"tcc_{str(total_baixados + 1).zfill(2)}_{uuid[:8]}.pdf"
                dest = RAW_DIR / safe_name
                if dest.exists():
                    print(f"      [~] PDF já existe, pulando download.")
                    pdf_saved = True
                else:
                    print(f"      [↓] Baixando PDF...")
                    pdf_saved = download_pdf(pdf_url, dest)
                    if pdf_saved:
                        print(f"      [✓] Salvo: {safe_name}")
                    time.sleep(1)  # cortesia ao servidor
            else:
                print("      [~] PDF não encontrado (acesso restrito ou sem bitstream).")

            # -- Salva metadados + resumo --
            resumos_coletados.append({
                "index": total_baixados + 1,
                "uuid": uuid,
                "titulo": title,
                "autor": author,
                "ano": year,
                "palavras_chave": subjects,
                "resumo": resumo,
                "abstract": abstract,
                "pdf_salvo": pdf_saved,
            })

            total_baixados += 1

        page += 1

    # Salva consolidado de resumos
    out_path = INTERIM_DIR / "resumos_api.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resumos_coletados, f, ensure_ascii=False, indent=4)

    print(f"\n{'='*60}")
    print(f"[✓] Coleta concluída!")
    print(f"    TCCs processados : {total_baixados}")
    print(f"    PDFs baixados    : {sum(1 for r in resumos_coletados if r['pdf_salvo'])}")
    print(f"    Resumos salvos   : {out_path}")


if __name__ == "__main__":
    main()
