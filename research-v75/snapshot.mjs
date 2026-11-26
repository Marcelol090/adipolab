import {createHash} from "node:crypto";
export const ROLES=Object.freeze({
  "catalog.json": "bibliographic_metadata",
  "bibliographic-audit.json": "bibliographic_review",
  "cycles.json": "research_plan",
  "integrity-registry.json": "identifier_metadata",
  "population-methods.json": "methodology_metadata",
  "provenance-registry.json": "methodology_metadata",
  "quality-results.json": "synthetic_results",
  "quality-sources.json": "methodology_metadata",
  "research-integrity.json": "research_integrity_metadata",
  "review-registry.json": "review_metadata",
  "synthetic-results.json": "synthetic_results"
});
export function gitBlobSha1(bytes){if(!Buffer.isBuffer(bytes))throw new TypeError("Buffer required");return createHash("sha1").update("blob "+bytes.length+"\0").update(bytes).digest("hex")}
export function validateManifest(m){if(!m||m.version!==145||m.scope!=="public research records only"||m.clinicalValidation!=="not_established"||m.personalDataIncluded!==false||typeof m.baselineCommit!=="string"||!/^[0-9a-f]{40}$/.test(m.baselineCommit)||!Array.isArray(m.records)||m.records.length!==Object.keys(ROLES).length)return false;const seen=new Set();for(const r of m.records){if(!r||typeof r.file!=="string"||!Object.hasOwn(ROLES,r.file)||seen.has(r.file)||r.role!==ROLES[r.file]||typeof r.gitBlobSha1!=="string"||!/^[0-9a-f]{40}$/.test(r.gitBlobSha1)||!Number.isSafeInteger(r.bytes)||r.bytes<=0)return false;seen.add(r.file)}return true}
export function verifyRecord(r,bytes){return Buffer.isBuffer(bytes)&&bytes.length===r.bytes&&gitBlobSha1(bytes)===r.gitBlobSha1}
