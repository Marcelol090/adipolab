import json,tempfile,unittest
from pathlib import Path
from refresh_measurement_provenance import refresh
from test_measurement_provenance import mock_fetch,xml_fixture
from publish_measurement_snapshot import render,update

class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.cache=Path(self.temp.name)
        self.r=refresh(self.cache,mock_fetch)
        self.page=self.cache/"evidence.html"
        self.original='<html><section class="section"><h2>Proveniência das fontes de mensuração</h2>OLD</section></html>'
        self.page.write_text(self.original,encoding="utf-8")
    def tearDown(self):
        self.temp.cleanup()
    def test_valid_and_idempotent(self):
        update(self.cache,self.page)
        first=self.page.read_bytes()
        update(self.cache,self.page)
        self.assertEqual(first,self.page.read_bytes())
        self.assertIn("3/3",first.decode())
        self.assertNotIn("OLD",first.decode())
    def test_hash_mismatch_leaves_page_unchanged(self):
        (self.cache/"blobs"/(self.r["pubmed_sha256"]+".blob")).write_bytes(b"changed")
        with self.assertRaises(ValueError):update(self.cache,self.page)
        self.assertEqual(self.page.read_text(encoding="utf-8"),self.original)
    def test_incomplete_leaves_page_unchanged(self):
        def fail(url):
            if "efetch.fcgi" in url:raise TimeoutError()
            return mock_fetch(url)
        refresh(self.cache,fail)
        with self.assertRaises(ValueError):update(self.cache,self.page)
        self.assertEqual(self.page.read_text(encoding="utf-8"),self.original)
    def test_editorial_review_displayed(self):
        def flagged(url):
            return xml_fixture("RetractionIn") if "efetch.fcgi" in url else mock_fetch(url)
        refresh(self.cache,flagged)
        self.assertEqual(render(self.cache).count("Revisão editorial necessária"),3)
    def test_manifest_falsified(self):
        p=self.cache/"latest_attempt.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        r["sources"][0]["editorial_review_required"]=True
        p.write_text(json.dumps(r),encoding="utf-8")
        with self.assertRaises(ValueError):render(self.cache)

if __name__=="__main__":unittest.main()
