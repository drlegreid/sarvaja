/**
 * Route sync — browser hash ↔ Trame state synchronization.
 *
 * Per FEAT-008: Named URI routing for dashboard navigation.
 *
 * Strategy:
 *   Python → Browser: Python sets state.route_hash, this script
 *                     detects the change and updates window.location.hash.
 *   Browser → Python: On hashchange (back/forward), calls Trame trigger
 *                     'on_route_change' to update Python state.
 *
 * Loading: Dynamically loaded from window_isolator.js setup() to guarantee
 *          trame.state is available.
 */
(function() {
    'use strict';

    if (window.__routeSyncActive) return;
    window.__routeSyncActive = true;

    var _suppressHashChange = false;
    var _lastPushedHash = '';
    var _baseTitle = 'Sarvaja';

    /**
     * Update document.title based on current hash.
     * Per SRVJ-FEAT-014: Browser title reflects current entity.
     *
     * Examples:
     *   #/projects/WS-X/tasks          → "Sarvaja - Tasks"
     *   #/projects/WS-X/tasks/BUG-012  → "Sarvaja - BUG-012"
     *   #/executive                     → "Sarvaja - Executive"
     */
    function updateTitle(hash) {
        if (!hash || hash === '#/' || hash === '#') {
            document.title = _baseTitle;
            return;
        }
        var path = hash.replace(/^#\/?/, '').replace(/\/$/, '');
        var parts = path.split('/');

        // Standalone: #/executive → ["executive"]
        // Entity list: #/projects/WS-X/tasks → ["projects","WS-X","tasks"]
        // Entity detail: #/projects/WS-X/tasks/BUG-012 → ["projects","WS-X","tasks","BUG-012"]
        var viewName = '';
        var entityId = '';

        if (parts[0] === 'projects' && parts.length >= 3) {
            viewName = parts[2];
            if (parts.length >= 4) {
                entityId = parts.slice(3).join('/');
            }
        } else {
            viewName = parts[0];
        }

        var label = entityId || (viewName.charAt(0).toUpperCase() + viewName.slice(1));
        document.title = _baseTitle + ' - ' + label;
    }

    function setup() {
        if (!window.trame || !window.trame.state) {
            setTimeout(setup, 100);
            return;
        }

        var trameState = window.trame.state;

        // === Capture deep link hash BEFORE polling overwrites it ===
        // Polling pushes route_hash (#/rules default) to browser, overwriting
        // the deep link hash. Capture it now, apply after Trame settles.
        var _initialHash = window.location.hash;
        var _initialLoadPending = (
            _initialHash && _initialHash !== '#/' && _initialHash !== '#'
        );

        // === Watch route_hash state changes (Python → Browser) ===
        var _lastRouteHash = '';
        setInterval(function() {
            // Don't push default hash while a deep link is pending
            if (_initialLoadPending) return;
            var currentHash = trameState.state.route_hash;
            if (currentHash && currentHash !== _lastRouteHash) {
                _lastRouteHash = currentHash;
                updateTitle(currentHash);
                if (window.location.hash !== currentHash) {
                    _suppressHashChange = true;
                    _lastPushedHash = currentHash;
                    window.location.hash = currentHash;
                }
            }
        }, 200);

        // === Listen for hashchange (Browser → Python) ===
        window.addEventListener('hashchange', function() {
            if (_suppressHashChange) {
                _suppressHashChange = false;
                return;
            }
            var newHash = window.location.hash;
            if (newHash && newHash !== _lastPushedHash) {
                function markLocal() {
                    if (window.__govMarkLocalChange) {
                        window.__govMarkLocalChange();
                    }
                }
                markLocal();
                setTimeout(markLocal, 400);
                setTimeout(markLocal, 800);
                setTimeout(markLocal, 1200);
                trame.trigger('on_route_change', [newHash]);
                updateTitle(newHash);
            }
        });

        // === Initial page load: apply captured deep link hash ===
        if (_initialLoadPending) {
            updateTitle(_initialHash);
            setTimeout(function() {
                _initialLoadPending = false;
                // Pulse markLocal to cover the full Python→WebSocket→client
                // roundtrip. The window isolator blocks remote writes after
                // 1000ms, but deep link state changes arrive via WebSocket.
                function markLocal() {
                    if (window.__govMarkLocalChange) {
                        window.__govMarkLocalChange();
                    }
                }
                markLocal();
                setTimeout(markLocal, 400);
                setTimeout(markLocal, 800);
                setTimeout(markLocal, 1200);
                trame.trigger('on_route_change', [_initialHash]);
            }, 1500);
        }

        console.log('[FEAT-008] Route sync active');
    }

    // Called from window_isolator.js or standalone
    window.__routeSyncSetup = setup;

    // Auto-start if trame is already available
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
