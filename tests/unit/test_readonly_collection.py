"""
Unit tests for Read-Only Collection Wrapper.

Per DOC-SIZE-01-v1: Tests for governance/readonly/collection.py module.
Tests: ReadOnlyCollection — query, get, add, update, delete delegate to parent.
"""

from unittest.mock import MagicMock

from governance.readonly.collection import ReadOnlyCollection


def _make_collection(parent=None):
    """Create a ReadOnlyCollection with a mock parent."""
    if parent is None:
        parent = MagicMock()
    return ReadOnlyCollection(name="test_collection", parent=parent)


# ── Init ───────────────────────────────────────────────────


class TestReadOnlyCollectionInit:
    def test_name_stored(self):
        col = _make_collection()
        assert col.name == "test_collection"

    def test_parent_stored(self):
        parent = MagicMock()
        col = ReadOnlyCollection(name="col", parent=parent)
        assert col._parent is parent


# ── query ──────────────────────────────────────────────────


class TestQuery:
    def test_delegates_to_parent(self):
        parent = MagicMock()
        parent.query.return_value = {"documents": [["doc1"]]}
        col = ReadOnlyCollection(name="my_col", parent=parent)

        result = col.query(query_texts=["search term"], n_results=5)

        parent.query.assert_called_once_with(
            collection="my_col",
            query_text="search term",
            n_results=5,
        )
        assert result == {"documents": [["doc1"]]}

    def test_empty_query_texts(self):
        parent = MagicMock()
        parent.query.return_value = {}
        col = _make_collection(parent)

        col.query(query_texts=None)

        parent.query.assert_called_once_with(
            collection="test_collection",
            query_text="",
            n_results=10,
        )

    def test_default_n_results(self):
        parent = MagicMock()
        parent.query.return_value = {}
        col = _make_collection(parent)

        col.query(query_texts=["q"])

        parent.query.assert_called_once_with(
            collection="test_collection",
            query_text="q",
            n_results=10,
        )

    def test_extra_kwargs_passed(self):
        parent = MagicMock()
        parent.query.return_value = {}
        col = _make_collection(parent)

        col.query(query_texts=["q"], where={"key": "val"})

        parent.query.assert_called_once_with(
            collection="test_collection",
            query_text="q",
            n_results=10,
            where={"key": "val"},
        )


# ── get ────────────────────────────────────────────────────


class TestGet:
    def test_delegates_to_parent(self):
        parent = MagicMock()
        parent.get.return_value = {"ids": ["id1"], "documents": ["doc1"]}
        col = _make_collection(parent)

        result = col.get(ids=["id1"])

        parent.get.assert_called_once_with(
            collection="test_collection",
            ids=["id1"],
        )
        assert result["ids"] == ["id1"]

    def test_none_ids_defaults_to_empty(self):
        parent = MagicMock()
        parent.get.return_value = {}
        col = _make_collection(parent)

        col.get(ids=None)

        parent.get.assert_called_once_with(
            collection="test_collection",
            ids=[],
        )


# ── add (deprecated) ──────────────────────────────────────


class TestAdd:
    def test_delegates_to_parent(self):
        parent = MagicMock()
        parent.add.return_value = {"status": "redirected"}
        col = _make_collection(parent)

        result = col.add(documents=["doc1"], ids=["id1"])

        parent.add.assert_called_once_with(
            collection="test_collection",
            documents=["doc1"],
            ids=["id1"],
        )
        assert result["status"] == "redirected"

    def test_none_defaults(self):
        parent = MagicMock()
        parent.add.return_value = {}
        col = _make_collection(parent)

        col.add()

        parent.add.assert_called_once_with(
            collection="test_collection",
            documents=[],
            ids=[],
        )


# ── update (deprecated) ───────────────────────────────────


class TestUpdate:
    def test_delegates_to_parent(self):
        parent = MagicMock()
        parent.update.return_value = {"status": "redirected"}
        col = _make_collection(parent)

        result = col.update(documents=["updated"], ids=["id1"])

        parent.update.assert_called_once_with(
            collection="test_collection",
            documents=["updated"],
            ids=["id1"],
        )

    def test_none_defaults(self):
        parent = MagicMock()
        parent.update.return_value = {}
        col = _make_collection(parent)

        col.update()

        parent.update.assert_called_once_with(
            collection="test_collection",
            documents=[],
            ids=[],
        )


# ── delete (deprecated) ───────────────────────────────────


class TestDelete:
    def test_delegates_to_parent(self):
        parent = MagicMock()
        parent.delete.return_value = {"deleted": 1}
        col = _make_collection(parent)

        result = col.delete(ids=["id1"])

        parent.delete.assert_called_once_with(
            collection="test_collection",
            ids=["id1"],
        )
        assert result["deleted"] == 1

    def test_none_defaults(self):
        parent = MagicMock()
        parent.delete.return_value = {}
        col = _make_collection(parent)

        col.delete()

        parent.delete.assert_called_once_with(
            collection="test_collection",
            ids=[],
        )
