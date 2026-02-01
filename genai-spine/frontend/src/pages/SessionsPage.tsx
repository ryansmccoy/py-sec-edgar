import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Trash2, Plus, Send, Loader2 } from 'lucide-react'
import { api, SessionInfo, SessionMessage } from '../api'

export default function SessionsPage() {
  const queryClient = useQueryClient()
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [newSessionModel, setNewSessionModel] = useState('gpt-4o-mini')
  const [messageInput, setMessageInput] = useState('')

  // Fetch sessions
  const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: api.listSessions,
  })

  // Fetch messages for selected session
  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', selectedSessionId],
    queryFn: () => api.getMessages(selectedSessionId!),
    enabled: !!selectedSessionId,
  })

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (model: string) => api.createSession({ model }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      setSelectedSessionId(data.id)
    },
  })

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => api.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      if (selectedSessionId === deleteSessionMutation.variables) {
        setSelectedSessionId(null)
      }
    },
  })

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      api.sendMessage(sessionId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', selectedSessionId] })
      setMessageInput('')
    },
  })

  const sessions = sessionsData?.sessions || []
  const messages = messagesData?.messages || []

  const handleCreateSession = () => {
    createSessionMutation.mutate(newSessionModel)
  }

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Delete this session?')) {
      deleteSessionMutation.mutate(sessionId)
    }
  }

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSessionId || !messageInput.trim()) return
    sendMessageMutation.mutate({ sessionId: selectedSessionId, content: messageInput.trim() })
  }

  const selectedSession = sessions.find((s) => s.id === selectedSessionId)

  return (
    <div className="h-full flex gap-4">
      {/* Session List Sidebar */}
      <div className="w-80 bg-white border border-gray-200 rounded-lg p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Sessions</h2>
          <button
            onClick={handleCreateSession}
            disabled={createSessionMutation.isPending}
            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            <Plus size={16} />
            New
          </button>
        </div>

        {/* Model selector for new sessions */}
        <div className="mb-4">
          <select
            value={newSessionModel}
            onChange={(e) => setNewSessionModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4-turbo">GPT-4 Turbo</option>
            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
            <option value="llama3.2:latest">Llama 3.2 (Ollama)</option>
          </select>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto space-y-2">
          {sessionsLoading ? (
            <div className="text-center text-gray-500 py-4">Loading...</div>
          ) : sessions.length === 0 ? (
            <div className="text-center text-gray-500 py-4">
              No sessions yet.
              <br />
              Click "New" to start.
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => setSelectedSessionId(session.id)}
                className={`p-3 border rounded-md cursor-pointer transition-colors ${
                  selectedSessionId === session.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <MessageSquare size={14} className="text-gray-400 flex-shrink-0" />
                      <span className="text-sm font-medium truncate">{session.model}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="p-1 text-red-500 hover:bg-red-50 rounded"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg flex flex-col">
        {!selectedSessionId ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <MessageSquare size={48} className="mx-auto mb-2 opacity-50" />
              <p>Select a session or create a new one to start chatting</p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="border-b border-gray-200 p-4">
              <h3 className="font-semibold">{selectedSession?.model}</h3>
              <p className="text-sm text-gray-500">
                Session ID: {selectedSessionId.slice(0, 8)}...
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messagesLoading ? (
                <div className="text-center text-gray-500">Loading messages...</div>
              ) : messages.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  No messages yet. Send a message to start the conversation.
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-2 ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                      <div
                        className={`text-xs mt-1 ${
                          msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}
                      >
                        {new Date(msg.created_at).toLocaleTimeString()}
                        {msg.tokens && ` • ${msg.tokens} tokens`}
                        {msg.cost && ` • $${msg.cost.toFixed(4)}`}
                      </div>
                    </div>
                  </div>
                ))
              )}

              {/* Loading indicator for pending message */}
              {sendMessageMutation.isPending && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                    <Loader2 size={16} className="animate-spin" />
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={sendMessageMutation.isPending}
                />
                <button
                  type="submit"
                  disabled={!messageInput.trim() || sendMessageMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {sendMessageMutation.isPending ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} />
                  )}
                  Send
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
