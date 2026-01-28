"""
Core Document Viewing MCP Tools
===============================
Core document viewing operations with pagination and type detection.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per RD-DOC-SERVICE: Document service with type detection + pagination

Tools:
- doc_get: Get document content by path (with pagination)
- docs_list: List documents in directory

Created: 2026-01-13 (extracted from documents.py)
Refactored: 2026-01-19 (compact aliases per RD-MCP-TOOL-NAMING)
"""

from pathlib import Path

from governance.mcp_tools.common import format_mcp_result
from .common import (
    EVIDENCE_DIR,
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
    GAPS_DIR,
)

# Per RD-DOC-SERVICE: File type detection via extension mapping
FILE_TYPE_MAP = {
    # Documentation
    ".md": {"type": "markdown", "syntax": "markdown"},
    ".txt": {"type": "text", "syntax": "text"},
    ".rst": {"type": "restructuredtext", "syntax": "rst"},
    # Data formats
    ".json": {"type": "json", "syntax": "json"},
    ".yaml": {"type": "yaml", "syntax": "yaml"},
    ".yml": {"type": "yaml", "syntax": "yaml"},
    ".xml": {"type": "xml", "syntax": "xml"},
    ".toml": {"type": "toml", "syntax": "toml"},
    ".csv": {"type": "csv", "syntax": "csv"},
    # Code - Python
    ".py": {"type": "code", "syntax": "python", "language": "Python"},
    ".pyi": {"type": "code", "syntax": "python", "language": "Python stub"},
    # Code - JavaScript/TypeScript
    ".js": {"type": "code", "syntax": "javascript", "language": "JavaScript"},
    ".ts": {"type": "code", "syntax": "typescript", "language": "TypeScript"},
    ".jsx": {"type": "code", "syntax": "jsx", "language": "React JSX"},
    ".tsx": {"type": "code", "syntax": "tsx", "language": "React TSX"},
    # Code - Haskell
    ".hs": {"type": "code", "syntax": "haskell", "language": "Haskell"},
    ".lhs": {"type": "code", "syntax": "haskell", "language": "Literate Haskell"},
    # Code - Other
    ".java": {"type": "code", "syntax": "java", "language": "Java"},
    ".go": {"type": "code", "syntax": "go", "language": "Go"},
    ".rs": {"type": "code", "syntax": "rust", "language": "Rust"},
    ".rb": {"type": "code", "syntax": "ruby", "language": "Ruby"},
    ".sh": {"type": "code", "syntax": "bash", "language": "Shell"},
    ".bash": {"type": "code", "syntax": "bash", "language": "Bash"},
    ".ps1": {"type": "code", "syntax": "powershell", "language": "PowerShell"},
    ".sql": {"type": "code", "syntax": "sql", "language": "SQL"},
    ".tql": {"type": "code", "syntax": "typeql", "language": "TypeQL"},
    # Config
    ".env": {"type": "config", "syntax": "dotenv"},
    ".ini": {"type": "config", "syntax": "ini"},
    ".cfg": {"type": "config", "syntax": "ini"},
    # Logs
    ".log": {"type": "log", "syntax": "log"},
}


def register_core_document_tools(mcp) -> None:
    """Register core document viewing MCP tools."""

    @mcp.tool()
    def doc_get(path: str, max_lines: int = 500, offset: int = 0) -> str:
        """
        Get document content by path. Supports relative or absolute paths.

        Use this to view rule markdown files, evidence files, task details,
        or any document linked from TypeDB entities. Supports pagination
        for large files via offset/max_lines parameters.

        Per RD-DOC-SERVICE: Document service with type detection + pagination.

        Args:
            path: Document path (relative to project root or absolute)
            max_lines: Maximum lines to return (default 500, 0 = unlimited)
            offset: Line offset for pagination (default 0, 1-indexed internally)

        Returns:
            JSON object with path, content, line_count, file_type, and pagination
        """
        # Resolve path - try multiple locations
        doc_path = Path(path)
        candidates = []
        if not doc_path.is_absolute():
            candidates = [
                Path(path),
                DOCS_DIR / path,
                EVIDENCE_DIR / path,
                RULES_DIR / path,
                GAPS_DIR / path,
                BACKLOG_DIR / path,
            ]
            for candidate in candidates:
                if candidate.exists():
                    doc_path = candidate
                    break

        if not doc_path.exists():
            return format_mcp_result({
                "error": f"Document not found: {path}",
                "tried_paths": [str(c) for c in candidates] if candidates else [path]
            })

        try:
            # Read file content
            content = doc_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            total_lines = len(lines)

            # Apply pagination
            if offset > 0:
                lines = lines[offset:]
            if max_lines > 0:
                lines = lines[:max_lines]

            # Detect file type
            suffix = doc_path.suffix.lower()
            file_info = FILE_TYPE_MAP.get(suffix, {"type": "unknown", "syntax": "text"})

            result = {
                "path": str(doc_path),
                "content": "\n".join(lines),
                "line_count": total_lines,
                "file_type": file_info.get("type", "unknown"),
                "syntax": file_info.get("syntax", "text"),
            }

            # Add language for code files
            if "language" in file_info:
                result["language"] = file_info["language"]

            # Add pagination info if applicable
            if offset > 0 or (max_lines > 0 and total_lines > max_lines):
                result["pagination"] = {
                    "offset": offset,
                    "limit": max_lines if max_lines > 0 else total_lines,
                    "returned": len(lines),
                    "total": total_lines,
                    "has_more": offset + len(lines) < total_lines
                }

            return format_mcp_result(result)

        except Exception as e:
            return format_mcp_result({"error": f"Failed to read document: {str(e)}"})

    @mcp.tool()
    def docs_list(
        directory: str = "docs",
        pattern: str = "*.md",
        recursive: bool = False
    ) -> str:
        """
        List documents in a directory.

        Args:
            directory: Directory to list (relative to project root)
            pattern: File pattern (default "*.md")
            recursive: Search recursively (default False)

        Returns:
            JSON array of document paths with basic metadata
        """
        # Resolve directory
        if directory.startswith("/"):
            dir_path = Path(directory)
        else:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path = DOCS_DIR / directory

        if not dir_path.exists():
            return format_mcp_result({
                "error": f"Directory not found: {directory}",
                "tried": str(dir_path)
            })

        try:
            # Find matching files
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))

            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            documents = []
            for f in files:
                stat = f.stat()
                suffix = f.suffix.lower()
                file_info = FILE_TYPE_MAP.get(suffix, {"type": "unknown"})

                documents.append({
                    "path": str(f),
                    "name": f.name,
                    "size": stat.st_size,
                    "type": file_info.get("type", "unknown"),
                    "modified": stat.st_mtime
                })

            return format_mcp_result({
                "directory": str(dir_path),
                "pattern": pattern,
                "recursive": recursive,
                "count": len(documents),
                "documents": documents
            })

        except Exception as e:
            return format_mcp_result({"error": f"Failed to list documents: {str(e)}"})

    # Legacy aliases for backward compatibility
    governance_get_document = doc_get
    governance_list_documents = docs_list
    mcp.tool(name="governance_get_document")(governance_get_document)
    mcp.tool(name="governance_list_documents")(governance_list_documents)
