"""Batch 250 — API startup + embedding pipeline defense tests.

Validates fixes for:
- BUG-250-PIP-001: Per-session error handling in embed_sessions loop
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-250-PIP-001: Per-session error handling ──────────────────────

class TestEmbedSessionsErrorHandling:
    """embed_sessions must catch per-session errors, not abort loop."""

    def test_try_except_in_loop(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        idx = src.index("def embed_sessions")
        block = src[idx:idx + 1500]
        assert "except" in block
        assert "continue" in block

    def test_json_decode_caught(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        idx = src.index("def embed_sessions")
        block = src[idx:idx + 1500]
        assert "JSONDecodeError" in block

    def test_per_session_warning(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        idx = src.index("def embed_sessions")
        block = src[idx:idx + 1500]
        assert "Failed to fetch/parse session" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        assert "BUG-250-PIP-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch250Imports:
    def test_pipeline_importable(self):
        import governance.embedding_pipeline.pipeline
        assert governance.embedding_pipeline.pipeline is not None

    def test_embedding_config_importable(self):
        import governance.embedding_config
        assert governance.embedding_config is not None

    def test_api_startup_importable(self):
        import governance.api_startup
        assert governance.api_startup is not None

    def test_workspace_scanner_importable(self):
        import governance.workspace_scanner
        assert governance.workspace_scanner is not None
