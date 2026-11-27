"""Read-only structural review of an archived HTML guide. Never exports diets or targets."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from html.parser import HTMLParser

class Sections(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections=set()
    def handle_starttag(self, tag, attrs):
        if tag=="section":
            self.sections.add(dict(attrs).get("id",""))

def inspect(raw):
    text=raw.decode("utf-8-sig")
    parser=Sections()
    parser.feed(text)
    identifiers=set(re.findall(r"\b(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)",text))
    block=re.search(r"\bconst\s+CYCLES_DATA\s*=([\s\S]*?)(?=\n\s*(?:const|let|var|function)\s+|</script>)",text)
    cycles=sorted(set(int(n) for n in re.findall(r"(?<![\w])c([0-9])\s*:\s*\{",block.group(1),re.I))) if block else []
    refs=set(re.findall(r"https?://(?:pubmed\.ncbi\.nlm\.nih\.gov|pmc\.ncbi\.nlm\.nih\.gov|doi\.org)/[^\s\"'<>]+",text,re.I))
    return {"schema":"adipolab.nutrition-source-review.v1","source_sha256":hashlib.sha256(raw).hexdigest(),"scope":"structural source inspection only","meal_structure_present":"MEALS" in identifiers,"energy_calculation_present":"calcTargets" in identifiers,"diet_view_present":"view-dieta" in parser.sections,"cycle_data_present":block is not None,"explicit_cycle_ids":["C"+str(n) for n in cycles],"direct_scientific_identifier_links":len(refs),"clinical_validation":False,"nutritional_adequacy_verified":False,"current_encrypted_version_verified":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("guide",type=Path);ap.add_argument("output",type=Path)
    a=ap.parse_args()
    if a.guide.stat().st_size>5_000_000:raise ValueError("Source exceeds review limit")
    result=inspect(a.guide.read_bytes())
    with a.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=="__main__":main()
