import argparse, tempfile, shutil, json
from pathlib import Path
from publish_verified_audit import build,publish

def run(v190,v170,template):
    with tempfile.TemporaryDirectory() as t:
        root=Path(t); a=root/"v190"; b=root/"v170"
        a.mkdir();b.mkdir()
        for n in ("v190_manifest.json","evidence_v190.sqlite","measurement_audit.json","safety_audit.json","safety_reporting.csv"):
            shutil.copy2(v190/n,a/n)
        for n in ("v170_manifest.json","all_registry_references.csv"):
            shutil.copy2(v170/n,b/n)
        page=root/"evidence.html";shutil.copy2(template,page)
        x=publish(a,b,page);first=page.read_bytes()
        assert x["summary"]["publication_count"]==1409
        assert x["summary"]["quarantine_count"]==3
        assert x["summary"]["registry_links_resolved"]==1042
        assert x["clinical_validation"] is False
        assert publish(a,b,page)==x and page.read_bytes()==first
        for f in (a/"measurement_audit.json",b/"all_registry_references.csv",a/"evidence_v190.sqlite"):
            original=f.read_bytes()
            try:
                f.write_bytes(original+b"tamper")
                try:publish(a,b,page)
                except ValueError:pass
                else:raise AssertionError("Tamper accepted")
                assert page.read_bytes()==first
            finally:f.write_bytes(original)
        print("PASS real archive, publication idempotence, 3 tamper cases, unchanged page on failure")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("v190",type=Path);p.add_argument("v170",type=Path);p.add_argument("template",type=Path)
    a=p.parse_args();run(a.v190,a.v170,a.template)
