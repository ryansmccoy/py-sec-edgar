const API_BASE = '/api'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatCompletionRequest {
  model: string
  messages: ChatMessage[]
  max_tokens?: number
  temperature?: number
}

export interface ChatCompletionResponse {
  id: string
  model: string
  choices: Array<{
    index: number
    message: ChatMessage
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export interface SummarizeRequest {
  content: string
  max_sentences?: number
}

export interface ExtractRequest {
  content: string
  entity_types: string[]
}

export interface ClassifyRequest {
  content: string
  categories: string[]
}

export interface RewriteRequest {
  content: string
  mode: 'clean' | 'format' | 'organize' | 'summarize'
}

export interface InferTitleRequest {
  content: string
  max_words?: number
}

export interface GenerateCommitRequest {
  diff: string
  context?: string
  style?: 'conventional' | 'simple' | 'detailed'
}

export interface HealthResponse {
  status: string
  version?: string
}

export interface Model {
  id: string
  object: string
  owned_by: string
}

export interface ModelsResponse {
  data: Model[]
}

export interface Prompt {
  id: string
  name: string
  slug: string
  description?: string
  template: string
  category?: string
  tags?: string[]
  version?: number
}

export interface PricingInfo {
  model: string
  input_price: number
  output_price: number
}

export interface UsageStats {
  total_requests: number
  total_tokens: number
  total_cost: number
}

// Session types
export interface SessionCreate {
  model: string
  system_prompt?: string
  metadata?: Record<string, unknown>
}

export interface SessionInfo {
  id: string
  model: string
  system_prompt?: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface SessionMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  tokens?: number
  cost?: number
  created_at: string
}

export interface SendMessageRequest {
  content: string
}

export interface SendMessageResponse {
  message: SessionMessage
  response: SessionMessage
}

// API Functions
export const api = {
  // Health
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE}/health`)
    if (!response.ok) throw new Error('Health check failed')
    return response.json()
  },

  // Models
  async getModels(): Promise<ModelsResponse> {
    const response = await fetch(`${API_BASE}/v1/models`)
    if (!response.ok) throw new Error('Failed to fetch models')
    return response.json()
  },

  // Chat Completion
  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const response = await fetch(`${API_BASE}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Chat completion failed')
    return response.json()
  },

  // Summarize
  async summarize(request: SummarizeRequest): Promise<{ summary: string }> {
    const response = await fetch(`${API_BASE}/v1/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Summarization failed')
    return response.json()
  },

  // Extract
  async extract(request: ExtractRequest): Promise<{ entities: unknown[] }> {
    const response = await fetch(`${API_BASE}/v1/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Extraction failed')
    return response.json()
  },

  // Classify
  async classify(request: ClassifyRequest): Promise<{ category: string }> {
    const response = await fetch(`${API_BASE}/v1/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Classification failed')
    return response.json()
  },

  // Rewrite
  async rewrite(request: RewriteRequest): Promise<{ rewritten: string }> {
    const response = await fetch(`${API_BASE}/v1/rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Rewrite failed')
    return response.json()
  },

  // Infer Title
  async inferTitle(request: InferTitleRequest): Promise<{ title: string }> {
    const response = await fetch(`${API_BASE}/v1/infer-title`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Title inference failed')
    return response.json()
  },

  // Generate Commit
  async generateCommit(request: GenerateCommitRequest): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/v1/generate-commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Commit generation failed')
    return response.json()
  },

  // Prompts
  async getPrompts(): Promise<{ prompts: Prompt[] }> {
    const response = await fetch(`${API_BASE}/v1/prompts`)
    if (!response.ok) throw new Error('Failed to fetch prompts')
    return response.json()
  },

  // Pricing
  async getPricing(): Promise<{ models: PricingInfo[] }> {
    const response = await fetch(`${API_BASE}/v1/pricing`)
    if (!response.ok) throw new Error('Failed to fetch pricing')
    return response.json()
  },

  // Usage
  async getUsage(): Promise<UsageStats> {
    const response = await fetch(`${API_BASE}/v1/usage`)
    if (!response.ok) throw new Error('Failed to fetch usage')
    return response.json()
  },

  // Sessions
  async createSession(request: SessionCreate): Promise<SessionInfo> {
    const response = await fetch(`${API_BASE}/v1/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Failed to create session')
    return response.json()
  },

  async listSessions(): Promise<{ sessions: SessionInfo[] }> {
    const response = await fetch(`${API_BASE}/v1/sessions`)
    if (!response.ok) throw new Error('Failed to fetch sessions')
    return response.json()
  },

  async getSession(sessionId: string): Promise<SessionInfo> {
    const response = await fetch(`${API_BASE}/v1/sessions/${sessionId}`)
    if (!response.ok) throw new Error('Failed to fetch session')
    return response.json()
  },

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to delete session')
    return response.json()
  },

  async sendMessage(sessionId: string, request: SendMessageRequest): Promise<SendMessageResponse> {
    const response = await fetch(`${API_BASE}/v1/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error('Failed to send message')
    return response.json()
  },

  async getMessages(sessionId: string): Promise<{ messages: SessionMessage[] }> {
    const response = await fetch(`${API_BASE}/v1/sessions/${sessionId}/messages`)
    if (!response.ok) throw new Error('Failed to fetch messages')
    return response.json()
  },
}
