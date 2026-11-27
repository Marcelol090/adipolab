/* Read-only audit summary. No clinical predictions or personal data. */
(function(root) {
  "use strict";
  const keys = ["schema","audit_version","publication_count","quarantine_count","registry_links_resolved","registry_links_total","checks_passed","checks_total"];
  function validate(x) {
    if (!x || typeof x !== "object" || Array.isArray(x) ||
        Object.keys(x).sort().join(",") !== [...keys].sort().join(",")) throw new Error("Formato de auditoria inválido.");
    if (x.schema !== "adipolab.audit-summary.v1" || x.audit_version !== "v190") throw new Error("Versão de auditoria incompatível.");
    for (const k of keys.slice(2)) {
      if (!Number.isSafeInteger(x[k]) || x[k] < 0 || x[k] > 10000000) throw new Error("Contagem inválida.");
    }
    if (x.quarantine_count > x.publication_count || x.registry_links_resolved > x.registry_links_total || x.checks_passed > x.checks_total || x.checks_total === 0) throw new Error("Totais inconsistentes.");
    return Object.freeze({...x});
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {validate};
  if (!root.document) return;
  const doc=root.document, status=doc.getElementById("snapshot-status"), file=doc.getElementById("snapshot-file");
  const format=n=>n.toLocaleString("pt-BR");
  function render(data) {
    const x=validate(data);
    const values={publications:format(x.publication_count),links:format(x.registry_links_resolved)+"/"+format(x.registry_links_total),quarantine:format(x.quarantine_count),checks:format(x.checks_passed)+"/"+format(x.checks_total)};
    for (const [key,value] of Object.entries(values)) doc.querySelector('[data-metric="'+key+'"]').textContent=value;
    status.textContent="Resumo importado; estrutura e totais conferidos no navegador. A origem do arquivo não é autenticada pelo navegador. Não representa validação clínica.";
  }
  file.addEventListener("change",async()=>{
    const f=file.files[0]; if(!f)return;
    try {if(f.size>65536)throw new Error("Arquivo excede 64 KB.");render(JSON.parse(await f.text()));}
    catch(e){status.textContent="Importação recusada: "+e.message+" Os indicadores anteriores foram mantidos.";}
    finally{file.value="";}
  });
})(typeof globalThis!=="undefined"?globalThis:this);
