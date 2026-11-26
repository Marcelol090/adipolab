import {identify,groupSources} from "./integrity.mjs";
import {audit} from "./model.mjs";
import {validateManifest,verifyRecord} from "./snapshot.mjs";
import {validateRegistry as validateReview} from "./review.mjs";
import {validateRegistry as validateIntegrity} from "./research-integrity.mjs";
import {validateRegistry as validatePopulation} from "./population-methods.mjs";
import {checkRegistry} from "./lab.mjs";
import {auditBibliography} from "./bibliographic-audit.mjs";
import {readFileSync} from "node:fs";
export const FILES=Object.freeze(["catalog.json","quality-sources.json","integrity-registry.json","provenance-registry.json","population-methods.json","research-integrity.json","bibliographic-audit.json","review-registry.json","cycles.json","quality-results.json","synthetic-results.json","snapshot-v144.json"]);
export function loadRecords(){return Object.fromEntries(FILES.map(f=>[f,JSON.parse(readFileSync(new URL("./"+f,import.meta.url),"utf8"))]))}
const sameId=(a,b)=>{const x=identify(a),y=identify(b);return !!x&&!!y&&x.kind===y.kind&&x.key===y.key};
export function inspect(d){
 const cat=d["catalog.json"],q=d["quality-sources.json"],i=d["integrity-registry.json"],p=d["provenance-registry.json"],pop=d["population-methods.json"],ri=d["research-integrity.json"],b=d["bibliographic-audit.json"],r=d["review-registry.json"],c=d["cycles.json"];
 const primary=[...cat.records,...q.sources,...p.sources,...pop.studies,...ri.sources];
 const groups=groupSources(primary), duplicates=groups.filter(g=>g.records.length>1),known=new Set([...cat.records,...q.sources].map(x=>x.id));
 const byId=new Map(primary.map(x=>[x.id,x]));
 const checks={
 catalog:audit(cat.records).length===0,
 referenceIds:byId.size===primary.length,
 integrityLinks:i.records.length===known.size&&new Set(i.records.map(x=>x.id)).size===known.size&&i.records.every(x=>known.has(x.id)&&sameId(x.url,byId.get(x.id).url)&&x.rawImported===false&&x.clinicalValidated===false),
 review:validateReview(r,known),
 population:validatePopulation(pop),
 bibliography:auditBibliography(b,cat.records)&&b.audits.every(x=>sameId(x.url,byId.get(x.id).url)),
 integrity:validateIntegrity(ri),
 cycleRegistry:checkRegistry(c),
 cycleConsistency:c.cycles.length===r.cycles.length&&c.cycles.every((x,j)=>x.id===r.cycles[j].cycle&&["title","criterion","gap","status"].every(k=>x[k]===r.cycles[j][k])),
 unresolvedConsistency:ri.unresolved.map(x=>x.id).sort().join(",")===b.audits.filter(x=>x.identity==="indexed_only").map(x=>x.id).sort().join(","),
 syntheticLabels:d["quality-results.json"].synthetic===true&&d["synthetic-results.json"].synthetic===true,
 missingNotZero:d["quality-results.json"].allMissing.mean===null,
 noClinicalClaims:cat.records.every(x=>x.microdata==="not_imported"&&x.clinicalValidation==="not_established")&&q.sources.every(x=>x.rawImported===false&&x.clinicalValidated===false)&&p.humanRawData==="not_imported"&&p.clinicalValidation==="not_established"&&i.rawImported===false&&i.clinicalVerdict==="not_established"&&r.microdataImported===false&&r.verdict==="not_established"&&pop.clinicalVerdict==="not_established"&&ri.clinicalValidation==="not_established"&&c.clinicalVerdict==="not_established",
 manifest:validateManifest(d["snapshot-v144.json"])
 };
 return {primaryRecords:primary.length,distinctPrimaryIdentifiers:groups.length,duplicates,cycleCount:c.cycles.length,openCycles:c.cycles.filter(x=>x.status==="open").length,checks,limitations:["Primary identifier groups do not resolve all cross-database aliases or cohort overlap.","Metadata consistency is not scientific reproducibility.","No individual clinical validation, biological model training or raw human data import established."]};
}
export function checkSnapshot(d){return d["snapshot-v144.json"].records.every(r=>verifyRecord(r,readFileSync(new URL("./"+r.file,import.meta.url))))}
