# Anatomy of a Business

An interactive introductory accounting demonstration for the University of
Dayton. Students launch a simple corporation, classify its financing, investing,
and operating activities, inspect four connected financial statements, and
consider how different users interpret the information.

## Learning flow

1. **Launch Lab** — choose a simple first-year business plan.
2. **Activity Map** — classify economic events by business purpose.
3. **Financial Statements** — connect accounts to the income statement,
   retained earnings, balance sheet, and statement of cash flows.
4. **Decision Desk** — interpret the results as an investor, creditor, or
   manager and explore the surrounding annual-report components.

The scenario intentionally uses straightforward, cash-based events. It does not
teach journal entries or accrual-accounting timing.

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

## Deploy with GitHub and Streamlit Community Cloud

1. Create a GitHub repository and push this folder to its `main` branch.
2. In Streamlit Community Cloud, select the repository and branch.
3. Set the entrypoint to `streamlit_app.py`.
4. In Advanced settings, select Python 3.12.
5. Deploy. No secrets or external services are required for this draft.

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
