import hashlib
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from refresh_measurement_provenance import SOURCES, EXPECTED_PMIDS, refresh, verify_mapping, verify_crossref, verify_pubmed, fetch

def encode(x):return json.dumps(x).encode()
def mapping():
    return {"status":"ok","records":[{"pmcid":k,"pmid":EXPECTED_PMIDS[k],"doi":v} for i,(k,v) in enumerate(SOURCES.items())]}
def xml_fixture(flag=""):
    articles=[]
    for pmc,doi in SOURCES.items():
        pmid=EXPECTED_PMIDS[pmc]
        links=f'<CommentsCorrectionsList><CommentsCorrections RefType="{flag}"/></CommentsCorrectionsList>' if flag else ""
        articles.append(f'<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID>{links}</MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">{doi}</ArticleId></ArticleIdList></PubmedData></PubmedArticle>')
    return ("<PubmedArticleSet>"+"".join(articles)+"</PubmedArticleSet>").encode()
def mock_fetch(url):
    if "efetch.fcgi" in url:return xml_fixture()
    if "idconv" in url:return encode(mapping())
    doi=url.split("/works/",1)[1]
    return encode({"status":"ok","message":{"DOI":doi,"update-to":[]}})
class Tests(unittest.TestCase):
    def test_mapping(self):self.assertEqual(set(verify_mapping(encode(mapping()))),set(SOURCES))
    def test_mismatch(self):
        m=mapping();m["records"][0]["doi"]="10.1234/wrong"
        with self.assertRaises(ValueError):verify_mapping(encode(m))
    def test_missing(self):
        m=mapping();m["records"].pop()
        with self.assertRaises(ValueError):verify_mapping(encode(m))
    def test_duplicate(self):
        m=mapping();m["records"].append(m["records"][0])
        with self.assertRaises(ValueError):verify_mapping(encode(m))
    def test_editorial_flags(self):
        self.assertEqual(verify_crossref(encode({"status":"ok","message":{"DOI":"10.1234/a","update-to":[{"type":"retraction"}]}}),"10.1234/a"),["retraction"])
    def test_crossref_mismatch(self):
        with self.assertRaises(ValueError):verify_crossref(encode({"status":"ok","message":{"DOI":"10.1234/b"}}),"10.1234/a")
    def test_complete_then_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);first=refresh(p,mock_fetch);self.assertEqual(first["status"],"complete")
            snapshot=(p/"last_complete.json").read_bytes()
            def fail_some(url):
                if "10.1017/" in url:raise TimeoutError()
                return mock_fetch(url)
            second=refresh(p,fail_some);self.assertEqual(second["status"],"partial")
            self.assertEqual((p/"last_complete.json").read_bytes(),snapshot)
            self.assertEqual(json.loads((p/"latest_attempt.json").read_bytes())["status"],"partial")
            for h in [first["idconv_sha256"],first["pubmed_sha256"]]+[r["sha256"] for r in first["sources"]]:
                self.assertEqual(hashlib.sha256((p/"blobs"/(h+".blob")).read_bytes()).hexdigest(),h)
    def test_failed_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            def fail(url):raise TimeoutError()
            self.assertEqual(refresh(p,fail)["status"],"failed")
            self.assertFalse((p/"last_complete.json").exists())
    def test_pubmed_flags(self):
        self.assertEqual(set(verify_pubmed(xml_fixture("RetractionIn"))),set(EXPECTED_PMIDS.values()))
        self.assertTrue(all(x==["RetractionIn"] for x in verify_pubmed(xml_fixture("RetractionIn")).values()))
    def test_pubmed_missing(self):
        with self.assertRaises(ValueError):verify_pubmed(b"<PubmedArticleSet/>")
    def test_pubmed_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fail(url):
                if "efetch.fcgi" in url:raise TimeoutError()
                return mock_fetch(url)
            r=refresh(Path(tmp),fail)
            self.assertEqual(r["status"],"partial")
            self.assertTrue(all(x["editorial_review_required"] for x in r["sources"]))
    def test_pubmed_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            def flagged(url):
                return xml_fixture("RetractionIn") if "efetch.fcgi" in url else mock_fetch(url)
            r=refresh(Path(tmp),flagged)
            self.assertEqual(r["status"],"complete")
            self.assertTrue(all(x["editorial_review_required"] for x in r["sources"]))
    def test_retry(self):
        calls=[];delays=[]
        def opener(request,timeout):
            calls.append(request)
            raise urllib.error.URLError("synthetic")
        with self.assertRaises(urllib.error.URLError):fetch("https://example.org",opener,delays.append)
        self.assertEqual(len(calls),3);self.assertEqual(delays,[1,2])
if __name__=="__main__":unittest.main()
