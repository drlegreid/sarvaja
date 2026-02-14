"""Tests for governance/routes/files.py — File content endpoint.

Covers: Security checks (allowed_prefixes, path traversal prevention),
FileContentResponse construction, markdown rendering, error handling.
"""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException


class TestGetFileContentSecurity(unittest.TestCase):
    """Tests for get_file_content security checks."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_disallowed_prefix(self):
        """Files outside allowed dirs raise 403."""
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="secrets/api_key.txt"))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access denied", ctx.exception.detail)

    def test_root_path_denied(self):
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="config.json"))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_src_path_denied(self):
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="src/main.py"))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_backslash_normalised(self):
        """Backslash paths get normalized to forward-slash."""
        from governance.routes.files import get_file_content
        # evidence\ prefix should work after normalization but file won't exist
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="evidence\\test.md"))
        # Should pass prefix check (403) and hit file-not-found (404)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_path_traversal_denied(self):
        """Path traversal via ../ is caught."""
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="evidence/../../etc/passwd"))
        # Could be 403 (traversal check) or 404 (file not found)
        self.assertIn(ctx.exception.status_code, [403, 404])

    def test_allowed_prefixes_evidence(self):
        """evidence/ prefix passes the prefix check (may 404)."""
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="evidence/nonexistent.md"))
        # Passes prefix check, fails on missing file
        self.assertEqual(ctx.exception.status_code, 404)

    def test_allowed_prefixes_docs(self):
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="docs/nonexistent.md"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_allowed_prefixes_results(self):
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="results/nonexistent.json"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_allowed_prefixes_data(self):
        from governance.routes.files import get_file_content
        with self.assertRaises(HTTPException) as ctx:
            self._run(get_file_content(path="data/nonexistent.csv"))
        self.assertEqual(ctx.exception.status_code, 404)


class TestGetFileContentSuccess(unittest.TestCase):
    """Tests for successful file reads."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_read_text_file(self):
        """Read a plain text file from evidence dir."""
        from governance.routes.files import get_file_content

        # Capture real os functions before patching to avoid recursion
        _real_join = os.path.join
        _real_realpath = os.path.realpath

        with tempfile.TemporaryDirectory() as tmpdir:
            edir = _real_join(tmpdir, "evidence")
            os.makedirs(edir)
            fpath = _real_join(edir, "test.txt")
            with open(fpath, "w") as f:
                f.write("Hello test")

            with patch("governance.routes.files.os.path.dirname", return_value=tmpdir):
                with patch("governance.routes.files.os.path.join",
                           side_effect=lambda *a: _real_join(*a)):
                    with patch("governance.routes.files.os.path.realpath",
                               side_effect=lambda p: _real_realpath(p)):
                        with patch("governance.routes.files.os.path.exists",
                                   return_value=True):
                            with patch("governance.routes.files.os.path.isfile",
                                       return_value=True):
                                with patch("governance.routes.files.open",
                                           create=True,
                                           return_value=open(fpath, "r")):
                                    with patch("governance.routes.files.os.stat") as mock_stat:
                                        st = MagicMock()
                                        st.st_size = 10
                                        st.st_mtime = 1707820800.0
                                        mock_stat.return_value = st
                                        result = self._run(
                                            get_file_content(path="evidence/test.txt")
                                        )
            self.assertEqual(result.path, "evidence/test.txt")
            self.assertEqual(result.content, "Hello test")
            self.assertEqual(result.size, 10)
            self.assertIsNone(result.rendered_html)

    def test_markdown_rendering(self):
        """Markdown files get rendered_html populated."""
        from governance.routes.files import get_file_content

        _real_join = os.path.join

        with patch("governance.routes.files.os.path.dirname", return_value="/fake"):
            with patch("governance.routes.files.os.path.join",
                       side_effect=lambda *a: _real_join(*a)):
                with patch("governance.routes.files.os.path.realpath",
                           side_effect=lambda p: p):
                    with patch("governance.routes.files.os.path.exists",
                               return_value=True):
                        with patch("governance.routes.files.os.path.isfile",
                                   return_value=True):
                            with patch("builtins.open",
                                       unittest.mock.mock_open(read_data="# Hello")):
                                with patch("governance.routes.files.os.stat") as mock_stat:
                                    st = MagicMock()
                                    st.st_size = 7
                                    st.st_mtime = 1707820800.0
                                    mock_stat.return_value = st
                                    with patch(
                                        "governance.services.cc_session_ingestion.render_markdown",
                                        return_value="<h1>Hello</h1>"
                                    ):
                                        result = self._run(
                                            get_file_content(path="docs/readme.md")
                                        )
        self.assertEqual(result.rendered_html, "<h1>Hello</h1>")


