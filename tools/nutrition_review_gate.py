"""Document unresolved nutrition evidence; does not calculate diets or weight goals."""
def review_status(report):
    if not isinstance(report,dict) or report.get("schema")!="adipolab.nutrition-source-review.v2":
        raise ValueError("Unsupported source review")
    allowed={"C"+str(i) for i in range(10)}
    for k in ("explicit_cycle_ids","cycle_label_markers"):
        values=report.get(k)
        if not isinstance(values,list) or any(not isinstance(v,str) or v not in allowed for v in values) or len(values)!=len(set(values)):
            raise ValueError("Invalid cycle markers")
    if any(report.get(k) is not False for k in ("clinical_validation","nutritional_adequacy_verified","current_encrypted_version_verified")):
        raise ValueError("Structural reports cannot certify clinical or nutrition validity")
    return [{"cycle":"C"+str(i),"document_status":"structure_marker" if "C"+str(i) in report["explicit_cycle_ids"] else "label_only" if "C"+str(i) in report["cycle_label_markers"] else "not_identified","nutrition_status":"not_assessed","clinical_validation":False} for i in range(10)]
