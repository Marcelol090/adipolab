import unittest
from audit_nutrition_source import inspect
class TestSourceReview(unittest.TestCase):
    def test_structural_only(self):
        src=b'<section id="view-dieta"></section><script>\nconst MEALS={secret:"synthetic private text"};\nfunction calcTargets(){}\nconst CYCLES_DATA={c0:{},c2:{}};\nfunction next(){}\n</script>'
        r=inspect(src)
        self.assertTrue(r["meal_structure_present"])
        self.assertTrue(r["energy_calculation_present"])
        self.assertEqual(r["explicit_cycle_ids"],["C0","C2"])
        self.assertNotIn("synthetic private text",str(r))
        self.assertFalse(r["clinical_validation"])
    def test_absent_not_validated(self):
        r=inspect(b"<html>empty</html>")
        self.assertEqual(r["explicit_cycle_ids"],[])
        self.assertFalse(r["cycle_data_present"])
        self.assertFalse(r["nutritional_adequacy_verified"])
    def test_labels_do_not_establish_cycle_structure(self):
        r=inspect(b'<div>Ciclo 0</div><div>CICLO 9</div><div>Ciclo 9</div><div>Ciclo 10</div>')
        self.assertEqual(r["cycle_label_markers"],["C0","C9"])
        self.assertEqual(r["explicit_cycle_ids"],[])
        self.assertFalse(r["cycle_data_present"])
        self.assertFalse(r["nutritional_adequacy_verified"])
    def test_source_link_is_not_validation(self):
        r=inspect(b'<a href="https://doi.org/10.1234/example">link</a>')
        self.assertEqual(r["direct_scientific_identifier_links"],1)
        self.assertFalse(r["clinical_validation"])
if __name__=="__main__":unittest.main()
