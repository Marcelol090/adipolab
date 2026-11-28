// Public methodological control only; not an intervention search or clinical validation.
import { createHash } from "node:crypto";
import { writeFile, mkdir, rename } from "node:fs/promises";
import { resolve } from "node:path";
const control={"pmid":"38626948","doi":"10.1136/bmj-2023-078378"};
function inspect(source,body){
 const norm=v=>typeof v==="string"?v.trim().toLowerCase().replace(/^https:\/\/doi\.org\//,""):"";
 const fail=()=>{throw new Error("Invalid or mismatched control metadata")};
 if(source==="crossref"){
  const m=body?.message;if(body?.status!=="ok"||norm(m?.DOI)!==control.doi)fail();
  if(m["update-to"]!==undefined&&!Array.isArray(m["update-to"]))fail();
  const updates=m["update-to"]??[];if(updates.some(x=>!x||typeof x.type!=="string"))fail();
  return {status:"matched",editorial_review_required:updates.length>0};
 }
 if(source==="europe_pmc"){
  const rows=body?.resultList?.result;
  if(body?.hitCount!==1||!Array.isArray(rows)||rows.length!==1)fail();
  const r=rows[0];if(r.source!=="MED"||r.id!==control.pmid||norm(r.doi)!==control.doi)fail();
  return {status:"matched"};
 }
 if(source==="pubmed"){
  const r=body?.result?.[control.pmid];
  if(body?.error||!r||r.uid!==control.pmid||!Array.isArray(r.articleids)||!r.articleids.some(a=>a.idtype==="doi"&&norm(a.value)===control.doi))fail();
  return {status:"matched"};
 }
 fail();
}
const fixtures={"crossref":{"status":"ok","message":{"DOI":"10.1136/bmj-2023-078378"}},"europe_pmc":{"hitCount":1,"resultList":{"result":[{"source":"MED","id":"38626948","doi":"10.1136/bmj-2023-078378"}]}},"pubmed":{"result":{"38626948":{"uid":"38626948","articleids":[{"idtype":"doi","value":"10.1136/bmj-2023-078378"}]}}}};
function selfTest(){let n=0;const assert=v=>{if(!v)throw new Error("Fixture assertion failed");n++};for(const [s,b] of Object.entries(fixtures)){assert(inspect(s,b).status==="matched");for(const bad of [null,{}, {error:"unavailable"}]){let rejected=false;try{inspect(s,bad)}catch{rejected=true}assert(rejected)}}assert(inspect("crossref",{status:"ok",message:{DOI:control.doi,"update-to":[{type:"retraction"}]}}).editorial_review_required);for(const b of [{status:"ok",message:{DOI:"10.0000/wrong"}},{status:"ok",message:{DOI:control.doi,"update-to":{}}}]){let rejected=false;try{inspect("crossref",b)}catch{rejected=true}assert(rejected)}return n;}
const knownNotice={"doi":"10.1136/bmj.q902","pmid":"38636956","kind":"correction","scope":"author affiliations","provenance":"publisher notice and PubMed record","url":"https://www.bmj.com/content/385/bmj.q902","verification":"documentary_not_live_api"};
function assessEditorial(results,known){
  const crossref=results.find(r=>r.source==="crossref");
  return {status:known.length>0||crossref?.editorial_review_required===true?"review_required":"not_fully_assessed",known_notices:known,crossref_metadata:crossref?.status==="matched"?"checked":"unverified",retraction_status:"not_established"};
}
const editorialTests=[[[],[{"doi":"10.1136/bmj.q902","pmid":"38636956","kind":"correction","scope":"author affiliations","provenance":"publisher notice and PubMed record","url":"https://www.bmj.com/content/385/bmj.q902","verification":"documentary_not_live_api"}],"review_required","unverified"],[[{"source":"crossref","status":"matched","editorial_review_required":false}],[{"doi":"10.1136/bmj.q902","pmid":"38636956","kind":"correction","scope":"author affiliations","provenance":"publisher notice and PubMed record","url":"https://www.bmj.com/content/385/bmj.q902","verification":"documentary_not_live_api"}],"review_required","checked"],[[{"source":"crossref","status":"matched","editorial_review_required":true}],[],"review_required","checked"],[[{"source":"crossref","status":"matched","editorial_review_required":false}],[],"not_fully_assessed","checked"],[[{"source":"crossref","status":"http_error"}],[],"not_fully_assessed","unverified"]];
function testEditorial(assessEditorial,tests){let count=0;for(const [r,k,s,m] of tests){const a=assessEditorial(r,k);if(a.status!==s||a.crossref_metadata!==m||a.retraction_status!=="not_established")throw Error("Editorial regression");count++}return count}
const endpoints={
 crossref:"https://api.crossref.org/works/"+control.doi,
 europe_pmc:"https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+new URLSearchParams({query:"EXT_ID:"+control.pmid+" AND SRC:MED",format:"json",resultType:"lite"}),
 pubmed:"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"+new URLSearchParams({db:"pubmed",id:control.pmid,retmode:"json"})
};
async function probe(source,url){
 try{
  const response=await fetch(url,{redirect:"error",signal:AbortSignal.timeout(12000),headers:{Accept:"application/json","User-Agent":"AdipoLab bibliographic control audit"}});
  if(!response.ok)return {source,status:"http_error",http_status:response.status};
  const reader=response.body.getReader();let size=0;const chunks=[];
  for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>1048576){await reader.cancel();throw new Error("Response too large")}chunks.push(value)}
  const bytes=Buffer.concat(chunks);
  return {source,...inspect(source,JSON.parse(bytes.toString("utf8"))),response_sha256:createHash("sha256").update(bytes).digest("hex")};
 }catch(e){return {source,status:"unverified",error:e.name}}
}
if(process.argv.includes("--self-test")){console.log("Fixture cases passed:",selfTest()+testEditorial(assessEditorial,editorialTests))}
else{
 const dir=process.argv[2];if(!dir)throw new Error("Usage: node tools/audit_api_controls.mjs LOCAL_CACHE_DIRECTORY");
 const results=await Promise.all(Object.entries(endpoints).map(([s,u])=>probe(s,u)));
 const summary={schema:"adipolab.api-control.v2",retrieved_at:new Date().toISOString(),control,results,editorial:assessEditorial(results,[knownNotice]),status:results.every(r=>r.status==="matched")?"complete":"partial",clinical_validation:false};
 await mkdir(resolve(dir),{recursive:true});
 const filename=resolve(dir,"latest_api_control.json"),tmp=filename+"."+process.pid+".tmp";
 await writeFile(tmp,JSON.stringify(summary,null,2),{flag:"wx"});await rename(tmp,filename);
 console.log(JSON.stringify(summary,null,2));if(summary.status!=="complete")process.exitCode=1;
}
