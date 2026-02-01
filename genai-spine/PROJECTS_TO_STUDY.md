# Projects to Study for GenAI Spine Features

**Focus Areas:** Prompt Management, Versioning UI, Multi-user Support
**Goal:** Learn from best implementations to improve GenAI Spine

---

## 🎯 Top 5 Projects to Clone & Study

### 1. **Langfuse** - Best Prompt Versioning & Management ⭐⭐⭐⭐⭐

**Why Study This:**
- Industry-leading prompt versioning system
- Beautiful UI for prompt management
- Production-grade prompt testing/evaluation
- Multi-user with teams and projects

**Clone & Run:**
```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
# Visit http://localhost:3000
```

**Key Files to Study:**

1. **Prompt Versioning Logic:**
   - `packages/shared/src/server/repositories/prompts.ts` - Database layer
   - `web/src/features/prompts/server/utils/validation.ts` - Validation
   - `web/src/server/api/routers/prompts.ts` - API endpoints

2. **Prompt UI Components:**
   - `web/src/features/prompts/components/NewPromptForm.tsx` - Create prompt form
   - `web/src/features/prompts/components/PromptHistoryNode.tsx` - Version history UI
   - `web/src/components/layouts/prompt-detail.tsx` - Detail view with tabs
   - `web/src/features/prompts/components/prompt-detail.tsx` - Version comparison

3. **Multi-user/Teams:**
   - `web/src/features/rbac/` - Role-based access control
   - `web/src/server/api/routers/projects.ts` - Project/workspace isolation
   - `web/src/features/auth/` - Authentication flows

**What to Copy:**
- ✅ Prompt version numbering (v1, v2, v3...)
- ✅ Side-by-side version comparison UI
- ✅ Prompt testing interface with example inputs
- ✅ "Promote to production" workflow
- ✅ Prompt usage analytics (which versions are used most)
- ✅ Team/project structure for isolation

**Demo Features to Test:**
1. Create a prompt template
2. Edit it → creates new version automatically
3. Compare v1 vs v2 side-by-side
4. Test prompt with different inputs
5. See which version is used in production
6. View analytics (usage per version)

---

### 2. **Dify** - Best Prompt IDE & Workflow Builder ⭐⭐⭐⭐⭐

**Why Study This:**
- Full-featured "Prompt IDE" with testing
- Visual prompt designer
- Variable substitution with preview
- Multi-user with workspaces

**Clone & Run:**
```bash
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker compose up
# Visit http://localhost:3000
```

**Key Files to Study:**

1. **Prompt Editor (IDE):**
   - `web/app/components/app/configuration/config-prompt/` - Prompt editor UI
   - `web/app/components/base/prompt-editor/` - Rich text editor for prompts
   - `web/app/components/app/configuration/debug/` - Testing interface

2. **Variable System:**
   - `api/core/prompt/prompt_template.py` - Template variable parsing
   - `web/app/components/app/configuration/config-var/` - Variable configuration UI
   - `api/core/prompt/advanced_prompt_transform.py` - Jinja2 template support

3. **Prompt Versioning:**
   - `api/models/model.py` - AppModelConfig (stores prompt versions)
   - `web/app/components/app/overview/appCard.tsx` - App version management

4. **Multi-workspace:**
   - `api/models/account.py` - Account and workspace models
   - `api/controllers/console/workspace/` - Workspace management
   - `web/app/(commonLayout)/workspace/` - Workspace UI

**What to Copy:**
- ✅ Rich text editor with syntax highlighting
- ✅ Variable picker UI (`{{variable_name}}` autocomplete)
- ✅ Live preview with variable substitution
- ✅ Testing panel (right side of editor)
- ✅ Workspace switcher in header
- ✅ Prompt history with restore capability

**Demo Features to Test:**
1. Create an app with prompts
2. Add variables like `{{user_input}}`, `{{context}}`
3. Use the testing panel with real values
4. See live preview of final prompt
5. Create multiple workspaces
6. Share app between workspace members

