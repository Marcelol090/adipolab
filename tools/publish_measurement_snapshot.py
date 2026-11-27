"""Regenerate public measurement provenance only from a fully checked local cache."""
import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from refresh_measurement_provenance import SCHEMA, SOURCES, verify_mapping, verify_crossref, verify_pubmed, atomic_write

def blob(cache,digest):
    if not isinstance(digest,str) or not re.fullmatch("[a-f0-9]{64}",digest):
        raise ValueError("Invalid hash")
    b=(cache/"blobs"/(digest+".blob")).read_bytes()
    if hashlib.sha256(b).hexdigest()!=digest:raise ValueError("Cache hash mismatch")
    return b

def render(cache):
    latest=json.loads((cache/"latest_attempt.json").read_text(encoding="utf-8"))
    if latest.get("schema")!=SCHEMA or latest.get("status")!="complete" or latest.get("clinical_validation") is not False:
        raise ValueError("Latest attempt is incomplete; do not publish a new snapshot")
    when=datetime.fromisoformat(latest["retrieved_at"])
    if when.tzinfo is None or when>datetime.now(timezone.utc):raise ValueError("Invalid retrieval date")
    mapping=verify_mapping(blob(cache,latest["idconv_sha256"]))
    pubmed=verify_pubmed(blob(cache,latest["pubmed_sha256"]))
    source_rows=latest["sources"]
    if len(source_rows)!=len(SOURCES) or {r["pmcid"] for r in source_rows}!=set(SOURCES):
        raise ValueError("Source coverage mismatch")
    rows=[]
    for r in sorted(source_rows,key=lambda x:x["pmcid"]):
        m=mapping[r["pmcid"]]
        if any(r.get(k)!=v for k,v in m.items()) or r["status"]!="metadata_checked":
            raise ValueError("Source crosswalk mismatch")
        cr=verify_crossref(blob(cache,r["sha256"]),m["doi"])
        pm=pubmed[m["pmid"]]
        if cr!=r["editorial_links"] or pm!=r["pubmed_editorial_links"] or bool(cr or pm)!=r["editorial_review_required"]:
            raise ValueError("Editorial flags disagree with source blobs")
        msg="Revisão editorial necessária; referência não utilizável como evidência positiva." if cr or pm else "Nenhum alerta nos campos editoriais examinados; não equivale a ausência de retratação."
        rows.append(f'<dt><a href="https://pubmed.ncbi.nlm.nih.gov/{m["pmid"]}/" rel="noreferrer">{m["pmcid"]}</a></dt><dd>DOI: {html.escape(m["doi"])} · {msg}</dd>')
    date=when.astimezone(timezone.utc).strftime("%d/%m/%Y, %H:%M UTC")
    return ('<section class="section" id="measurement-provenance"><h2>Proveniência das fontes de mensuração</h2><p>3/3 referências conferidas pelo PMC ID Converter, Crossref e PubMed. Última consulta completa: <time datetime="'+html.escape(when.isoformat())+'">'+date+'</time>. Registro estático; não sincroniza automaticamente.</p><dl>'+''.join(rows)+'</dl><p class="muted">Verificação bibliográfica limitada a três estudos. Não substitui auditoria integral de retratações, avaliação de risco de viés ou validação clínica.</p></section>')

def update(cache,page):
    original=page.read_text(encoding="utf-8")
    pattern=r'<section class="section"(?: id="measurement-provenance")?><h2>Proveniência das fontes de mensuração</h2>.*?</section>'
    output,n=re.subn(pattern,lambda _:render(cache),original,flags=re.S)
    if n!=1:raise ValueError("Expected one provenance section")
    atomic_write(page,output.encode("utf-8"))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("cache",type=Path)
    p.add_argument("page",type=Path)
    a=p.parse_args()
    update(a.cache,a.page)
    print("Verified snapshot published in local HTML; raw cache not included.")
