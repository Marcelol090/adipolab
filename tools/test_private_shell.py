"""Regression test for the private shell using an ephemeral synthetic AES-GCM payload."""
import base64
import functools
import json
import re
import subprocess
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
original = (ROOT / "index.html").read_text(encoding="utf-8")
pattern = r'const encrypted=\[.*?\]\.join\(""\);'
iv_pattern = r'const iv=Uint8Array\.from\("[0-9a-f]+"'
base = subprocess.check_output(["git", "-C", str(ROOT), "show", "698cafb998c4d8dd9c2fc17786e9a0ec8c713fb8:index.html"]).decode("utf-8")
for pat in [pattern, iv_pattern]:
    assert re.search(pat, base, re.S).group() == re.search(pat, original, re.S).group(), "Existing ciphertext or IV changed"

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server = ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as pw:
        chrome=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        browser=pw.chromium.launch(headless=True,**({"executable_path":str(chrome)} if chrome.exists() else {}))
        page=browser.new_page()
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto(url+"/index.html")
        expect(page.locator("#unlock")).to_be_visible()
        expect(page.locator("#adipolab-evidence-notice")).to_have_count(0)
        # Only synthetic content and a synthetic key, never the user's key.
        iv=re.search(r'const iv=Uint8Array\.from\("([0-9a-f]+)"',original).group(1)
        encrypted=page.evaluate("""async (ivHex) => {
            const iv=Uint8Array.from(ivHex.match(/../g),x=>parseInt(x,16));
            const key=await crypto.subtle.importKey("raw",new Uint8Array(32).fill(17),"AES-GCM",false,["encrypt"]);
            const plain=new TextEncoder().encode('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Fixture</title></head><body><main id="synthetic">Synthetic fixture</main></body></html>');
            const enc=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv},key,plain));
            return btoa(String.fromCharCode(...enc));
        }""",iv)
        fixture,count=re.subn(pattern,lambda _: "const encrypted="+json.dumps(encrypted)+";",original,flags=re.S)
        assert count==1
        page.route(url+"/index.html?fixture=1",lambda r:r.fulfill(status=200,content_type="text/html; charset=utf-8",body=fixture))
        page.goto(url+"/index.html?fixture=1")
        page.locator("#key").fill("bad")
        page.locator("#go").click()
        expect(page.locator("#status")).to_contain_text("64")
        page.locator("#key").fill("22"*32)
        page.locator("#go").click()
        expect(page.locator("#status")).to_contain_text("desbloquear")
        expect(page.locator("#adipolab-evidence-notice")).to_have_count(0)
        page.locator("#key").fill("11"*32)
        page.locator("#go").click()
        expect(page.locator("#synthetic")).to_be_visible()
        expect(page.locator("#adipolab-evidence-notice")).to_be_visible()
        expect(page.locator("#adipolab-evidence-notice a")).to_have_attribute("href","/evidence.html")
        expect(page.locator("#key")).to_have_count(0)
        assert not errors,errors
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print("PASS original ciphertext and IV unchanged; real browser AES-GCM synthetic rejection and unlock; notice and link")
