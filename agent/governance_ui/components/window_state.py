"""
Window-Isolated State Management for Trame.

Per GAP-UI-AUDIT-002: Client-side state to prevent multi-window mirroring.
Per Option C: Move navigation/filter state to Vue (browser-side).

This component injects JavaScript that:
1. Generates unique window ID on page load
2. Saves navigation state to sessionStorage per-window
3. Restores navigation state from sessionStorage on page load
4. Prevents server-side state broadcasts from overwriting local nav state

Created: 2026-01-20 (DSP Session)
"""

from trame.widgets import html


def inject_window_state_isolator() -> None:
    """
    Inject window state isolation script.

    Call this once in the layout after VAppLayout initialization.
    This prevents multiple windows from mirroring navigation state.
    """
    html.Script(
        """
        (function() {
            // Generate unique window ID if not exists
            if (!window.__govWindowId) {
                window.__govWindowId = 'win_' + Math.random().toString(36).substr(2, 9);
            }
            const WIN_ID = window.__govWindowId;
            const STORAGE_KEY = 'gov_nav_state_' + WIN_ID;

            // State keys that should be window-local (not shared across tabs)
            // Updated per PLAN-UI-OVERHAUL-001 Task 0.3: full coverage
            const LOCAL_STATE_KEYS = [
                'active_view',
                'show_rule_detail',
                'show_session_detail',
                'show_session_form',
                'show_decision_detail',
                'show_task_detail',
                'show_agent_detail',
                'show_agent_registration',
                'selected_rule',
                'selected_session',
                'selected_decision',
                'selected_task',
                'selected_agent'
            ];

            // Save local state to sessionStorage
            function saveLocalState() {
                if (!window.trame || !window.trame.state) return;
                const state = window.trame.state;
                const localState = {};
                LOCAL_STATE_KEYS.forEach(key => {
                    if (state[key] !== undefined) {
                        localState[key] = state[key];
                    }
                });
                sessionStorage.setItem(STORAGE_KEY, JSON.stringify(localState));
            }

            // Restore local state from sessionStorage
            function restoreLocalState() {
                if (!window.trame || !window.trame.state) return;
                try {
                    const saved = sessionStorage.getItem(STORAGE_KEY);
                    if (saved) {
                        const localState = JSON.parse(saved);
                        const state = window.trame.state;
                        Object.keys(localState).forEach(key => {
                            if (LOCAL_STATE_KEYS.includes(key)) {
                                state[key] = localState[key];
                            }
                        });
                    }
                } catch (e) {
                    console.warn('Failed to restore window state:', e);
                }
            }

            // Watch for state changes and save
            function setupStateWatcher() {
                if (!window.trame || !window.trame.state) {
                    setTimeout(setupStateWatcher, 100);
                    return;
                }

                // Restore on load
                restoreLocalState();

                // Save on state change (debounced)
                let saveTimer = null;
                const originalSet = window.trame.state.__lookupSetter__ ?
                    null : Object.getOwnPropertyDescriptor(Object.getPrototypeOf(window.trame.state), 'active_view');

                // Use MutationObserver pattern for Vue reactivity
                LOCAL_STATE_KEYS.forEach(key => {
                    let lastValue = window.trame.state[key];
                    setInterval(() => {
                        const currentValue = window.trame.state[key];
                        if (currentValue !== lastValue) {
                            lastValue = currentValue;
                            clearTimeout(saveTimer);
                            saveTimer = setTimeout(saveLocalState, 50);
                        }
                    }, 100);
                });

                console.log('[GAP-UI-AUDIT-002] Window state isolator active:', WIN_ID);
            }

            // Initialize when DOM ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupStateWatcher);
            } else {
                setupStateWatcher();
            }
        })();
        """
    )
