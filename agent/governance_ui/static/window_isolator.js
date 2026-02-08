/**
 * Window State Isolator v7 - Per GAP-UI-AUDIT-002
 *
 * Prevents multi-window state mirroring in Trame by wrapping
 * trame.state.state with a JS Proxy that blocks remote writes
 * to navigation/selection keys.
 *
 * Root cause: Trame broadcasts ALL state changes to ALL connected
 * WebSocket clients via wslink. The wslink client directly sets
 * trame.state.state[key] = value, bypassing _updateFromServer().
 *
 * Strategy: Replace trame.state.state with a Proxy. For isolated
 * keys, only allow writes when a local user interaction is in
 * progress (click/keydown on nav elements). Remote broadcasts
 * are silently dropped for these keys.
 *
 * v7 fix (GAP-UI-POLLING-001): Allow initial server state sync.
 * The proxy was blocking initial state like active_view='rules'
 * because no user interaction had occurred yet. Now we allow all
 * writes until 1s after setup, then start blocking remote updates.
 *
 * Key findings from v4/v5/v6 debugging:
 * - state[key] bracket access does NOT work on trame.state (use .state.state[key])
 * - Vue.watch doesn't fire because state.state is NOT Vue-reactive
 * - _updateFromServer() is NOT the only state update path
 * - wslink sets state.state[key] directly via index-5f6ebc8d.js
 * - Proxy on state.state IS the correct interception point
 */
(function() {
    if (window.__govIsolatorActive) return;
    window.__govIsolatorActive = true;

    if (!window.__govWindowId) {
        window.__govWindowId = 'win_' + Math.random().toString(36).substr(2, 9);
    }
    var WIN_ID = window.__govWindowId;
    var STORAGE_KEY = 'gov_nav_state_' + WIN_ID;

    // Keys to isolate per-window (navigation + selection + viewer state)
    var localKeySet = {};
    [
        // Navigation state
        'active_view',
        // Detail view visibility
        'show_rule_detail',
        'show_session_detail',
        'show_session_form',
        'show_decision_detail',
        'show_task_detail',
        'show_agent_detail',
        'show_agent_registration',
        'show_task_form',
        'show_rule_form',
        // Selection state
        'selected_rule',
        'selected_session',
        'selected_decision',
        'selected_task',
        'selected_agent',
        // File viewer state (GAP-UI-SESSION-ISOLATION-001)
        'show_file_viewer',
        'file_viewer_path',
        'file_viewer_content',
        'file_viewer_loading',
        'file_viewer_error',
        // Task execution state
        'show_task_execution',
        'task_execution_log',
        'task_execution_loading'
    ].forEach(function(k) { localKeySet[k] = true; });

    var localChangeInProgress = false;
    var localChangeTimer = null;
    var initialSyncComplete = false;  // Allow initial state sync from server

    function markLocalChange() {
        localChangeInProgress = true;
        clearTimeout(localChangeTimer);
        localChangeTimer = setTimeout(function() {
            localChangeInProgress = false;
        }, 500);
    }

    function markInitialSyncComplete() {
        // Called after initial state is loaded - start blocking remote updates
        initialSyncComplete = true;
        console.log('[isolator] Initial sync complete, now blocking remote updates');
    }

    function saveToStorage(stateObj) {
        var filtered = {};
        Object.keys(localKeySet).forEach(function(key) {
            if (stateObj[key] !== undefined) filtered[key] = stateObj[key];
        });
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
        } catch(e) {}
    }

    function loadFromStorage() {
        try {
            var saved = sessionStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : null;
        } catch(e) { return null; }
    }

    function setup() {
        if (!window.trame || !window.trame.state) {
            setTimeout(setup, 50);
            return;
        }

        var trameState = window.trame.state;
        var realState = trameState.state;

        // Capture user interactions as LOCAL changes
        // Expanded selector to include table rows, cards, and other clickable elements
        document.addEventListener('click', function(e) {
            var clickable = e.target.closest(
                '[data-testid^="nav-"], .v-list-item, .v-tab, .v-btn, ' +
                'tr[cursor=pointer], .v-data-table tbody tr, .v-card, ' +
                '[role="row"], [role="listitem"], [role="option"]'
            );
            if (clickable) {
                markLocalChange();
            }
        }, true);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                markLocalChange();
            }
        }, true);

        // === CORE: Proxy on state.state ===
        // Intercepts ALL property writes on the internal state object.
        // For isolated keys, only allows writes during local user interaction.
        var proxy = new Proxy(realState, {
            set: function(target, prop, value) {
                if (localKeySet[prop]) {
                    // Allow writes during: (1) initial sync, (2) local user interaction
                    if (!initialSyncComplete || localChangeInProgress) {
                        target[prop] = value;
                        if (initialSyncComplete) {
                            // Only save to storage after initial sync (local changes)
                            saveToStorage(target);
                        }
                        return true;
                    } else {
                        // Remote broadcast after initial sync: block the write silently
                        console.debug('[isolator] Blocked remote write:', prop, '=', JSON.stringify(value));
                        return true; // Return true to avoid TypeError
                    }
                }
                // Non-isolated keys: pass through normally
                target[prop] = value;
                return true;
            },
            get: function(target, prop) {
                return target[prop];
            },
            deleteProperty: function(target, prop) {
                delete target[prop];
                return true;
            }
        });

        // Replace the internal state with our proxy
        trameState.state = proxy;

        // === Restore from sessionStorage on page load ===
        var stored = loadFromStorage();
        if (stored) {
            var restored = [];
            Object.keys(localKeySet).forEach(function(key) {
                if (key in stored && realState[key] !== stored[key]) {
                    // Write directly to realState (bypass proxy) for restore
                    realState[key] = stored[key];
                    restored.push(key + '=' + JSON.stringify(stored[key]));
                }
            });
            if (restored.length > 0) {
                console.log('[isolator] Restored from sessionStorage:', restored.join(', '));
            }
        }

        // Save initial state
        saveToStorage(realState);

        // Mark initial sync complete after a short delay
        // This allows Trame's initial state sync to complete before we start blocking
        setTimeout(function() {
            markInitialSyncComplete();
        }, 1000);

        // Also expose markLocalChange for programmatic use
        window.__govMarkLocalChange = markLocalChange;

        console.log('[GAP-UI-AUDIT-002] Window isolator v7 (Proxy + InitSync) active:', WIN_ID);
    }

    // Start setup when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
