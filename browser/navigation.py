"""Four earned stations; changing the view never changes the learning frontier."""
def frontier(state):
    return ('1 · Launch Lab','2 · Activity Map','3 · Financial Statements','4 · Decision Desk').index(state['page'])


def can_advance(state, target):
    reached = frontier(state)
    return target == reached + 1 and (
        (reached == 0) or
        (reached == 1 and state['activity_checked']) or
        (reached == 2 and state['statement_checked'])
    )


def normalize_restored(state):
    """Old server bookmarks may name a station without its required work."""
    pages = ('1 · Launch Lab','2 · Activity Map','3 · Financial Statements','4 · Decision Desk')
    maximum = 0
    minimum = 0
    if state.get('scenario_choices'):
        maximum = 1
        minimum = 1
        if state.get('activity_checked'):
            maximum = 2
            if state.get('statement_results'):
                minimum = 2
            if state.get('statement_checked'):
                maximum = 3
                if state.get('decision_completed'):
                    minimum = 3
    current = pages.index(state['page'])
    state['page'] = pages[max(minimum, min(current, maximum))]
