import unittest
from browser_support import browser_app
from accounting import build_scenario, calculate_summary
from browser.build import shared_source


def button(app,label):
    return next(item for item in app.button if item.label==label)


class CompleteBrowserLessonTests(unittest.TestCase):
    def test_all_stations_and_statement_review(self):
        app=browser_app().run()
        button(app,'Launch the business →').click().run()
        self.assertFalse(any(b.label == 'See the financial statements →' for b in app.button))
        scenario=build_scenario('Balanced','Essential setup','Balanced growth','Return some value to shareholders')
        for event in scenario.events:
            app.selectbox(key='activity_'+event.event_id).set_value(event.activity_type)
        button(app,'Check the activity map').click().run()
        button(app,'See the financial statements →').click().run()
        self.assertTrue(button(app,'Enter the Decision Desk →').disabled)
        namespace={}
        exec(shared_source(),namespace)
        questions=namespace['statement_question_data'](calculate_summary(scenario))
        for name,question in questions.items():
            app.radio(key='statement_selection').set_value(name).run()
            app.radio(key=namespace['statement_answer_key'](name)).set_value(question['correct'])
            button(app,'Check this statement').click().run()
        button(app,'Enter the Decision Desk →').click().run()
        button(app,'Complete the activity').click().run()
        self.assertTrue(app.session_state.decision_completed)
        before=app.query_params['progress']
        button(app,'Back').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs),4)
        self.assertEqual(app.query_params['progress'],before)
        self.assertEqual(len(app.radio),0)
        self.assertEqual([b.label for b in app.main.button],['Back','Forward'])
