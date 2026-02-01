import { useQuery } from '@tanstack/react-query'
import { DollarSign, Loader2 } from 'lucide-react'
import { api } from '../api'

export default function UsagePage() {
  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ['usage'],
    queryFn: api.getUsage,
  })

  const { data: pricing, isLoading: pricingLoading } = useQuery({
    queryKey: ['pricing'],
    queryFn: api.getPricing,
  })

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <DollarSign className="text-blue-600" />
        Cost Tracking & Usage
      </h1>

      {/* Usage Stats */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Usage Statistics</h2>

        {usageLoading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="animate-spin" size={18} />
            <span>Loading usage...</span>
          </div>
        ) : usage ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-blue-700" data-testid="usage-requests">
                {usage.total_requests.toLocaleString()}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600">Total Tokens</p>
              <p className="text-2xl font-bold text-green-700" data-testid="usage-tokens">
                {usage.total_tokens.toLocaleString()}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600">Total Cost</p>
              <p className="text-2xl font-bold text-purple-700" data-testid="usage-cost">
                ${usage.total_cost.toFixed(4)}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No usage data available.</p>
        )}
      </div>

      {/* Model Pricing */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Model Pricing</h2>

        {pricingLoading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="animate-spin" size={18} />
            <span>Loading pricing...</span>
          </div>
        ) : pricing?.models && pricing.models.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Model</th>
                  <th className="text-right py-2">Input / 1K tokens</th>
                  <th className="text-right py-2">Output / 1K tokens</th>
                </tr>
              </thead>
              <tbody>
                {pricing.models.map((model) => (
                  <tr key={model.model} className="border-b">
                    <td className="py-2 font-medium">{model.model}</td>
                    <td className="text-right py-2">
                      ${model.input_price.toFixed(6)}
                    </td>
                    <td className="text-right py-2">
                      ${model.output_price.toFixed(6)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No pricing data available.</p>
        )}

        <div className="mt-4 p-3 bg-gray-50 rounded-md text-sm text-gray-600">
          <p>💡 Local models (Ollama) are free to use.</p>
          <p>OpenAI and Anthropic models require API keys and incur costs.</p>
        </div>
      </div>

      {/* Cost Estimation Info */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold mb-3">Cost Estimation</h2>
        <p className="text-gray-600 mb-3">
          Use the <code className="bg-gray-100 px-1 rounded">/v1/estimate-cost</code> endpoint
          to estimate costs before execution:
        </p>
        <pre className="p-3 bg-gray-50 rounded text-sm overflow-auto">
{`POST /v1/estimate-cost
{
  "model": "gpt-4o",
  "input_tokens": 100,
  "output_tokens": 500
}`}
        </pre>
      </div>
    </div>
  )
}
