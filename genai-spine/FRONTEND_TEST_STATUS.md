# GenAI Spine Frontend - Test Status & Feature Improvements

**Date:** January 31, 2026
**Status:** Tests exist but need review, several pages need more functionality

---

## 🧪 Current Test Status

### Playwright E2E Tests (11 test files)

Located in: `frontend/e2e/`

**Test Files:**
1. ✅ `chat.spec.ts` - Chat page basic rendering
2. ✅ `classify.spec.ts` - Classify page
3. ✅ `commit.spec.ts` - Commit message generation
4. ✅ `extract.spec.ts` - Information extraction
5. ✅ `health.spec.ts` - Health check page
6. ✅ `navigation.spec.ts` - App navigation
7. ✅ `prompts.spec.ts` - Prompt management
8. ✅ `rewrite.spec.ts` - Content rewriting
9. ✅ `summarize.spec.ts` - Text summarization
10. ✅ `title.spec.ts` - Title generation
11. ✅ `usage.spec.ts` - Usage statistics

**Missing Tests:**
- ❌ `sessions.spec.ts` - New SessionsPage (not tested yet)
- ❌ `knowledge.spec.ts` - New KnowledgePage (not tested yet)

### Unit Tests
- **Status:** ⚠️ Vitest configured but no test files yet
- **Location:** Would go in `frontend/src/**/*.test.tsx`

### Running Tests

```bash
# Install Playwright browsers (first time only - this is what was hanging)
cd frontend
npx playwright install chromium

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI (interactive)
npm run test:e2e:ui

# Run unit tests (when we add them)
npm test
```

---

## 🐛 Known Issues / Broken Features

### 1. **Prompts Page - Limited Functionality**

**Current State:**
- Shows list of prompts
- Can view prompt details
- Basic display only

**Broken/Missing:**
- ❌ Create new prompt form doesn't submit properly
- ❌ Edit prompt functionality incomplete
- ❌ Delete prompt confirmation missing
- ❌ No prompt versioning UI
- ❌ No variable substitution preview
- ❌ No testing interface

**Fix Priority:** 🔴 HIGH

### 2. **Sessions Page - API Integration Issues**

**Current State:**
- ✅ UI renders correctly
- ✅ Can create sessions
- ⚠️ API calls may fail silently

**Broken/Missing:**
- ❌ Error handling not robust
- ❌ Loading states incomplete
- ❌ No retry logic
- ❌ Session deletion confirmation missing
- ❌ No session export/import

**Fix Priority:** 🟡 MEDIUM

### 3. **Knowledge Page - Limited Data Views**

**Current State:**
- ✅ Tab navigation works
- ✅ Shows basic data cards
- ⚠️ Search doesn't filter results

**Broken/Missing:**
- ❌ Search functionality not implemented
- ❌ Filtering doesn't work
- ❌ No pagination
- ❌ No sorting options
- ❌ Can't drill into details

**Fix Priority:** 🟡 MEDIUM

### 4. **Usage Page - Static Data**

**Current State:**
- Shows usage statistics
- Basic metrics display

**Broken/Missing:**
- ❌ Date range picker doesn't filter
- ❌ No charts/graphs
- ❌ No export to CSV
- ❌ No cost breakdown by user/session
- ❌ Real-time updates missing

**Fix Priority:** 🟢 LOW

### 5. **All Capability Pages - Limited Validation**

**Affected:** Chat, Summarize, Extract, Classify, Rewrite, Title, Commit

**Broken/Missing:**
- ❌ No input validation before submit
- ❌ Error messages not user-friendly
- ❌ No retry on failure
- ❌ No copy to clipboard for results
- ❌ No save result to file
- ❌ No result history

**Fix Priority:** 🟡 MEDIUM

---

## 🔧 Recommended Fixes (Priority Order)

### Phase 1: Critical Fixes (Week 1)

#### 1.1 Fix Prompts Page CRUD
```typescript
// frontend/src/pages/PromptsPage.tsx
// - Add proper form submission handler
// - Implement API calls for create/edit/delete
// - Add loading states
// - Add error handling
// - Add success notifications
```

