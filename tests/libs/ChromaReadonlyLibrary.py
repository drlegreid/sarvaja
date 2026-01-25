"""
Robot Framework Library for ChromaDB Read-Only Wrapper Tests.

Per P7.5: ChromaDB sunset - read-only wrapper.
Migrated from tests/test_chroma_readonly.py
"""
from pathlib import Path
from robot.api.deco import keyword


class ChromaReadonlyLibrary:
    """Library for testing ChromaDB read-only wrapper."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Module Tests
    # =============================================================================

    @keyword("Readonly Wrapper Module Exists")
    def readonly_wrapper_module_exists(self):
        """Read-only wrapper module must exist."""
        wrapper_file = self.governance_dir / "chroma_readonly.py"
        return {"exists": wrapper_file.exists()}

    @keyword("Chroma Readonly Class Works")
    def chroma_readonly_class_works(self):
        """ChromaReadOnly class must be importable."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly()
            return {"created": wrapper is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Wrapper Has Required Methods")
    def wrapper_has_required_methods(self):
        """Wrapper must have required methods."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly()

            return {
                "has_query": hasattr(wrapper, 'query'),
                "has_get": hasattr(wrapper, 'get'),
                "has_list_collections": hasattr(wrapper, 'list_collections'),
                "has_add": hasattr(wrapper, 'add'),
                "has_update": hasattr(wrapper, 'update'),
                "has_delete": hasattr(wrapper, 'delete')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Read Operation Tests
    # =============================================================================

    @keyword("Query Returns Results")
    def query_returns_results(self):
        """Query should return results from ChromaDB."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.query(
                collection="test",
                query_text="test query"
            )

            return {"is_dict": isinstance(result, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get By ID Works")
    def get_by_id_works(self):
        """Get by ID should retrieve document."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.get(
                collection="test",
                ids=["doc-1"]
            )

            return {"is_dict": isinstance(result, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Collections Works")
    def list_collections_works(self):
        """List collections should return collection names."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.list_collections()

            return {"is_list": isinstance(result, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Write Deprecation Tests
    # =============================================================================

    @keyword("Add Is Deprecated")
    def add_is_deprecated(self):
        """Add should be deprecated and redirect to TypeDB."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.add(
                collection="test",
                documents=["test doc"],
                ids=["doc-1"]
            )

            return {
                "is_dict": isinstance(result, dict),
                "is_deprecated": 'deprecated' in result or 'redirected' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Update Is Deprecated")
    def update_is_deprecated(self):
        """Update should be deprecated."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.update(
                collection="test",
                documents=["updated doc"],
                ids=["doc-1"]
            )

            return {
                "is_dict": isinstance(result, dict),
                "is_deprecated": 'deprecated' in result or 'redirected' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delete Is Deprecated")
    def delete_is_deprecated(self):
        """Delete should be deprecated."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.delete(
                collection="test",
                ids=["doc-1"]
            )

            return {
                "is_dict": isinstance(result, dict),
                "is_deprecated": 'deprecated' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # TypeDB Redirect Tests
    # =============================================================================

    @keyword("Add Redirects To TypeDB")
    def add_redirects_to_typedb(self):
        """Add should redirect rules/decisions to TypeDB."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.add(
                collection="test",
                documents=["New rule content"],
                ids=["RULE-099"]
            )

            result_str = str(result).lower()
            return {
                "has_redirect": 'redirected' in result or 'typedb' in result_str
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Wrapper Uses Data Router")
    def wrapper_uses_data_router(self):
        """Wrapper should use DataRouter for TypeDB writes."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            return {
                "has_router": hasattr(wrapper, 'router') or hasattr(wrapper, '_router')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Deprecation Warning Tests
    # =============================================================================

    @keyword("Add Logs Deprecation Warning")
    def add_logs_deprecation_warning(self):
        """Add should log deprecation warning."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            result = wrapper.add(
                collection="test",
                documents=["test"],
                ids=["doc-1"]
            )

            result_str = str(result).lower()
            return {
                "has_deprecation": 'deprecated' in result or 'warning' in result_str or 'redirected' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Deprecation Status Works")
    def get_deprecation_status_works(self):
        """Should be able to check deprecation status."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            status = wrapper.get_deprecation_status()

            return {
                "is_dict": isinstance(status, dict),
                "has_writes_deprecated": 'writes_deprecated' in status,
                "writes_deprecated_true": status.get('writes_deprecated') is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Backwards Compatibility Tests
    # =============================================================================

    @keyword("Has Collection Interface")
    def has_collection_interface(self):
        """Should provide collection-like interface."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            return {"has_get_collection": hasattr(wrapper, 'get_collection')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Collection Returns Wrapper")
    def get_collection_returns_wrapper(self):
        """Get collection should return read-only wrapper."""
        try:
            from governance.chroma_readonly import ChromaReadOnly

            wrapper = ChromaReadOnly(skip_connection=True)
            collection = wrapper.get_collection("test_collection")

            return {
                "not_none": collection is not None,
                "has_query": hasattr(collection, 'query')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Factory Function Creates Wrapper")
    def factory_function_creates_wrapper(self):
        """Factory function should create wrapper."""
        try:
            from governance.chroma_readonly import create_readonly_client

            wrapper = create_readonly_client(skip_connection=True)
            return {"created": wrapper is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Factory Accepts Readonly Options")
    def factory_accepts_readonly_options(self):
        """Factory should accept options."""
        try:
            from governance.chroma_readonly import create_readonly_client

            wrapper = create_readonly_client(
                skip_connection=True,
                log_deprecations=True
            )
            return {"log_deprecations_true": wrapper.log_deprecations is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
