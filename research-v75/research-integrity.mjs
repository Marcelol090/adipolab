export function validateRegistry(r){
if(!r||r.version!==144||r.scope!=="research_integrity_only"||r.clinicalValidation!=="not_established"||r.personalDataIncluded!==false||r.modelTrained!==false||r.rawDataImported!==false||r.certaintyAssessed!==false)return false;
if(!Array.isArray(r.sources)||!Array.isArray(r.reasons)||!Array.isArray(r.unresolved)||!Array.isArray(r.stages))return false;
const unique=(a,key)=>a.every(x=>x&&typeof x[key]==="string"&&x[key].trim())&&new Set(a.map(x=>x[key])).size===a.length;
if(!unique(r.sources,"id")||!unique(r.sources,"url")||!unique(r.reasons,"code")||!unique(r.unresolved,"id")||!unique(r.stages,"id"))return false;
if(r.sources.length!==7||r.sources.some(x=>x.rawImported!==false||x.access!=="indexed_metadata_and_excerpts"||typeof x.limit!=="string"||!x.limit.trim()||!/^https:\/\/[a-z0-9.-]+\//i.test(x.url)))return false;
const reasonSet=new Set(r.reasons.map(x=>x.code));
if(r.unresolved.some(x=>x.resolved!==false||!reasonSet.has(x.reason)||typeof x.detail!=="string"||!x.detail.trim()))return false;
return r.stages.length===6&&r.stages[0].id==="discovery"&&r.stages[0].status==="completed_for_methodology_sources"&&r.stages.slice(1).every(x=>x.status==="not_completed"&&x.evidence===null)
}
