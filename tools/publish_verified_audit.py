"""Publish aggregate audit data only after verifying the recovered archive."""
import argparse
import csv
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from export_evidence_summary import export_summary,file_sha256
from refresh_measurement_provenance import atomic_write

def checked_file(directory,manifest,name):
    h=manifest.get("hashes",{}).get(name)
    f=directory/name
    if not isinstance(h,str) or not re.fullmatch("[a-f0-9]{64}",h) or file_sha256(f)!=h:
        raise ValueError("Hash mismatch: "+name)
    return f

def build(v190,v170):
    m=json.loads((v190/"v190_manifest.json").read_text(encoding="utf-8"))
    old=json.loads((v170/"v170_manifest.json").read_text(encoding="utf-8"))
    if old["version"]!="v170":raise ValueError("Wrong registry archive")
    names=("evidence_v190.sqlite","measurement_audit.json","safety_audit.json","safety_reporting.csv")
    for n in names:checked_file(v190,m,n)
    links=checked_file(v170,old,"all_registry_references.csv")
    db=v190/names[0]
    out=export_summary(db,v190/"v190_manifest.json")
    with links.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    keys={(r["nct"],r["pmid"],r["reference_type"]) for r in rows}
    with closing(sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True)) as c:
        pmids={r[0] for r in c.execute("SELECT pmid FROM publication")}
        if len(keys)!=len(rows) or len(rows)!=out["registry_links_total"] or sum(r["pmid"] in pmids for r in rows)!=out["registry_links_resolved"] or len({r["pmid"] for r in rows})!=m["registry_unique_pmids"]:
            raise ValueError("Registry links disagree")
        audit={n:json.loads(r) for n,r in c.execute("SELECT name,report FROM audit_summary")}
        for n in ("measurement","safety"):
            if audit[n]!=json.loads((v190/(n+"_audit.json")).read_text(encoding="utf-8")):raise ValueError("Audit report mismatch")
        apis=dict(c.execute("SELECT status,COUNT(*) FROM api GROUP BY status"))
    if set(apis)-{"pass","failed"}:raise ValueError("Unknown API status")
    a,b=audit["measurement"],audit["safety"]
    if not all(a["checks"].values()) or a["r2_issues"] or b["issues"]:raise ValueError("Unresolved archive audit issues")
    if sum(a["paired_by_measure"].values())!=a["paired_aggregate_cells"]:raise ValueError("Measurement aggregate mismatch")
    sc=b["counts"]
    if sc["deaths_complete"]+sc["deaths_incomplete"]!=sc["groups"]:raise ValueError("Safety group mismatch")
    if file_sha256(db)!=m["hashes"][names[0]]:raise ValueError("Archive changed")
    return {"summary":out,"verified_manifest_files":len(names),"verified_registry_csv":True,"registry_unique_pmids":m["registry_unique_pmids"],"measurement_aggregate_comparisons":a["paired_aggregate_cells"],"measurement_strata":a["strata_region_sex_blocks"],"safety_studies":sc["studies"],"safety_groups":sc["groups"],"safety_event_stats":sc["event_stats"],"mortality_reporting_incomplete_groups":sc["deaths_incomplete"],"historical_api_pass":apis.get("pass",0),"historical_api_failed":apis.get("failed",0),"clinical_validation":False}

def render(data):
    x=data["summary"]
    fmt=lambda n:f"{n:,}".replace(",",".")
    return (
        '<section class="section" id="verified-audit"><h2>Arquivo científico recuperado e conferido</h2>'
        '<p>Resumo público derivado do arquivo v190 recuperado, conferido contra seu manifesto original e o CSV bibliográfico v170. A verificação é documental, não clínica.</p>'
        f'<p><strong>{data["verified_manifest_files"]}/4</strong> hashes v190 conferidos · <strong>{fmt(data["registry_unique_pmids"])}</strong> PMIDs distintos nos vínculos · <strong>{fmt(x["registry_links_resolved"])}/{fmt(x["registry_links_total"])}</strong> vínculos resolvidos.</p>'
        f'<p>{data["measurement_aggregate_comparisons"]} comparações agregadas em {data["measurement_strata"]} estratos; {data["safety_studies"]} estudos com resultados, {data["safety_groups"]} grupos, {fmt(data["safety_event_stats"])} registros estatísticos de eventos. {data["mortality_reporting_incomplete_groups"]} grupos sem informação completa de óbitos.</p>'
        f'<p>Auditoria histórica de fontes: {data["historical_api_pass"]} verificações aprovadas e {data["historical_api_failed"]} falha; inclui consulta de snapshot local. Não indica disponibilidade atual das APIs.</p>'
        '<p class="muted">O banco completo fica no dispositivo. Apenas os totais agregados são publicados. Não existe validação clínica nem sincronização automática em tempo real.</p></section>'
    )

def publish(v190,v170,page):
    data=build(v190,v170)
    original=page.read_text(encoding="utf-8")
    old=re.compile(r'<section class="section" id="verified-audit">.*?</section>',re.S)
    if old.search(original):
        output,n=old.subn(lambda _:render(data),original)
        if n!=1:raise ValueError("Duplicate snapshot")
    else:
        anchor='<section class="section"><h2>Estado da integração</h2>'
        if original.count(anchor)!=1:raise ValueError("Missing integration anchor")
        output=original.replace(anchor,render(data)+anchor)
    before='O resumo histórico da v190 não é sincronizado automaticamente. A auditoria integral depende do arquivo SQLite e do manifesto originais.'
    after='O arquivo SQLite e o manifesto originais foram recuperados e verificados. A publicação utiliza uma exportação agregada reproduzível, sem sincronização automática.'
    output=output.replace(before,after)
    x=data["summary"]
    fmt=lambda n:f"{n:,}".replace(",",".")
    metrics={"publications":fmt(x["publication_count"]),"quarantine":fmt(x["quarantine_count"]),"links":fmt(x["registry_links_resolved"])+"/"+fmt(x["registry_links_total"]),"checks":fmt(x["checks_passed"])+"/"+fmt(x["checks_total"])}
    for key,value in metrics.items():
        output,n=re.subn(r'(<strong data-metric="'+key+r'">).*?(</strong>)',lambda m:m[1]+value+m[2],output,flags=re.S)
        if n!=1:raise ValueError("Missing or duplicated metric")
    output,n=re.subn(r'(<p[^>]*id="snapshot-status"[^>]*>).*?(</p>)',lambda m:m[1]+"Resumo v190 conferido na publicação a partir do arquivo original recuperado; não sincronizado automaticamente. Não representa estudos independentes nem benefício clínico."+m[2],output,flags=re.S)
    if n!=1:raise ValueError("Missing or duplicated status")
    atomic_write(page,output.encode("utf-8"))
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("v190",type=Path);p.add_argument("v170",type=Path);p.add_argument("page",type=Path)
    a=p.parse_args()
    print(json.dumps(publish(a.v190,a.v170,a.page),ensure_ascii=True))
