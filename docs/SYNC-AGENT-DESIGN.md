# Sync Agent Design

## Problem Statement

Local skills (ACE skillbooks) and session logs need to be synchronized:
- Between local machines (laptop ↔ server)
- To shared team repositories
- For backup and disaster recovery
- For cross-session learning continuity

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SYNC AGENT                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Watcher   │  │  Resolver   │  │  Publisher  │                 │
│  │  (Changes)  │──│  (Conflicts)│──│   (Push)    │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│         │                │                │                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Local State Store                         │   │
│  │  ChromaDB: skills, memories, sessions, rules                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   Sync Transports   │
                    ├─────────────────────┤
                    │ • Git (skillbooks)  │
                    │ • S3/R2 (sessions)  │
                    │ • WebDAV (local)    │
                    │ • ClearML (MLOps)   │
                    └─────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │  Server  │    │  GitHub  │    │  Team    │
       │  128GB   │    │   Repo   │    │  Share   │
       └──────────┘    └──────────┘    └──────────┘
```

---

## Components

### 1. Watcher

Monitors local state for changes:

```python
class SyncWatcher:
    """Watches for changes in local collections."""
    
    def __init__(self, chromadb_client, collections: list[str]):
        self.client = chromadb_client
        self.collections = collections
        self.last_sync = {}
    
    async def detect_changes(self) -> list[Change]:
        """Detect changes since last sync."""
        changes = []
        for collection in self.collections:
            # Get documents modified since last sync
            docs = self.client.get_collection(collection).get(
                where={"updated_at": {"$gt": self.last_sync.get(collection, "1970-01-01")}}
            )
            for doc in docs:
                changes.append(Change(
                    collection=collection,
                    doc_id=doc["id"],
                    action="upsert",
                    data=doc
                ))
        return changes
```

### 2. Resolver

Handles merge conflicts:

```python
class ConflictResolver:
    """Resolves sync conflicts between local and remote."""
    
    STRATEGIES = {
        "skills": "merge_latest",      # Combine skills, prefer newest
        "sessions": "local_wins",       # Local sessions are authoritative
        "rules": "remote_wins",         # Rules from governance repo win
        "memories": "merge_dedupe"      # Merge and deduplicate
    }
    
    def resolve(self, local: Document, remote: Document, collection: str) -> Document:
        strategy = self.STRATEGIES.get(collection, "local_wins")
        
        if strategy == "merge_latest":
            return self._merge_by_timestamp(local, remote)
        elif strategy == "local_wins":
            return local
        elif strategy == "remote_wins":
            return remote
        elif strategy == "merge_dedupe":
            return self._merge_dedupe(local, remote)
```

### 3. Publisher

Pushes changes to transports:

```python
class SyncPublisher:
    """Publishes changes to sync transports."""
    
    def __init__(self, transports: list[SyncTransport]):
        self.transports = transports
    
    async def publish(self, changes: list[Change]):
        for transport in self.transports:
            try:
                await transport.push(changes)
            except SyncError as e:
                logger.error(f"Sync failed for {transport.name}: {e}")
                # Queue for retry
                await self.retry_queue.add(changes, transport)
```

---

## Sync Transports

### Git Transport (Skillbooks)

```python
class GitTransport(SyncTransport):
    """Syncs skillbooks via Git."""
    
    def __init__(self, repo_path: str, remote: str = "origin"):
        self.repo = git.Repo(repo_path)
        self.remote = remote
    
    async def push(self, changes: list[Change]):
        # Filter to skillbook changes
        skillbook_changes = [c for c in changes if c.collection == "skills"]
        
        for change in skillbook_changes:
            # Write skillbook JSON
            path = f"skillbooks/{change.doc_id}.json"
            with open(path, "w") as f:
                json.dump(change.data, f, indent=2)
        
        # Commit and push
        self.repo.index.add([f"skillbooks/{c.doc_id}.json" for c in skillbook_changes])
        self.repo.index.commit(f"sync: {len(skillbook_changes)} skillbook updates")
        self.repo.remote(self.remote).push()
    
    async def pull(self) -> list[Change]:
        self.repo.remote(self.remote).pull()
        # Read skillbooks and return as changes
        ...
```

### ClearML Transport (Sessions)

```python
class ClearMLTransport(SyncTransport):
    """Syncs sessions via ClearML."""
    
    def __init__(self, project: str = "sim-ai-poc"):
        from clearml import Task
        self.project = project
    
    async def push(self, changes: list[Change]):
        session_changes = [c for c in changes if c.collection == "sessions"]
        
        for change in session_changes:
            task = Task.create(
                project_name=self.project,
                task_name=f"session_{change.doc_id}",
                task_type=Task.TaskTypes.data_processing
            )
            task.upload_artifact("session_log", change.data)
            task.close()
```

### WebDAV Transport (Local Network)

```python
class WebDAVTransport(SyncTransport):
    """Syncs to local NAS/WebDAV share."""
    
    def __init__(self, url: str, username: str, password: str):
        from webdav3.client import Client
        self.client = Client({
            "webdav_hostname": url,
            "webdav_login": username,
            "webdav_password": password
        })
    
    async def push(self, changes: list[Change]):
        for change in changes:
            path = f"/sim-ai/{change.collection}/{change.doc_id}.json"
            self.client.upload_sync(
                local_path=self._to_temp_file(change.data),
                remote_path=path
            )
