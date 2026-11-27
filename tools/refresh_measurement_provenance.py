"""Public bibliographic integrity checks, not a clinical prediction or intervention engine."""
import argparse
import hashlib
import json
import os
import re
import time
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
    "PMC13086945": "10.1038/s43856-026-01440-w",
    "PMC12171921": "10.1017/s1368980025000291",
    "PMC3953447": "10.1371/journal.pone.0091586",
}
BASE = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
SCHEMA = "adipolab.measurement-provenance.v1"
MAX_BYTES = 1024 * 1024

def stamp():
    return datetime.now(timezone.utc).isoformat()

def fetch(url, opener=urllib.request.urlopen, sleeper=time.sleep):
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"AdipoLab measurement provenance audit","Accept":"application/json"})
            with opener(request,timeout=10) as response:
                content=response.read(MAX_BYTES+1)
            if len(content)>MAX_BYTES:raise ValueError("Response exceeds limit")
            return content
        except urllib.error.HTTPError as error:
            if error.code not in (429,500,502,503,504) or attempt==2:raise
            delay=error.headers.get("Retry-After","")
            if delay.isdigit() and int(delay)>10:raise
            sleeper(max(1,int(delay)) if delay.isdigit() else 2**attempt)
        except (urllib.error.URLError,TimeoutError):
            if attempt==2:raise
            sleeper(2**attempt)

def norm(doi):
    return str(doi or "").strip().lower().removeprefix("https://doi.org/")

def verify_mapping(raw):
    obj=json.loads(raw)
    if obj.get("status")!="ok":raise ValueError("ID converter status not OK")
    out={}
    for r in obj.get("records",[]):
        pmc=r.get("pmcid")
        if pmc not in SOURCES or pmc in out:raise ValueError("Unexpected or duplicate PMCID")
        pmid=str(r.get("pmid",""))
        doi=norm(r.get("doi"))
        if not re.fullmatch(r"[1-9][0-9]*",pmid) or not re.fullmatch(r"10\.[0-9]{4,9}/[^\s]+",doi):raise ValueError("Incomplete crosswalk")
        expected=SOURCES[pmc]
        if expected is not None and doi!=expected:raise ValueError("DOI mismatch")
        out[pmc]={"pmcid":pmc,"pmid":pmid,"doi":doi}
    if set(out)!=set(SOURCES):raise ValueError("Incomplete source coverage")
    return out

def verify_crossref(raw, doi):
    obj=json.loads(raw)
    if obj.get("status")!="ok":raise ValueError("Crossref status not OK")
    msg=obj.get("message",{})
    if norm(msg.get("DOI"))!=doi:raise ValueError("Crossref DOI mismatch")
    updates=msg.get("update-to",[])
    if not isinstance(updates,list) or any(not isinstance(x,dict) for x in updates):raise ValueError("Invalid update list")
    relation=msg.get("relation",{})
    if not isinstance(relation,dict):raise ValueError("Invalid relation object")
    flags=[str(x.get("type","unknown")) for x in updates]
    for k,v in relation.items():
        if v and any(a in k.lower() for a in ("retract","concern","withdraw","correct","update")):flags.append(k)
    return sorted(set(flags))

def atomic_write(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
        tmp=Path(f.name)
        f.write(content)
    try:os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)

def store_blob(cache, content):
    digest=hashlib.sha256(content).hexdigest()
    path=cache/"blobs"/(digest+".json")
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        atomic_write(path,content)
    return digest

def run(cache, fetcher=fetch):
    cache.mkdir(parents=True,exist_ok=True)
    summary={"schema":SCHEMA,"retrieved_at":stamp(),"sources":[],"clinical_validation":False,"scope":"identifier and Crossref metadata checks only"}
    try:
        import urllib.parse
        u=BASE+"?"+urllib.parse.urlencode({"ids":",".join(SOURCES),"format":"json"})
        raw=fetcher(u);mapping=verify_mapping(raw)
        summary["idconv_sha256"]=store_blob(cache,raw)
    except Exception as e:
        summary["status"]="failed";summary["error"]=type(e).__name__
        return summary
    for pmc,m in mapping.items():
        r={**m,"status":"unverified"}
        try:
            u="https://api.crossref.org/works/"+urllib.parse.quote(m["doi"],safe="/")
            raw=fetcher(u);flags=verify_crossref(raw,m["doi"])
            r.update(status="metadata_checked",editorial_links=flags,sha256=store_blob(cache,raw))
        except Exception as e:r["error"]=type(e).__name__
        summary["sources"].append(r)
    summary["status"]="complete" if all(r["status"]=="metadata_checked" for r in summary["sources"]) else "partial"
    return summary

def refresh(cache, fetcher=fetch):
    result=run(cache,fetcher)
    atomic_write(cache/"latest_attempt.json",json.dumps(result,indent=2).encode())
    if result["status"]=="complete":
        atomic_write(cache/"last_complete.json",json.dumps(result,indent=2).encode())
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache",type=Path)
    args=parser.parse_args()
    result=refresh(args.cache)
    print(json.dumps(result,ensure_ascii=True))
    return 0 if result["status"]=="complete" else 1

if __name__=="__main__":raise SystemExit(main())
