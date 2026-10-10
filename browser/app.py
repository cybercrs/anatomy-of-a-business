"""Browser entrypoint; the Community Cloud script is kept unchanged."""
import runpy
from pathlib import Path
import sys
# Stlite puts the entrypoint directory first; keep root packages authoritative.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from browser.common import LiveUI, ReviewUI, VIEW_KEY, restore_view, keep_widgets, navigation, save_view, scroll
from browser.navigation import frontier, can_advance, normalize_restored

app = runpy.run_path(str(Path(__file__).with_name('shared_app.py')))
g = app['go_to'].__globals__
app['initialize_state']()
app['restore_progress_from_url']()
normalize_restored(st.session_state)
if VIEW_KEY not in st.session_state:
    restore_view(st.session_state, st.query_params.get('view'), frontier(st.session_state))
    restored = {'funding_choice','asset_choice','operating_choice','dividend_choice','organization_answer','statement_selection'}
    restored.update('activity_' + key for key in app['progress_snapshot']()['activity_selections'])
    restored.update(app['statement_answer_key'](name) for name in app['STATEMENT_NAMES'])
    st.session_state['_browser_widgets'] = sorted(key for key in restored if key in st.session_state)
keep_widgets(st.session_state)


def transition(original, *args):
    if st.session_state[VIEW_KEY] != frontier(st.session_state):
        return
    original(*args)
    st.session_state[VIEW_KEY] = frontier(st.session_state)
    st.session_state['_browser_scroll'] = True


def go_to(page):
    target = app['PAGES'].index(page)
    if can_advance(st.session_state, target):
        transition(app['go_to'], page)


def restart():
    if st.session_state[VIEW_KEY] != frontier(st.session_state):
        return
    app['reset_experience']()
    app['initialize_state']()
    st.session_state[VIEW_KEY] = 0


class UI(LiveUI):
    def radio(self, label, options, **kwargs):
        if kwargs.get('key') == 'page':
            st.caption(' · '.join(page.split(' · ', 1)[1] for page in options[:frontier(st.session_state) + 1]))
            return st.session_state.page
        return super().__getattr__('radio')(label, options, **kwargs)

    def button(self, label, **kwargs):
        if kwargs.get('on_click') is restart:
            kwargs['disabled'] = st.session_state[VIEW_KEY] < frontier(st.session_state)
        if kwargs.get('on_click') is go_to:
            target = app['PAGES'].index(kwargs['args'][0])
            kwargs['disabled'] = not can_advance(st.session_state, target)
        return super().button(label, **kwargs)


g.update(st=UI(), go_to=go_to,
         launch_scenario=lambda: transition(app['launch_scenario']), reset_experience=restart)
app['hero']()
reached = frontier(st.session_state)
app['sidebar']()
navigation(st.session_state, reached, len(app['PAGES']))
view = st.session_state[VIEW_KEY]
if view < reached:
    ui = ReviewUI(st.session_state)
    ui.session_state.page = app['PAGES'][view]
    g['st'] = ui
renderers = ('render_launch_lab','render_activity_map','render_financial_statements','render_decision_desk')
if view == 2 and view < reached:
    # Four peer statement views remain available for inspection without edits.
    for tab, name in zip(st.tabs(app['STATEMENT_NAMES']), app['STATEMENT_NAMES']):
        with tab:
            ui.session_state.statement_selection = name
            app['render_financial_statements']()
else:
    app[renderers[view]]()
g['st'] = st
app['save_progress_to_url']()
save_view(st.session_state)
scroll()
