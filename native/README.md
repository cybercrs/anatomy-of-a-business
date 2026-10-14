# Anatomy of a Business — native browser app

The final student-facing app uses HTML, CSS and JavaScript, with no Python interpreter, Streamlit, Pyodide, WebAssembly, installation step, external asset request, npm runtime dependency, storage service or central score store. The existing Python application and published stlite root remain unchanged. The isolated source branch is `native/html-js`; publication adds only `js/` to the existing `stlite-browser` branch. No Pages setting is changed.

## Teaching and calculations

The unchanged teaching renderers export all 36 funding/equipment/operating/dividend combinations, including 720 page/feedback variants. Shared prose is interned to reduce duplication. The four connected statements, organization discussion, optional dividend event, activity explanations, three user perspectives, annual-report components and debrief model answers remain. No Receivables-specific teaching changes are applied. The independent JavaScript accounting model matches the Python event and financial-summary outcomes for every plan.

The original gates remain: the activity map must be checked, and all four statement questions must be explored. Wrong answers receive the original feedback and still satisfy those exploration gates. Results can be rechecked on the actual current station. No attempts or first-pass score is introduced. Anatomy defines no downloads or dataframe controls.

## Review and saving

Back and Forward are discreet boxed native buttons with accessible names, keyboard focus and 44px targets. Earlier stations render static answers with no edits, checks, revisions, completion or reset. Financial-statement peer tabs remain available as read-only views. Forward stops at the actual earned station; ordinary activity controls advance. The action model rejects review mutations independently of the controls.

The original base64url JSON version-1 `progress` snapshots remain compatible in both directions. To use an old Python or stlite bookmark, preserve its query parameters and change only the path to `/anatomy-of-a-business/js/`. The separate `view` is bounded by earned progress. Legacy unearned station requests are clamped using the accepted browser rules. Submitted answers and unsubmitted selections remain distinct. Plan, organization, activity and statement drafts survive refresh/bookmarks. Arbitrary extra query parameters, repeated values and fragments are retained. As in the original, answer permutations are stable during an activity instance and are regenerated after refresh/reset; the old save format contains no option-order seed. Native random permutations use unbiased Web Crypto sampling.

Reset starts a fresh activity at the current frontier and leaves older copied bookmarks intact. Independent tabs/contexts have no shared storage. URL progress is learner-controlled recovery data, not an authenticated grade record.

## Build and validation

From the repository root in Accounting Teaching Apps:

```bash
/workspace/.cloud-setup/venvs/main/bin/python native/export.py
node --test native/tests/*.test.mjs
/workspace/.cloud-setup/venvs/main/bin/python -m unittest discover -s tests -v
/workspace/.cloud-setup/venvs/main/bin/python native/build.py
/workspace/.cloud-setup/venvs/main/bin/python native/tests/browser.py
/workspace/.cloud-setup/venvs/main/bin/python native/tests/responsive.py
```

The exporter reads the unchanged Python source only during development. The build copies only six native assets and a hash manifest. `--site-output PATH` writes only `PATH/js/`. Serve the built directory over HTTP(S); `file://` is unsupported. Current ES-module browsers with Web Crypto and structured cloning are required. Chromium is tested; physical devices and broader browser coverage are unmeasured.

Reviewed screenshots and detailed checks are in `review/` and `VALIDATION.md`. Publication verifies the exact source/static commits, preserves every existing non-js static blob, and checks the subsequent Pages deployment. Hosted browser QA remains unavailable under the known Pages-hostname proxy denial; no alternate route is used.

The original tab icon is embedded as a self-contained SVG data asset. Final metadata QA verifies the exact title, decodes the icon, and confirms only index.html changed among runtime assets; lesson JavaScript/CSS/content are unchanged.
