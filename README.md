# Anatomy of a Business

An interactive introductory accounting demonstration for the University of
Dayton. Students launch a simple corporation, classify its financing, investing,
and operating activities, inspect four connected financial statements, and
consider how different users interpret the information.

**Live app:** [anatomy-of-a-business.streamlit.app](https://anatomy-of-a-business.streamlit.app/)

**Source:** [github.com/cybercrs/anatomy-of-a-business](https://github.com/cybercrs/anatomy-of-a-business)

## Learning flow

1. **Launch Lab** — choose a simple first-year business plan.
2. **Activity Map** — classify economic events by business purpose.
3. **Financial Statements** — connect accounts to the income statement,
   retained earnings, balance sheet, and statement of cash flows.
4. **Decision Desk** — interpret the results as an investor, creditor, or
   manager and explore the surrounding annual-report components.

The scenario intentionally uses straightforward, cash-based events. It does not
teach journal entries or accrual-accounting timing.

## Refresh recovery

The app stores a compact, versioned snapshot of the current activity in the
browser URL. If a Streamlit session disconnects, refreshing the same page
restores the selected station, business choices, submitted activity map, and
financial-statement progress. The snapshot contains no name, account, or other
identifying information. Selecting **Start over** replaces it with a new
activity state.

## Run locally

Python 3.12 is recommended to match Streamlit Community Cloud's default.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Run the domain tests:

```bash
python -m unittest discover -s tests -v
```

## Deployment

The app is deployed through Streamlit Community Cloud from the `main` branch of
the public GitHub repository. The entrypoint is `streamlit_app.py`, and pushes
to `main` trigger a new deployment. No secrets or external services are
required.

The root-level `requirements.txt`, `streamlit_app.py`, and
`.streamlit/config.toml` are arranged for Community Cloud's repository-root
execution model.

## Project structure

```text
.
├── .streamlit/
│   └── config.toml
├── tests/
│   └── test_accounting.py
├── accounting.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## Branding note

The visual theme uses a University of Dayton-inspired red and blue palette for
an internal course activity. It does not include or reproduce an institutional
or athletics logo.
