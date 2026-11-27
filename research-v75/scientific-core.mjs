const integer=n=>Number.isSafeInteger(n)&&n>=0;
const hash=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
const keys=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&Object.keys(x).sort().join("|")===k.split(" ").sort().join("|");
const modeKeys="mode pairs passed points scans extraFunction2 missingScans unpairedRaw studyQcFiles calibrationFiles studyQcPeaks calibrationPeaks groups finiteCells missingCells replayPassed replayTotal warningMinimum warningExact archiveSha256 ipoSha256";
const limitKeys="rawDataPublished matrixPersisted warningDetailsCaptured historicalReproduction independentMolecularIdentity independentBiologicalValidation individualPrediction";
export function auditCore(r){
 if(!keys(r,"schema version scope study source tissue software reports master modes limitations note")||r.schema!==1||r.version!=="2.0.0-alpha.1"||r.scope!=="aggregate_analytical_qc"||r.study!=="ST005210"||r.tissue!=="epicardial_adipose"||r.software!=="XCMS 4.12.0"||r.source!=="https://www.metabolomicsworkbench.org/data/DRCCMetadata.php?Mode=Study&StudyID=ST005210"||typeof r.note!=="string")throw Error("Invalid registry scope");
 if(!keys(r.reports,"equivalence repair")||!keys(r.reports.equivalence,"sha256 status")||!keys(r.reports.repair,"sha256 status")||!hash(r.reports.equivalence.sha256)||!hash(r.reports.repair.sha256)||r.reports.equivalence.status!=="REVIEW"||r.reports.repair.status!=="PASS"||r.reports.equivalence.sha256===r.reports.repair.sha256)throw Error("Invalid report provenance");
 if(!keys(r.master,"passed total inputsUnchanged")||!integer(r.master.passed)||r.master.total!==16||r.master.passed>r.master.total||typeof r.master.inputsUnchanged!=="boolean")throw Error("Invalid master");
 if(!keys(r.limitations,limitKeys)||Object.values(r.limitations).some(v=>v!==false))throw Error("Unsupported claim");
 if(!Array.isArray(r.modes)||r.modes.length!==2||new Set(r.modes.map(x=>x?.mode)).size!==2)throw Error("Invalid modes");
 for(const m of r.modes){
 if(!keys(m,modeKeys)||!["NEG","POS"].includes(m.mode)||!hash(m.archiveSha256)||!hash(m.ipoSha256)||typeof m.warningExact!=="boolean")throw Error("Invalid polarity record");
 for(const k of modeKeys.split(" ").filter(k=>!["mode","warningExact","archiveSha256","ipoSha256"].includes(k)))if(!integer(m[k]))throw Error("Invalid count "+k);
 if(m.passed>m.pairs||m.replayPassed>m.replayTotal||m.groups===0||m.scans===0||m.points===0||m.pairs!==57||m.replayTotal!==7)throw Error("Invalid bounds");
 }
 const checks=[];
 const check=(id,label,pass)=>checks.push({id,label,pass});
 for(const m of r.modes){
 check(m.mode+"-pairs","Equivalência das aquisições",m.passed===m.pairs&&m.missingScans===0&&m.scans===m.pairs*1182);
 check(m.mode+"-extra","Varreduras adicionais função 2",m.extraFunction2===m.pairs*74);
 check(m.mode+"-files","Cobertura amostras/QC e calibração",m.studyQcFiles===55&&m.calibrationFiles===2&&m.studyQcFiles+m.calibrationFiles===m.pairs&&m.unpairedRaw===7);
 check(m.mode+"-matrix","Dimensões reconciliadas",m.finiteCells+m.missingCells===m.groups*m.studyQcFiles&&m.missingCells===0);
 check(m.mode+"-replay","Reprocessamento técnico",m.replayPassed===m.replayTotal);
 }
 check("master","Master e integridade de entradas",r.master.passed===r.master.total&&r.master.inputsUnchanged);
 check("warnings","Avisos preservados",r.modes.every(m=>m.mode==="NEG"?m.warningMinimum===30&&m.warningExact:m.warningMinimum===50&&!m.warningExact));
 const sum=k=>r.modes.reduce((a,m)=>a+m[k],0);
 const totals={pairs:sum("pairs"),passed:sum("passed"),points:sum("points"),scans:sum("scans"),extras:sum("extraFunction2"),unpaired:sum("unpairedRaw"),peaks:sum("studyQcPeaks")+sum("calibrationPeaks"),groups:sum("groups"),finiteCells:sum("finiteCells"),replayPassed:sum("replayPassed")};
 check("totals","Reconciliação com relatórios arquivados",totals.pairs===114&&totals.passed===114&&totals.points===1250672824&&totals.scans===134748&&totals.extras===8436&&totals.unpaired===14&&totals.peaks===569340&&totals.groups===4876&&totals.finiteCells===268180&&totals.replayPassed===14);
 return {checks,passed:checks.filter(x=>x.pass).length,total:checks.length,totals,limitations:r.limitations};
}
