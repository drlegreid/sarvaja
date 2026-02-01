# UI-COLOR-01-v1: Color Harmony & Palette Standards

**Category:** `ui` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Tags:** `ui`, `ux`, `color`, `accessibility`, `wcag`, `design-system`

---

## Directive

All UI components MUST follow color harmony principles:

1. **Toolbar Contrast** - Elements on colored backgrounds (app bar, cards) MUST use colors with sufficient contrast. Never place saturated colors on saturated backgrounds (e.g., red on purple, blue on green).

2. **Status Indication on Colored Surfaces** - Use `white` outlined chips on the app bar. Indicate status via icon color or small dot, NOT the chip border/background color.

3. **Semantic Color Palette** - Use Vuetify semantic tokens (`success`, `warning`, `error`, `info`, `primary`, `secondary`) consistently. Never use raw hex colors in view code.

4. **Surface-Aware Colors** - Components MUST adapt their color intensity to the surface they sit on:
   - On dark/colored surfaces: Use `white`, `grey-lighten-3`, or pastel variants
   - On light surfaces: Use standard semantic colors
   - On cards/containers: Use `tonal` or `outlined` variants

5. **Color Combinations to AVOID** (low contrast, visual clash):
   | Background | Avoid Foreground |
   |------------|-----------------|
   | `deep-purple` | `error` (red), `primary` (blue), `info` (blue) |
   | `error` (red) | `deep-purple`, `primary`, `warning` |
   | `success` (green) | `info` (blue), `warning` (amber) |
   | Dark backgrounds | Any saturated dark color |

6. **Approved Toolbar Palette** (on `deep-purple` app bar):
   - Chips: `white` outlined (consistent for all toolbar chips)
   - Status icons: `light-green` (healthy), `amber` (degraded), `pink-lighten-3` (error)
   - Text: `white` or `grey-lighten-3`
   - Buttons: `text` variant (inherits white from parent)

---

## WCAG Contrast Requirements

| Context | Minimum Ratio | Standard |
|---------|--------------|----------|
| Normal text | 4.5:1 | WCAG 2.1 AA |
| Large text (>18px) | 3:1 | WCAG 2.1 AA |
| UI components | 3:1 | WCAG 2.1 AA |
| Decorative only | No requirement | - |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Red chip on purple app bar | White outlined chip + red icon |
| Saturated-on-saturated | Use tonal/outlined variants |
| Raw hex colors in views | Use Vuetify semantic tokens |
| Same color for different meanings | Map meaning → unique color |
| Ignore dark mode contrast | Test both light and dark themes |

---

## Validation

- [ ] Toolbar chips use `white` outlined on colored app bar
- [ ] Status indicated via icon color, not chip color on dark surfaces
- [ ] No saturated-on-saturated color combinations
- [ ] Color contrast meets WCAG AA (4.5:1 minimum)
- [ ] Colors defined in `constants.py`, not inline

---

*Per UI-DESIGN-02-v1: UI/UX Design Standards*
*Per UI-RESP-01-v1: Responsive Design*
