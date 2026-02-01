import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { GitCommit, Loader2 } from 'lucide-react'
import { api } from '../api'

const SAMPLE_DIFF = `diff --git a/src/auth.py b/src/auth.py
index 1234567..abcdefg 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -45,6 +45,12 @@ def authenticate_user(username: str, password: str) -> User:
     if not user:
         raise AuthError("User not found")

+    # Rate limiting: max 5 attempts per minute
+    if get_login_attempts(username) > 5:
+        raise AuthError("Too many login attempts. Please wait 60 seconds.")
+
+    increment_login_attempts(username)
+
     if not verify_password(password, user.password_hash):
         raise AuthError("Invalid password")`

const STYLES = [
  { value: 'conventional', label: 'Conventional', description: 'feat: / fix: / docs:' },
  { value: 'simple', label: 'Simple', description: 'Plain description' },
  { value: 'detailed', label: 'Detailed', description: 'Multi-line with body' },
] as const

type CommitStyle = typeof STYLES[number]['value']

export default function CommitPage() {
  const [diff, setDiff] = useState(SAMPLE_DIFF)
  const [context, setContext] = useState('Adding rate limiting to prevent brute force attacks')
  const [style, setStyle] = useState<CommitStyle>('conventional')

  const mutation = useMutation({
    mutationFn: api.generateCommit,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!diff.trim()) return

    mutation.mutate({ diff, context: context || undefined, style })
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <GitCommit className="text-blue-600" />
        Commit Message Generation
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <label className="label">Git Diff</label>
          <textarea
            className="textarea h-64 font-mono text-sm"
            value={diff}
            onChange={(e) => setDiff(e.target.value)}
            placeholder="Paste your git diff here..."
            data-testid="commit-input"
          />

          <div className="mt-4">
            <label className="label">Context (optional)</label>
            <input
              type="text"
              className="input"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Brief description of the change..."
            />
          </div>

          <div className="mt-4">
            <label className="label">Commit Style</label>
            <div className="flex gap-2">
              {STYLES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setStyle(s.value)}
                  className={`px-4 py-2 rounded-md border ${
                    style === s.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium">{s.label}</p>
                  <p className="text-xs text-gray-500">{s.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isPending || !diff.trim()}
              data-testid="commit-submit"
            >
              {mutation.isPending ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                'Generate Commit Message'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Result */}
      {mutation.data && (
        <div className="card bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-2">Generated Commit Message</h2>
          <pre className="font-mono text-sm whitespace-pre-wrap bg-white p-4 rounded-md" data-testid="commit-result">
            {mutation.data.message}
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
