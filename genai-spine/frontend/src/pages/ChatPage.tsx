import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import { api, ChatMessage } from '../api'

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'You are a helpful assistant.' },
  ])
  const [input, setInput] = useState('')
  const [model, setModel] = useState('llama3.2:latest')
  const [temperature, setTemperature] = useState(0.7)

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
  })

  const mutation = useMutation({
    mutationFn: api.chatCompletion,
    onSuccess: (data) => {
      const assistantMessage = data.choices[0].message
      setMessages((prev) => [...prev, assistantMessage])
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || mutation.isPending) return

    const userMessage: ChatMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')

    mutation.mutate({
      model,
      messages: [...messages, userMessage],
      temperature,
      max_tokens: 500,
    })
  }

  const clearChat = () => {
    setMessages([{ role: 'system', content: 'You are a helpful assistant.' }])
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <MessageSquare className="text-blue-600" />
        Chat Completion
      </h1>

      {/* Settings */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Model</label>
            <select
              className="select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {models?.data?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.id}
                </option>
              ))}
              <option value="llama3.2:latest">llama3.2:latest</option>
            </select>
          </div>
          <div>
            <label className="label">Temperature: {temperature}</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={clearChat}
              className="btn btn-secondary w-full"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="card mb-4 min-h-[300px] max-h-[500px] overflow-y-auto">
        {messages.filter(m => m.role !== 'system').map((msg, i) => (
          <div
            key={i}
            className={`mb-4 p-3 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-100 ml-12'
                : 'bg-gray-100 mr-12'
            }`}
          >
            <p className="text-xs text-gray-500 mb-1">
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </p>
            <p className="whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}

        {mutation.isPending && (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="animate-spin" size={16} />
            <span>Thinking...</span>
          </div>
        )}

        {mutation.isError && (
          <div className="p-3 bg-red-100 text-red-700 rounded-lg">
            Error: {(mutation.error as Error).message}
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="input flex-1"
          disabled={mutation.isPending}
          data-testid="chat-input"
        />
        <button
          type="submit"
          className="btn btn-primary flex items-center gap-2"
          disabled={mutation.isPending || !input.trim()}
          data-testid="chat-submit"
        >
          <Send size={18} />
          Send
        </button>
      </form>

      {/* Usage Info */}
      {mutation.data?.usage && (
        <div className="mt-4 text-sm text-gray-500">
          Tokens: {mutation.data.usage.prompt_tokens} input, {mutation.data.usage.completion_tokens} output
        </div>
      )}
    </div>
  )
}
