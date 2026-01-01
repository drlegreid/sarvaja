# R&D: Document Viewer Component (DOCVIEW-001 to DOCVIEW-005)

**Status:** TODO
**Priority:** HIGH
**Vision:** Multi-format document viewer with lazy loading, search, and chapter navigation

---

## Overview

Enterprise-grade document viewer component for displaying documents referenced in governance entities (Rules, Decisions, Sessions, Evidence). Supports multiple formats with intelligent rendering and navigation.

**Trigger GAPs:** GAP-UI-038, GAP-UI-039

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| DOCVIEW-001 | OctoCode research: Document viewer libraries | 📋 TODO | **HIGH** | Search GitHub for Vue/Trame compatible viewers |
| DOCVIEW-002 | Evaluate libraries: markdown-it, vue-pdf, csv-parser | 📋 TODO | HIGH | Compare features, bundle size, Trame compat |
| DOCVIEW-003 | Design: Fullscreen modal with lazy loading | 📋 TODO | HIGH | Chapter navigation, search, progress indicator |
| DOCVIEW-004 | PoC: Basic Markdown + CSV viewer integration | 📋 TODO | MEDIUM | Proof of concept in Trame dashboard |
| DOCVIEW-005 | TDD: Document viewer test specifications | 📋 TODO | MEDIUM | Tests derive from spec per RULE-023 |

---

## Requirements

### Functional Requirements

1. **Multi-Format Support**
   - Markdown (`.md`) - Primary format for session evidence
   - CSV (`.csv`) - Data tables
   - TypeQL (`.tql`) - Schema files with syntax highlighting
   - Plain text (`.txt`, `.log`)
   - JSON (`.json`) - Structured data
   - YAML (`.yaml`) - Config files

2. **Navigation**
   - Chapter/section navigation sidebar
   - Table of contents auto-generation
   - Search within document
   - Jump to line number
   - Breadcrumb navigation

3. **Performance**
   - Lazy loading for large documents (>1MB)
   - Virtual scrolling for huge files
   - Caching of recently viewed documents
   - Progress indicator for loading

4. **UX**
   - Fullscreen modal overlay
   - Close on ESC key
   - Dark/light theme support
   - Copy code blocks
   - Print/export option

### Non-Functional Requirements

- Bundle size < 100KB (gzipped)
- Time to first render < 500ms
- Vue 3 / Trame compatible
- Accessible (WCAG 2.1 AA)

---

## Library Candidates (for OctoCode research)

### Markdown

| Library | Stars | Size | Features |
|---------|-------|------|----------|
| markdown-it | 15k+ | ~200KB | Plugins, fast |
| marked | 28k+ | ~30KB | Simple, fast |
| vue-markdown | 2k+ | ~50KB | Vue native |

### Code Highlighting

| Library | Stars | Size | Features |
|---------|-------|------|----------|
| highlight.js | 22k+ | Varies | 180 languages |
| prism.js | 10k+ | ~20KB | Plugin system |
| shiki | 5k+ | ~100KB | VSCode themes |

### PDF (future)

| Library | Stars | Size | Features |
|---------|-------|------|----------|
| vue-pdf-embed | 1k+ | ~200KB | Vue 3 native |
| pdfjs-dist | 40k+ | ~2MB | Full featured |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Viewer Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DocumentViewer Component                                        │
│  ├── Modal Container (fullscreen)                               │
│  │   ├── Header: Title + Close button                           │
│  │   ├── Toolbar: Search + Download + Print                     │
│  │   └── Content Area                                            │
│  │       ├── Sidebar: ToC / Chapter navigation                  │
│  │       └── Renderer (per format)                              │
│  │           ├── MarkdownRenderer                               │
│  │           ├── CsvRenderer (table view)                       │
│  │           ├── CodeRenderer (syntax highlight)                │
│  │           └── PlainTextRenderer                              │
│  │                                                               │
│  └── API Integration                                             │
│      ├── GET /api/documents/{path}                              │
│      └── GET /api/documents/{path}/chunks?offset=X&limit=Y      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration with Governance UI

### Usage Pattern

```python
# In Trame component
def on_document_click(doc_path):
    """Open document in viewer modal."""
    state.viewer_document = doc_path
    state.viewer_open = True

# API endpoint
@app.get("/api/documents/{path:path}")
async def get_document(path: str, offset: int = 0, limit: int = 1000):
    """Lazy load document chunks."""
    ...
```

### Trigger Points

- Rule directive references (`docs/rules/*.md`)
- Session evidence files (`evidence/*.md`)
- Gap references (`docs/gaps/*.md`)
- Decision context files

---

## Success Criteria

1. **DOCVIEW-001 Complete:** 3+ library candidates evaluated
2. **DOCVIEW-002 Complete:** Decision matrix with scores
3. **DOCVIEW-003 Complete:** Figma/ASCII wireframe approved
4. **DOCVIEW-004 Complete:** Working PoC with Markdown + CSV
5. **DOCVIEW-005 Complete:** 10+ test cases covering viewer functionality

---

*Per RULE-010: Evidence-Based Wisdom - R&D spike for document viewer*
*Per GAP-UI-038, GAP-UI-039: Document reference viewer requirements*
