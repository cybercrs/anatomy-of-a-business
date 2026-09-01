import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from accounting import build_scenario
from resume_state import decode_resume_state


APP_PATH = Path(__file__).parents[1] / "streamlit_app.py"


def button_with_label(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def widget_with_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


def progress_token(app: AppTest) -> str:
    value = app.query_params["progress"]
    return value[-1] if isinstance(value, list) else value


class StreamlitFlowTests(unittest.TestCase):
    def test_income_statement_progress_survives_a_new_session(self):
        app = AppTest.from_file(APP_PATH).run()
        widget_with_key(app.selectbox, "funding_choice").select("Owner-powered").run()
        button_with_label(app, "Launch the business →").click().run()

        scenario = build_scenario(
            "Owner-powered",
            "Essential setup",
            "Balanced growth",
            "Return some value to shareholders",
        )
        for event in scenario.events:
            widget_with_key(app.selectbox, f"activity_{event.event_id}").select(
                event.activity_type
            )
        button_with_label(app, "Check the activity map").click().run()
        self.assertTrue(
            any("Complete map" in message.value for message in app.success)
        )

        button_with_label(app, "See the financial statements →").click().run()
        income_answer = widget_with_key(
            app.radio, "statement_answer_income_statement"
        )
        correct_answer = next(
            option for option in income_answer.options if "earned net income" in option
        )
        income_answer.set_value(correct_answer).run()
        button_with_label(app, "Check this statement").click().run()
        self.assertTrue(any(message.value.startswith("Correct.") for message in app.success))
        self.assertEqual(app.session_state["page"], "3 · Financial Statements")

        resumed = AppTest.from_file(APP_PATH)
        resumed.query_params["progress"] = [progress_token(app)]
        resumed.run()

        self.assertFalse(list(resumed.exception))
        self.assertEqual(resumed.session_state["page"], "3 · Financial Statements")
        self.assertEqual(resumed.session_state["funding_choice"], "Owner-powered")
        self.assertTrue(resumed.session_state["statement_results"]["Income Statement"])
        self.assertTrue(
            any(message.value.startswith("Correct.") for message in resumed.success)
        )

    def test_start_over_replaces_saved_progress(self):
        app = AppTest.from_file(APP_PATH).run()
        button_with_label(app, "Launch the business →").click().run()
        button_with_label(app, "Start over").click().run()

        saved = decode_resume_state(progress_token(app))
        self.assertIsNotNone(saved)
        self.assertEqual(saved["page"], 0)
        self.assertFalse(saved["launched"])
        self.assertIsNone(app.session_state["scenario_choices"])


if __name__ == "__main__":
    unittest.main()
