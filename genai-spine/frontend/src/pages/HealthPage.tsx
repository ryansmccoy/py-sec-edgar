import { useQuery } from '@tanstack/react-query'
import { Activity, CheckCircle, XCircle, Server, Database, Cpu } from 'lucide-react'
import { api } from '../api'

export default function HealthPage() {
  const { data: health, isLoading, isError, error } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  })

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
  })

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Activity className="text-blue-600" />
        Health & Service Discovery
      </h1>

      {/* Service Status */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Service Status</h2>

        <div className="flex items-center gap-4">
          {isLoading ? (
            <div className="flex items-center gap-2 text-yellow-600">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-yellow-600 border-t-transparent" />
              <span>Checking...</span>
            </div>
          ) : isError ? (
            <div className="flex items-center gap-2 text-red-600">
              <XCircle />
              <span>Offline - {(error as Error)?.message || 'Connection failed'}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle />
              <span>Online - {health?.status || 'Healthy'}</span>
            </div>
          )}
        </div>

        {health && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
              <Server className="text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Version</p>
                <p className="font-medium">{health.version || '0.1.0'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
              <Database className="text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Storage</p>
                <p className="font-medium">SQLite</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
              <Cpu className="text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Provider</p>
                <p className="font-medium">Ollama</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Available Models */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Available Models</h2>

        {models?.data && models.data.length > 0 ? (
          <div className="space-y-2">
            {models.data.map((model) => (
              <div
                key={model.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
              >
                <span className="font-medium">{model.id}</span>
                <span className="badge badge-info">{model.owned_by}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No models available. Pull a model with:</p>
        )}

        <div className="mt-4 p-3 bg-gray-100 rounded-md">
          <code className="text-sm">
            docker compose exec ollama ollama pull llama3.2:latest
          </code>
        </div>
      </div>

      {/* API Endpoints */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold mb-4">API Endpoints</h2>
        <div className="space-y-2 text-sm">
          <p>
            <a href="/api/docs" target="_blank" className="text-blue-600 hover:underline">
              Swagger UI →
            </a>
          </p>
          <p>
            <a href="/api/redoc" target="_blank" className="text-blue-600 hover:underline">
              ReDoc →
            </a>
          </p>
          <p>
            <a href="/api/openapi.json" target="_blank" className="text-blue-600 hover:underline">
              OpenAPI JSON →
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
