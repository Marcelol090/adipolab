import { chromium } from "playwright";
import assert from "node:assert/strict";
import {createServer} from "node:http";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
const allowed=new Set(["index.html","lab.html","integrity.html","model.mjs","catalog.json","integrity-registry.json"]);
const server=createServer(async(req,res)=>{const pathname=new URL(req.url,"http://localhost").pathname;const file=pathname==="/research-v75/"?"index.html":pathname.startsWith("/research-v75/")?pathname.slice(14):"";if(!allowed.has(file)){res.writeHead(404).end();return}try{const data=await readFile(fileURLToPath(new URL("./"+file,import.meta.url)));res.writeHead(200,{"Content-Type":file.endsWith(".mjs")?"text/javascript":file.endsWith(".json")?"application/json":"text/html; charset=utf-8"}).end(data)}catch{res.writeHead(500).end()}});
await new Promise(r=>server.listen(0,"127.0.0.1",r));const origin="http://127.0.0.1:"+server.address().port;
let browser;let checks=0;
function check(x,msg){assert.ok(x,msg);checks++}
try{browser=await chromium.launch({headless:true});
for(const [width,height,scheme] of [[1440,900,"light"],[390,844,"dark"],[320,640,"light"]]){
const context=await browser.newContext({viewport:{width,height},colorScheme:scheme});const page=await context.newPage();const errors=[],external=[];page.on("pageerror",e=>errors.push(e.message));await page.route("**/*",route=>{if(!route.request().url().startsWith(origin+"/")){external.push(route.request().url());return route.abort()}return route.continue()});
await page.goto(origin+"/research-v75/");await page.locator("#checks").filter({hasText:"32/32"}).waitFor();check(await page.locator("#refs article:visible").count()===50,"initial references");await page.locator("#search").fill("zzzzzzzzzzzzzz");check(await page.locator("#refs article:visible").count()===0,"empty filter");check(await page.locator("#empty").isVisible(),"empty message");await page.locator("#search").fill("");await page.locator("#lang").selectOption("ja");check(await page.locator("#refs article:visible").count()===1,"language filter");await page.locator("#lang").selectOption("");check(await page.locator("#refs article:visible").count()===50,"reset filter");check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"library viewport overflow");
await page.getByRole("link",{name:"Laboratório v130"}).click();await page.waitForURL("**/lab.html");check(await page.locator("[data-review-version]").count()===10,"areas");check(await page.locator("[data-cycle-review]").count()===10,"cycles");check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"lab viewport overflow");
await page.getByRole("link",{name:"Auditoria v130"}).click();await page.waitForURL("**/integrity.html");check(await page.locator("[data-record]").count()===57,"identifier records");check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"audit viewport overflow");check(await page.evaluate(()=>localStorage.length===0&&sessionStorage.length===0),"no storage");check(external.length===0,"no external requests");check(errors.length===0,"page errors: "+errors.join(","));await context.close();
}console.log("Browser checks passed: "+checks);
}finally{await browser?.close();await new Promise(r=>server.close(r))}