class TestGetFileContentErrors(unittest.TestCase):
    """Tests for error conditions."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_directory_not_file(self):
        """Directories return 400."""
        from governance.routes.files import get_file_content

        with patch("governance.routes.files.os.path.dirname", return_value="/fake"):
            with patch("governance.routes.files.os.path.join",
                       side_effect=lambda *a: "/".join(a)):
                with patch("governance.routes.files.os.path.realpath",
                           side_effect=lambda p: p):
                    with patch("governance.routes.files.os.path.exists",
                               return_value=True):
                        with patch("governance.routes.files.os.path.isfile",
                                   return_value=False):
                            with self.assertRaises(HTTPException) as ctx:
                                self._run(
                                    get_file_content(path="evidence/subdir")
                                )
                            self.assertEqual(ctx.exception.status_code, 400)

    def test_binary_file(self):
        """Binary files return 400."""
        from governance.routes.files import get_file_content

        with patch("governance.routes.files.os.path.dirname", return_value="/fake"):
            with patch("governance.routes.files.os.path.join",
                       side_effect=lambda *a: "/".join(a)):
                with patch("governance.routes.files.os.path.realpath",
                           side_effect=lambda p: p):
                    with patch("governance.routes.files.os.path.exists",
                               return_value=True):
                        with patch("governance.routes.files.os.path.isfile",
                                   return_value=True):
                            with patch("builtins.open",
                                       side_effect=UnicodeDecodeError(
                                           "utf-8", b"", 0, 1, "bad")):
                                with self.assertRaises(HTTPException) as ctx:
                                    self._run(
                                        get_file_content(path="evidence/img.png")
                                    )
                                self.assertEqual(ctx.exception.status_code, 400)
                                self.assertIn("binary", ctx.exception.detail)

    def test_generic_read_error(self):
        """Generic errors return 500."""
        from governance.routes.files import get_file_content

        with patch("governance.routes.files.os.path.dirname", return_value="/fake"):
            with patch("governance.routes.files.os.path.join",
                       side_effect=lambda *a: "/".join(a)):
                with patch("governance.routes.files.os.path.realpath",
                           side_effect=lambda p: p):
                    with patch("governance.routes.files.os.path.exists",
                               return_value=True):
                        with patch("governance.routes.files.os.path.isfile",
                                   return_value=True):
                            with patch("builtins.open",
                                       side_effect=PermissionError("denied")):
                                with self.assertRaises(HTTPException) as ctx:
                                    self._run(
                                        get_file_content(path="evidence/locked.md")
                                    )
                                self.assertEqual(ctx.exception.status_code, 500)


class TestFileContentResponseModel(unittest.TestCase):
    """Tests for the FileContentResponse Pydantic model."""

    def test_basic_fields(self):
        from governance.models import FileContentResponse
        resp = FileContentResponse(
            path="evidence/test.md",
            content="# Test",
            size=6,
            modified_at="2026-02-13T10:00:00",
        )
        self.assertEqual(resp.path, "evidence/test.md")
        self.assertEqual(resp.size, 6)
        self.assertIsNone(resp.rendered_html)

    def test_with_rendered_html(self):
        from governance.models import FileContentResponse
        resp = FileContentResponse(
            path="docs/readme.md",
            content="# Hello",
            size=7,
            modified_at="2026-02-13T10:00:00",
            rendered_html="<h1>Hello</h1>",
        )
        self.assertEqual(resp.rendered_html, "<h1>Hello</h1>")


if __name__ == "__main__":
    unittest.main()
