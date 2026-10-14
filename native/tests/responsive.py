"""Focused post-review layout/status check; reuses the actual full-route bookmark."""
import importlib.util
import json
import statistics
import threading
import urllib.parse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("native_browser_qa", HERE / "browser.py")
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
result_path = qa.RESULTS / "browser-results.json"
original = json.loads(result_path.read_text())
assert all(check["status"] == "passed" for check in original["checks"])
(qa.RESULTS / "full-route-results.json").write_text(json.dumps(original, indent=2) + "\n")
query = urllib.parse.urlsplit(original["completion_bookmark"]).query
server = ThreadingHTTPServer(("127.0.0.1", 0), partial(qa.Handler, directory=str(qa.NATIVE / "dist")))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = "http://127.0.0.1:" + str(server.server_port)
address = origin + qa.PREFIX
errors = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True,
        proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost"})
    context = browser.new_context()
    context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    for width in (1280, 900, 390):
        page.set_viewport_size({"width": width, "height": 960 if width > 390 else 844})
        page.goto(address + "?" + query, wait_until="networkidle")
        page.wait_for_function("document.documentElement.dataset.ready==='true'")
        before = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)["progress"][0]
        page.screenshot(path=str(qa.RESULTS / ("completed-" + ("narrow" if width == 390 else "desktop") + ".png")), full_page=True)
        for view in (2, 1, 0):
            page.get_by_role("button", name="Back", exact=True).click()
            page.wait_for_function("v=>document.documentElement.dataset.view===String(v)", arg=view)
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)["progress"][0] == before
            expect(page.locator("#lesson input,#lesson select")).to_have_count(0)
            expect(page.get_by_role("button", name="Start over", exact=True)).to_be_disabled()
            if view == 2:
                assert page.evaluate("""()=>{
                    const nodes=[...document.querySelector('#lesson').children];
                    const caption=nodes.findIndex(e=>e.textContent.startsWith('Statements explored:'));
                    return nodes[caption+1].textContent==='All four statement questions have been explored.';
                }""")
                page.screenshot(path=str(qa.RESULTS / ("review-" + ("narrow" if width == 390 else "desktop") + ".png")), full_page=True)
        for view in (1, 2, 3):
            page.get_by_role("button", name="Forward", exact=True).click()
            page.wait_for_function("v=>document.documentElement.dataset.view===String(v)", arg=view)
        expect(page.get_by_role("button", name="Forward", exact=True)).to_be_disabled()
        page.get_by_role("button", name="Start over", exact=True).click()
        page.wait_for_function("document.documentElement.dataset.view==='0'")
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    samples = []
    for _ in range(5):
        cold = browser.new_context()
        fresh = cold.new_page()
        cold.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
        session = cold.new_cdp_session(fresh)
        session.send("Network.enable")
        session.send("Network.setCacheDisabled", {"cacheDisabled": True})
        fresh.goto(address, wait_until="networkidle")
        fresh.wait_for_function("document.documentElement.dataset.ready==='true'")
        samples.append(fresh.evaluate("performance.getEntriesByName('anatomy-ready')[0].startTime"))
        cold.close()
    browser.close()
server.shutdown()
assert not errors, errors
original["checks"].append({"name": "Final status placement and 900px grid: all four stations, readonly state, reset; 1280/900/390px", "status": "passed"})
original["cold_initialization_ms"] = {"samples": samples, "median": statistics.median(samples),
    "conditions": "Final bundle; five cache-disabled fresh Chromium contexts on local loopback; no hosted or capacity claim."}
original["final_visual_scope"] = "After the complete 36-route pass: medium-width grid and statement-status placement only; full lesson/calculations unchanged."
result_path.write_text(json.dumps(original, indent=2) + "\n")
print("PASS: final responsive/status checks; measurements", samples, flush=True)
