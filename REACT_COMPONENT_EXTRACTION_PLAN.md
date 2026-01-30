# React Component Extraction Plan

## Objective

Extract a simplified version of capture-spine's NewsfeedPage for py-sec-edgar as a **unified SEC filing feed reader**.

---

## Source Components (capture-spine)

### Core Components to Extract

| Component | Lines | Purpose | Extract? |
|-----------|-------|---------|----------|
| `NewsfeedPage.tsx` | ~200 | Page orchestration | ✅ Simplify |
| `useNewsfeedState.ts` | 1111 | Centralized state | ✅ Simplify to ~200 lines |
| `ArticleList.tsx` | 421 | Virtualized list | ✅ Extract |
| `ArticleDetail.tsx` | 508 | Content viewer | ✅ Simplify |
| `ArticleRow.tsx` | ~150 | Row rendering | ✅ Extract |
| `FeedSidebar.tsx` | ~300 | Feed navigation | ✅ Simplify |
| `HeaderBar.tsx` | ~200 | Toolbar | ✅ Simplify |

### Components to Remove (Not Needed for py-sec-edgar)

| Component | Reason |
|-----------|--------|
| Knowledge items (notes, prompts) | py-sec-edgar doesn't need knowledge graph |
| User authentication | Single-user, no auth needed |
| Time Machine | Advanced feature, not needed initially |
| Live streaming | Can add later if needed |
| Semantic topics | Advanced feature |
| Admin hierarchy | Not needed |

---

## Target Component Structure

```
py-sec-edgar-feed-ui/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── index.tsx                    # Main export
│   ├── UnifiedFilingFeed.tsx        # Main component
│   ├── components/
│   │   ├── FilingList.tsx           # From ArticleList
│   │   ├── FilingRow.tsx            # From ArticleRow
│   │   ├── FilingDetail.tsx         # From ArticleDetail
│   │   ├── FilingSidebar.tsx        # From FeedSidebar (simplified)
│   │   └── FilingToolbar.tsx        # From HeaderBar (simplified)
│   ├── hooks/
│   │   ├── useFilingFeed.ts         # Simplified from useNewsfeedState
│   │   └── useInfiniteScroll.ts     # Copy as-is
│   ├── api/
│   │   ├── client.ts                # Simple fetch client
│   │   └── types.ts                 # Filing types
│   └── styles/
│       └── index.css                # Tailwind CSS
└── stories/                         # Storybook stories
    └── UnifiedFilingFeed.stories.tsx
```

---

## Simplified useFilingFeed Hook

```typescript
// src/hooks/useFilingFeed.ts
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useState, useMemo } from 'react';
import type { Filing, FilingFilters } from '../api/types';

export interface UseFilingFeedOptions {
  apiEndpoint: string;
  initialFilters?: Partial<FilingFilters>;
}

export function useFilingFeed(options: UseFilingFeedOptions) {
  const { apiEndpoint, initialFilters = {} } = options;

  // Filter state
  const [filters, setFilters] = useState<FilingFilters>({
    formTypes: initialFilters.formTypes || [],
    companies: initialFilters.companies || [],
    dateRange: initialFilters.dateRange || null,
    searchQuery: '',
  });

  // Selected filing
  const [selectedFiling, setSelectedFiling] = useState<Filing | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  // Fetch filings with infinite scroll
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['filings', filters],
    queryFn: async ({ pageParam = 0 }) => {
      const params = new URLSearchParams({
        offset: String(pageParam),
        limit: '50',
        ...filtersToParams(filters),
      });
      const response = await fetch(`${apiEndpoint}/filings?${params}`);
      return response.json();
    },
    getNextPageParam: (lastPage, pages) => {
      if (lastPage.filings.length < 50) return undefined;
      return pages.length * 50;
    },
  });

  // Flatten pages
  const filings = useMemo(() => {
    return data?.pages.flatMap(page => page.filings) ?? [];
  }, [data]);

  // Navigation
  const selectNext = () => {
    if (selectedIndex < filings.length - 1) {
      const newIndex = selectedIndex + 1;
      setSelectedIndex(newIndex);
      setSelectedFiling(filings[newIndex]);
    }
  };

  const selectPrevious = () => {
    if (selectedIndex > 0) {
      const newIndex = selectedIndex - 1;
      setSelectedIndex(newIndex);
      setSelectedFiling(filings[newIndex]);
    }
  };

  return {
    filings,
    selectedFiling,
    selectedIndex,
    setSelectedFiling: (filing: Filing | null) => {
      setSelectedFiling(filing);
      setSelectedIndex(filing ? filings.indexOf(filing) : -1);
    },
    selectNext,
    selectPrevious,
    filters,
    setFilters,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  };
}

function filtersToParams(filters: FilingFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.formTypes.length > 0) {
    params.form_types = filters.formTypes.join(',');
  }
  if (filters.companies.length > 0) {
    params.ciks = filters.companies.join(',');
  }
  if (filters.searchQuery) {
    params.search = filters.searchQuery;
  }
  if (filters.dateRange) {
    params.date_from = filters.dateRange[0].toISOString();
    params.date_to = filters.dateRange[1].toISOString();
  }
  return params;
}
```

