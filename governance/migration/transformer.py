"""
Document Transformer
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Transforms ChromaDB documents to TypeDB format.
"""
import re
from typing import Dict, Any
from datetime import datetime


class DocumentTransformer:
    """Transforms ChromaDB documents to TypeDB format."""

    # ID patterns for type detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

    def detect_type(self, doc_id: str) -> str:
        """
        Detect document type from ID pattern.

        Args:
            doc_id: Document ID

        Returns:
            Type string: 'rule', 'decision', 'session', or 'document'
        """
        if self.RULE_PATTERN.match(doc_id):
            return 'rule'
        elif self.DECISION_PATTERN.match(doc_id):
            return 'decision'
        elif self.SESSION_PATTERN.match(doc_id):
            return 'session'
        else:
            return 'document'

    def transform(self, chroma_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform ChromaDB document to TypeDB format.

        Args:
            chroma_doc: ChromaDB document dict

        Returns:
            Transformed document for TypeDB
        """
        doc_id = chroma_doc.get('id', 'unknown')
        content = chroma_doc.get('content', chroma_doc.get('document', ''))
        metadata = chroma_doc.get('metadata', {})
        doc_type = self.detect_type(doc_id)

        result = {
            'id': doc_id,
            'content': content,
            'type': doc_type,
            'metadata': metadata,
            'source': 'chromadb_migration'
        }

        # Generate TypeQL based on type
        if doc_type == 'rule':
            result['typeql'] = self._generate_rule_typeql(doc_id, content, metadata)
        elif doc_type == 'decision':
            result['typeql'] = self._generate_decision_typeql(doc_id, content, metadata)
        elif doc_type == 'session':
            result['typeql'] = self._generate_session_typeql(doc_id, content, metadata)
        else:
            result['typeql'] = self._generate_document_typeql(doc_id, content, metadata)

        return result

    def _generate_rule_typeql(
        self,
        rule_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for rule."""
        name = metadata.get('name', content[:50] if content else 'Migrated Rule')
        directive = metadata.get('directive', content)
        return f'''
            insert $r isa rule-entity,
                has id "{self._escape(rule_id)}",
                has name "{self._escape(name)}",
                has directive "{self._escape(directive)}",
                has category "migrated",
                has priority "MEDIUM",
                has status "ACTIVE",
                has created-date {datetime.now().isoformat()};
        '''

    def _generate_decision_typeql(
        self,
        decision_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for decision."""
        name = metadata.get('name', content[:50] if content else 'Migrated Decision')
        return f'''
            insert $d isa decision,
                has decision-id "{self._escape(decision_id)}",
                has decision-name "{self._escape(name)}",
                has decision-context "{self._escape(content[:500] if content else '')}",
                has decision-status "ACTIVE",
                has decision-date {datetime.now().isoformat()};
        '''

    def _generate_session_typeql(
        self,
        session_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for session."""
        # Sessions are primarily stored as embeddings, not in TypeDB directly
        return f'''
            # Session {session_id} - stored as embedding
            # Content length: {len(content)} chars
        '''

    def _generate_document_typeql(
        self,
        doc_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for generic document."""
        return f'''
            insert $doc isa vector-document,
                has id "{self._escape(doc_id)}",
                has content "{self._escape(content[:1000] if content else '')}",
                has source-type "migrated",
                has source "{self._escape(metadata.get('source', 'chromadb'))}",
                has created-date {datetime.now().isoformat()};
        '''

    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for TypeQL string literals."""
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
