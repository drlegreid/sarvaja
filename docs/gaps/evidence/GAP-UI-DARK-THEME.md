# GAP-UI-DARK-THEME: Dark Mode Support

**Status:** OPEN
**Priority:** LOW
**Category:** UI/UX
**Discovered:** 2026-01-14

## Current State

- Vuetify 3 default light theme
- App bar: purple (`color="deep-purple"`)
- Trace bar: dark (`color="grey-darken-4"`)
- No theme toggle component
- No user preference persistence

## Implementation Required

### Option A: Simple Toggle (Recommended)

Add theme toggle to app bar:

```python
# In governance_dashboard.py VAppLayout
v3.VSwitch(
    v_model="dark_mode",
    prepend_icon="mdi-theme-light-dark",
    hide_details=True,
)
```

Add Vuetify theme config:

```python
# In server setup
vuetify.VuetifyPlugin(
    app=server,
    theme=vuetify.ThemeOptions(
        defaultTheme="system",  # or "light"
    )
)
```

### Option B: System Preference

Respect OS dark mode setting automatically.

## Related

- UI-TRAME-01-v1: Trame component standards
- GAP-UI-048: Trace bar already uses dark colors
