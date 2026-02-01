import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Edit3, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_NOTES = `meeting w/ john tmrw 2pm re: Q4 budget
- need to discuss marketing spend (prob 500k?)
- also talk abt new hires - 3 devs + 1 PM
- john mentioned potential office expansion... austin maybe??
- follow up on vendor contracts expiring dec 31
- IMPORTANT: get approval for cloud migration before EOY
btw sarah mentioned sales r up 15% this qtr - nice!`

const MODES = [
  { value: 'clean', label: 'Clean', description: 'Fix grammar, spelling, punctuation' },
  { value: 'format', label: 'Format', description: 'Structure into proper format' },
  { value: 'organize', label: 'Organize', description: 'Group related items' },
  { value: 'summarize', label: 'Summarize', description: 'Condense to key points' },
] as const

type RewriteMode = typeof MODES[number]['value']

export default function RewritePage() {
  const [content, setContent] = useState(SAMPLE_NOTES)
  const [mode, setMode] = useState<RewriteMode>('clean')

  const mutation = useMutation({
    mutationFn: api.rewrite,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return

    mutation.mutate({ content, mode })
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Edit3 className="text-blue-600" />
        Content Rewriting
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Original Content</label>
          <textarea
            className="textarea h-48"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter rough notes, messy text, etc..."
            data-testid="rewrite-input"
          />

          <div className="mt-4">
            <label className="label">Rewrite Mode</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {MODES.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setMode(m.value)}
                  className={`p-3 rounded-md border text-left transition-colors ${
                    mode === m.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium">{m.label}</p>
                  <p className="text-xs text-gray-500">{m.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !content.trim()}
              data-testid="rewrite-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                `Rewrite (${mode})`
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-2">Rewritten Content</h2>
          <div className="whitespace-pre-wrap" data-testid="rewrite-result">
            {mutation.data.rewritten}
          </div>
        </div>
      )}

      {mutation.isError && (
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-700">Error: {(mutation.error as Error).message}</p>
        </div>
      )}
    </div>
  )
}
