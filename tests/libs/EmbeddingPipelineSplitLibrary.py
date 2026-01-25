"""
RF-004: Robot Framework Library for Embedding Pipeline Split Tests.

Wraps tests/test_embedding_pipeline_split.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Files under 400 lines.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class EmbeddingPipelineSplitLibrary:
    """Robot Framework library for Embedding Pipeline Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def package_or_file_exists(self) -> Dict[str, Any]:
        """Check if embedding_pipeline exists as package or file."""
        package_dir = GOVERNANCE_DIR / "embedding_pipeline"
        old_file = GOVERNANCE_DIR / "embedding_pipeline.py"
        return {
            "package_exists": package_dir.exists(),
            "file_exists": old_file.exists(),
            "either_exists": package_dir.exists() or old_file.exists()
        }

    def chunking_module_exists(self) -> bool:
        """Check if chunking module exists in package."""
        package_dir = GOVERNANCE_DIR / "embedding_pipeline"
        if not package_dir.exists():
            return False
        return (package_dir / "chunking.py").exists()

    def pipeline_module_exists(self) -> bool:
        """Check if pipeline module exists in package."""
        package_dir = GOVERNANCE_DIR / "embedding_pipeline"
        if not package_dir.exists():
            return False
        return (package_dir / "pipeline.py").exists()

    def import_embedding_pipeline_class(self) -> bool:
        """Try to import EmbeddingPipeline class."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            return EmbeddingPipeline is not None
        except ImportError:
            return False

    def import_create_embedding_pipeline(self) -> bool:
        """Try to import create_embedding_pipeline function."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline
            return create_embedding_pipeline is not None
        except ImportError:
            return False

    def create_pipeline_instance(self) -> bool:
        """Test creating EmbeddingPipeline instance."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            pipeline = EmbeddingPipeline()
            return pipeline is not None
        except Exception:
            return False

    def pipeline_has_methods(self) -> Dict[str, bool]:
        """Check pipeline has required methods."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            pipeline = EmbeddingPipeline()
            return {
                "embed_rules": hasattr(pipeline, 'embed_rules'),
                "embed_sessions": hasattr(pipeline, 'embed_sessions'),
                "embed_session_chunked": hasattr(pipeline, 'embed_session_chunked')
            }
        except Exception:
            return {"error": True}

    def import_chunk_content(self) -> Dict[str, Any]:
        """Try to import chunk_content function."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
            return {"imported": True, "exists": chunk_content is not None}
        except ImportError as e:
            return {"imported": False, "error": str(e)}

    def test_chunk_content_splits_long(self) -> Dict[str, Any]:
        """Test chunk_content splits long text."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
            long_text = "This is a test line.\n" * 100
            chunks = chunk_content(long_text, chunk_size=500)
            all_under_limit = all(len(c) <= 500 for c in chunks)
            return {
                "chunk_count": len(chunks),
                "multiple_chunks": len(chunks) > 1,
                "all_under_limit": all_under_limit
            }
        except ImportError:
            return {"skip": True, "reason": "chunking module not implemented"}
        except Exception as e:
            return {"error": str(e)}

    def test_chunk_content_preserves_short(self) -> Dict[str, Any]:
        """Test chunk_content preserves short text."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
            short_text = "Short content"
            chunks = chunk_content(short_text, chunk_size=500)
            return {
                "chunk_count": len(chunks),
                "single_chunk": len(chunks) == 1,
                "preserved": chunks[0] == short_text if chunks else False
            }
        except ImportError:
            return {"skip": True, "reason": "chunking module not implemented"}
        except Exception as e:
            return {"error": str(e)}

    def all_modules_under_400_lines(self) -> Dict[str, Any]:
        """Check all modules in package are under 400 lines."""
        package_dir = GOVERNANCE_DIR / "embedding_pipeline"

        if not package_dir.exists():
            old_file = GOVERNANCE_DIR / "embedding_pipeline.py"
            if old_file.exists():
                line_count = len(old_file.read_text().splitlines())
                return {
                    "is_package": False,
                    "single_file_lines": line_count,
                    "needs_refactoring": line_count > 400
                }
            return {"exists": False}

        results = {"all_under_limit": True, "files": {}}
        for py_file in package_dir.glob("*.py"):
            line_count = len(py_file.read_text().splitlines())
            results["files"][py_file.name] = line_count
            if line_count > 400:
                results["all_under_limit"] = False

        return results

    def test_embed_session_chunked(self) -> Dict[str, Any]:
        """Test embed_session_chunked works."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(
                embedding_generator=MockEmbeddings(dimension=64),
                chunk_size=100
            )
            long_content = "Test content. " * 50
            docs = pipeline.embed_session_chunked("TEST-SESSION", long_content)

            return {
                "doc_count": len(docs),
                "has_docs": len(docs) >= 1,
                "correct_source": all(d.source == "TEST-SESSION" for d in docs),
                "correct_type": all(d.source_type == "session" for d in docs)
            }
        except Exception as e:
            return {"error": str(e)}

    def test_run_full_pipeline(self) -> Dict[str, Any]:
        """Test run_full_pipeline works."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
            result = pipeline.run_full_pipeline(dry_run=True)

            return {
                "has_rules": 'rules' in result,
                "has_decisions": 'decisions' in result,
                "has_sessions": 'sessions' in result,
                "has_total": 'total' in result
            }
        except Exception as e:
            return {"error": str(e)}