---

### 3. **PromptFlow** (Microsoft) - Best Prompt Testing & Evaluation ⭐⭐⭐⭐

**Why Study This:**
- Systematic prompt testing framework
- Variant comparison (A/B testing prompts)
- Evaluation metrics and scoring
- Professional IDE integration

**Clone & Run:**
```bash
git clone https://github.com/microsoft/promptflow.git
cd promptflow
pip install promptflow promptflow-tools
pf flow serve --source examples/flows/chat/chat-basic --port 8080
# Or use VS Code extension: search "Prompt flow" in extensions
```

**Key Files to Study:**

1. **Prompt Variants:**
   - `src/promptflow/promptflow/_core/flow.py` - Flow execution
   - `examples/flows/chat/chat-basic/` - Example with variants
   - Look for `.variant_*` files in examples

2. **Evaluation Framework:**
   - `src/promptflow-evals/promptflow/evals/evaluators/` - Built-in evaluators
   - `examples/flows/evaluation/` - Evaluation flow examples

3. **Testing UI:**
   - VS Code extension source (TypeScript)
   - `src/promptflow-devkit/promptflow/_sdk/operations/` - Test execution

**What to Copy:**
- ✅ Variant system (Prompt A vs Prompt B)
- ✅ Batch testing with datasets
- ✅ Evaluation metrics (relevance, coherence, groundedness)
- ✅ Results comparison table
- ✅ Export test results to CSV

**Demo Features to Test:**
1. Install VS Code extension
2. Open a flow with prompt variants
3. Run batch test with test dataset
4. Compare results between variants
5. View evaluation metrics
6. Export results for analysis

---

### 4. **LibreChat** - Best Multi-user Auth & UX ⭐⭐⭐⭐

**Why Study This:**
- Production-ready authentication system
- Clean user management UI
- Preset prompts (simpler than versioning)
- Beautiful chat interface

**Clone & Run:**
```bash
git clone https://github.com/danny-avila/LibreChat.git
cd LibreChat
cp .env.example .env
docker compose up
# Visit http://localhost:3080
```

**Key Files to Study:**

1. **Authentication:**
   - `api/server/routes/auth.js` - Auth routes
   - `api/strategies/` - Passport.js strategies (local, OAuth)
   - `client/src/components/Auth/` - Login/register UI

2. **User Management:**
   - `api/models/User.js` - User model
   - `api/server/controllers/UserController.js` - User CRUD
   - `client/src/components/Nav/Settings/` - User settings UI

3. **Preset System (Simple Prompts):**
   - `api/models/Preset.js` - Preset model
   - `api/server/services/Endpoints/` - Preset handling per provider
   - `client/src/components/Endpoints/SaveAsPresetDialog.tsx` - Save preset UI
   - `client/src/components/Endpoints/PresetItems.tsx` - Preset list

4. **Clean UI Patterns:**
   - `client/src/components/Chat/Messages/` - Message components
   - `client/src/components/ui/` - Reusable UI components (using shadcn/ui)
   - `client/src/hooks/` - Custom React hooks

**What to Copy:**
- ✅ JWT authentication with refresh tokens
- ✅ OAuth integration (Google, GitHub)
- ✅ User registration flow with email verification
- ✅ User settings panel
- ✅ Preset (template) system - simple but effective
- ✅ shadcn/ui component library for beautiful UI

**Demo Features to Test:**
1. Register new account
2. Log in with credentials
3. Create a conversation preset (system message + settings)
4. Save preset for reuse
5. Share preset with team (if feature exists)
6. Test user settings (profile, API keys)

---

### 5. **LiteLLM Proxy** - Best API Key Management ⭐⭐⭐⭐

**Why Study This:**
- Production-grade API key system
- Per-key budgets and rate limits
- Usage tracking per key
- Admin UI for key management

**Clone & Run:**
```bash
git clone https://github.com/BerriAI/litellm.git
cd litellm
pip install litellm[proxy]
litellm --config litellm_config.yaml
# Visit http://localhost:4000 (UI)
```

