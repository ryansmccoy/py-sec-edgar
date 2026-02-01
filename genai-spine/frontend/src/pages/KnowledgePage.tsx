import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, Search, FileText, MessageSquare, Clock, DollarSign } from 'lucide-react'
import { api } from '../api'

type DataView = 'prompts' | 'sessions' | 'usage' | 'executions'

export default function KnowledgePage() {
  const [view, setView] = useState<DataView>('prompts')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch data based on view
  const { data: promptsData } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts,
    enabled: view === 'prompts',
  })

  const { data: sessionsData } = useQuery({
    queryKey: ['sessions'],
    queryFn: api.listSessions,
    enabled: view === 'sessions',
  })

  const { data: usageData } = useQuery({
    queryKey: ['usage'],
    queryFn: api.getUsage,
    enabled: view === 'usage',
  })

  const views: { id: DataView; label: string; icon: typeof Database }[] = [
    { id: 'prompts', label: 'Prompts', icon: FileText },
    { id: 'sessions', label: 'Sessions', icon: MessageSquare },
    { id: 'usage', label: 'Usage Stats', icon: DollarSign },
    { id: 'executions', label: 'Executions', icon: Clock },
  ]

  // Filter data based on search
  const filteredPrompts = promptsData?.prompts.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredSessions = sessionsData?.sessions.filter((s) =>
    s.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white border border-gray-200 rounded-lg mb-4">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Database size={24} className="text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">Knowledge Explorer</h1>
              <p className="text-gray-600 text-sm">
                Browse and search GenAI data: prompts, sessions, usage, and execution history
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search across all data..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* View Tabs */}
        <div className="border-t border-gray-200 flex">
          {views.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setView(id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 transition-colors ${
                view === id
                  ? 'bg-blue-50 border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={18} />
              <span className="font-medium">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Data Display */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg p-6 overflow-auto">
        {view === 'prompts' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold">
                Prompts ({filteredPrompts?.length || 0})
              </h2>
              <p className="text-sm text-gray-600">
                Domain-agnostic prompt templates for various AI tasks
              </p>
            </div>

            {filteredPrompts && filteredPrompts.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredPrompts.map((prompt) => (
                  <div
                    key={prompt.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold">{prompt.name}</h3>
                      {prompt.version && (
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                          v{prompt.version}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mb-2">
                      <code className="bg-gray-100 px-1 rounded">{prompt.slug}</code>
                    </p>
                    {prompt.description && (
                      <p className="text-sm text-gray-600 mb-3">{prompt.description}</p>
                    )}
                    {prompt.category && (
                      <span className="inline-block text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        {prompt.category}
                      </span>
                    )}
                    {prompt.tags && prompt.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {prompt.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">No prompts found</div>
            )}
          </div>
        )}

        {view === 'sessions' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold">
                Chat Sessions ({filteredSessions?.length || 0})
              </h2>
              <p className="text-sm text-gray-600">
                Multi-turn conversation history across all models
              </p>
            </div>

            {filteredSessions && filteredSessions.length > 0 ? (
              <div className="space-y-2">
                {filteredSessions.map((session) => (
                  <div
                    key={session.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <MessageSquare size={18} className="text-gray-400" />
                        <div>
                          <div className="font-medium">{session.model}</div>
                          <div className="text-xs text-gray-500">
                            ID: {session.id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(session.created_at).toLocaleString()}
                      </div>
                    </div>
                    {session.system_prompt && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                        <span className="text-gray-600">System: </span>
                        {session.system_prompt}
                      </div>
                    )}
                    {Object.keys(session.metadata).length > 0 && (
                      <div className="mt-2 text-xs text-gray-500">
                        Metadata: {JSON.stringify(session.metadata)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">No sessions found</div>
            )}
          </div>
        )}

        {view === 'usage' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold">Usage Statistics</h2>
              <p className="text-sm text-gray-600">
                Aggregate metrics across all GenAI operations
              </p>
            </div>

            {usageData ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
                  <div className="text-blue-600 text-sm font-medium mb-1">Total Requests</div>
                  <div className="text-3xl font-bold text-blue-900">
                    {usageData.total_requests.toLocaleString()}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-6">
                  <div className="text-green-600 text-sm font-medium mb-1">Total Tokens</div>
                  <div className="text-3xl font-bold text-green-900">
                    {usageData.total_tokens.toLocaleString()}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-6">
                  <div className="text-purple-600 text-sm font-medium mb-1">Total Cost</div>
                  <div className="text-3xl font-bold text-purple-900">
                    ${usageData.total_cost.toFixed(4)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">Loading usage data...</div>
            )}
          </div>
        )}

        {view === 'executions' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold">Execution History</h2>
              <p className="text-sm text-gray-600">
                Detailed log of all LLM requests (coming soon)
              </p>
            </div>

            <div className="text-center py-12 text-gray-400">
              <Clock size={48} className="mx-auto mb-3 opacity-50" />
              <p className="font-medium">Execution History Coming Soon</p>
              <p className="text-sm mt-2">
                This view will show detailed logs of all LLM executions including timing, tokens,
                cost, and success/failure status.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Database size={20} className="text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-1">Domain-Agnostic Design</p>
            <p className="text-blue-700">
              This UI displays generic GenAI data without domain-specific logic. You can extend it
              to view capture-spine copilot chats, entityspine extractions, or feedspine
              enrichments by connecting to their databases and presenting the data through this
              generic lens.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
