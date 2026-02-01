import { useQuery } from '@tanstack/react-query'
import { FileCode, Loader2 } from 'lucide-react'
import { api } from '../api'

export default function PromptsPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts,
  })

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <FileCode className="text-blue-600" />
        Prompt Management
      </h1>

      <div className="card">
        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="animate-spin" size={18} />
            <span>Loading prompts...</span>
          </div>
        )}

        {isError && (
          <div className="text-red-600">
            Error loading prompts: {(error as Error).message}
          </div>
        )}

        {data?.prompts && data.prompts.length > 0 ? (
          <div className="space-y-4">
            {data.prompts.map((prompt) => (
              <div
                key={prompt.id}
                className="p-4 border border-gray-200 rounded-lg"
                data-testid="prompt-item"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{prompt.name}</h3>
                    <p className="text-sm text-gray-500">{prompt.slug}</p>
                  </div>
                  <div className="flex gap-2">
                    {prompt.category && (
                      <span className="badge badge-info">{prompt.category}</span>
                    )}
                    {prompt.version && (
                      <span className="badge bg-gray-100 text-gray-600">
                        v{prompt.version}
                      </span>
                    )}
                  </div>
                </div>
                {prompt.description && (
                  <p className="mt-2 text-sm text-gray-600">{prompt.description}</p>
                )}
                {prompt.tags && prompt.tags.length > 0 && (
                  <div className="mt-2 flex gap-1">
                    {prompt.tags.map((tag) => (
                      <span key={tag} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <details className="mt-3">
                  <summary className="text-sm text-blue-600 cursor-pointer">
                    View Template
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-auto">
                    {prompt.template}
                  </pre>
                </details>
              </div>
            ))}
          </div>
        ) : (
          !isLoading && (
            <div className="text-center py-8 text-gray-500">
              <FileCode size={48} className="mx-auto mb-4 opacity-50" />
              <p>No prompts found.</p>
              <p className="text-sm mt-2">
                Create prompts via the API or seed default prompts.
              </p>
            </div>
          )
        )}
      </div>

      {/* API Info */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold mb-3">API Endpoints</h2>
        <div className="space-y-2 text-sm font-mono">
          <p>GET /v1/prompts - List all prompts</p>
          <p>POST /v1/prompts - Create prompt</p>
          <p>GET /v1/prompts/:id - Get prompt</p>
          <p>PUT /v1/prompts/:id - Update prompt</p>
          <p>DELETE /v1/prompts/:id - Delete prompt</p>
          <p>GET /v1/prompts/:id/versions - List versions</p>
        </div>
      </div>
    </div>
  )
}
