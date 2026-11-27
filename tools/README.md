# Evidence summary integration

The evidence page defaults to historical v190 audit counts, explicitly labelled as not synchronized. To use the actual SQLite archive, run locally:

```powershell
python tools/export_evidence_summary.py PATH_TO/evidence_v190.sqlite PATH_TO/v190_manifest.json evidence-summary.json
```

Then select the resulting JSON in the evidence page. The exporter opens the database read-only and refuses a mismatched manifest, invalid clinical status or inconsistent counts. The browser validates the allowed schema and reads the file locally; it does not authenticate its origin. It never uploads the file or stores it permanently. Do not commit private databases, participant records, or passwords.

Tests (synthetic fixtures only):
```
python tools/test_export_evidence_summary.py
node tools/test_evidence_data.cjs
```

The underlying encrypted prototype remains unchanged. Neither the exporter nor the page establishes clinical efficacy, safety or individualized predictions.
