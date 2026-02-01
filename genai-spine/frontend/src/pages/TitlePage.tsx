import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Type, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_CONTENTS = [
  `Today we're releasing version 2.0 of our open-source database library. This major
update includes a completely rewritten query engine that's 5x faster, native support
for JSON documents, and improved connection pooling. We've also added real-time
replication and automatic failover for production deployments.`,
  `After three months of testing in beta, we're excited to announce that our mobile
app is now available on both iOS and Android. Users can track their fitness goals,
connect with friends, and earn rewards for hitting milestones. Early feedback has
been overwhelmingly positive, with a 4.8 star rating in the App Store.`,
  `The quarterly earnings report shows revenue up 23% year-over-year, driven primarily
by growth in our cloud services division. Operating margin improved to 18%, and
we're raising our full-year guidance. The board has approved a new $500M share
buyback program.`,
]

export default function TitlePage() {
  const [content, setContent] = useState(SAMPLE_CONTENTS[0])
  const [maxWords, setMaxWords] = useState(7)

  const mutation = useMutation({
    mutationFn: api.inferTitle,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return

    mutation.mutate({ content, max_words: maxWords })
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Type className="text-blue-600" />
        Title Inference
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Content</label>
          <textarea
            className="textarea h-40"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter content to generate a title for..."
            data-testid="title-input"
          />

          <div className="mt-4 flex items-center gap-4">
            <div className="flex-1">
              <label className="label">Max Words: {maxWords}</label>
              <input
                type="range"
                min="3"
                max="15"
                value={maxWords}
                onChange={(e) => setMaxWords(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !content.trim()}
              data-testid="title-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                'Generate Title'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Sample Contents */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-3">Try These Samples</h2>
        <div className="space-y-2">
          {SAMPLE_CONTENTS.map((text, i) => (
            <button
              key={i}
              onClick={() => setContent(text)}
              className="w-full text-left p-2 text-sm bg-gray-50 rounded hover:bg-gray-100 transition-colors"
            >
              {text.substring(0, 100)}...
            </button>
          ))}
        </div>
      </div>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-2">Generated Title</h2>
          <p className="text-2xl font-bold text-green-700" data-testid="title-result">
            {mutation.data.title}
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
