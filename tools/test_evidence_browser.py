from pathlib import Path
import json,threading,functools,os
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Quiet,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f"http://127.0.0.1:{server.server_port}"
fixture={"schema":"adipolab.audit-summary.v1","audit_version":"v190","publication_count":10000000,"quarantine_count":1,"registry_links_resolved":10000000,"registry_links_total":10000000,"checks_passed":1,"checks_total":2}
results=[]
try:
    with sync_playwright() as pw:
        chrome=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        kw={"executable_path":str(chrome)} if chrome.exists() else {}
        browser=pw.chromium.launch(headless=True,**kw)
        for width in [320,390,768,1440]:
            for scheme in ["light","dark"]:
                context=browser.new_context(viewport={"width":width,"height":850},color_scheme=scheme)
                page=context.new_page();errors=[];external=[]
                page.on("pageerror",lambda error:errors.append(str(error)))
                def route(r):
                    if r.request.url.startswith(base+"/"):r.continue_()
                    else:external.append(r.request.url);r.abort()
                page.route("**/*",route)
                page.goto(base+"/evidence.html",wait_until="networkidle")
                expect(page.locator("#snapshot-status")).to_contain_text("não verificada")
                before=page.locator('[data-metric="publications"]').inner_text()
                page.locator("#snapshot-file").set_input_files({"name":"synthetic.json","mimeType":"application/json","buffer":json.dumps(fixture).encode()})
                expect(page.locator("#snapshot-status")).to_contain_text("não é autenticada")
                expect(page.locator('[data-metric="publications"]')).to_have_text("10.000.000")
                expect(page.locator('[data-metric="links"]')).to_have_text("10.000.000/10.000.000")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"),f"overflow {width}/{scheme}"
                page.locator("#snapshot-file").set_input_files({"name":"invalid.json","mimeType":"application/json","buffer":b'{"patient":"synthetic"}'})
                expect(page.locator("#snapshot-status")).to_contain_text("recusada")
                expect(page.locator('[data-metric="publications"]')).to_have_text("10.000.000")
                page.locator("#snapshot-reset").focus()
                page.keyboard.press("Enter")
                expect(page.locator('[data-metric="publications"]')).to_have_text(before)
                expect(page.locator("#snapshot-status")).to_contain_text("não verificada")
                assert page.evaluate("localStorage.length===0 && sessionStorage.length===0")
                assert not external and not errors,(external,errors)
                results.append({"width":width,"scheme":scheme,"passed":True})
                context.close()
        browser.close()
finally:server.shutdown();server.server_close()
print(json.dumps({"browser_tests":results,"passed":len(results)},ensure_ascii=True))
