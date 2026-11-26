import test from "node:test";import assert from "node:assert/strict";import {readFileSync} from "node:fs";import {auditBibliography} from "./bibliographic-audit.mjs";
const read=f=>JSON.parse(readFileSync(new URL(f,import.meta.url),"utf8")),reg=read("./bibliographic-audit.json"),cat=read("./catalog.json");
test("bibliographic audit",()=>assert.ok(auditBibliography(reg,cat.records)));
test("UK Biobank recorded",()=>assert.ok(cat.records.find(r=>r.id==="E033").cohorts.includes("UK Biobank")));
test("blocked source remains provisional",()=>{const r=structuredClone(reg);r.audits.find(a=>a.id==="E047").identity="confirmed";assert.equal(auditBibliography(r,cat.records),false)});
test("unknown reference rejected",()=>{const r=structuredClone(reg);r.audits[0].id="UNKNOWN";assert.equal(auditBibliography(r,cat.records),false)});
test("duplicate audit rejected",()=>{const r=structuredClone(reg);r.audits.push(r.audits[0]);assert.equal(auditBibliography(r,cat.records),false)});
test("unsupported individual validation rejected",()=>{const r=structuredClone(reg);r.audits[0].individualValidation=true;assert.equal(auditBibliography(r,cat.records),false)});
test("embedded catalog matches canonical JSON",()=>{const h=readFileSync(new URL("./index.html",import.meta.url),"utf8");assert.deepEqual(JSON.parse(h.match(/const data=([\s\S]*?);const q=/)[1]),cat)});
