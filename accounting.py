"""Core accounting model for the Anatomy of a Business demonstration.

The model intentionally uses simple, cash-based introductory events. It is not
a journal-entry trainer; it connects business activities to account categories
and the four financial statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ACTIVITY_TYPES = ("Financing", "Investing", "Operating")

FUNDING_PLANS = {
    "Owner-powered": {
        "description": "Rely primarily on shareholders.",
        "common_stock": 100_000,
        "loan": 20_000,
    },
    "Balanced": {
        "description": "Use an even mix of owners and creditors.",
        "common_stock": 70_000,
        "loan": 50_000,
    },
    "Credit-forward": {
        "description": "Use more creditor financing and less owner financing.",
        "common_stock": 40_000,
        "loan": 80_000,
    },
}

ASSET_PLANS = {
    "Essential setup": {
        "description": "A focused equipment package for a small launch.",
        "equipment": 45_000,
    },
    "Expanded setup": {
        "description": "More equipment to support a larger operation.",
        "equipment": 65_000,
    },
}

OPERATING_PLANS = {
    "Focused service": {
        "description": "A smaller operation with a controlled cost base.",
        "revenue": 58_000,
        "wages": 22_000,
        "other_expenses": 18_000,
    },
    "Balanced growth": {
        "description": "A moderate expansion in customers and staffing.",
        "revenue": 76_000,
        "wages": 30_000,
        "other_expenses": 22_000,
    },
    "Big campus push": {
        "description": "A larger launch with more revenue and higher costs.",
        "revenue": 100_000,
        "wages": 40_000,
        "other_expenses": 31_000,
    },
}

DIVIDEND_POLICIES = {
    "Keep earnings in the business": {
        "description": "Pay no dividend this year.",
        "dividends": 0,
    },
    "Return some value to shareholders": {
        "description": "Pay a modest cash dividend.",
        "dividends": 10_000,
    },
}


@dataclass(frozen=True)
class BusinessEvent:
    """A plain-language business event and its introductory classifications."""

    event_id: str
    title: str
    description: str
    amount: int
    activity_type: str
    account_effects: dict[str, int]
    account_categories: tuple[str, ...]
    statements: tuple[str, ...]
    explanation: str

    @property
    def cash_effect(self) -> int:
        return self.account_effects.get("Cash", 0)


@dataclass(frozen=True)
class Scenario:
    """A complete first-year scenario selected by the student."""

    funding_plan: str
    asset_plan: str
    operating_plan: str
    dividend_policy: str
    events: tuple[BusinessEvent, ...]


@dataclass(frozen=True)
class FinancialSummary:
    """Calculated financial-statement totals for one scenario."""

    cash: int
    equipment: int
    total_assets: int
    notes_payable: int
    common_stock: int
    revenue: int
    wages_expense: int
    other_expenses: int
    total_expenses: int
    net_income: int
    dividends: int
    ending_retained_earnings: int
    total_liabilities_and_equity: int
    operating_cash_flow: int
    investing_cash_flow: int
    financing_cash_flow: int
    net_change_in_cash: int

    @property
    def is_balanced(self) -> bool:
        return self.total_assets == self.total_liabilities_and_equity


def build_scenario(
    funding_plan: str,
    asset_plan: str,
    operating_plan: str,
    dividend_policy: str,
) -> Scenario:
    """Create a scenario from the four student choices."""

    funding = FUNDING_PLANS[funding_plan]
    assets = ASSET_PLANS[asset_plan]
    operations = OPERATING_PLANS[operating_plan]
    dividend = DIVIDEND_POLICIES[dividend_policy]

    events: list[BusinessEvent] = [
        BusinessEvent(
            event_id="issue_stock",
            title="Shareholders invest in the company",
            description=(
                "The corporation issues common stock and receives cash from its "
                "new shareholders."
            ),
            amount=funding["common_stock"],
            activity_type="Financing",
            account_effects={
                "Cash": funding["common_stock"],
                "Common Stock": funding["common_stock"],
            },
            account_categories=("Asset", "Equity"),
            statements=("Balance Sheet", "Statement of Cash Flows"),
            explanation=(
                "Issuing stock raises money from owners, so it is a financing "
                "activity—not revenue from customers."
            ),
        ),
        BusinessEvent(
            event_id="bank_loan",
            title="The company borrows from a bank",
            description=(
                "The bank provides cash and the corporation promises to repay "
                "the note."
            ),
            amount=funding["loan"],
            activity_type="Financing",
            account_effects={
                "Cash": funding["loan"],
                "Notes Payable": funding["loan"],
            },
            account_categories=("Asset", "Liability"),
            statements=("Balance Sheet", "Statement of Cash Flows"),
            explanation=(
                "Borrowing raises money from a creditor, so it is a financing "
                "activity and creates a liability."
            ),
        ),
        BusinessEvent(
            event_id="buy_equipment",
            title="The company purchases equipment",
            description=(
                "The corporation pays cash for the equipment it needs to serve "
                "customers."
            ),
            amount=assets["equipment"],
            activity_type="Investing",
            account_effects={
                "Cash": -assets["equipment"],
                "Equipment": assets["equipment"],
            },
            account_categories=("Asset",),
            statements=("Balance Sheet", "Statement of Cash Flows"),
            explanation=(
                "Purchasing a long-term resource the company will use is an "
                "investing activity. One asset increases while another decreases."
            ),
        ),
        BusinessEvent(
            event_id="serve_customers",
            title="The company serves customers",
            description=(
                "Customers pay cash for the services provided during the year."
            ),
            amount=operations["revenue"],
            activity_type="Operating",
            account_effects={
                "Cash": operations["revenue"],
                "Service Revenue": operations["revenue"],
            },
            account_categories=("Asset", "Revenue"),
            statements=(
                "Income Statement",
                "Retained Earnings",
                "Balance Sheet",
                "Statement of Cash Flows",
            ),
            explanation=(
                "Providing the company’s normal service is an operating activity "
                "and produces revenue."
            ),
        ),
        BusinessEvent(
            event_id="pay_employees",
            title="The company pays employees",
            description=(
                "Employees are paid cash for helping operate the business during "
                "the year."
            ),
            amount=operations["wages"],
            activity_type="Operating",
            account_effects={
                "Cash": -operations["wages"],
                "Wages Expense": operations["wages"],
            },
            account_categories=("Asset", "Expense"),
            statements=(
                "Income Statement",
                "Retained Earnings",
                "Balance Sheet",
                "Statement of Cash Flows",
            ),
            explanation=(
                "Paying employees supports day-to-day operations, so it is an "
                "operating activity and creates an expense."
            ),
        ),
        BusinessEvent(
            event_id="pay_operating_costs",
            title="The company pays its other operating costs",
            description=(
                "The corporation pays cash for rent, utilities, marketing, and "
                "other routine costs."
            ),
            amount=operations["other_expenses"],
            activity_type="Operating",
            account_effects={
                "Cash": -operations["other_expenses"],
                "Operating Expense": operations["other_expenses"],
            },
            account_categories=("Asset", "Expense"),
            statements=(
                "Income Statement",
                "Retained Earnings",
                "Balance Sheet",
                "Statement of Cash Flows",
            ),
            explanation=(
                "Routine costs incurred to generate revenue are operating "
                "activities and expenses."
            ),
        ),
    ]

    if dividend["dividends"]:
        events.append(
            BusinessEvent(
                event_id="pay_dividend",
                title="The company pays a dividend",
                description=(
                    "The board returns some cash to shareholders after the first "
                    "year of business."
                ),
                amount=dividend["dividends"],
                activity_type="Financing",
                account_effects={
                    "Cash": -dividend["dividends"],
                    "Dividends": dividend["dividends"],
                },
                account_categories=("Asset", "Equity"),
                statements=(
                    "Retained Earnings",
                    "Balance Sheet",
                    "Statement of Cash Flows",
                ),
                explanation=(
                    "A dividend is a return to owners, so it is a financing "
                    "activity. It is not an expense."
                ),
            )
        )

    return Scenario(
        funding_plan=funding_plan,
        asset_plan=asset_plan,
        operating_plan=operating_plan,
        dividend_policy=dividend_policy,
        events=tuple(events),
    )


def _account_balance(events: Iterable[BusinessEvent], account: str) -> int:
    return sum(event.account_effects.get(account, 0) for event in events)


def calculate_summary(scenario: Scenario) -> FinancialSummary:
    """Build the simplified four-statement summary for a scenario."""

    events = scenario.events
    cash = _account_balance(events, "Cash")
    equipment = _account_balance(events, "Equipment")
    notes_payable = _account_balance(events, "Notes Payable")
    common_stock = _account_balance(events, "Common Stock")
    revenue = _account_balance(events, "Service Revenue")
    wages = _account_balance(events, "Wages Expense")
    other_expenses = _account_balance(events, "Operating Expense")
    dividends = _account_balance(events, "Dividends")
    total_expenses = wages + other_expenses
    net_income = revenue - total_expenses
    ending_retained_earnings = net_income - dividends

    cash_flows = {
        activity: sum(
            event.cash_effect
            for event in events
            if event.activity_type == activity
        )
        for activity in ACTIVITY_TYPES
    }

    total_assets = cash + equipment
    total_liabilities_and_equity = (
        notes_payable + common_stock + ending_retained_earnings
    )

    return FinancialSummary(
        cash=cash,
        equipment=equipment,
        total_assets=total_assets,
        notes_payable=notes_payable,
        common_stock=common_stock,
        revenue=revenue,
        wages_expense=wages,
        other_expenses=other_expenses,
        total_expenses=total_expenses,
        net_income=net_income,
        dividends=dividends,
        ending_retained_earnings=ending_retained_earnings,
        total_liabilities_and_equity=total_liabilities_and_equity,
        operating_cash_flow=cash_flows["Operating"],
        investing_cash_flow=cash_flows["Investing"],
        financing_cash_flow=cash_flows["Financing"],
        net_change_in_cash=sum(cash_flows.values()),
    )


def grade_activity_answers(
    scenario: Scenario, answers: dict[str, str]
) -> tuple[int, list[tuple[BusinessEvent, str, bool]]]:
    """Grade business-activity classifications in scenario order."""

    results: list[tuple[BusinessEvent, str, bool]] = []
    for event in scenario.events:
        answer = answers.get(event.event_id, "Not sure yet")
        results.append((event, answer, answer == event.activity_type))
    score = sum(is_correct for _, _, is_correct in results)
    return score, results