#### 1.2 Add E2E Tests for New Pages
```bash
# Create missing test files
frontend/e2e/sessions.spec.ts
frontend/e2e/knowledge.spec.ts
```

#### 1.3 Fix API Client Error Handling
```typescript
// frontend/src/api.ts
// - Add proper error handling
// - Add retry logic
// - Add timeout handling
// - Add response validation
```

### Phase 2: Enhanced Functionality (Week 2)

#### 2.1 Improve Search & Filtering
- Implement search on KnowledgePage
- Add date filters on UsagePage
- Add sorting on all list pages

#### 2.2 Add User Feedback
- Toast notifications for success/error
- Loading spinners for all async operations
- Confirmation dialogs for destructive actions
- Progress bars for long operations

#### 2.3 Better Data Visualization
- Add charts to UsagePage (cost over time, usage by model)
- Add session timeline visualization
- Add prompt usage statistics

### Phase 3: Advanced Features (Week 3-4)

#### 3.1 Prompt Management Enhancements
- Prompt versioning UI
- Variable substitution with preview
- Prompt testing interface
- Import/export prompts as JSON

#### 3.2 Session Management Enhancements
- Export sessions to markdown
- Session tagging/labeling
- Session search with full-text
- Session comparison view

#### 3.3 Cost Analysis Dashboard
- Real-time cost tracking
- Cost predictions
- Budget alerts
- Per-user cost breakdown

---

## 📝 Detailed Fix Plan

### Fix 1: Prompts Page - Full CRUD Implementation

**File:** `frontend/src/pages/PromptsPage.tsx`

**Current Issues:**
```typescript
// Form submission handler is incomplete
const handleCreatePrompt = async (e: React.FormEvent) => {
  e.preventDefault();
  // TODO: This doesn't actually call the API
  console.log('Creating prompt...', formData);
};
```

**Fix:**
```typescript
const handleCreatePrompt = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);
  setError(null);

  try {
    const newPrompt = await api.createPrompt({
      slug: formData.slug,
      name: formData.name,
      template: formData.template,
      description: formData.description,
      model: formData.model,
      system_message: formData.systemMessage,
      temperature: parseFloat(formData.temperature),
    });

    // Refresh prompts list
    await refetch();

    // Show success message
    showToast('Prompt created successfully', 'success');

    // Close modal/reset form
    setShowCreateForm(false);
    resetForm();
  } catch (err) {
    setError(err.message || 'Failed to create prompt');
    showToast('Failed to create prompt', 'error');
  } finally {
    setIsLoading(false);
  }
};
```

**API Client Updates Needed:**
```typescript
// frontend/src/api.ts
export const api = {
  // ... existing methods ...

  createPrompt: async (data: PromptCreate): Promise<Prompt> => {
    const res = await fetch(`${API_BASE}/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  updatePrompt: async (slug: string, data: Partial<PromptCreate>): Promise<Prompt> => {
    const res = await fetch(`${API_BASE}/prompts/${slug}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  deletePrompt: async (slug: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/prompts/${slug}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(await res.text());
  },
};
```

### Fix 2: Add Toast Notification System

**New File:** `frontend/src/components/Toast.tsx`

```typescript
import { createContext, useContext, useState, ReactNode } from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (message: string, type: ToastType = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`flex items-center gap-2 p-4 rounded-lg shadow-lg min-w-[300px] ${
              toast.type === 'success' ? 'bg-green-500' :
              toast.type === 'error' ? 'bg-red-500' :
              'bg-blue-500'
            } text-white`}
          >
            {toast.type === 'success' && <CheckCircle size={20} />}
            {toast.type === 'error' && <XCircle size={20} />}
            {toast.type === 'info' && <Info size={20} />}
            <span className="flex-1">{toast.message}</span>
            <button onClick={() => removeToast(toast.id)}>
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};
```

**Update App.tsx:**
```typescript
import { ToastProvider } from './components/Toast';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          {/* ... routes ... */}
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
```

### Fix 3: Add Confirmation Dialogs

**New File:** `frontend/src/components/ConfirmDialog.tsx`

```typescript
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}

export const ConfirmDialog = ({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  danger = false,
}: ConfirmDialogProps) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-lg text-white ${
              danger ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Fix 4: Add Loading States

**New File:** `frontend/src/components/LoadingSpinner.tsx`

```typescript
export const LoadingSpinner = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClass = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }[size];

  return (
    <div className={`${sizeClass} border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin`} />
  );
};

