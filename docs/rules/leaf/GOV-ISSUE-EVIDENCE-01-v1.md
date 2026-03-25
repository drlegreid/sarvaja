# GOV-ISSUE-EVIDENCE-01-v1: GitHub Issue Evidence Attachment

| Field | Value |
|-------|-------|
| **Rule ID** | GOV-ISSUE-EVIDENCE-01-v1 |
| **Category** | governance |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-24 |

## Directive

When creating or updating GitHub issues that reference evidence (screenshots, test results, logs), all evidence artifacts MUST be **uploaded to GitHub** — never referenced as local file paths.

## Rationale

Local file paths (e.g., `evidence/test-results/screenshot.png`) are invisible to anyone reading the issue on GitHub. This creates a false impression of evidence that cannot be verified. The `evidence/` directory is `.gitignore`d, so these files never reach the remote repository.

## Requirements

1. **Screenshots**: Upload via GitHub draft release assets, then reference the download URL in the issue body or comments
2. **Test output**: Paste inline as fenced code blocks or upload as release assets
3. **Never** reference local paths like `evidence/test-results/*.png` in GitHub issues
4. **Always** verify images render when viewing the issue on github.com

## Upload Procedure

```bash
# 1. Create a draft release to host evidence assets
gh release create evidence-issue-{NUMBER} \
  --repo {OWNER}/{REPO} \
  --title "Evidence: {EPIC/FEATURE} #{NUMBER}" \
  --notes "Screenshots for issue #{NUMBER}" \
  --draft \
  evidence/test-results/*.png

# 2. Get the asset URLs
gh release view evidence-issue-{NUMBER} \
  --repo {OWNER}/{REPO} \
  --json assets --jq '.assets[].url'

# 3. Reference in issue body or comment
# ![Description](https://github.com/{OWNER}/{REPO}/releases/download/{TAG}/{FILE}.png)
```

## Enforcement

- At issue creation time: verify all `![image]()` references resolve to GitHub URLs
- Code review: reject issues/PRs that reference local evidence paths
- Session close: check all created issues for dangling local references

## Anti-Patterns

| Wrong | Right |
|-------|-------|
| `evidence/test-results/P18.png` | `https://github.com/.../releases/download/.../P18.png` |
| "See screenshot in evidence/" | `![P18 timeline](https://github.com/...)` |
| "Screenshots captured" (no links) | "Screenshots: ![img1](...) ![img2](...)" |
