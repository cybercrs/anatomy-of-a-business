"""Full local native Chromium QA at the actual project-prefixed /js/ path."""
from __future__ import annotations

import json
import re
import statistics
import sys
import threading
import time
import traceback
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from resume_state import decode_resume_state, encode_resume_state  # noqa: E402

NATIVE = ROOT / "native"
RESULTS = NATIVE / "test-results"
PREFIX = "/anatomy-of-a-business/js/"
RESULTS.mkdir(exist_ok=True)
ORACLE = json.loads((NATIVE / "tests/python-oracles.json").read_text())
LEGACY = json.loads((NATIVE / "tests/legacy-links.json").read_text())
checks, requests, external, errors, console_errors = [], [], [], [], []


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        requests.append(path)
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif path.startswith(PREFIX):
            self.path = path[len(PREFIX) - 1:]
            super().do_GET()
        else:
            self.send_error(404)


def passed(name):
    checks.append({"name": name, "status": "passed"})
    print("PASSED:", name, flush=True)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(NATIVE / "dist")))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    url = origin + PREFIX
    result = {"url": url, "conditions": "Local loopback; Chromium; external requests blocked; no hosted proxy bypass."}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True,
            proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost"})
        context = browser.new_context(viewport={"width": 1280, "height": 960})

        def attach(context):
            def route(request_route):
                if not request_route.request.url.startswith(origin):
                    external.append(request_route.request.url)
                    request_route.abort()
                else:
                    request_route.continue_()
            context.route("**/*", route)
            def page_events(page):
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            context.on("page", page_events)

        attach(context)
        page = context.new_page()

        def loaded(view=None):
            page.wait_for_function("document.documentElement.dataset.ready==='true'")
            page.wait_for_function("document.documentElement.dataset.saving==='false'")
            if view is not None:
                page.wait_for_function("value=>document.documentElement.dataset.view===String(value)", arg=view)
            expect(page).to_have_title("Anatomy of a Business")
            assert not re.search(r"\b(?:pilot|preview|test(?:ing)?\s+(?:app|version|site))\b",
                                 page.locator("body").inner_text(), re.I)
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")

        def go(address=url, view=None):
            page.goto(address, wait_until="networkidle")
            loaded(view)

        def state():
            token = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)["progress"][0]
            value = decode_resume_state(token)
            assert value is not None
            return value

        def button(name):
            page.get_by_role("button", name=name, exact=True).click()
            loaded()

        def shot(name):
            page.screenshot(path=str(RESULTS / (name + ".png")), full_page=True)

        def select(key, value):
            page.locator("#" + key).select_option(value)
            loaded()

        def statement(name, answer, check=True):
            page.get_by_role("tab", name=name, exact=True).click()
            page.get_by_role("radio", name=answer.replace(r"\$", "$"), exact=True).check()
            loaded()
            if check:
                button("Check this statement")

        try:
            go(view=0)
            expect(page.get_by_role("button", name="Back", exact=True)).to_be_disabled()
            expect(page.get_by_role("button", name="Forward", exact=True)).to_be_disabled()
            page.get_by_role("radio", name="Partnership", exact=True).check()
            button("Check the organization")
            expect(page.locator("#lesson")).to_contain_text("this scenario points to a corporation")
            page.get_by_role("radio", name="Corporation", exact=True).check()
            button("Check the organization")
            expect(page.locator("#lesson")).to_contain_text("Exactly. A corporation")
            shot("launch-desktop")
            passed("Organization alternatives, repeated checks, native title and initial navigation")

            before_plan = state()
            select("funding_choice", "Credit-forward")
            select("asset_choice", "Expanded setup")
            select("operating_choice", "Big campus push")
            select("dividend_choice", "Keep earnings in the business")
            plan_url = page.url
            page.reload()
            loaded(0)
            expect(page.locator("#funding_choice")).to_have_value("Credit-forward")
            expect(page.locator("#asset_choice")).to_have_value("Expanded setup")
            assert state()["organization_answer"] == "Corporation"
            assert page.url == plan_url
            passed("Unlaunched plan and organization drafts survive refresh")
            go(url + "?progress=" + encode_resume_state(before_plan), 0)

            button("Launch the business →")
            loaded(1)
            expect(page.get_by_role("button", name="See the financial statements →", exact=True)).to_have_count(0)
            select("activity_issue_stock", "Investing")
            draft_url = page.url
            button("Back")
            loaded(0)
            assert state()["activity_selections"]["issue_stock"] == "Investing"
            expect(page.locator("#lesson input,#lesson select,#lesson button")).to_have_count(0)
            expect(page.get_by_role("button", name="Start over", exact=True)).to_be_disabled()
            button("Forward")
            loaded(1)
            expect(page.get_by_role("button", name="Forward", exact=True)).to_be_disabled()
            page.reload()
            loaded(1)
            expect(page.locator("#activity_issue_stock")).to_have_value("Investing")
            assert state()["activity_answers"] == {}
            assert page.url == draft_url
            button("Check the activity map")
            expect(page.locator("#lesson")).to_contain_text("You mapped")
            expect(page.get_by_role("button", name="See the financial statements →", exact=True)).to_be_enabled()
            config = next(x for x in ORACLE if x["choices"] == [
                "Balanced", "Essential setup", "Balanced growth", "Return some value to shareholders"])
            for event in config["events"]:
                select("activity_" + event["event_id"], event["activity_type"])
            button("Check the activity map")
            button("Check the activity map")
            expect(page.locator("#lesson")).to_contain_text("Complete map: 7 of 7")
            shot("activity-map-desktop")
            passed("Wrong map, unchanged original exploration gate, repeat submission, review and draft refresh")

            button("See the financial statements →")
            loaded(2)
            expect(page.get_by_role("button", name="Enter the Decision Desk →", exact=True)).to_be_disabled()
            first = "Income Statement"
            question = config["questions"][first]
            wrong = next(x for x in question["options"] if x != question["correct"])
            statement(first, wrong)
            assert state()["statement_results"][first] is False
            statement(first, question["correct"], check=False)
            statement_url = page.url
            page.reload()
            loaded(2)
            expect(page.get_by_role("radio", name=question["correct"].replace(r"\$", "$"), exact=True)).to_be_checked()
            assert state()["statement_results"][first] is False
            assert page.url == statement_url
            button("Check this statement")
            for name, question in config["questions"].items():
                if name != first:
                    statement(name, question["correct"])
            expect(page.get_by_role("button", name="Enter the Decision Desk →", exact=True)).to_be_enabled()
            assert all(state()["statement_results"].values())
            shot("statements-desktop")
            passed("All four statements, wrong answer, corrected draft restoration and original checked-question gate")

            button("Enter the Decision Desk →")
            loaded(3)
            for name in ("Investor", "Creditor", "Manager"):
                page.get_by_role("tab", name=name, exact=True).click()
                expect(page.get_by_role("tab", name=name, exact=True)).to_have_attribute("aria-selected", "true")
            for summary in page.locator("#lesson details summary").all():
                summary.click()
            button("Complete the activity")
            expect(page.locator("#lesson")).to_contain_text("Congratulations on completing Anatomy of a Business!")
            assert state()["decision_completed"] is True
            completed_url = page.url
            result["completion_bookmark"] = completed_url
            shot("completed-desktop")
            passed("Complete lesson, three user perspectives, annual report components and debrief model answers")

            before = state()
            for view in (2, 1, 0):
                button("Back")
                loaded(view)
                assert state() == before
                if view == 2:
                    for name in config["questions"]:
                        page.get_by_role("tab", name=name, exact=True).click()
                        loaded(2)
                        assert state() == before
                expect(page.locator("#lesson input,#lesson select")).to_have_count(0)
                expect(page.get_by_role("button", name="Start over", exact=True)).to_be_disabled()
                if view == 2:
                    shot("review-desktop")
            forward = page.get_by_role("button", name="Forward", exact=True)
            forward.focus()
            page.keyboard.press("Tab")
            page.keyboard.press("Shift+Tab")
            expect(forward).to_be_focused()
            assert forward.evaluate("el=>el.matches(':focus-visible')&&getComputedStyle(el).outlineWidth==='2px'")
            page.keyboard.press("Enter")
            loaded(1)
            for view in (2, 3):
                button("Forward")
                loaded(view)
            expect(forward).to_be_disabled()
            assert state() == before
            review_url = completed_url.replace("view=3", "view=2")
            go(review_url, 2)
            assert state() == before
            page.reload()
            loaded(2)
            assert state() == before
            go(completed_url.replace("view=3", "view=999"), 3)
            assert state() == before
            passed("Every backward/forward review, peer statement tabs, keyboard, future rejection and review bookmark refresh")

            page.set_viewport_size({"width": 390, "height": 844})
            loaded(3)
            shot("completed-narrow")
            for name in ("Back", "Forward"):
                box = page.get_by_role("button", name=name, exact=True).bounding_box()
                assert box["width"] >= 44 and box["height"] >= 44
                assert box["x"] >= 260 and box["x"] + box["width"] <= 390
            button("Back")
            loaded(2)
            shot("review-narrow")
            button("Forward")
            loaded(3)
            button("Start over")
            loaded(0)
            assert state()["launched"] is False
            shot("launch-narrow")
            independent = browser.new_context(viewport={"width": 1280, "height": 960})
            attach(independent)
            other = independent.new_page()
            other.goto(url, wait_until="networkidle")
            other.wait_for_function("document.documentElement.dataset.ready==='true'")
            assert other.locator("html").get_attribute("data-reached") == "0"
            go(completed_url, 3)
            assert state()["decision_completed"] is True
            assert other.locator("html").get_attribute("data-reached") == "0"
            independent.close()
            page.set_viewport_size({"width": 1280, "height": 960})
            passed("390px screenshots and 44px arrows, reset, independent contexts and retained old bookmarks")

            for fixture in LEGACY:
                address = url + "?progress=" + fixture["token"] + "&view=" + str(fixture["state"]["page"]) + "&tag=a%20b&tag=c%2Fd#saved"
                go(address, fixture["state"]["page"])
                assert state()["activity_answers"] == fixture["state"]["activity_answers"]
                assert state()["statement_results"] == fixture["state"]["statement_results"]
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)
                assert query["tag"] == ["a b", "c/d"]
                assert urllib.parse.urlsplit(page.url).fragment == "saved"
            go(url + "?progress=invalid!&view=999", 0)
            expect(page.locator("#lesson")).to_contain_text("This saved link could not be restored")
            unearned = {**LEGACY[1]["state"], "page": 3}
            go(url + "?progress=" + encode_resume_state(unearned) + "&view=999", 1)
            passed("Original Python links, native links, query/fragment preservation, malformed links and legacy unearned stations")

            for config in ORACLE:
                go(view=0)
                for key, choice in zip(("funding_choice", "asset_choice", "operating_choice", "dividend_choice"), config["choices"]):
                    select(key, choice)
                button("Launch the business →")
                for event in config["events"]:
                    select("activity_" + event["event_id"], event["activity_type"])
                button("Check the activity map")
                expect(page.locator("#lesson")).to_contain_text("Complete map: " + str(len(config["events"])) + " of " + str(len(config["events"])))
                button("See the financial statements →")
                for name, question in config["questions"].items():
                    statement(name, question["correct"])
                    assert state()["statement_results"][name] is True
                button("Enter the Decision Desk →")
                button("Complete the activity")
                assert state()["decision_completed"] is True
            passed("All 36 full business-plan routes, optional dividends and statement-question variants")

            timings = []
            for _ in range(5):
                cold = browser.new_context(viewport={"width": 1280, "height": 960})
                attach(cold)
                fresh = cold.new_page()
                session = cold.new_cdp_session(fresh)
                session.send("Network.enable")
                session.send("Network.setCacheDisabled", {"cacheDisabled": True})
                fresh.goto(url, wait_until="networkidle")
                fresh.wait_for_function("document.documentElement.dataset.ready==='true'")
                timings.append(fresh.evaluate("performance.getEntriesByName('anatomy-ready')[0].startTime"))
                cold.close()
            result["cold_initialization_ms"] = {"samples": timings, "median": statistics.median(timings),
                "conditions": "Five cache-disabled fresh Chromium contexts on local loopback; no hosted or capacity claim."}
            passed("Five fresh cache-disabled local initialization measurements")
            assert external == errors == console_errors == []
            assert not any("/vendor/" in path or path.endswith((".wasm", ".whl", ".py")) or "/_stcore/" in path for path in requests)
            passed("Only native local assets; zero external requests, runtime downloads, page errors or console errors")
        except Exception:
            checks.append({"name": "Browser walkthrough", "status": "failed", "error": traceback.format_exc()})
            page.screenshot(path=str(RESULTS / "failure.png"), full_page=True)
            result["body_on_failure"] = page.locator("body").inner_text()
        browser.close()
    server.shutdown()
    result.update(checks=checks, requests=sorted(set(requests)), external_requests=external,
                  page_errors=errors, console_errors=console_errors,
                  downloads="Not applicable: the unchanged Anatomy lesson defines no downloads or dataframes.")
    (RESULTS / "browser-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("body_on_failure", "completion_bookmark")}, indent=2), flush=True)
    return int(any(check["status"] == "failed" for check in checks))


if __name__ == "__main__":
    raise SystemExit(main())
