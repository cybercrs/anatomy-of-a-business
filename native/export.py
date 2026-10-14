"""Export unchanged teaching renderers and independent accounting oracles.

Python is development tooling only; no interpreter is included in the site.
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from accounting import (ACTIVITY_TYPES, ASSET_PLANS, DIVIDEND_POLICIES,
                        FUNDING_PLANS, OPERATING_PLANS, build_scenario,
                        calculate_summary)  # noqa: E402
from browser.build import shared_source  # noqa: E402
from resume_state import encode_resume_state  # noqa: E402


class State(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None

    def __setattr__(self, key, value):
        self[key] = value


class Container:
    def __init__(self, recorder, node):
        self.recorder, self.node = recorder, node

    def __enter__(self):
        self.recorder.stack.append(self.node["children"])
        return self

    def __exit__(self, *args):
        self.recorder.stack.pop()

    def metric(self, label, value, **kwargs):
        self.node["children"].append({"kind": "metric", "label": label, "value": value})


class Recorder:
    def __init__(self):
        self.session_state = State()
        self.stack = [[]]

    def node(self, kind, **kwargs):
        node = {"kind": kind, **kwargs}
        self.stack[-1].append(node)
        return node

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, text, unsafe_allow_html=False):
        self.node("html" if unsafe_allow_html else "markdown", text=text.strip())

    def __getattr__(self, kind):
        if kind in {"header", "subheader", "write", "success", "warning", "info", "caption"}:
            return lambda text: self.node(kind, text=text.replace(r"\$", "$"))
        raise AttributeError(kind)

    def radio(self, label, options, **kwargs):
        options = list(options)
        self.node("radio", label=label.replace(r"\$", "$"),
                  options=[x.replace(r"\$", "$") for x in options], key=kwargs["key"])
        value = self.session_state.get(kwargs["key"], options[kwargs.get("index", 0)])
        self.session_state[kwargs["key"]] = value
        return value

    def selectbox(self, label, options, **kwargs):
        options = list(options)
        self.node("select", label=label, options=options, key=kwargs["key"])
        value = self.session_state.get(kwargs["key"], options[kwargs.get("index", 0)])
        self.session_state[kwargs["key"]] = value
        return value

    def button(self, label, **kwargs):
        self.node("button", label=label, key=kwargs.get("key"),
                  disabled=kwargs.get("disabled", False))
        return False

    def form_submit_button(self, label, **kwargs):
        self.node("button", label=label, action="submit-activity")
        return False

    def progress(self, value, **kwargs):
        self.node("progress", value=value)

    def columns(self, count):
        count = count if isinstance(count, int) else len(count)
        group = self.node("columns", children=[])
        columns = []
        for _ in range(count):
            node = {"kind": "column", "children": []}
            group["children"].append(node)
            columns.append(Container(self, node))
        return columns

    def tabs(self, labels):
        group = self.node("tabs", children=[])
        tabs = []
        for label in labels:
            node = {"kind": "tab", "label": label, "children": []}
            group["children"].append(node)
            tabs.append(Container(self, node))
        return tabs

    def form(self, key):
        return Container(self, self.node("form", key=key, children=[]))

    def expander(self, label, **kwargs):
        return Container(self, self.node("details", label=label,
                                        expanded=kwargs.get("expanded", False), children=[]))

    @contextmanager
    def capture(self):
        self.stack = [[]]
        yield self.stack[0]


def export():
    recorder = Recorder()
    namespace = {}
    with patch.dict(sys.modules, {"streamlit": recorder}):
        exec(compile(shared_source(), "original_teaching_renderer", "exec"), namespace)
    namespace["shuffled_options"] = lambda key, options: tuple(options)
    with recorder.capture() as css_nodes:
        namespace["inject_styles"]()
    with recorder.capture() as hero:
        namespace["hero"]()
    css = css_nodes[0]["text"].replace("<style>", "").replace("</style>", "").strip() + "\n"
    configs = []
    oracles = []
    for combination in itertools.product(FUNDING_PLANS, ASSET_PLANS, OPERATING_PLANS, DIVIDEND_POLICIES):
        funding, asset, operating, dividend = combination
        scenario = build_scenario(*combination)
        summary = calculate_summary(scenario)
        recorder.session_state = State()
        namespace["initialize_state"]()
        base = copy.deepcopy(recorder.session_state)
        base.update(funding_choice=funding, asset_choice=asset, operating_choice=operating,
                    dividend_choice=dividend, scenario_choices={
                        "funding_plan": funding, "asset_plan": asset,
                        "operating_plan": operating, "dividend_policy": dividend})

        def screen(renderer, **values):
            recorder.session_state = State(copy.deepcopy(base))
            recorder.session_state.update(values)
            with recorder.capture() as nodes:
                namespace[renderer]()
            return copy.deepcopy(nodes)

        launch = {status: screen("render_launch_lab",
                                 organization_checked=status != "unchecked",
                                 organization_answer="Corporation" if status == "correct" else "Partnership")
                  for status in ("unchecked", "wrong", "correct")}
        activity = {
            "unchecked": screen("render_activity_map"),
            "checked": screen("render_activity_map", activity_checked=True,
                              activity_answers={event.event_id: "Not sure yet" for event in scenario.events}),
            "correct": screen("render_activity_map", activity_checked=True,
                              activity_answers={event.event_id: event.activity_type for event in scenario.events}),
        }
        questions = namespace["statement_question_data"](summary)
        statements = {}
        for name, question in questions.items():
            statements[name] = {}
            for status in ("unchecked", "wrong", "correct"):
                statements[name][status] = screen(
                    "render_financial_statements", statement_selection=name,
                    statement_results={} if status == "unchecked" else {name: status == "correct"})
        decision = {status: screen("render_decision_desk", activity_checked=True,
                                  statement_checked=True, decision_completed=status == "complete")
                    for status in ("open", "complete")}
        config = {"choices": combination, "events": [asdict(event) for event in scenario.events],
                  "questions": questions, "launch": launch, "activity": activity,
                  "statements": statements, "decision": decision}
        configs.append(config)
        oracles.append({"choices": combination, "events": config["events"],
                        "summary": asdict(summary), "questions": questions})
    data = {"title": "Anatomy of a Business", "pages": namespace["PAGES"],
            "statements": namespace["STATEMENT_NAMES"], "hero": hero,
            "plans": [FUNDING_PLANS, ASSET_PLANS, OPERATING_PLANS, DIVIDEND_POLICIES],
            "activities": ACTIVITY_TYPES, "configs": configs}
    here = Path(__file__).resolve().parent
    (here / "tests").mkdir(exist_ok=True)
    # Intern repeated JSON subtrees rather than sending 36 copies of teaching prose.
    pool, indices = [], {}

    def intern(value):
        if not isinstance(value, (str, list, tuple, dict)):
            return value
        key = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        if key in indices:
            return {"$": indices[key]}
        converted = ({k: intern(v) for k, v in value.items()} if isinstance(value, dict)
                     else [intern(v) for v in value] if isinstance(value, (list, tuple)) else value)
        index = len(pool)
        indices[key] = index
        pool.append(converted)
        return {"$": index}

    root = intern(data)
    source = ("// Generated from unchanged teaching renderers; no curriculum overrides.\n"
              "const pool=" + json.dumps(pool, ensure_ascii=True, separators=(",", ":")) + ";\n"
              "const cache=new Map();function read(v){if(v&&typeof v==='object'&&!Array.isArray(v)"
              "&&Object.hasOwn(v,'$')){const i=v.$;if(!cache.has(i))cache.set(i,read(pool[i]));"
              "return cache.get(i);}if(Array.isArray(v))return v.map(read);"
              "if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,read(x)]));return v;}\n"
              "export const DATA=read(" + json.dumps(root) + ");\n")
    (here / "content.js").write_text(source)
    (here / "original.css").write_text(css)
    (here / "tests/python-oracles.json").write_text(json.dumps(oracles, indent=2) + "\n")
    fixtures = []
    for page in range(4):
        state = {"page": page, "funding": "Balanced", "asset": "Essential setup",
                 "operating": "Balanced growth", "dividend": "Return some value to shareholders",
                 "organization_answer": "Corporation", "organization_checked": True,
                 "launched": page > 0, "activity_selections": {}, "activity_answers": {},
                 "activity_checked": page >= 2, "statement_selection": "Income Statement",
                 "statement_answers": {}, "statement_results": {}, "decision_completed": page == 3}
        default = next(c for c in configs if list(c["choices"]) == [
            "Balanced", "Essential setup", "Balanced growth", "Return some value to shareholders"])
        if page >= 2:
            state["activity_answers"] = {e["event_id"]: e["activity_type"] for e in default["events"]}
        if page == 3:
            state["statement_results"] = {name: True for name in namespace["STATEMENT_NAMES"]}
            state["statement_answers"] = {name: q["correct"] for name, q in default["questions"].items()}
        fixtures.append({"state": state, "token": encode_resume_state(state)})
    (here / "tests/legacy-links.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    manifest = {"configurations": len(configs), "stations": 4, "statement_views": 4,
                "rendered_variants": len(configs) * (3 + 3 + 12 + 2),
                "app_owned_assets": [], "curriculum_changes": [], "content_bytes": len(source.encode())}
    (here / "tests/content-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    export()
