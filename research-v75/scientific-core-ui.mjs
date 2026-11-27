import {auditCore} from "./scientific-core.mjs";
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString("pt-BR");
const node=(tag,t,cls)=>{const e=document.createElement(tag);e.textContent=t;if(cls)e.className=cls;return e};
function card(label,value,detail){const a=node("article","","card");a.append(node("small",label),node("div",value,"number"),node("p",detail));return a}
const limits={rawDataPublished:"RAW e microdados não publicados neste aplicativo",matrixPersisted:"Matrizes integrais não persistidas pelo reprocessamento",warningDetailsCaptured:"Conteúdo completo dos avisos não capturado",historicalReproduction:"Reprodução histórica exata não estabelecida",independentMolecularIdentity:"Identificação molecular independente não estabelecida",independentBiologicalValidation:"Validação biológica independente não estabelecida",individualPrediction:"Previsão fisiológica individual não estabelecida"};
let registry;
function show(){
 const a=auditCore(registry),t=a.totals;
 $("status").textContent=a.passed+"/"+a.total+" verificações de consistência aprovadas";
 $("metrics").replaceChildren(card("Aquisições",fmt(t.passed)+"/"+fmt(t.pairs),"Correspondência RAW–NetCDF"),card("Pontos espectrais",fmt(t.points),"Valores exatos comparados"),card("Varreduras",fmt(t.scans),"Correspondência numérica"),card("Registros de picos",fmt(t.peaks),"Não são moléculas únicas"),card("Agrupamentos",fmt(t.groups),"Sinais não identificados"),card("Células finitas",fmt(t.finiteCells),"Matrizes verificadas, não exportadas"));
 $("modes").replaceChildren(...registry.modes.filter(m=>$("mode").value==="all"||$("mode").value===m.mode).map(m=>{const e=node("article","","card");e.dataset.mode=m.mode;e.append(node("h3",m.mode),node("p",fmt(m.points)+" pontos · "+fmt(m.scans)+" varreduras"),node("p",fmt(m.studyQcPeaks+m.calibrationPeaks)+" registros de picos · "+fmt(m.groups)+" grupos"),node("p","Matriz "+fmt(m.groups)+" × "+m.studyQcFiles+" · "+fmt(m.missingCells)+" ausentes"),node("p","Avisos: "+(m.warningExact?"":"pelo menos ")+m.warningMinimum+"; conteúdo integral indisponível"));return e}));
 $("checks").replaceChildren(...a.checks.map(c=>{const p=node("p",c.id+" · "+c.label+" — "+(c.pass?"PASS":"REVIEW"));p.dataset.check=c.id;return p}));
 $("limits").replaceChildren(...Object.values(limits).map(t=>node("p",t,"note")),node("p","14 RAW não possuem CDF depositado; excluídos da equivalência pareada. Metmix processado separadamente."));
 const src=node("a","ST005210 · Metabolomics Workbench");src.href=registry.source;src.rel="noopener noreferrer";
 $("provenance").replaceChildren(src,node("p","XCMS 4.12.0 · hashes identificam relatórios locais, não cópias públicas."),...Object.entries(registry.reports).map(([name,v])=>node("p",name+" · "+v.status+" · SHA-256 "+v.sha256)));
}
try{const res=await fetch("./scientific-core.json");if(!res.ok)throw Error("HTTP "+res.status);registry=await res.json();show();$("run").disabled=false;$("run").addEventListener("click",show);$("mode").addEventListener("change",show)}catch(e){$("status").textContent="Registro indisponível ou inválido: "+e.message}
