# Prompt 07: Everything Search + File Monitoring Integration

## Context
You are integrating [voidtools Everything](https://www.voidtools.com/) search into capture-spine AND building a file monitoring system.

**This is part of the Productivity Suite** - see `capture-spine/docs/features/productivity/`:
- `document-lineage.md` - Track file origins and changes
- `IMPLEMENTATION_GUIDE.md` - Overall approach

Everything is a fast file search utility for Windows with:
- **HTTP Server API** (port 8080 by default)
- **Command-line interface** (`es.exe`)
- Advanced filtering (date modified, size, path, regex)

## Why Integrate?

1. **Instant file search** - Find any file across all projects instantly
2. **Date-modified filtering** - Find files changed in last N hours (your use case!)
3. **Track file changes** - Monitor directories, create lineage records
4. **Link files to conversations** - Know which chat created which file

## Everything HTTP API Reference

### Enable HTTP Server
In Everything: Tools → Options → HTTP Server → Enable HTTP Server (default port 8080)

### API Endpoints

**Search:**
```
GET http://localhost:8080/?search=<query>&json=1
```

**Parameters:**
- `search` - Search query (supports regex, wildcards)
- `json=1` - Return JSON format
- `count=<n>` - Limit results
- `offset=<n>` - Pagination
- `sort=<field>` - Sort by (name, path, size, date_modified)
- `ascending=0|1` - Sort direction

**Query Syntax (POWERFUL!):**
- `*.md` - Wildcard
- `dm:today` - Date modified today
- `dm:last6hours` - Last 6 hours
- `dm:last24hours` - Last 24 hours
- `dm:2024-01-15..2024-01-20` - Date range
- `path:C:\projects` - Path filter
- `path:B:\github\py-sec-edgar` - Your workspace!
- `regex:pattern` - Regex search
- `size:>1mb` - Size filter
- `ext:md;py;ts` - Multiple extensions

**Combined Query Examples:**
```
# Markdown files changed in last 6 hours in your workspace
path:B:\github\py-sec-edgar *.md dm:last6hours

# Python files modified today
path:B:\github\py-sec-edgar *.py dm:today

# All source files changed recently
path:B:\github\py-sec-edgar ext:md;py;ts;tsx dm:last24hours
```

### Example Response
```json
{
  "totalResults": 42,
  "results": [
    {
      "type": "file",
      "name": "README.md",
      "path": "B:\\github\\py-sec-edgar\\capture-spine",
      "size": 1234,
      "date_modified": 133512345678901234  // Windows FILETIME
    }
  ]
}
```

## Your Task

### 1. Create Everything Service
Location: `capture-spine/app/services/everything_search.py`

```python
"""Everything Search integration for fast file search and monitoring."""
import httpx
from typing import List, Optional, AsyncIterator
from datetime import datetime, timedelta
from pydantic import BaseModel
from pathlib import Path

class FileSearchResult(BaseModel):
    name: str
    path: str
    full_path: str
    size: int
    date_modified: datetime
    type: str  # "file" or "folder"
    extension: str | None

class EverythingSearchService:
    """
    Fast file search using voidtools Everything HTTP API.
    Falls back to filesystem scan when Everything not available.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self._available: bool | None = None

    async def is_available(self) -> bool:
        """Check if Everything HTTP server is running."""
        if self._available is not None:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/?search=test&json=1&count=1")
                self._available = response.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def search(
        self,
        query: str,
        path_filter: str | None = None,
        extensions: list[str] | None = None,
        modified_within_hours: int | None = None,
        limit: int = 100,
    ) -> list[FileSearchResult]:
        """
        Search files using Everything.

        Args:
            query: Search query (supports wildcards, regex)
            path_filter: Limit to this directory path
            extensions: Filter by extensions (e.g., ["md", "py"])
            modified_within_hours: Only files modified within N hours
            limit: Max results
        """
        if not await self.is_available():
            return await self._fallback_search(query, path_filter, extensions, modified_within_hours, limit)

        # Build Everything query
        search_parts = []

        if path_filter:
            search_parts.append(f'path:"{path_filter}"')

        if extensions:
            ext_str = ";".join(extensions)
            search_parts.append(f"ext:{ext_str}")

        if modified_within_hours:
            search_parts.append(f"dm:last{modified_within_hours}hours")

        if query:
            search_parts.append(query)

        full_query = " ".join(search_parts)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    "search": full_query,
                    "json": 1,
                    "count": limit,
                    "sort": "date_modified",
                    "ascending": 0,  # Newest first
                }
            )
            response.raise_for_status()
            data = response.json()

        return [self._parse_result(r) for r in data.get("results", [])]

    async def find_recently_modified(
        self,
        hours: int = 6,
        path_filter: str | None = None,
        extensions: list[str] | None = None,
    ) -> list[FileSearchResult]:
        """Find files modified in last N hours."""
        return await self.search(
            query="",
            path_filter=path_filter,
            extensions=extensions,
            modified_within_hours=hours,
            limit=500,
        )

    async def monitor_directory(
        self,
        path: str,
        poll_interval_seconds: int = 60,
        extensions: list[str] | None = None,
    ) -> AsyncIterator[list[FileSearchResult]]:
        """
        Continuously monitor directory for changes.
        Yields batches of changed files.
        """
        import asyncio
        seen_modified: dict[str, datetime] = {}

        while True:
            results = await self.find_recently_modified(
                hours=1,  # Check last hour, dedup ourselves
                path_filter=path,
                extensions=extensions,
            )

            # Find new/changed files
            changes = []
            for result in results:
                prev_modified = seen_modified.get(result.full_path)
                if prev_modified is None or result.date_modified > prev_modified:
                    changes.append(result)
                    seen_modified[result.full_path] = result.date_modified

            if changes:
                yield changes

            await asyncio.sleep(poll_interval_seconds)

    def _parse_result(self, result: dict) -> FileSearchResult:
        """Parse Everything API result."""
        # Convert Windows FILETIME to datetime
        ft = result.get("date_modified", 0)
        # FILETIME is 100-nanosecond intervals since Jan 1, 1601
        dt = datetime(1601, 1, 1) + timedelta(microseconds=ft // 10)

        name = result["name"]
        path = result["path"]
        full_path = f"{path}\\{name}"

        return FileSearchResult(
            name=name,
            path=path,
            full_path=full_path,
            size=result.get("size", 0),
            date_modified=dt,
            type=result.get("type", "file"),
            extension=Path(name).suffix.lstrip(".") if "." in name else None,
        )

    async def _fallback_search(
        self,
        query: str,
        path_filter: str | None,
        extensions: list[str] | None,
        modified_within_hours: int | None,
        limit: int,
    ) -> list[FileSearchResult]:
        """Fallback to filesystem scan when Everything not available."""
        # Use logic from scan_docs.py / scan_python_changes.py
        ...
```

### 2. Create File Monitor Service
Location: `capture-spine/app/features/file_monitor/service.py`

```python
"""File monitoring with document lineage tracking."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..services.everything_search import EverythingSearchService, FileSearchResult

class FileMonitorService:
    """
    Monitors directories for file changes and creates lineage records.
    """

    def __init__(
        self,
        db_session,
        everything: EverythingSearchService,
    ):
        self.db = db_session
        self.everything = everything

    async def scan_and_record(
        self,
        path: str,
        extensions: list[str] = ["md", "py", "ts", "tsx"],
        hours: int = 24,
    ) -> list[dict]:
        """
        Scan for recent changes and create/update lineage records.
        """
        results = await self.everything.find_recently_modified(
            hours=hours,
            path_filter=path,
            extensions=extensions,
        )

        records = []
        for file_result in results:
            record = await self._create_or_update_lineage(file_result)
            records.append(record)

        return records

    async def link_to_chat(
        self,
        file_path: str,
        chat_session_id: UUID,
        link_type: str = "created",  # or "modified", "referenced"
    ):
        """Link a file to a chat session that created/modified it."""
        # Insert into document_chat_links table
        ...

    async def get_file_history(self, file_path: str) -> list[dict]:
        """Get history of a file including linked chats."""
        ...
```

### 3. Create API Endpoints
Location: `capture-spine/app/routers/files.py`

```python
from fastapi import APIRouter, Query, Depends
from typing import Optional

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/search")
async def search_files(
    q: str = Query("", description="Search query"),
    path: Optional[str] = Query(None, description="Limit to path"),
    hours: Optional[int] = Query(None, description="Modified in last N hours"),
    extensions: Optional[str] = Query(None, description="Extensions (comma-separated)"),
    limit: int = Query(100, le=1000),
):
    """
    Search files using Everything (or fallback).

    Examples:
    - /api/files/search?hours=6 - Files modified in last 6 hours
    - /api/files/search?q=*.md&path=B:\\github - Markdown files in github folder
    - /api/files/search?extensions=py,ts&hours=24 - Code files changed today
    """
    ...

@router.get("/recent")
async def get_recent_files(
    hours: int = Query(6),
    path: Optional[str] = Query(None),
    extensions: Optional[str] = Query("md,py,ts,tsx"),
):
    """Get recently modified files (your main use case!)."""
    ...

@router.get("/lineage/{file_path:path}")
async def get_file_lineage(file_path: str):
    """Get lineage history for a file including linked chats."""
    ...

@router.post("/lineage/{file_path:path}/link-chat")
async def link_file_to_chat(
    file_path: str,
    chat_session_id: str,
    link_type: str = "created",
):
    """Link a file to a chat session."""
    ...

@router.get("/health")
async def everything_health():
    """Check if Everything Search is available."""
    ...
```

### 4. Create UI Component
Location: `capture-spine/frontend/src/features/files/`

```typescript
// FileMonitor.tsx - Show recent file changes
interface FileChange {
  name: string;
  path: string;
  full_path: string;
  size: number;
  date_modified: string;
  extension: string | null;
}

export function FileMonitor() {
  const [hours, setHours] = useState(6);
  const [files, setFiles] = useState<FileChange[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ['recent-files', hours],
    queryFn: () => fetch(`/api/files/recent?hours=${hours}`).then(r => r.json()),
    refetchInterval: 60000,  // Refresh every minute
  });

  return (
    <div className="file-monitor">
      <div className="header">
        <h3>Recent File Changes</h3>
        <select value={hours} onChange={e => setHours(Number(e.target.value))}>
          <option value={1}>Last hour</option>
          <option value={6}>Last 6 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={48}>Last 48 hours</option>
        </select>
      </div>

      <div className="file-list">
        {data?.results?.map(file => (
          <FileRow key={file.full_path} file={file} />
        ))}
      </div>
    </div>
  );
}
```

### 5. Database Tables
Add migration for document lineage (from `document-lineage.md`):

```sql
-- Track file versions and origins
CREATE TABLE document_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    version INTEGER NOT NULL DEFAULT 1,
    origin_type VARCHAR(50),  -- 'vscode_copilot', 'capture_chat', 'manual', 'unknown'
    origin_chat_session_id UUID,
    git_commit_hash VARCHAR(40),
    content_preview TEXT,
    line_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(file_path, version)
);

-- Link files to chat sessions
CREATE TABLE document_chat_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    lineage_id UUID REFERENCES document_lineage(id),
    chat_session_id UUID NOT NULL,
    chat_source VARCHAR(50),  -- 'vscode_copilot', 'capture_spine'
    link_type VARCHAR(50) NOT NULL,  -- 'created', 'modified', 'referenced', 'discussed'
    context_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lineage_file ON document_lineage(file_path);
CREATE INDEX idx_lineage_chat ON document_lineage(origin_chat_session_id);
CREATE INDEX idx_links_file ON document_chat_links(file_path);
CREATE INDEX idx_links_chat ON document_chat_links(chat_session_id);
```

## Use Cases

1. **"Show me files changed in last 6 hours"** - Your immediate need
   ```
   GET /api/files/recent?hours=6
   ```

2. **"What markdown docs were modified today?"**
   ```
   GET /api/files/search?extensions=md&hours=24
   ```

3. **"Which chat created this file?"**
   ```
   GET /api/files/lineage/capture-spine/docs/features/productivity/README.md
   ```

4. **"Monitor my workspace for changes"** - Background task that creates lineage records

5. **"Open file in VS Code"** - Click result to open
   ```typescript
   const openInVSCode = (path: string) => {
     window.open(`vscode://file/${path}`, '_blank');
   };
   ```

## Success Criteria
- [ ] Everything Search detection works
- [ ] `/api/files/search` returns results
- [ ] `/api/files/recent?hours=6` shows recent files
- [ ] Falls back gracefully when Everything not running
- [ ] Document lineage records created
- [ ] Files can be linked to chat sessions
- [ ] UI shows recent changes with filtering
- [ ] Can click to open file in VS Code

## Configuration

```python
# capture-spine/app/config.py
EVERYTHING_ENABLED = os.getenv("EVERYTHING_ENABLED", "true").lower() == "true"
EVERYTHING_URL = os.getenv("EVERYTHING_URL", "http://localhost:8080")
FILE_MONITOR_POLL_SECONDS = int(os.getenv("FILE_MONITOR_POLL_SECONDS", "60"))
```

## Notes
- Everything must be running with HTTP server enabled
- Default port is 8080 (configurable in Everything settings)
- Date format in Everything is Windows FILETIME (100-nanosecond intervals since 1601)
- Gracefully fall back to filesystem scan if Everything not available
- Consider adding WebSocket for real-time file change notifications
