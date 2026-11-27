export const METHODS=[
  {
    "method": "tape",
    "label": "Fita métrica",
    "supports": [
      "circumference"
    ],
    "limit": "Perímetro não separa tecidos."
  },
  {
    "method": "photo",
    "label": "Fotografia convencional",
    "supports": [
      "appearance"
    ],
    "limit": "Contorno qualitativo; não confirma quantidade adiposa ou genótipo."
  },
  {
    "method": "scale",
    "label": "Balança",
    "supports": [
      "total_mass"
    ],
    "limit": "Massa total não informa composição."
  },
  {
    "method": "dxa",
    "label": "DXA",
    "supports": [
      "fat_mass_estimate"
    ],
    "limit": "Estimativa de composição, não identificação automática de tecido subcutâneo."
  },
  {
    "method": "clinical_mri",
    "label": "Ressonância com protocolo clínico",
    "supports": [
      "adipose_tissue_volume"
    ],
    "limit": "Depende de segmentação, adequação e avaliação profissional."
  },
  {
    "method": "clinical_ultrasound",
    "label": "Ultrassonografia clínica",
    "supports": [
      "local_tissue_thickness"
    ],
    "limit": "Espessura em ponto de exame não equivale a volume regional."
  },
  {
    "method": "genetic_report",
    "label": "Laudo genético",
    "supports": [
      "reported_genotype"
    ],
    "limit": "Interpretação profissional; não prediz isoladamente distribuição corporal."
  }
];
export function evidenceRole(method,outcome){const m=METHODS.find(x=>x.method===method);return m&&m.supports.includes(outcome)?"method_compatible_not_validated":"not_supported"}
export function provenanceStatus(r){if(!r||typeof r!=="object")return "missing";if(r.origin==="synthetic")return "synthetic_only";if(r.origin==="estimated")return "estimate_only";if(r.origin==="historical_report")return "historical_unverified";if(r.origin!=="clinical_report"||typeof r.date!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(r.date)||r.reviewed!==true)return "unverified";const d=new Date(r.date+"T00:00:00Z");if(!Number.isFinite(d.getTime())||d.toISOString().slice(0,10)!==r.date)return "unverified";return "documented_not_independently_validated"}
export function reviewStatus(r){if(!r||typeof r!=="object")return "unverified";return r.identityConfirmed===true&&r.populationReported===true&&r.methodReported===true&&r.limitationsReported===true?"metadata_reviewable":"unverified"}