```

---

## Sync Configuration

```yaml
# config/sync_config.yaml
sync:
  enabled: true
  interval_seconds: 300  # 5 minutes
  
  collections:
    - name: skills
      transport: git
      bidirectional: true
      
    - name: sessions
      transport: clearml
      bidirectional: false  # Push only
      
    - name: rules
      transport: git
      bidirectional: true
      conflict_strategy: remote_wins
      
    - name: memories
      transport: webdav
      bidirectional: true
      
  transports:
    git:
      repo: "./skillbooks"
      remote: "origin"
      branch: "main"
      
    clearml:
      project: "sim-ai-poc"
      
    webdav:
      url: "${WEBDAV_URL}"
      username: "${WEBDAV_USER}"
      password: "${WEBDAV_PASS}"
```

---

## Sync Agent Implementation

```python
# agent/sync_agent.py
"""
Sync Agent for Sim.ai PoC.
Synchronizes skills, sessions, and rules across environments.
"""
import asyncio
from datetime import datetime
from typing import Optional
import yaml

from chromadb import Client as ChromaClient


class SyncAgent:
    """Agent responsible for synchronizing local state."""
    
    def __init__(self, config_path: str = "config/sync_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.chromadb = ChromaClient()
        self.watcher = SyncWatcher(self.chromadb, self._get_collections())
        self.resolver = ConflictResolver()
        self.publisher = SyncPublisher(self._init_transports())
        
        self.running = False
        self.last_sync = None
    
    def _get_collections(self) -> list[str]:
        return [c["name"] for c in self.config["sync"]["collections"]]
    
    def _init_transports(self) -> list[SyncTransport]:
        transports = []
        for name, config in self.config["sync"]["transports"].items():
            if name == "git":
                transports.append(GitTransport(**config))
            elif name == "clearml":
                transports.append(ClearMLTransport(**config))
            elif name == "webdav":
                transports.append(WebDAVTransport(**config))
        return transports
    
    async def sync_once(self) -> dict:
        """Perform a single sync cycle."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "changes_pushed": 0,
            "changes_pulled": 0,
            "conflicts_resolved": 0,
            "errors": []
        }
        
        try:
            # Detect local changes
            local_changes = await self.watcher.detect_changes()
            
            # Pull remote changes
            for transport in self.publisher.transports:
                remote_changes = await transport.pull()
                
                # Resolve conflicts
                for remote in remote_changes:
                    local = self._find_local(remote)
                    if local:
                        resolved = self.resolver.resolve(local, remote, remote.collection)
                        results["conflicts_resolved"] += 1
                    else:
                        await self._apply_remote(remote)
                        results["changes_pulled"] += 1
            
            # Push local changes
            await self.publisher.publish(local_changes)
            results["changes_pushed"] = len(local_changes)
            
            self.last_sync = datetime.utcnow()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    async def run(self, interval: Optional[int] = None):
        """Run sync agent continuously."""
        interval = interval or self.config["sync"]["interval_seconds"]
        self.running = True
        
        while self.running:
            results = await self.sync_once()
            print(f"Sync completed: {results}")
            await asyncio.sleep(interval)
    
    def stop(self):
        """Stop the sync agent."""
        self.running = False


# CLI entry point
if __name__ == "__main__":
    import sys
    
    agent = SyncAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single sync
        results = asyncio.run(agent.sync_once())
        print(results)
    else:
        # Continuous sync
        try:
            asyncio.run(agent.run())
        except KeyboardInterrupt:
            agent.stop()
```

---

## Integration with Existing Infrastructure

### With ClearML (Already Deployed)

Your existing ClearML containers can store session artifacts:
```bash
# Start ClearML if not running
cd C:\Users\natik\Documents\Vibe\clearml
docker compose up -d
```

### With localgai claude-mem

Leverage existing memory infrastructure:
```python
# Query existing memories
mcp__claude-mem__chroma_query_documents(["localgai sync protocol"])
```

### With Git (Skillbooks)

```bash
# Initialize skillbooks repo
mkdir skillbooks
cd skillbooks
git init
git remote add origin https://github.com/youruser/sim-ai-skillbooks.git
```

---

## Deployment

```bash
# Install sync dependencies
pip install gitpython webdav3 clearml

# Configure transports
cp config/sync_config.yaml.example config/sync_config.yaml
# Edit with your credentials

# Run sync agent
python agent/sync_agent.py

# Or single sync
python agent/sync_agent.py --once
```

---

## Recommendation

**Should you develop a sync agent?**

**YES**, but incrementally:

1. **Phase 1:** Git sync for skillbooks (simplest, most valuable)
2. **Phase 2:** ClearML integration for sessions (you have it deployed)
3. **Phase 3:** WebDAV for local network sync (laptop ↔ server)
4. **Phase 4:** Custom transport for advanced needs

Start with Git transport - it provides version history, conflict resolution, and team collaboration out of the box.