**Key Files to Study:**

1. **API Key Management:**
   - `litellm/proxy/auth/` - Authentication middleware
   - `litellm/proxy/management_endpoints/key_management_endpoints.py` - Key CRUD
   - `litellm/proxy/_types.py` - Key models (LiteLLM_VerificationToken)

2. **Budget & Rate Limiting:**
   - `litellm/proxy/utils.py` - Budget checking logic
   - `litellm/router.py` - Rate limit implementation
   - `litellm/proxy/spend_tracking/` - Usage tracking

3. **Admin UI:**
   - `ui/litellm-dashboard/` - React admin dashboard
   - Look for key management components

**What to Copy:**
- ✅ API key generation (prefixed keys like `sk-...`)
- ✅ Per-key budgets (max spend per month)
- ✅ Per-key rate limits (requests per minute)
- ✅ Key expiration dates
- ✅ Usage dashboard per key
- ✅ Key revocation/regeneration

**Demo Features to Test:**
1. Start proxy server
2. Create API key via UI
3. Set budget limit ($10/month)
4. Set rate limit (10 req/min)
5. Test key with requests
6. View usage dashboard
7. Revoke key and verify it stops working

---

## 🎨 UI Component Libraries to Study

### 1. **shadcn/ui** (Used by LibreChat)
- Beautiful, accessible React components
- Built on Radix UI primitives
- Copy components directly into your project
- **Study:** https://ui.shadcn.com/

**Components to Add to GenAI Spine:**
- Dialog (for modals)
- Dropdown Menu (for actions)
- Tabs (for KnowledgePage)
- Toast (for notifications)
- Form components (Input, Select, Textarea)

### 2. **Headless UI** (Tailwind official)
- Unstyled, accessible components
- Works perfectly with Tailwind
- **Study:** https://headlessui.com/

### 3. **Radix UI** (Primitives)
- Low-level UI primitives
- Maximum flexibility
- **Study:** https://www.radix-ui.com/

---

## 📚 Code Patterns to Extract

### Pattern 1: Prompt Versioning Database Schema

**From Langfuse:**
```typescript
// Simplified version
interface Prompt {
  id: string;
  name: string;
  projectId: string;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

interface PromptVersion {
  id: string;
  promptId: string; // FK to Prompt
  version: number; // Auto-incremented: 1, 2, 3...
  prompt: string; // The actual prompt text
  config: Record<string, any>; // Model, temperature, etc.
  labels: string[]; // e.g., ["production", "testing"]
  createdBy: string;
  createdAt: Date;
}
```

**Adapt for GenAI Spine (File-based):**
```
data/prompts/
  my-prompt/
    metadata.json  # Prompt metadata
    v1.json        # Version 1
    v2.json        # Version 2
    v3.json        # Version 3 (latest)
    current -> v2.json  # Symlink to production version
```

### Pattern 2: Variable Substitution

**From Dify:**
```python
# Simple Jinja2-like template
template = "Summarize this text: {{text}}\n\nIn {{language}} language."
variables = {"text": "Hello world", "language": "Spanish"}

# Parse and substitute
import re
def substitute_variables(template: str, variables: dict) -> str:
    pattern = r'\{\{(\w+)\}\}'

    def replace(match):
        var_name = match.group(1)
        return str(variables.get(var_name, f"{{{{var_name}}}}"))

    return re.sub(pattern, replace, template)
```

**GenAI Spine Implementation:**
```python
# src/genai_spine/prompts/template.py
from typing import Any
import re

class PromptTemplate:
    def __init__(self, template: str, variables: list[str]):
        self.template = template
        self.variables = variables

    def render(self, **kwargs) -> str:
        """Render template with variables."""
        result = self.template
        for var, value in kwargs.items():
            if var not in self.variables:
                raise ValueError(f"Unknown variable: {var}")
            result = result.replace(f"{{{{{var}}}}}", str(value))
        return result

    def get_variables(self) -> list[str]:
        """Extract variables from template."""
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, self.template)))
```

