import itertools
import unittest

from accounting import (
    ACTIVITY_TYPES,
    ASSET_PLANS,
    DIVIDEND_POLICIES,
    FUNDING_PLANS,
    OPERATING_PLANS,
    build_scenario,
    calculate_summary,
    grade_activity_answers,
)


class ScenarioTests(unittest.TestCase):
    def all_scenarios(self):
        for choices in itertools.product(
            FUNDING_PLANS,
            ASSET_PLANS,
            OPERATING_PLANS,
            DIVIDEND_POLICIES,
        ):
            yield build_scenario(*choices)

    def test_every_scenario_balances(self):
        for scenario in self.all_scenarios():
            with self.subTest(scenario=scenario):
                summary = calculate_summary(scenario)
                self.assertTrue(summary.is_balanced)

    def test_cash_flow_reconciles_to_balance_sheet_cash(self):
        for scenario in self.all_scenarios():
            with self.subTest(scenario=scenario):
                summary = calculate_summary(scenario)
                self.assertEqual(summary.net_change_in_cash, summary.cash)

    def test_scenarios_cover_all_three_activity_types(self):
        for scenario in self.all_scenarios():
            represented = {event.activity_type for event in scenario.events}
            self.assertEqual(represented, set(ACTIVITY_TYPES))

    def test_retained_earnings_uses_net_income_and_dividends(self):
        for scenario in self.all_scenarios():
            summary = calculate_summary(scenario)
            self.assertEqual(
                summary.ending_retained_earnings,
                summary.net_income - summary.dividends,
            )

    def test_activity_grading_uses_business_purpose(self):
        scenario = build_scenario(
            "Balanced",
            "Essential setup",
            "Balanced growth",
            "Return some value to shareholders",
        )
        answers = {
            event.event_id: event.activity_type for event in scenario.events
        }
        score, results = grade_activity_answers(scenario, answers)
        self.assertEqual(score, len(scenario.events))
        self.assertTrue(all(is_correct for _, _, is_correct in results))

    def test_dividends_are_not_an_expense(self):
        scenario = build_scenario(
            "Balanced",
            "Essential setup",
            "Balanced growth",
            "Return some value to shareholders",
        )
        dividend_event = next(
            event for event in scenario.events if event.event_id == "pay_dividend"
        )
        self.assertNotIn("Expense", dividend_event.account_categories)
        self.assertEqual(dividend_event.activity_type, "Financing")


if __name__ == "__main__":
    unittest.main()