---

## Simplified Main Component

```tsx
// src/UnifiedFilingFeed.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useFilingFeed } from './hooks/useFilingFeed';
import { FilingList } from './components/FilingList';
import { FilingDetail } from './components/FilingDetail';
import { FilingSidebar } from './components/FilingSidebar';
import { FilingToolbar } from './components/FilingToolbar';
import './styles/index.css';

export interface UnifiedFilingFeedProps {
  /**
   * API endpoint for fetching filings.
   * Can be FeedSpine, capture-spine, or custom API.
   */
  apiEndpoint: string;

  /**
   * Initial filters to apply.
   */
  initialFilters?: {
    formTypes?: string[];
    companies?: string[];
    dateRange?: [Date, Date];
  };

  /**
   * Custom rendering for filing metadata.
   */
  renderMetadata?: (filing: Filing) => React.ReactNode;

  /**
   * Called when a filing is selected.
   */
  onFilingSelect?: (filing: Filing) => void;

  /**
   * Enable/disable sidebar (default: true).
   */
  showSidebar?: boolean;
}

const queryClient = new QueryClient();

export function UnifiedFilingFeed({
  apiEndpoint,
  initialFilters,
  renderMetadata,
  onFilingSelect,
  showSidebar = true,
}: UnifiedFilingFeedProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <UnifiedFilingFeedInner
        apiEndpoint={apiEndpoint}
        initialFilters={initialFilters}
        renderMetadata={renderMetadata}
        onFilingSelect={onFilingSelect}
        showSidebar={showSidebar}
      />
    </QueryClientProvider>
  );
}

function UnifiedFilingFeedInner(props: UnifiedFilingFeedProps) {
  const {
    filings,
    selectedFiling,
    setSelectedFiling,
    selectNext,
    selectPrevious,
    filters,
    setFilters,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useFilingFeed({
    apiEndpoint: props.apiEndpoint,
    initialFilters: props.initialFilters,
  });

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'j' || e.key === 'ArrowDown') {
        e.preventDefault();
        selectNext();
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault();
        selectPrevious();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [selectNext, selectPrevious]);

  return (
    <div className="filing-feed flex h-full bg-gray-50">
      {/* Left: Sidebar (optional) */}
      {props.showSidebar && (
        <FilingSidebar
          filters={filters}
          onFiltersChange={setFilters}
        />
      )}

      {/* Center: Filing List */}
      <div className="flex-1 min-w-0">
        <FilingToolbar
          filters={filters}
          onFiltersChange={setFilters}
        />
        <FilingList
          filings={filings}
          selectedFiling={selectedFiling}
          onSelectFiling={(filing) => {
            setSelectedFiling(filing);
            props.onFilingSelect?.(filing);
          }}
          isLoading={isLoading}
          isFetchingNextPage={isFetchingNextPage}
          hasNextPage={hasNextPage}
          onLoadMore={fetchNextPage}
        />
      </div>

      {/* Right: Detail Panel */}
      {selectedFiling && (
        <FilingDetail
          filing={selectedFiling}
          renderMetadata={props.renderMetadata}
          onClose={() => setSelectedFiling(null)}
        />
      )}
    </div>
  );
}
```

---

## SEC-Specific Filing Detail

