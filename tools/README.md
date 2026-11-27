# Evidence summary integration

The evidence page defaults to historical v190 audit counts, explicitly labelled as not synchronized. To use the actual SQLite archive, run locally:

```powershell
python tools/export_evidence_summary.py PATH_TO/evidence_v190.sqlite PATH_TO/v190_manifest.json evidence-summary.json
```

Then select the resulting JSON in the evidence page. The exporter opens the database read-only and requires the matching SHA-256 in the v190 manifest and a closed, checkpointed database snapshot; it refuses a mismatched manifest, invalid clinical status or inconsistent counts. The browser validates the allowed schema and reads the file locally; it does not authenticate its origin. The SHA-256 check verifies consistency with the supplied manifest, not an independent signature. It never uploads the file or stores it permanently. Do not commit private databases, participant records, or passwords.

Tests (synthetic fixtures only):
```
python tools/test_export_evidence_summary.py
node tools/test_evidence_data.cjs
```

The underlying encrypted prototype remains unchanged. Neither the exporter nor the page establishes clinical efficacy, safety or individualized predictions.

Browser regression test (requires Playwright and a local Chromium or Chrome):

    python tools/test_evidence_browser.py

Checks four viewport widths in light and dark mode, synthetic imports, rejection, reset, overflow, and absence of external requests or storage writes.


Measurement-source metadata refresh (three fixed public studies; no personal information):

    python tools/refresh_measurement_provenance.py PATH_TO_LOCAL_CACHE

The output distinguishes complete, partial and failed retrievals. Raw responses are stored locally by SHA-256; latest_attempt.json records the newest attempt and last_complete.json preserves the most recent complete result. A missing editorial link in Crossref is not proof that a publication has no editorial warning. This module does not replace the full v190 retraction audit or establish clinical validation. Do not commit the cache.

Regression tests:

    python tools/test_measurement_provenance.py