### Pattern 3: Multi-user with Workspaces

**From Dify:**
```python
# Simplified models
class User:
    id: str
    email: str
    name: str
    hashed_password: str

class Workspace:
    id: str
    name: str
    created_by: str  # User ID

class WorkspaceMember:
    workspace_id: str
    user_id: str
    role: str  # "owner", "admin", "member", "viewer"
```

**GenAI Spine File Structure:**
```
data/
  users/
    user-123/
      profile.json
      api_keys.json
  workspaces/
    workspace-abc/
      metadata.json  # name, owner, created_at
      members.json   # user_id -> role mapping
      prompts/       # workspace-specific prompts
      sessions/      # workspace-specific sessions
      usage/         # workspace-specific usage
```

### Pattern 4: API Key Authentication

**From LiteLLM:**
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Verify API key and return user/workspace info."""
    api_key = credentials.credentials

    # Check format
    if not api_key.startswith("gai_"):  # GenAI Spine prefix
        raise HTTPException(401, "Invalid API key format")

    # Look up in database/file
    key_data = load_api_key(api_key)
    if not key_data:
        raise HTTPException(401, "Invalid API key")

    # Check expiration
    if key_data["expires_at"] < datetime.now():
        raise HTTPException(401, "API key expired")

    # Check budget
    if key_data["usage"] >= key_data["budget_limit"]:
        raise HTTPException(429, "Budget limit exceeded")

    return {
        "user_id": key_data["user_id"],
        "workspace_id": key_data["workspace_id"],
        "key_id": key_data["id"]
    }
```

---

## 🔧 Specific Features to Clone

### Feature 1: Prompt Version Comparison UI

**Study:** Langfuse's `PromptHistoryNode.tsx`

**Implement in GenAI Spine:**
```tsx
// frontend/src/components/PromptVersionComparison.tsx
interface Props {
  promptSlug: string;
  versionA: number;
  versionB: number;
}

export const PromptVersionComparison = ({ promptSlug, versionA, versionB }: Props) => {
  const { data: versions } = useQuery(['prompt-versions', promptSlug]);

  const v1 = versions?.find(v => v.version === versionA);
  const v2 = versions?.find(v => v.version === versionB);

  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <h3>Version {versionA}</h3>
        <pre className="bg-gray-100 p-4 rounded">{v1?.template}</pre>
        <div className="text-sm text-gray-600">
          Created: {v1?.created_at}
          Model: {v1?.model}
        </div>
      </div>
      <div>
        <h3>Version {versionB}</h3>
        <pre className="bg-gray-100 p-4 rounded">{v2?.template}</pre>
        <div className="text-sm text-gray-600">
          Created: {v2?.created_at}
          Model: {v2?.model}
        </div>
      </div>
      {/* Show diff highlighting */}
      <DiffView oldText={v1?.template} newText={v2?.template} />
    </div>
  );
};
```

### Feature 2: Variable Input Form

**Study:** Dify's config-var component

**Implement in GenAI Spine:**
```tsx
// frontend/src/components/VariableInputs.tsx
interface Variable {
  name: string;
  type: 'string' | 'number' | 'select';
  required: boolean;
  default?: any;
  options?: string[]; // for select type
}

export const VariableInputs = ({
  variables,
  values,
  onChange
}: {
  variables: Variable[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
}) => {
  return (
    <div className="space-y-4">
      {variables.map(variable => (
        <div key={variable.name}>
          <label className="block text-sm font-medium mb-1">
            {variable.name}
            {variable.required && <span className="text-red-500">*</span>}
          </label>

          {variable.type === 'select' ? (
            <select
              value={values[variable.name] || ''}
              onChange={e => onChange({...values, [variable.name]: e.target.value})}
              className="w-full border rounded px-3 py-2"
            >
              {variable.options?.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <input
              type={variable.type === 'number' ? 'number' : 'text'}
              value={values[variable.name] || variable.default || ''}
              onChange={e => onChange({...values, [variable.name]: e.target.value})}
              className="w-full border rounded px-3 py-2"
            />
          )}
        </div>
      ))}
    </div>
  );
};
```

### Feature 3: Workspace Switcher

**Study:** Dify's workspace switcher in header

**Implement in GenAI Spine:**
```tsx
// frontend/src/components/WorkspaceSwitcher.tsx
export const WorkspaceSwitcher = () => {
  const { data: workspaces } = useQuery(['workspaces']);
  const { data: currentWorkspace } = useQuery(['current-workspace']);

  return (
    <Dropdown>
      <DropdownTrigger>
        <button className="flex items-center gap-2">
          <Building2 size={20} />
          <span>{currentWorkspace?.name}</span>
          <ChevronDown size={16} />
        </button>
      </DropdownTrigger>

      <DropdownContent>
        {workspaces?.map(ws => (
          <DropdownItem
            key={ws.id}
            onClick={() => switchWorkspace(ws.id)}
          >
            {ws.name}
            {ws.id === currentWorkspace?.id && <Check size={16} />}
          </DropdownItem>
        ))}
        <DropdownSeparator />
        <DropdownItem onClick={() => createWorkspace()}>
          <Plus size={16} /> New Workspace
        </DropdownItem>
      </DropdownContent>
    </Dropdown>
  );
};
```

---

## ✅ Action Plan - What to Do This Weekend

### Day 1: Clone & Explore (Saturday)

**Morning (3 hours):**
```bash
# Clone top 3 projects
git clone https://github.com/langfuse/langfuse.git
git clone https://github.com/langgenius/dify.git
git clone https://github.com/danny-avila/LibreChat.git

# Start each and explore
cd langfuse && docker compose up -d
# Test prompt versioning for 30 min

cd ../dify/docker && docker compose up -d
# Test prompt IDE for 30 min

cd ../../LibreChat && docker compose up -d
# Test presets and auth for 30 min
```

**Afternoon (3 hours):**
- Take screenshots of best UI patterns
- Document workflows (how versioning works, etc.)
- Make notes on file structure
- Identify components to copy

### Day 2: Code Study (Sunday)

**Morning (3 hours):**
- Read Langfuse prompt versioning code
- Read Dify variable substitution code
- Read LibreChat auth code
- Copy patterns into notes

**Afternoon (2 hours):**
- Design GenAI Spine improvements:
  - Prompt versioning schema
  - Variable system
  - Multi-user structure
- Create implementation plan

### Day 3: Implementation (Monday)

**Start with Quick Wins:**
1. Add prompt versioning to existing prompts (2 hours)
2. Add variable substitution to templates (2 hours)
3. Create version comparison UI (3 hours)

---

## 📖 Recommended Reading Order

1. **Start:** Clone Langfuse → Test prompt versioning → Read code
2. **Then:** Clone Dify → Test prompt IDE → Read variable system
3. **Then:** Clone LibreChat → Test auth → Read user management
4. **Optional:** Clone LiteLLM → Test API keys → Read budget tracking
5. **Optional:** Install PromptFlow VS Code extension → Test variants

**Total Time:** ~8-10 hours to clone, test, and understand all patterns

---

## 🎯 What You'll Learn

By studying these 5 projects, you'll understand:

✅ **Prompt Versioning** - How to version prompts properly (Langfuse)
✅ **Prompt IDE** - How to build rich editing experience (Dify)
✅ **Testing Framework** - How to test prompts systematically (PromptFlow)
✅ **Multi-user** - How to add authentication and workspaces (LibreChat)
✅ **API Keys** - How to manage API keys and budgets (LiteLLM)
✅ **UI Patterns** - Beautiful component patterns (all projects)

**Result:** GenAI Spine will be on par with or better than competitors in these areas.

---

Ready to start? Clone Langfuse first - it has the best prompt versioning you can learn from! 🚀
