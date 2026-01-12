# Skill: Exploratory Testing

**ID:** SKILL-QA-EXPLORE-001
**Tags:** qa, testing, exploration, heuristics
**Requires:** playwright, rest-api, Bash

## When to Use
- New feature validation
- Regression testing
- Edge case discovery
- User flow validation

## Procedure
1. Identify test scope (UI, API, E2E)
2. Apply relevant heuristics checklist
3. Document findings with screenshots/evidence
4. Create bug reports for issues found
5. Suggest automation candidates

## Heuristics Checklist

### UI Heuristics
- [ ] All buttons clickable and responsive
- [ ] Forms validate on submit and blur
- [ ] Error messages clear and actionable
- [ ] Loading states present during async ops
- [ ] Responsive at 320px, 768px, 1024px, 1920px
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Color contrast meets WCAG AA (4.5:1)

### API Heuristics
- [ ] Endpoints return expected status codes
- [ ] Error responses have meaningful messages
- [ ] Pagination works correctly
- [ ] Authentication required where expected
- [ ] Response times under threshold (<500ms)

### DevOps Heuristics
- [ ] Containers restart on failure
- [ ] Health endpoints respond correctly
- [ ] Logs capture errors properly
- [ ] Environment variables validated

## Evidence Output
- `evidence/QA-EXPLORE-{date}.md` - Exploration log
- `evidence/BUG-*.md` - Bug reports found
- Screenshots in `.playwright-mcp/`
