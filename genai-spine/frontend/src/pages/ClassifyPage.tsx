import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FolderOpen, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_TEXTS = [
  "The S&P 500 rose 2% today following positive earnings reports from major tech companies.",
  "Scientists at CERN have discovered a new particle that could revolutionize our understanding of physics.",
  "The Lakers defeated the Celtics 112-108 in an overtime thriller last night.",
  "The new Python 3.12 release includes significant performance improvements and better error messages.",
]

const DEFAULT_CATEGORIES = ['finance', 'technology', 'science', 'sports', 'politics', 'entertainment']

export default function ClassifyPage() {
  const [content, setContent] = useState(SAMPLE_TEXTS[0])
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES.join(', '))

  const mutation = useMutation({
    mutationFn: api.classify,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim() || !categories.trim()) return

    const categoryList = categories.split(',').map((c) => c.trim()).filter(Boolean)

    mutation.mutate({
      content,
      categories: categoryList,
    })
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <FolderOpen className="text-blue-600" />
        Content Classification
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Content to Classify</label>
          <textarea
            className="textarea h-32"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter text to classify..."
            data-testid="classify-input"
          />

          <div className="mt-4">
            <label className="label">Categories (comma-separated)</label>
            <input
              type="text"
              className="input"
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              placeholder="finance, technology, science, ..."
            />
          </div>

          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !content.trim()}
              data-testid="classify-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                'Classify'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Sample Texts */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-3">Try These Samples</h2>
        <div className="space-y-2">
          {SAMPLE_TEXTS.map((text, i) => (
            <button
              key={i}
              onClick={() => setContent(text)}
              className="w-full text-left p-2 text-sm bg-gray-50 rounded hover:bg-gray-100 transition-colors"
            >
              {text.substring(0, 80)}...
            </button>
          ))}
        </div>
      </div>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-2">Classification Result</h2>
          <p className="text-2xl font-bold text-green-700" data-testid="classify-result">
            {mutation.data.category}
          </p>
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
