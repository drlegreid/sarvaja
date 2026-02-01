"""
Window-Isolated State Management for Trame.

Per GAP-UI-AUDIT-002: Client-side state to prevent multi-window mirroring.

The JS file (static/window_isolator.js) is loaded via a <script> tag
injected into Trame's HTML template by GovernanceDashboard._inject_html_script().

Neither html.Script() nor v-effect works in this Trame/Vue 3 build:
- html.Script: Vue 3 strips <script> tags from component templates
- v-effect: not a registered Vue directive in this build

v6 wraps trame.state.state with a JS Proxy that blocks remote writes
to navigation/selection keys. Only allows writes during local user
interaction (click/keydown on nav elements). Data payloads pass through.

Key findings from v4/v5 debugging:
- state[key] bracket access does NOT work on trame.state
- Vue.watch doesn't fire (state.state is NOT Vue-reactive)
- _updateFromServer is NOT the only state update path
- wslink sets state.state[key] directly (discovered via Proxy logging)
- Proxy on state.state IS the correct interception point

Created: 2026-01-20 (DSP Session)
Updated: 2026-02-01 - v6: Proxy on state.state (replaces v4 Vue.watch / v5 _updateFromServer)
"""


def inject_window_state_isolator() -> None:
    """No-op: script is now loaded via HTML template injection.

    Kept for backward compatibility with governance_dashboard.py import.
    The actual injection is done by GovernanceDashboard._inject_html_script()
    which adds <script src="/govstatic/window_isolator.js"> to index.html.
    """
    pass
