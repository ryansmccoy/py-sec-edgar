import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Tags, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_NEWS = `Apple CEO Tim Cook announced today that the company will invest $1 billion in a new
research facility in Austin, Texas. The facility, expected to open in 2027, will focus
on artificial intelligence and machine learning research. Cook made the announcement
during a press conference at Apple Park in Cupertino, California.

"This investment represents our commitment to American innovation," Cook said. The
project has received support from Texas Governor Greg Abbott and Austin Mayor Kirk Watson.
Apple's chief technology officer, Craig Federighi, will oversee the new facility's
development alongside VP of Machine Learning, John Giannandrea.

The move follows similar investments by Microsoft in Seattle and Google in New York City.
Industry analysts from Goldman Sachs and Morgan Stanley have praised the decision,
predicting it will create over 5,000 new jobs in the Austin area.`

const ENTITY_TYPES = ['PERSON', 'ORG', 'LOCATION', 'DATE', 'MONEY', 'PRODUCT']

export default function ExtractPage() {
  const [content, setContent] = useState(SAMPLE_NEWS)
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['PERSON', 'ORG', 'LOCATION'])

  const mutation = useMutation({
    mutationFn: api.extract,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim() || selectedTypes.length === 0) return

    mutation.mutate({
      content,
      entity_types: selectedTypes,
    })
  }

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Tags className="text-blue-600" />
        Entity Extraction
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Content</label>
          <textarea
            className="textarea h-48"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your text here..."
            data-testid="extract-input"
          />

          <div className="mt-4">
            <label className="label">Entity Types</label>
            <div className="flex flex-wrap gap-2">
              {ENTITY_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleType(type)}
                  className={`badge cursor-pointer ${
                    selectedTypes.includes(type)
                      ? 'badge-info'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !content.trim() || selectedTypes.length === 0}
              data-testid="extract-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                'Extract Entities'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-4">Extracted Entities</h2>
          <pre className="text-sm bg-white p-4 rounded-md overflow-auto" data-testid="extract-result">
            {JSON.stringify(mutation.data.entities, null, 2)}
          </pre>
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
