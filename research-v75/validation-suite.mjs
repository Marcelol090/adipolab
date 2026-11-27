const count=v=>Number.isSafeInteger(v)&&v>=0;
const fraction=(a,b)=>b>0?100*a/b:null;
export function audit(r){
 if(!r||r.version!==162||r.scope!=="published_aggregate_measurement_quality"||r.rawDataImported!==false||r.personalDataIncluded!==false||r.physicalExperimentsPerformed!==false||r.clinicalValidation!=="not_established"||!Array.isArray(r.records)||r.records.length!==3||!Array.isArray(r.requirements)||r.requirements.length!==5)throw Error("invalid registry");
 const ids=new Set(r.records.map(x=>x.id));if(ids.size!==3||!["BIO01","CHEM01","PHYS01"].every(x=>ids.has(x)))throw Error("invalid record set");
 for(const x of r.records){if(!x.locator||!x.limitation||!/^https:\/\/[a-z0-9.-]+\//i.test(x.url)||!["full_text_section","indexed_full_text_excerpt","indexed_abstract"].includes(x.access)||!x.data)throw Error("missing evidence provenance")}
 const b=r.records.find(x=>x.id==="BIO01").data,c=r.records.find(x=>x.id==="CHEM01").data,p=r.records.find(x=>x.id==="PHYS01").data;
 if(![b.pairedSamples,b.additionalVisceralSamples,b.subcutaneousSamples,b.visceralSamples,b.totalSamples,b.subcutaneousNuclei,b.visceralNuclei,c.totalAnalytes,c.below20,c.above20,c.unavailable,p.equations,p.proportionalBias].every(count)||b.totalSamples===0||c.totalAnalytes===0||p.equations===0||!Number.isFinite(c.medianCV)||c.medianCV<0||typeof p.reportedIndividualAccuracy!=="boolean")throw Error("invalid measurement");
 if(new Set(r.requirements.map(x=>x.id)).size!==5||r.requirements.some(x=>!["not_available","not_performed"].includes(x.status)||!x.required))throw Error("unsupported readiness claim");
 const checks=[
 {id:"BIO01-A",domain:"biology",label:"Contagem de amostras por compartimento",pass:b.subcutaneousSamples+b.visceralSamples===b.totalSamples},
 {id:"BIO01-B",domain:"biology",label:"Coerência de amostras pareadas",pass:b.pairedSamples===b.subcutaneousSamples&&b.pairedSamples+b.additionalVisceralSamples===b.visceralSamples},
 {id:"CHEM01-A",domain:"chemistry",label:"Reconciliação do painel analítico",pass:c.below20+c.above20+c.unavailable===c.totalAnalytes},
 {id:"PHYS01-A",domain:"physiology",label:"Viés não excede o número de equações",pass:p.proportionalBias<=p.equations},
 {id:"PHYS01-B",domain:"physiology",label:"Conclusão de precisão individual preservada",pass:p.reportedIndividualAccuracy===false}
 ];
 return {version:162,scope:r.scope,checks,passed:checks.filter(x=>x.pass).length,total:checks.length,metrics:{tissueSamples:b.totalSamples,nuclei:b.subcutaneousNuclei+b.visceralNuclei,analytes:c.totalAnalytes,analytesMissing:c.unavailable,missingPercent:fraction(c.unavailable,c.totalAnalytes),below20AllPercent:fraction(c.below20,c.totalAnalytes),below20ObservedPercent:fraction(c.below20,c.totalAnalytes-c.unavailable),medianCV:c.medianCV,equations:p.equations,proportionalBiasPercent:fraction(p.proportionalBias,p.equations)},requirements:r.requirements,clinicalValidation:"not_established",physicalExperimentsPerformed:false};
}
