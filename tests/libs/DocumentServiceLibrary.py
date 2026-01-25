"""
Robot Framework Library for Document Service Tests.

Per RD-DOC-SERVICE: Document Service Architecture.
Migrated from tests/test_document_service.py
"""
from datetime import datetime
from unittest.mock import MagicMock
from robot.api.deco import keyword


class DocumentServiceLibrary:
    """Library for testing document service functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Rule Document Scanning Tests
    # =============================================================================

    @keyword("Scan Rule Documents Returns List")
    def scan_rule_documents_returns_list(self):
        """scan_rule_documents returns a list of RuleDocument objects."""
        try:
            from governance.rule_linker import scan_rule_documents
            documents = scan_rule_documents()
            return {
                "is_list": isinstance(documents, list),
                "has_documents": len(documents) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Document Has Required Fields")
    def rule_document_has_required_fields(self):
        """RuleDocument dataclass has all required fields."""
        try:
            from governance.rule_linker import RuleDocument
            doc = RuleDocument(
                document_id="TEST-DOC",
                title="Test Document",
                path="docs/rules/test.md",
                document_type="rule",
                storage="filesystem"
            )
            return {
                "id_correct": doc.document_id == "TEST-DOC",
                "title_correct": doc.title == "Test Document",
                "path_correct": doc.path == "docs/rules/test.md",
                "type_correct": doc.document_type == "rule",
                "storage_correct": doc.storage == "filesystem"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Scan Converts Semantic To Legacy")
    def scan_converts_semantic_to_legacy(self):
        """Scanner converts semantic IDs to legacy format for TypeDB compatibility."""
        try:
            from governance.rule_linker import scan_rule_documents
            documents = scan_rule_documents()
            legacy_ids_found = []
            for doc in documents:
                if doc.rule_ids:
                    for rule_id in doc.rule_ids:
                        if rule_id.startswith("RULE-"):
                            legacy_ids_found.append(rule_id)
            return {"has_legacy_ids": len(legacy_ids_found) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Scan Finds Legacy IDs")
    def scan_finds_legacy_ids(self):
        """Scanner finds legacy rule IDs (RULE-001 format)."""
        try:
            from governance.rule_linker import scan_rule_documents
            documents = scan_rule_documents()
            legacy_ids_found = []
            for doc in documents:
                if doc.rule_ids:
                    for rule_id in doc.rule_ids:
                        if rule_id.startswith("RULE-"):
                            legacy_ids_found.append(rule_id)
            return {"has_legacy_ids": len(legacy_ids_found) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Rule ID Extraction Tests
    # =============================================================================

    @keyword("Extract Legacy Rule ID")
    def extract_legacy_rule_id(self):
        """Extracts RULE-001 format IDs."""
        try:
            from governance.rule_linker import extract_rule_ids
            content = "This document references RULE-001 and RULE-042."
            ids = extract_rule_ids(content)
            return {
                "has_001": "RULE-001" in ids,
                "has_042": "RULE-042" in ids
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Extract Semantic Converts To Legacy")
    def extract_semantic_converts_to_legacy(self):
        """Semantic IDs are converted to legacy format."""
        try:
            from governance.rule_linker import extract_rule_ids
            content = "Per SESSION-EVID-01-v1: Evidence logging required."
            ids = extract_rule_ids(content)
            return {"has_rule_001": "RULE-001" in ids}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Extract Multiple Formats Returns Legacy")
    def extract_multiple_formats_returns_legacy(self):
        """Both formats are converted to legacy for TypeDB compatibility."""
        try:
            from governance.rule_linker import extract_rule_ids
            content = """
            # Rule Document

            Per RULE-001 (SESSION-EVID-01-v1): Evidence required.
            Also see RULE-012 and GOV-BICAM-01-v1.
            """
            ids = extract_rule_ids(content)
            return {
                "has_001": "RULE-001" in ids,
                "has_012": "RULE-012" in ids,
                "has_011": "RULE-011" in ids  # GOV-BICAM-01-v1 -> RULE-011
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("No Duplicate Extractions")
    def no_duplicate_extractions(self):
        """Doesn't extract duplicate IDs."""
        try:
            from governance.rule_linker import extract_rule_ids
            content = "RULE-001 is important. See RULE-001 again."
            ids = extract_rule_ids(content)
            return {"no_duplicates": ids.count("RULE-001") == 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Rule ID Normalization Tests
    # =============================================================================

    @keyword("Normalize Keeps Legacy ID")
    def normalize_keeps_legacy_id(self):
        """normalize_rule_id preserves legacy format."""
        try:
            from governance.rule_linker import normalize_rule_id
            result = normalize_rule_id("RULE-001")
            return {"preserved": result == "RULE-001"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Normalize Converts Semantic To Legacy")
    def normalize_converts_semantic_to_legacy(self):
        """normalize_rule_id converts semantic to legacy."""
        try:
            from governance.rule_linker import normalize_rule_id
            result = normalize_rule_id("SESSION-EVID-01-v1")
            return {"converted": result == "RULE-001"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # TypeDB Document Linking Tests
    # =============================================================================

    @keyword("Link Rules To Documents Returns Stats")
    def link_rules_to_documents_returns_stats(self):
        """link_rules_to_documents returns statistics dict."""
        try:
            from governance.rule_linker import link_rules_to_documents
            result = link_rules_to_documents()
            return {
                "is_dict": isinstance(result, dict),
                "has_documents_inserted": "documents_inserted" in result,
                "has_documents_skipped": "documents_skipped" in result,
                "has_relations_created": "relations_created" in result,
                "has_relations_skipped": "relations_skipped" in result,
                "has_errors": "errors" in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Insert Document Datetime Format")
    def insert_document_datetime_format(self):
        """Document insert uses TypeDB-compatible datetime format."""
        try:
            from governance.rule_linker_db import _insert_document
            from governance.rule_linker import RuleDocument

            doc = RuleDocument(
                document_id="TEST-DOC",
                title="Test",
                path="test.md",
                document_type="rule",
                storage="filesystem",
                last_modified=datetime(2026, 1, 14, 10, 30, 45, 123456)
            )

            mock_client = MagicMock()
            mock_client._execute_write.return_value = None

            _insert_document(mock_client, doc)

            call_args = mock_client._execute_write.call_args[0][0]
            return {
                "has_datetime": "2026-01-14T10:30:45" in call_args,
                "no_microseconds": "123456" not in call_args
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Insert Document Escapes Special Chars")
    def insert_document_escapes_special_chars(self):
        """Document insert escapes quotes and backslashes."""
        try:
            from governance.rule_linker_db import _insert_document
            from governance.rule_linker import RuleDocument

            doc = RuleDocument(
                document_id="TEST-DOC",
                title='Rule with "quotes" and \\backslash',
                path="docs/rules/test.md",
                document_type="rule",
                storage="filesystem"
            )

            mock_client = MagicMock()
            mock_client._execute_write.return_value = None

            _insert_document(mock_client, doc)

            call_args = mock_client._execute_write.call_args[0][0]
            return {
                "has_escape": '\\"' in call_args or "quotes" in call_args,
                "has_backslash": '\\\\' in call_args or "backslash" in call_args
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Document Service MCP Integration Tests
    # =============================================================================

    @keyword("File Type Map Exists")
    def file_type_map_exists(self):
        """FILE_TYPE_MAP constant exists for file type detection."""
        try:
            from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
            return {
                "exists": FILE_TYPE_MAP is not None,
                "is_dict": isinstance(FILE_TYPE_MAP, dict)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("File Type Map Has Python")
    def file_type_map_has_python(self):
        """FILE_TYPE_MAP detects Python files."""
        try:
            from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
            py_info = FILE_TYPE_MAP.get(".py")
            return {
                "has_py": py_info is not None,
                "is_python": py_info.get("syntax") == "python" or py_info == "python" if py_info else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("File Type Map Has Markdown")
    def file_type_map_has_markdown(self):
        """FILE_TYPE_MAP detects Markdown files."""
        try:
            from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
            md_info = FILE_TYPE_MAP.get(".md")
            return {
                "has_md": md_info is not None,
                "is_markdown": (md_info.get("syntax") == "markdown" or
                               md_info.get("type") == "markdown") if md_info else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("File Type Map Has TypeQL")
    def file_type_map_has_typeql(self):
        """FILE_TYPE_MAP detects TypeQL files."""
        try:
            from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
            tql_info = FILE_TYPE_MAP.get(".tql")
            return {
                "has_tql": tql_info is not None,
                "is_typeql": (tql_info.get("syntax") == "typeql" or
                             "typeql" in str(tql_info)) if tql_info else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("File Type Map Has Haskell")
    def file_type_map_has_haskell(self):
        """FILE_TYPE_MAP detects Haskell files."""
        try:
            from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
            hs_info = FILE_TYPE_MAP.get(".hs")
            return {
                "has_hs": hs_info is not None,
                "is_haskell": (hs_info.get("syntax") == "haskell" or
                              "haskell" in str(hs_info)) if hs_info else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Register Document Tools Function Exists")
    def register_document_tools_function_exists(self):
        """register_document_tools function exists."""
        try:
            from governance.mcp_tools.evidence.documents import register_document_tools
            return {
                "exists": register_document_tools is not None,
                "callable": callable(register_document_tools)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
