import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from export_evidence_summary import export_summary

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.db=p/"test.sqlite"
        self.manifest=p/"manifest.json"
        self.m={"version":"v190","publication_count":2,"quarantine_count":1,"registry_links_resolved":3,"registry_links_total":3,"checks":{"one":True,"two":False}}
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute("CREATE TABLE publication(quarantine INTEGER,clinically_validated INTEGER,title TEXT)")
            c.executemany("INSERT INTO publication VALUES(?,?,?)",[(0,0,"synthetic confidential title"),(1,0,"synthetic quarantined")])
        self.save()
    def save(self):self.manifest.write_text(json.dumps(self.m),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_export(self):
        x=export_summary(self.db,self.manifest)
        self.assertEqual((x["publication_count"],x["quarantine_count"],x["checks_passed"],x["checks_total"]),(2,1,1,2))
        self.assertNotIn("title",json.dumps(x))
        self.assertNotIn("confidential",json.dumps(x))
    def test_count_mismatch(self):
        self.m["publication_count"]=9;self.save()
        with self.assertRaises(ValueError):export_summary(self.db,self.manifest)
    def test_links_mismatch(self):
        self.m["registry_links_resolved"]=4;self.save()
        with self.assertRaises(ValueError):export_summary(self.db,self.manifest)
    def test_clinical_validation_flag(self):
        with closing(sqlite3.connect(self.db)) as c, c:c.execute("UPDATE publication SET clinically_validated=1")
        with self.assertRaises(ValueError):export_summary(self.db,self.manifest)
    def test_no_database_creation(self):
        p=self.db.with_name("absent.sqlite")
        with self.assertRaises(sqlite3.OperationalError):export_summary(p,self.manifest)
        self.assertFalse(p.exists())
    def test_manifest_version(self):
        self.m["version"]="v189";self.save()
        with self.assertRaises(ValueError):export_summary(self.db,self.manifest)
if __name__=="__main__":unittest.main()
