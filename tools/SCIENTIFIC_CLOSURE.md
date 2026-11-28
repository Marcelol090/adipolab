# Scientific closure ledger — v194–v200

This ledger records verification scope, not a validated intervention or individual prediction. The nine-cycle protocol remains clinically unvalidated. The work below does not recommend or optimize intentional extreme weight gain.

| Domain | Current decision | Evidence required before changing the decision |
| --- | --- | --- |
| Publication and cohort independence | Not established at catalogue scale | Original study IDs and documented cohort links; shared participants require independent adjudication. A DOI or PMID is a publication identifier, not an independent cohort. |
| Supplement integrity | Partial historical verification only | Original supplements, version and source URLs, matching file hashes, completeness checks and traceable extraction. |
| Risk of bias | Not assessed formally | Outcome-specific assessments by independent qualified reviewers; unresolved disagreements documented. |
| Missing data | Historical incompleteness documented | Original denominators, missingness by outcome and time point, reasons for exclusions, and auditable checks. Missing observations must never be imputed as zero by default. |
| External model validity | Not demonstrated | Independently collected representative data, prespecified validation endpoints, calibration and uncertainty assessment, independent clinical and ethics review. |
| Observational provenance | Partial historical verification only | Source versions, dates, units, population eligibility, transformation history and independently reproducible aggregate counts. |
| Reproducibility | Partial | Original v170/v190 archives and matching manifest hashes; independent execution of archive checks. Synthetic tests cannot establish biological or clinical validity. |

## Verified remote controls

- Commit 07851a2: [complete control](https://github.com/Marcelol090/adipolab/actions/runs/46095485888) and [partial control](https://github.com/Marcelol090/adipolab/actions/runs/46095481766), with one Europe PMC timeout.
- Commit 6d4c34c: [retry workflow](https://github.com/Marcelol090/adipolab/actions/runs/46096003285) and [second execution](https://github.com/Marcelol090/adipolab/actions/runs/46095999770) completed successfully.
- Commit f8e0863: [remote validation](https://github.com/Marcelol090/adipolab/actions/runs/46096013724) completed successfully.
- New evidence integrity workflow runs synthetic export and provenance tests plus public evidence browser regression. It does not access the original local archive, private engine, or personal records. Its results must be checked for the actual commit.
- Do not treat missing data, bibliographic coverage, CI success or any of these ledger entries as clinical efficacy or safety.

The source archive is not available in the current remote audit. Do not publish new aggregate values without reproducing them from verified inputs. Keep private materials off GitHub.