```tsx
// src/components/FilingDetail.tsx
import type { Filing } from '../api/types';

export interface FilingDetailProps {
  filing: Filing;
  renderMetadata?: (filing: Filing) => React.ReactNode;
  onClose: () => void;
}

export function FilingDetail({ filing, renderMetadata, onClose }: FilingDetailProps) {
  return (
    <div className="w-[400px] border-l border-gray-200 bg-white overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold truncate">{filing.title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            ✕
          </button>
        </div>
      </div>

      {/* SEC Metadata */}
      <div className="p-4 border-b border-gray-200">
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt className="text-gray-500">CIK</dt>
          <dd className="font-mono">{filing.cik}</dd>

          <dt className="text-gray-500">Form Type</dt>
          <dd className="font-semibold">{filing.formType}</dd>

          <dt className="text-gray-500">Filed</dt>
          <dd>{formatDate(filing.filedAt)}</dd>

          <dt className="text-gray-500">Accession</dt>
          <dd className="font-mono text-xs">{filing.accessionNumber}</dd>
        </dl>

        {/* Custom metadata slot */}
        {renderMetadata?.(filing)}
      </div>

      {/* Documents */}
      <div className="p-4">
        <h3 className="font-medium mb-2">Documents</h3>
        <ul className="space-y-1">
          {filing.documents.map((doc) => (
            <li key={doc.sequence}>
              <a
                href={doc.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded"
              >
                <span className="text-xs bg-gray-200 px-1 rounded">
                  {doc.type}
                </span>
                <span className="truncate flex-1">{doc.description}</span>
                <ExternalLink className="w-4 h-4 text-gray-400" />
              </a>
            </li>
          ))}
        </ul>
      </div>

      {/* Exhibits (if py-sec-edgar parsed them) */}
      {filing.exhibits && filing.exhibits.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <h3 className="font-medium mb-2">Exhibits</h3>
          <ul className="space-y-1">
            {filing.exhibits.map((exhibit) => (
              <li key={exhibit.number} className="text-sm">
                <span className="text-gray-500">Ex. {exhibit.number}:</span>{' '}
                {exhibit.description}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## API Types

```typescript
// src/api/types.ts

export interface Filing {
  id: string;
  cik: string;
  companyName: string;
  formType: string;
  filedAt: string;
  accessionNumber: string;
  title: string;
  url: string;
  documents: FilingDocument[];
  exhibits?: Exhibit[];

  // Optional py-sec-edgar parsed data
  parsedData?: {
    riskFactors?: string;
    businessDescription?: string;
    subsidiaries?: Subsidiary[];
  };
}

export interface FilingDocument {
  sequence: number;
  description: string;
  type: string;
  url: string;
  size?: number;
}

export interface Exhibit {
  number: string;
  description: string;
  url: string;
}

export interface Subsidiary {
  name: string;
  jurisdiction: string;
  ownership?: string;
}

export interface FilingFilters {
  formTypes: string[];
  companies: string[];
  dateRange: [Date, Date] | null;
  searchQuery: string;
}
```

---

## Backend API Contract

The UI expects a simple REST API:

```
GET /filings
  Query params:
    - offset: number (default 0)
    - limit: number (default 50)
    - form_types: string (comma-separated)
    - ciks: string (comma-separated)
    - search: string
    - date_from: ISO date string
    - date_to: ISO date string

  Response:
    {
      "filings": Filing[],
      "total": number,
      "hasMore": boolean
    }

GET /filings/:id
  Response: Filing (with full details)
```

This can be provided by:
1. **FeedSpine** - via `feedspine.api` module
2. **capture-spine** - existing API
3. **py-sec-edgar CLI** - new simple server

---

## Implementation Steps

### Phase 1: Core Components (1-2 days)
1. Create package structure with Vite + React + TypeScript
2. Extract and simplify `useFilingFeed` hook
3. Extract `FilingList` and `FilingRow` components
4. Add basic styling with Tailwind

### Phase 2: Detail Panel (1 day)
1. Create `FilingDetail` with SEC-specific metadata
2. Add document links
3. Add exhibit display
4. Add iframe preview (optional)

### Phase 3: Sidebar & Filters (1 day)
1. Create `FilingSidebar` with form type filters
2. Add company search
3. Add date range picker

### Phase 4: Integration (1 day)
1. Test with FeedSpine API
2. Test with capture-spine API
3. Add Storybook stories
4. Publish to npm as `@py-sec-edgar/feed-ui`

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.0.0",
    "date-fns": "^3.0.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "@storybook/react": "^8.0.0"
  }
}
```

---

## Comparison: capture-spine vs py-sec-edgar UI

| Feature | capture-spine | py-sec-edgar UI |
|---------|--------------|-----------------|
| **Lines of Code** | ~5000+ | ~1000 |
| **State Management** | 1111-line hook | ~200-line hook |
| **Authentication** | Full auth system | None |
| **Knowledge Items** | Notes, prompts, links | None |
| **Time Machine** | Full history | None |
| **Live Streaming** | WebSocket updates | None (polling) |
| **Multi-feed** | HN, RSS, SEC, etc. | SEC only |
| **Highlights** | Keyword highlighting | Basic search |

**Goal**: 80% of the UX with 20% of the complexity.