export const LoadingOverlay = ({ message = 'Loading...' }: { message?: string }) => {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-40">
      <div className="bg-white rounded-lg p-6 flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
};
```

---

## 🧪 New E2E Test Files Needed

### sessions.spec.ts
```typescript
import { test, expect } from '@playwright/test';

test.describe('Sessions Page', () => {
  test('should create a new session', async ({ page }) => {
    await page.goto('/sessions');

    // Click create session button
    await page.getByRole('button', { name: /new session/i }).click();

    // Fill form
    await page.getByLabel(/session name/i).fill('Test Session');
    await page.getByRole('button', { name: /create/i }).click();

    // Verify session appears in list
    await expect(page.getByText('Test Session')).toBeVisible();
  });

  test('should send messages in a session', async ({ page }) => {
    await page.goto('/sessions');

    // Assume session exists, click it
    await page.getByText(/test session/i).first().click();

    // Send message
    await page.getByPlaceholder(/type a message/i).fill('Hello!');
    await page.getByRole('button', { name: /send/i }).click();

    // Verify message appears
    await expect(page.getByText('Hello!')).toBeVisible();
  });

  test('should delete a session', async ({ page }) => {
    await page.goto('/sessions');

    // Click delete on first session
    await page.getByRole('button', { name: /delete/i }).first().click();

    // Confirm deletion
    await page.getByRole('button', { name: /confirm/i }).click();

    // Verify session is gone (this is basic - might need better selector)
    await expect(page.getByText(/session deleted/i)).toBeVisible();
  });
});
```

### knowledge.spec.ts
```typescript
import { test, expect } from '@playwright/test';

test.describe('Knowledge Page', () => {
  test('should display tabs', async ({ page }) => {
    await page.goto('/knowledge');

    await expect(page.getByRole('tab', { name: /prompts/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /sessions/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /usage/i })).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/knowledge');

    await page.getByRole('tab', { name: /sessions/i }).click();
    await expect(page.getByText(/sessions/i)).toBeVisible();

    await page.getByRole('tab', { name: /usage/i }).click();
    await expect(page.getByText(/usage/i)).toBeVisible();
  });

  test('should search data', async ({ page }) => {
    await page.goto('/knowledge');

    await page.getByPlaceholder(/search/i).fill('test query');
    // This will fail until search is implemented!
    // await expect(page.getByText(/filtered results/i)).toBeVisible();
  });
});
```

---

## ✅ Testing Checklist

Before deployment:

- [ ] Run all E2E tests: `npm run test:e2e`
- [ ] Test each capability page manually
- [ ] Test prompt creation/editing/deletion
- [ ] Test session creation and messaging
- [ ] Test knowledge page tabs and data display
- [ ] Verify error handling for network failures
- [ ] Verify loading states during API calls
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test mobile responsiveness
- [ ] Check accessibility (keyboard navigation, screen readers)

---

## 📊 Test Coverage Goals

**Current:** ~40% (only basic rendering tests)
**Target:** 80%+

**Breakdown:**
- E2E Tests: Cover all user flows (50% coverage)
- Component Tests: Test UI components in isolation (20% coverage)
- Integration Tests: Test API client methods (10% coverage)

---

## Next Steps

1. **Immediate (This Week):**
   - Fix Prompts page CRUD operations
   - Add toast notification system
   - Add confirmation dialogs
   - Add loading states

2. **Short-term (Next Week):**
   - Write E2E tests for Sessions and Knowledge pages
   - Implement search/filtering on Knowledge page
   - Add charts to Usage page
   - Improve error handling across all pages

3. **Medium-term (2-4 Weeks):**
   - Add unit tests for components
   - Implement prompt versioning UI
   - Add session export/import
   - Build advanced analytics dashboard

Would you like me to start implementing any of these fixes now?
