"""Anatomy of a Business — an interactive ACC 202 Chapter 1 demonstration."""

from __future__ import annotations

from html import escape

import streamlit as st

from accounting import (
    ACTIVITY_TYPES,
    ASSET_PLANS,
    DIVIDEND_POLICIES,
    FUNDING_PLANS,
    OPERATING_PLANS,
    BusinessEvent,
    FinancialSummary,
    build_scenario,
    calculate_summary,
    grade_activity_answers,
)


UD_RED = "#CE1141"
UD_BLUE = "#004B8D"
UD_NAVY = "#002D62"
INK = "#18212B"
MUTED = "#5C6977"
SURFACE = "#FFFFFF"
CANVAS = "#F3F6F9"

PAGES = (
    "1 · Launch Lab",
    "2 · Activity Map",
    "3 · Financial Statements",
    "4 · Decision Desk",
)


st.set_page_config(
    page_title="Anatomy of a Business | ACC 202",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --ud-red: {UD_RED};
            --ud-blue: {UD_BLUE};
            --ud-navy: {UD_NAVY};
            --ink: {INK};
            --muted: {MUTED};
            --surface: {SURFACE};
            --canvas: {CANVAS};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 95% 3%, rgba(206,17,65,.08), transparent 25rem),
                var(--canvas);
            color: var(--ink);
        }}

        [data-testid="stHeader"] {{ background: rgba(243,246,249,.88); }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--ud-navy) 0%, #001F45 100%);
        }}
        [data-testid="stSidebar"] * {{ color: white; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: white; }}
        [data-testid="stSidebar"] .stRadio label {{
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: .7rem;
            padding: .4rem .55rem;
            margin-bottom: .25rem;
        }}
        [data-testid="stSidebar"] .stRadio label:hover {{
            background: rgba(255,255,255,.12);
        }}
        [data-testid="stSidebar"] div.stButton > button {{
            color: var(--ud-navy) !important;
            background: white;
            border-color: white;
        }}
        [data-testid="stSidebar"] div.stButton > button * {{
            color: var(--ud-navy) !important;
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}

        h1, h2, h3 {{ color: var(--ud-navy); letter-spacing: -.025em; }}
        h2 {{ margin-top: 1.2rem !important; }}

        .hero {{
            position: relative;
            overflow: hidden;
            padding: 2.4rem 2.5rem;
            border-radius: 1.25rem;
            color: white;
            background:
                linear-gradient(112deg, rgba(0,45,98,.98) 0%, rgba(0,75,141,.96) 62%, rgba(206,17,65,.96) 130%);
            box-shadow: 0 18px 42px rgba(0,45,98,.16);
            margin-bottom: 1.6rem;
        }}
        .hero::after {{
            content: "";
            position: absolute;
            width: 20rem;
            height: 20rem;
            border: 2px solid rgba(255,255,255,.14);
            border-radius: 50%;
            right: -5rem;
            top: -11rem;
        }}
        .hero-kicker {{
            display: inline-block;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin-bottom: .75rem;
            color: #fff;
        }}
        .hero h1 {{ color: white; font-size: clamp(2.15rem, 5vw, 4rem); margin: 0; }}
        .hero p {{ color: rgba(255,255,255,.88); font-size: 1.08rem; max-width: 48rem; margin: .65rem 0 0; }}
        .chapter-pill {{
            display: inline-flex;
            margin-top: 1.1rem;
            padding: .35rem .7rem;
            border: 1px solid rgba(255,255,255,.3);
            border-radius: 999px;
            background: rgba(255,255,255,.1);
            color: white;
            font-size: .82rem;
            font-weight: 700;
        }}

        .section-lead {{ color: var(--muted); font-size: 1.02rem; max-width: 52rem; margin-top: -.45rem; }}
        .eyebrow {{
            color: var(--ud-red);
            font-size: .78rem;
            font-weight: 850;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }}

        .info-card, .event-card, .statement-card, .stakeholder-card {{
            background: var(--surface);
            border: 1px solid #DCE3EA;
            border-radius: 1rem;
            box-shadow: 0 8px 22px rgba(20,42,66,.06);
        }}
        .info-card {{ padding: 1.15rem 1.2rem; min-height: 9.3rem; }}
        .info-card .number {{
            width: 2rem;
            height: 2rem;
            display: grid;
            place-items: center;
            border-radius: .6rem;
            background: var(--ud-red);
            color: white;
            font-weight: 850;
            margin-bottom: .75rem;
        }}
        .info-card h3 {{ margin: 0 0 .35rem; font-size: 1.05rem; }}
        .info-card p {{ color: var(--muted); margin: 0; font-size: .92rem; line-height: 1.45; }}

        .event-card {{ padding: 1rem 1.1rem; margin: .55rem 0 .2rem; border-left: 5px solid var(--ud-blue); }}
        .event-card h4 {{ color: var(--ud-navy); margin: 0 0 .2rem; font-size: 1rem; }}
        .event-card p {{ color: var(--muted); margin: 0; line-height: 1.42; }}
        .event-amount {{ color: var(--ud-blue); font-weight: 850; white-space: nowrap; }}

        .choice-snapshot {{
            background: #EAF2F8;
            border: 1px solid #C5D9EA;
            border-radius: .85rem;
            padding: .8rem 1rem;
            color: var(--ud-navy);
            font-weight: 650;
            margin-bottom: 1rem;
        }}

        .activity-lane {{
            border-radius: 1rem;
            padding: 1rem 1.05rem;
            min-height: 8.4rem;
            background: white;
            border-top: 5px solid var(--lane-color);
            box-shadow: 0 8px 22px rgba(20,42,66,.06);
        }}
        .activity-lane h3 {{ margin: 0 0 .35rem; font-size: 1.05rem; }}
        .activity-lane p {{ margin: 0; color: var(--muted); font-size: .9rem; line-height: 1.42; }}

        .equation {{
            display: grid;
            grid-template-columns: 1fr auto 1fr auto 1fr;
            align-items: center;
            gap: .85rem;
            background: linear-gradient(135deg, var(--ud-navy), var(--ud-blue));
            color: white;
            border-radius: 1rem;
            padding: 1.15rem 1.35rem;
            box-shadow: 0 12px 26px rgba(0,45,98,.14);
            margin: .75rem 0 1.25rem;
        }}
        .equation .term {{ text-align: center; }}
        .equation .label {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .1em; opacity: .76; }}
        .equation .value {{ font-size: 1.45rem; font-weight: 850; }}
        .equation .operator {{ font-size: 1.55rem; opacity: .72; }}

        .statement-card {{ padding: 1.25rem 1.35rem; margin-top: .8rem; }}
        .statement-heading {{ text-align: center; padding-bottom: .75rem; border-bottom: 2px solid var(--ud-navy); }}
        .statement-heading h3 {{ margin: 0; }}
        .statement-heading p {{ margin: .2rem 0 0; color: var(--muted); font-size: .86rem; }}
        .statement-row {{ display: flex; justify-content: space-between; gap: 1rem; padding: .38rem .2rem; }}
        .statement-row.indent {{ padding-left: 1.25rem; color: var(--muted); }}
        .statement-row.total {{ border-top: 1px solid #AEBAC5; font-weight: 800; color: var(--ud-navy); margin-top: .25rem; }}
        .statement-row.grand-total {{ border-top: 3px double var(--ud-navy); font-weight: 900; color: var(--ud-navy); }}

        .flow {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: .7rem;
            align-items: stretch;
            margin: 1rem 0;
        }}
        .flow-step {{
            position: relative;
            background: white;
            border: 1px solid #DCE3EA;
            border-radius: .9rem;
            padding: 1rem;
            text-align: center;
        }}
        .flow-step:not(:last-child)::after {{
            content: "→";
            position: absolute;
            right: -.72rem;
            top: 42%;
            width: .75rem;
            color: var(--ud-red);
            font-weight: 900;
            z-index: 2;
        }}
        .flow-step strong {{ color: var(--ud-navy); display: block; margin-bottom: .3rem; }}
        .flow-step span {{ color: var(--muted); font-size: .84rem; line-height: 1.35; }}

        .stakeholder-card {{ padding: 1.2rem 1.25rem; border-top: 5px solid var(--ud-red); min-height: 13rem; }}
        .stakeholder-card h3 {{ margin-top: 0; }}
        .stakeholder-card .question {{ color: var(--ud-navy); font-weight: 750; font-size: 1.04rem; }}
        .stakeholder-card .evidence {{ color: var(--muted); font-size: .92rem; }}

        .sidebar-brand {{
            border-bottom: 1px solid rgba(255,255,255,.18);
            padding: .4rem 0 1rem;
            margin-bottom: 1rem;
        }}
        .sidebar-brand .course {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .13em; opacity: .75; }}
        .sidebar-brand .name {{ font-size: 1.18rem; font-weight: 850; margin-top: .2rem; }}
        .sidebar-progress {{ margin: 1.2rem 0 .5rem; font-size: .82rem; opacity: .8; }}
        .progress-track {{ height: .42rem; background: rgba(255,255,255,.15); border-radius: 99px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: var(--ud-red); border-radius: 99px; }}

        div.stButton > button, div.stFormSubmitButton > button {{
            border-radius: .7rem;
            font-weight: 760;
            min-height: 2.65rem;
        }}
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {{
            background: var(--ud-red);
            border-color: var(--ud-red);
        }}
        div[data-testid="stMetric"] {{
            background: white;
            border: 1px solid #DCE3EA;
            border-radius: .9rem;
            padding: .8rem 1rem;
            box-shadow: 0 6px 18px rgba(20,42,66,.05);
        }}

        @media (max-width: 760px) {{
            .hero {{ padding: 1.6rem 1.4rem; }}
            .equation {{ grid-template-columns: 1fr; gap: .35rem; }}
            .equation .operator {{ transform: rotate(90deg); line-height: .8; }}
            .flow {{ grid-template-columns: 1fr; }}
            .flow-step:not(:last-child)::after {{ content: "↓"; right: 49%; top: auto; bottom: -.75rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults = {
        "page": PAGES[0],
        "funding_choice": "Balanced",
        "asset_choice": "Essential setup",
        "operating_choice": "Balanced growth",
        "dividend_choice": "Return some value to shareholders",
        "organization_checked": False,
        "scenario_choices": None,
        "activity_answers": {},
        "activity_checked": False,
        "statement_checked": False,
        "scroll_to_top": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_experience() -> None:
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state.page = PAGES[0]
    st.session_state.scroll_to_top = True


def launch_scenario() -> None:
    st.session_state.scenario_choices = {
        "funding_plan": st.session_state.funding_choice,
        "asset_plan": st.session_state.asset_choice,
        "operating_plan": st.session_state.operating_choice,
        "dividend_policy": st.session_state.dividend_choice,
    }
    st.session_state.activity_answers = {}
    st.session_state.activity_checked = False
    st.session_state.statement_checked = False
    st.session_state.page = PAGES[1]
    st.session_state.scroll_to_top = True


def go_to(page: str) -> None:
    st.session_state.page = page
    st.session_state.scroll_to_top = True


def request_scroll_top() -> None:
    st.session_state.scroll_to_top = True


def apply_pending_scroll() -> None:
    """Start a newly selected station at its heading, not the prior page position."""

    if st.session_state.scroll_to_top:
        st.iframe(
            """
            <script>
            const main = window.parent.document.querySelector('section[data-testid="stMain"]');
            if (main) main.scrollTo({top: 0, left: 0, behavior: 'instant'});
            </script>
            """,
            height=1,
            tab_index=-1,
        )
        st.session_state.scroll_to_top = False


def money(value: int) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">University of Dayton · ACC 202</div>
            <h1>Anatomy of a Business</h1>
            <p>Build a company, follow its activities, and discover how financial statements tell one connected story.</p>
            <div class="chapter-pill">Chapter 1 · Introduction to Business and Financial Statements</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="course">ACC 202 · Chapter 1</div>
                <div class="name">Anatomy of a Business</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.radio(
            "Explore the business",
            PAGES,
            key="page",
            label_visibility="collapsed",
            on_change=request_scroll_top,
        )

        progress = 25
        if st.session_state.scenario_choices:
            progress = 50
        if st.session_state.activity_checked:
            progress = 75
        if st.session_state.statement_checked:
            progress = 100
        st.markdown(
            f"""
            <div class="sidebar-progress">Learning journey · {progress}%</div>
            <div class="progress-track"><div class="progress-fill" style="width:{progress}%"></div></div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Chapter 1 lens")
        st.caption(
            "Business activities → account categories → financial statements → decisions"
        )
        with st.expander("Quick definitions"):
            st.markdown(
                """
                **Financing:** obtaining or returning funds from owners and creditors  
                **Investing:** acquiring resources needed to operate  
                **Operating:** producing and delivering goods or services  
                **Accounting:** identifying, recording, and communicating economic events
                """
            )
        st.button("Start over", on_click=reset_experience, use_container_width=True)


def intro_cards() -> None:
    columns = st.columns(3)
    cards = (
        (
            "1",
            "Make business choices",
            "Select how a simple corporation will raise funds, acquire resources, operate, and reward owners.",
        ),
        (
            "2",
            "Follow the activities",
            "Classify each economic event as financing, investing, or operating.",
        ),
        (
            "3",
            "Read the business story",
            "See how accounts organize the events into four connected financial statements.",
        ),
    )
    for column, (number, title, text) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="number">{number}</div>
                    <h3>{title}</h3>
                    <p>{text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_launch_lab() -> None:
    st.markdown('<div class="eyebrow">Station 1</div>', unsafe_allow_html=True)
    st.header("Launch the company")
    st.markdown(
        '<p class="section-lead">Begin with the business itself. The accounting system exists to capture and communicate what the business does.</p>',
        unsafe_allow_html=True,
    )
    intro_cards()

    st.subheader("Why organize as a corporation?")
    st.write(
        "Our campus service expects several investors, wants to raise substantial funds, "
        "and wants owners to avoid personal liability. Which organization fits best?"
    )
    answer = st.radio(
        "Choose an organization",
        ("Sole proprietorship", "Partnership", "Corporation"),
        horizontal=True,
        key="organization_answer",
    )
    if st.button("Check the organization", type="secondary"):
        st.session_state.organization_checked = True
    if st.session_state.organization_checked:
        if answer == "Corporation":
            st.success(
                "Exactly. A corporation is a separate legal entity that can make "
                "ownership transfer and fundraising easier while limiting owners’ "
                "personal liability."
            )
        else:
            st.info(
                "That form can work for many businesses, but this scenario points to "
                "a corporation because it needs multiple investors, easier fundraising, "
                "and limited personal liability."
            )

    st.subheader("Choose the first-year plan")
    st.caption(
        "Every option produces a complete, balanced example. The choices change the "
        "financial story—not the underlying accounting relationships."
    )
    c1, c2 = st.columns(2)
    with c1:
        funding = st.selectbox(
            "How should the business be financed?",
            FUNDING_PLANS,
            key="funding_choice",
        )
        st.caption(FUNDING_PLANS[funding]["description"])
        asset = st.selectbox(
            "What resources should it acquire?",
            ASSET_PLANS,
            key="asset_choice",
        )
        st.caption(ASSET_PLANS[asset]["description"])
    with c2:
        operating = st.selectbox(
            "How ambitious should operations be?",
            OPERATING_PLANS,
            key="operating_choice",
        )
        st.caption(OPERATING_PLANS[operating]["description"])
        dividend = st.selectbox(
            "What should happen after a successful year?",
            DIVIDEND_POLICIES,
            key="dividend_choice",
        )
        st.caption(DIVIDEND_POLICIES[dividend]["description"])

    st.button(
        "Launch the business →",
        type="primary",
        on_click=launch_scenario,
        use_container_width=True,
    )


def require_scenario() -> bool:
    if st.session_state.scenario_choices:
        return True
    st.info("Launch a business in Station 1 before exploring this station.")
    st.button(
        "Go to Launch Lab",
        type="primary",
        on_click=go_to,
        args=(PAGES[0],),
    )
    return False


def current_scenario():
    return build_scenario(**st.session_state.scenario_choices)


def render_event_card(event: BusinessEvent) -> None:
    st.markdown(
        f"""
        <div class="event-card">
            <h4>{escape(event.title)} <span class="event-amount">· {money(event.amount)}</span></h4>
            <p>{escape(event.description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_activity_map() -> None:
    st.markdown('<div class="eyebrow">Station 2</div>', unsafe_allow_html=True)
    st.header("Follow the business activities")
    st.markdown(
        '<p class="section-lead">The accounting information system tracks the results of financing, investing, and operating activities. Classify each event by its business purpose.</p>',
        unsafe_allow_html=True,
    )
    if not require_scenario():
        return

    scenario = current_scenario()
    choices = st.session_state.scenario_choices
    st.markdown(
        f"""
        <div class="choice-snapshot">
            Plan: {escape(choices['funding_plan'])} financing · {escape(choices['asset_plan'])} · {escape(choices['operating_plan'])} · {escape(choices['dividend_policy'])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("activity_classification"):
        for index, event in enumerate(scenario.events, start=1):
            left, right = st.columns([2.15, 1])
            with left:
                render_event_card(event)
            with right:
                st.selectbox(
                    f"Classify event {index}",
                    ("Not sure yet",) + ACTIVITY_TYPES,
                    key=f"activity_{event.event_id}",
                )
        submitted = st.form_submit_button(
            "Check the activity map",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        st.session_state.activity_answers = {
            event.event_id: st.session_state[f"activity_{event.event_id}"]
            for event in scenario.events
        }
        st.session_state.activity_checked = True

    if not st.session_state.activity_checked:
        return

    score, results = grade_activity_answers(
        scenario, st.session_state.activity_answers
    )
    if score == len(results):
        st.success(f"Complete map: {score} of {len(results)} activities are correct.")
    else:
        st.warning(
            f"You mapped {score} of {len(results)} correctly. Review the purpose of "
            "each event below—the financial statements are still available for exploration."
        )

    for event, answer, is_correct in results:
        with st.expander(
            f"{'✓' if is_correct else '↺'} {event.title} — {event.activity_type}",
            expanded=not is_correct,
        ):
            if not is_correct:
                st.write(f"Your answer: **{answer}**")
            st.write(event.explanation)
            st.caption(
                f"Account categories: {', '.join(event.account_categories)} · "
                f"Statements affected: {', '.join(event.statements)}"
            )

    st.subheader("The three activity lanes")
    lanes = (
        ("Financing", "#CE1141", "How the business obtains funds from owners and creditors—and returns funds to owners."),
        ("Investing", "#8A5A00", "How the business acquires the long-term resources it needs to operate."),
        ("Operating", "#007A70", "How the business performs its day-to-day work to earn revenue and incur expenses."),
    )
    columns = st.columns(3)
    for column, (name, color, text) in zip(columns, lanes):
        with column:
            event_count = sum(e.activity_type == name for e in scenario.events)
            st.markdown(
                f"""
                <div class="activity-lane" style="--lane-color:{color}">
                    <h3>{name}</h3>
                    <p>{text}</p>
                    <p><strong>{event_count} event{'s' if event_count != 1 else ''} in this business</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.button(
        "See the financial statements →",
        type="primary",
        on_click=go_to,
        args=(PAGES[2],),
        use_container_width=True,
    )


def statement_html(title: str, subtitle: str, rows: list[tuple[str, int, str]]) -> str:
    body = []
    for label, value, row_class in rows:
        body.append(
            f'<div class="statement-row {row_class}"><span>{escape(label)}</span><span>{money(value)}</span></div>'
        )
    return (
        '<div class="statement-card">'
        f'<div class="statement-heading"><h3>{escape(title)}</h3><p>{escape(subtitle)}</p></div>'
        + "".join(body)
        + "</div>"
    )


def render_financial_statements() -> None:
    st.markdown('<div class="eyebrow">Station 3</div>', unsafe_allow_html=True)
    st.header("Read the financial statement story")
    st.markdown(
        '<p class="section-lead">Accounts organize the company’s activities. The four statements then communicate performance, retained earnings, financial position, and cash activity.</p>',
        unsafe_allow_html=True,
    )
    if not require_scenario():
        return

    scenario = current_scenario()
    summary = calculate_summary(scenario)
    balance_status = "Balanced" if summary.is_balanced else "Check needed"

    st.markdown(
        f"""
        <div class="equation">
            <div class="term"><div class="label">Assets</div><div class="value">{money(summary.total_assets)}</div></div>
            <div class="operator">=</div>
            <div class="term"><div class="label">Liabilities</div><div class="value">{money(summary.notes_payable)}</div></div>
            <div class="operator">+</div>
            <div class="term"><div class="label">Stockholders’ equity</div><div class="value">{money(summary.common_stock + summary.ending_retained_earnings)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Accounting equation status: {balance_status}. Assets are the resources; "
        "liabilities and stockholders’ equity are the claims on those resources."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue", money(summary.revenue))
    m2.metric("Net income", money(summary.net_income))
    m3.metric("Ending cash", money(summary.cash))
    m4.metric("Total assets", money(summary.total_assets))

    income_tab, retained_tab, balance_tab, cash_tab, connections_tab = st.tabs(
        (
            "1 · Income Statement",
            "2 · Retained Earnings",
            "3 · Balance Sheet",
            "4 · Cash Flows",
            "Connect the Statements",
        )
    )
    with income_tab:
        st.markdown(
            statement_html(
                "Campus Service Corporation",
                "Income Statement · For the Year",
                [
                    ("Service revenue", summary.revenue, ""),
                    ("Wages expense", summary.wages_expense, "indent"),
                    ("Other operating expenses", summary.other_expenses, "indent"),
                    ("Total expenses", summary.total_expenses, "total"),
                    ("Net income", summary.net_income, "grand-total"),
                ],
            ),
            unsafe_allow_html=True,
        )
        st.info("Question answered: Were the company’s operations successful during the period?")

    with retained_tab:
        st.markdown(
            statement_html(
                "Campus Service Corporation",
                "Retained Earnings · For the Year",
                [
                    ("Beginning retained earnings", 0, ""),
                    ("Add: Net income", summary.net_income, ""),
                    ("Less: Dividends", summary.dividends, "indent"),
                    ("Ending retained earnings", summary.ending_retained_earnings, "grand-total"),
                ],
            ),
            unsafe_allow_html=True,
        )
        st.info(
            "Connection: Net income comes from the income statement. Ending retained "
            "earnings will appear in stockholders’ equity on the balance sheet."
        )

    with balance_tab:
        st.markdown(
            statement_html(
                "Campus Service Corporation",
                "Balance Sheet · End of Year",
                [
                    ("Cash", summary.cash, "indent"),
                    ("Equipment", summary.equipment, "indent"),
                    ("Total assets", summary.total_assets, "grand-total"),
                    ("Notes payable", summary.notes_payable, "indent"),
                    ("Common stock", summary.common_stock, "indent"),
                    ("Retained earnings", summary.ending_retained_earnings, "indent"),
                    (
                        "Total liabilities and stockholders’ equity",
                        summary.total_liabilities_and_equity,
                        "grand-total",
                    ),
                ],
            ),
            unsafe_allow_html=True,
        )
        st.info("Question answered: What resources and claims exist at this point in time?")

    with cash_tab:
        st.markdown(
            statement_html(
                "Campus Service Corporation",
                "Statement of Cash Flows · For the Year",
                [
                    ("Cash from operating activities", summary.operating_cash_flow, ""),
                    ("Cash from investing activities", summary.investing_cash_flow, ""),
                    ("Cash from financing activities", summary.financing_cash_flow, ""),
                    ("Net change in cash", summary.net_change_in_cash, "total"),
                    ("Beginning cash", 0, "indent"),
                    ("Ending cash", summary.cash, "grand-total"),
                ],
            ),
            unsafe_allow_html=True,
        )
        st.info("Question answered: Where did cash come from, and how was it used?")

    with connections_tab:
        st.markdown(
            f"""
            <div class="flow">
                <div class="flow-step"><strong>Income Statement</strong><span>Calculates net income of {money(summary.net_income)}</span></div>
                <div class="flow-step"><strong>Retained Earnings</strong><span>Uses net income and dividends to reach {money(summary.ending_retained_earnings)}</span></div>
                <div class="flow-step"><strong>Balance Sheet</strong><span>Uses ending retained earnings and reports cash of {money(summary.cash)}</span></div>
                <div class="flow-step"><strong>Cash Flows</strong><span>Explains the change that produced ending cash of {money(summary.cash)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(
            "The statements answer different questions, but they describe the same "
            "business. That is why amounts reappear and connect across statements."
        )

    st.subheader("Statement checkpoint")
    with st.form("statement_checkpoint"):
        first_statement = st.radio(
            "Which statement must be prepared first?",
            ("Balance Sheet", "Income Statement", "Statement of Cash Flows"),
            horizontal=True,
        )
        connection = st.radio(
            "Where does ending retained earnings appear next?",
            ("As an expense", "In stockholders’ equity", "As financing revenue"),
            horizontal=True,
        )
        checked = st.form_submit_button("Check the connections", type="primary")
    if checked:
        st.session_state.statement_checked = True
        if first_statement == "Income Statement" and connection == "In stockholders’ equity":
            st.success("Both connections are correct. You have reconstructed the reporting sequence.")
        else:
            st.warning(
                "Review the flow: the income statement produces net income; retained "
                "earnings then becomes part of stockholders’ equity on the balance sheet."
            )

    st.button(
        "Enter the Decision Desk →",
        type="primary",
        on_click=go_to,
        args=(PAGES[3],),
        use_container_width=True,
    )


def stakeholder_card(
    title: str, question: str, evidence: str, interpretation: str
) -> None:
    st.markdown(
        f"""
        <div class="stakeholder-card">
            <h3>{escape(title)}</h3>
            <div class="question">“{escape(question)}”</div>
            <p class="evidence"><strong>Look first:</strong> {escape(evidence)}</p>
            <p>{escape(interpretation)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_desk() -> None:
    st.markdown('<div class="eyebrow">Station 4</div>', unsafe_allow_html=True)
    st.header("Use the information to make decisions")
    st.markdown(
        '<p class="section-lead">Accounting communicates the same economic events to users with different questions. Change perspectives to see what each user notices.</p>',
        unsafe_allow_html=True,
    )
    if not require_scenario():
        return

    summary = calculate_summary(current_scenario())
    investor, creditor, manager = st.tabs(("Investor", "Creditor", "Manager"))
    with investor:
        stakeholder_card(
            "External user · Investor",
            "Did the company operate successfully, and how much value remains in the business?",
            "Income statement, retained earnings, and balance sheet",
            (
                f"The company earned {money(summary.net_income)} and ended with "
                f"stockholders’ equity of {money(summary.common_stock + summary.ending_retained_earnings)}."
            ),
        )
    with creditor:
        stakeholder_card(
            "External user · Creditor",
            "What resources support the company’s promise to repay its debt?",
            "Balance sheet and statement of cash flows",
            (
                f"The company reports {money(summary.total_assets)} of assets and "
                f"{money(summary.notes_payable)} owed to the bank."
            ),
        )
    with manager:
        stakeholder_card(
            "Internal user · Manager",
            "How did our financing, investing, and operating choices shape the business?",
            "All four statements plus detailed internal reports",
            (
                f"Operations generated {money(summary.operating_cash_flow)} of cash; "
                f"the company invested {money(abs(summary.investing_cash_flow))} in equipment."
            ),
        )

    st.subheader("What surrounds the financial statements?")
    st.write(
        "A public company’s annual report gives users more than four statements. "
        "Open each component to see its role."
    )
    annual_report_items = {
        "Management Discussion and Analysis (MD&A)": (
            "Management discusses results, near-term obligations, and the ability to "
            "fund operations and expansion."
        ),
        "Notes to the Financial Statements": (
            "The notes clarify policies, uncertainties, and details that do not fit "
            "comfortably on the face of the statements."
        ),
        "Auditor’s Report": (
            "An independent CPA expresses an opinion about whether the statements "
            "fairly present the company’s financial position and results under GAAP."
        ),
        "Emerging reporting": (
            "ESG and cybersecurity reporting provide additional perspectives on risks, "
            "responsibilities, and impacts."
        ),
    }
    for label, text in annual_report_items.items():
        with st.expander(label):
            st.write(text)

    st.subheader("Class debrief")
    c1, c2, c3 = st.columns(3)
    prompts = (
        "Which business choice changed the company’s financial position most?",
        "Why do users need four statements instead of one all-purpose report?",
        "Which statement would you examine first as an investor, creditor, or manager—and why?",
    )
    for column, prompt in zip((c1, c2, c3), prompts):
        with column:
            st.markdown(
                f'<div class="info-card"><div class="number">?</div><p>{escape(prompt)}</p></div>',
                unsafe_allow_html=True,
            )

    st.success(
        "You completed the anatomy: business decisions created activities; activities "
        "affected accounts; accounts formed statements; statements supported decisions."
    )


inject_styles()
initialize_state()
sidebar()
apply_pending_scroll()
hero()

if st.session_state.page == PAGES[0]:
    render_launch_lab()
elif st.session_state.page == PAGES[1]:
    render_activity_map()
elif st.session_state.page == PAGES[2]:
    render_financial_statements()
else:
    render_decision_desk()
