#!/usr/bin/env python3
"""
Migrate claude-mem data to sim-ai ChromaDB

Phase 2 R&D: Inherit Experience Data Lakes
- Source: ~/.claude-mem/chroma (114 docs)
- Target: sim-ai ChromaDB (localhost:8001)

High-value document types to migrate:
- rules (11), rule (7) - governance patterns
- governance (6) - decision frameworks
- workflow (4) - automation scripts
- backlog (12) - task management patterns
- session_summary (8) - learnings
"""

import os
import chromadb
from typing import Optional

# Configuration
SOURCE_PATH = r"C:\Users\natik\.claude-mem\chroma"
SOURCE_COLLECTION = "claude_memories"

TARGET_HOST = os.getenv("CHROMADB_HOST", "localhost")
TARGET_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
TARGET_TOKEN = os.getenv("CHROMA_AUTH_TOKEN", "chroma-token-dev")
TARGET_COLLECTION = "sim_ai_knowledge"

# High-value types to migrate
HIGH_VALUE_TYPES = [
    "rules", "rule", "governance", "workflow", 
    "backlog", "session_summary", "audit"
]


def get_source_client() -> chromadb.ClientAPI:
    """Connect to source claude-mem ChromaDB"""
    return chromadb.PersistentClient(path=SOURCE_PATH)


def get_target_client() -> chromadb.ClientAPI:
    """Connect to target sim-ai ChromaDB"""
    headers = {"X-Chroma-Token": TARGET_TOKEN}
    return chromadb.HttpClient(
        host=TARGET_HOST, 
        port=TARGET_PORT, 
        headers=headers
    )


def analyze_source() -> dict:
    """Analyze source data structure"""
    client = get_source_client()
    col = client.get_collection(SOURCE_COLLECTION)
    
    results = col.get(include=["metadatas"], limit=200)
    
    stats = {
        "total": len(results["ids"]),
        "types": {},
        "projects": {},
        "high_value_count": 0
    }
    
    for meta in results["metadatas"]:
        if meta:
            doc_type = meta.get("type", "unknown")
            project = meta.get("project", "unknown")
            
            stats["types"][doc_type] = stats["types"].get(doc_type, 0) + 1
            stats["projects"][project] = stats["projects"].get(project, 0) + 1
            
            if doc_type in HIGH_VALUE_TYPES:
                stats["high_value_count"] += 1
    
    return stats


def migrate_high_value_docs(dry_run: bool = True) -> dict:
    """Migrate high-value documents to sim-ai"""
    source = get_source_client()
    source_col = source.get_collection(SOURCE_COLLECTION)
    
    # Get all high-value docs
    results = source_col.get(
        include=["documents", "metadatas", "embeddings"],
        limit=200
    )
    
    migrated = []
    skipped = []
    
    for i, (doc_id, doc, meta, emb) in enumerate(zip(
        results["ids"],
        results["documents"],
        results["metadatas"],
        results.get("embeddings", [None] * len(results["ids"]))
    )):
        if meta and meta.get("type") in HIGH_VALUE_TYPES:
            migrated.append({
                "id": doc_id,
                "type": meta.get("type"),
                "project": meta.get("project"),
                "has_embedding": emb is not None
            })
        else:
            skipped.append(doc_id)
    
    if not dry_run:
        target = get_target_client()
        # Create or get collection
        try:
            target_col = target.get_or_create_collection(TARGET_COLLECTION)
        except Exception as e:
            print(f"Error creating target collection: {e}")
            return {"error": str(e)}
        
        # Add documents
        for item in migrated:
            # Get full doc from source
            doc_data = source_col.get(
                ids=[item["id"]],
                include=["documents", "metadatas", "embeddings"]
            )
            
            try:
                target_col.add(
                    ids=[item["id"]],
                    documents=doc_data["documents"],
                    metadatas=doc_data["metadatas"],
                    embeddings=doc_data.get("embeddings")
                )
            except Exception as e:
                print(f"Error migrating {item['id']}: {e}")
    
    return {
        "migrated": len(migrated),
        "skipped": len(skipped),
        "dry_run": dry_run,
        "details": migrated[:5]  # First 5 for preview
    }


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Claude-mem -> Sim-ai Migration Tool")
    print("=" * 50)
    
    # Analyze source
    print("\n[Source Analysis]")
    stats = analyze_source()
    print(f"  Total docs: {stats['total']}")
    print(f"  High-value: {stats['high_value_count']}")
    print(f"\n  Types:")
    for t, c in sorted(stats["types"].items(), key=lambda x: -x[1])[:8]:
        marker = "*" if t in HIGH_VALUE_TYPES else " "
        print(f"    {marker} {t}: {c}")
    
    # Dry run migration
    print("\n[Migration Preview - dry run]")
    result = migrate_high_value_docs(dry_run=True)
    print(f"  Would migrate: {result['migrated']} docs")
    print(f"  Would skip: {result['skipped']} docs")
    
    if "--execute" in sys.argv:
        print("\n[Executing migration...]")
        result = migrate_high_value_docs(dry_run=False)
        print(f"  Migrated: {result['migrated']} docs")
    else:
        print("\n[!] Run with --execute to perform actual migration")
