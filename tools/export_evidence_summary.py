"""Export only aggregate audit counts, never publication contents or participant data."""
import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

def export_summary(db: Path, manifest: Path):
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if m.get("version") != "v190":
        raise ValueError("Expected v190 manifest")
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as c:
        if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        count, quarantine = c.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN quarantine=1 THEN 1 ELSE 0 END),0) FROM publication").fetchone()
        if c.execute("SELECT COUNT(*) FROM publication WHERE quarantine IS NULL OR quarantine NOT IN (0,1) OR clinically_validated IS NULL OR clinically_validated != 0").fetchone()[0]:
            raise ValueError("Unexpected publication status")
    if count != m["publication_count"] or quarantine != m["quarantine_count"]:
        raise ValueError("Database and manifest disagree")
    checks = m["checks"]
    if not isinstance(checks, dict) or not checks or any(type(v) is not bool for v in checks.values()):
        raise ValueError("Invalid checks")
    result = {"schema":"adipolab.audit-summary.v1","audit_version":"v190","publication_count":count,"quarantine_count":quarantine,"registry_links_resolved":m["registry_links_resolved"],"registry_links_total":m["registry_links_total"],"checks_passed":sum(checks.values()),"checks_total":len(checks)}
    if any(type(v) is not int or not 0 <= v <= 10000000 for v in list(result.values())[2:]) or result["registry_links_resolved"] > result["registry_links_total"]:
        raise ValueError("Invalid aggregate totals")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("database",type=Path)
    p.add_argument("manifest",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    result=export_summary(args.database,args.manifest)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print("Aggregate audit summary exported (no private records).")

if __name__ == "__main__":
    main()
