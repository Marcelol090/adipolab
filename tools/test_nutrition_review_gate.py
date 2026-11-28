import unittest
from audit_nutrition_source import inspect
from nutrition_review_gate import review_status
class TestGate(unittest.TestCase):
    def test_labels_never_validate(self):
        r=inspect(b"<div>Ciclo 9</div>")
        result=review_status(r)
        self.assertEqual(result[-1]["document_status"],"label_only")
        self.assertTrue(all(x["nutrition_status"]=="not_assessed" and not x["clinical_validation"] for x in result))
    def test_reject_forged_validation(self):
        r=inspect(b"<div>Ciclo 0</div>")
        for key in ["clinical_validation","nutritional_adequacy_verified","current_encrypted_version_verified"]:
            with self.assertRaises(ValueError):review_status(dict(r,**{key:True}))
    def test_invalid_cycle(self):
        r=inspect(b"<div>Ciclo 0</div>")
        r["cycle_label_markers"].append("C10")
        with self.assertRaises(ValueError):review_status(r)
if __name__=="__main__":unittest.main()
