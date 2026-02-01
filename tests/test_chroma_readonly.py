"""
ChromaDB Read-Only Wrapper Tests (P7.5)
Created: 2024-12-25

Tests for ChromaDB sunset - deprecating writes while allowing reads.
Strategic Goal: Transition to TypeDB-first architecture.
"""
import pytest
import json
from datetime import datetime


class TestReadOperations:
    """Tests for read operations (still allowed)."""

    @pytest.mark.unit
    def test_query_returns_results(self):
        """Query should return results from ChromaDB."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.query(
            collection="test",
            query_text="test query"
        )

        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_by_id(self):
        """Get by ID should retrieve document."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.get(
            collection="test",
            ids=["doc-1"]
        )

        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_list_collections(self):
        """List collections should return collection names."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.list_collections()

        assert isinstance(result, list)


class TestWriteDeprecation:
    """Tests for deprecated write operations."""

    @pytest.mark.unit
    def test_add_is_deprecated(self):
        """Add should be deprecated and redirect to TypeDB."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.add(
            collection="test",
            documents=["test doc"],
            ids=["doc-1"]
        )

        assert isinstance(result, dict)
        assert 'deprecated' in result or 'redirected' in result

    @pytest.mark.unit
    def test_update_is_deprecated(self):
        """Update should be deprecated."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.update(
            collection="test",
            documents=["updated doc"],
            ids=["doc-1"]
        )

        assert isinstance(result, dict)
        assert 'deprecated' in result or 'redirected' in result

    @pytest.mark.unit
    def test_delete_is_deprecated(self):
        """Delete should be deprecated."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.delete(
            collection="test",
            ids=["doc-1"]
        )

        assert isinstance(result, dict)
        assert 'deprecated' in result


class TestTypeDBRedirect:
    """Tests for TypeDB redirect functionality."""

    @pytest.mark.unit
    def test_add_redirects_to_typedb(self):
        """Add should redirect rules/decisions to TypeDB."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.add(
            collection="test",
            documents=["New rule content"],
            ids=["RULE-099"]
        )

        assert 'redirected' in result or 'typedb' in str(result).lower()

    @pytest.mark.unit
    def test_uses_data_router(self):
        """Wrapper should use DataRouter for TypeDB writes."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        assert hasattr(wrapper, 'router') or hasattr(wrapper, '_router')


class TestDeprecationWarnings:
    """Tests for deprecation warnings."""

    @pytest.mark.unit
    def test_add_logs_deprecation(self):
        """Add should log deprecation warning."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        result = wrapper.add(
            collection="test",
            documents=["test"],
            ids=["doc-1"]
        )

        # Should indicate deprecation
        assert 'deprecated' in result or 'warning' in str(result).lower() or 'redirected' in result

    @pytest.mark.unit
    def test_get_deprecation_status(self):
        """Should be able to check deprecation status."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        status = wrapper.get_deprecation_status()

        assert isinstance(status, dict)
        assert 'writes_deprecated' in status
        assert status['writes_deprecated'] is True


class TestBackwardsCompatibility:
    """Tests for backwards compatibility."""

    @pytest.mark.unit
    def test_collection_interface(self):
        """Should provide collection-like interface."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        assert hasattr(wrapper, 'get_collection')

    @pytest.mark.unit
    def test_get_collection_returns_wrapper(self):
        """Get collection should return read-only wrapper."""
        from governance.chroma_readonly import ChromaReadOnly

        wrapper = ChromaReadOnly(skip_connection=True)
        collection = wrapper.get_collection("test_collection")

        assert collection is not None
        assert hasattr(collection, 'query')


class TestReadOnlyIntegration:
    """Integration tests for read-only wrapper."""

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create wrapper."""
        from governance.chroma_readonly import create_readonly_client

        wrapper = create_readonly_client(skip_connection=True)
        assert wrapper is not None

    @pytest.mark.unit
    def test_factory_with_options(self):
        """Factory should accept options."""
        from governance.chroma_readonly import create_readonly_client

        wrapper = create_readonly_client(
            skip_connection=True,
            log_deprecations=True
        )
        assert wrapper.log_deprecations is True
