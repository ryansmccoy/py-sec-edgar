import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FileText, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_TEXT = `The development of artificial intelligence has accelerated dramatically over the past decade,
transforming industries from healthcare to finance. Machine learning algorithms now power
recommendation systems, fraud detection, and autonomous vehicles. Large language models like
GPT-4 and Claude have demonstrated remarkable capabilities in understanding and generating
human-like text, leading to applications in customer service, content creation, and code
generation.

However, these advances come with significant challenges. Concerns about AI safety, bias in
training data, and the potential for misuse have prompted calls for regulation and ethical
guidelines. The environmental impact of training large models, which requires enormous
computational resources, has also drawn attention from sustainability advocates.

Despite these challenges, investment in AI continues to grow. Major tech companies and
startups alike are racing to develop more capable and efficient models. The integration
of AI into everyday tools and workflows is expected to continue, with predictions that
AI will eventually augment most knowledge work tasks.`

export default function SummarizePage() {
  const [content, setContent] = useState(SAMPLE_TEXT)
  const [maxSentences, setMaxSentences] = useState(3)

  const mutation = useMutation({
    mutationFn: api.summarize,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return

    mutation.mutate({
      content,
      max_sentences: maxSentences,
    })
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <FileText className="text-blue-600" />
        Text Summarization
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Content to Summarize</label>
          <textarea
            className="textarea h-48"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your text here..."
            data-testid="summarize-input"
          />

          <div className="mt-4 flex items-center gap-4">
            <div className="flex-1">
              <label className="label">Max Sentences: {maxSentences}</label>
              <input
                type="range"
                min="1"
                max="10"
                value={maxSentences}
                onChange={(e) => setMaxSentences(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !content.trim()}
              data-testid="summarize-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                'Summarize'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-2">Summary</h2>
          <p className="whitespace-pre-wrap" data-testid="summarize-result">
            {mutation.data.summary}
          </p>
        </div>
      )}

      {mutation.isError && (
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-700">Error: {(mutation.error as Error).message}</p>
        </div>
      )}

      {/* Stats */}
      {content && (
        <div className="mt-4 text-sm text-gray-500">
          Input: {content.split(/\s+/).length} words
        </div>
      )}
    </div>
  )
}
