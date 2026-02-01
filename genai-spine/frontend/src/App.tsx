import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  MessageSquare,
  FileText,
  Tags,
  FolderOpen,
  Edit3,
  Type,
  GitCommit,
  FileCode,
  DollarSign,
  Database,
  Menu,
  X,
} from 'lucide-react'
import { api } from './api'

// Pages
import HealthPage from './pages/HealthPage'
import ChatPage from './pages/ChatPage'
import SessionsPage from './pages/SessionsPage'
import KnowledgePage from './pages/KnowledgePage'
import SummarizePage from './pages/SummarizePage'
import ExtractPage from './pages/ExtractPage'
import ClassifyPage from './pages/ClassifyPage'
import RewritePage from './pages/RewritePage'
import TitlePage from './pages/TitlePage'
import CommitPage from './pages/CommitPage'
import PromptsPage from './pages/PromptsPage'
import UsagePage from './pages/UsagePage'

const navItems = [
  { path: '/', label: 'Health', icon: Activity },
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/sessions', label: 'Sessions', icon: MessageSquare },
  { path: '/knowledge', label: 'Knowledge', icon: Database },
  { path: '/summarize', label: 'Summarize', icon: FileText },
  { path: '/extract', label: 'Extract', icon: Tags },
  { path: '/classify', label: 'Classify', icon: FolderOpen },
  { path: '/rewrite', label: 'Rewrite', icon: Edit3 },
  { path: '/title', label: 'Title', icon: Type },
  { path: '/commit', label: 'Commit', icon: GitCommit },
  { path: '/prompts', label: 'Prompts', icon: FileCode },
  { path: '/usage', label: 'Usage', icon: DollarSign },
]

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { data: health, isLoading: healthLoading, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  })

  const statusColor = healthError ? 'bg-red-500' : healthLoading ? 'bg-yellow-500' : 'bg-green-500'

  return (
    <BrowserRouter>
      <div className="min-h-screen flex">
        {/* Mobile menu button */}
        <button
          className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-white shadow-md"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        {/* Sidebar */}
        <aside
          className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gray-900 text-white transform transition-transform duration-200 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <div className="p-6 border-b border-gray-800">
            <h1 className="text-xl font-bold">GenAI Spine</h1>
            <p className="text-gray-400 text-sm mt-1">Demo UI v0.2.0</p>
            <div className="flex items-center gap-2 mt-3">
              <div className={`w-2 h-2 rounded-full ${statusColor}`} />
              <span className="text-sm text-gray-400">
                {healthError ? 'Offline' : healthLoading ? 'Checking...' : 'Online'}
              </span>
            </div>
          </div>

          <nav className="p-4">
            <ul className="space-y-1">
              {navItems.map(({ path, label, icon: Icon }) => (
                <li key={path}>
                  <NavLink
                    to={path}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-2 rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-800'
                      }`
                    }
                  >
                    <Icon size={18} />
                    <span>{label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
            <p className="text-xs text-gray-500">
              API: {health?.version || 'v0.1.0'}
            </p>
            <a
              href="/api/docs"
              target="_blank"
              className="text-xs text-blue-400 hover:underline"
            >
              OpenAPI Docs →
            </a>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<HealthPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/summarize" element={<SummarizePage />} />
            <Route path="/extract" element={<ExtractPage />} />
            <Route path="/classify" element={<ClassifyPage />} />
            <Route path="/rewrite" element={<RewritePage />} />
            <Route path="/title" element={<TitlePage />} />
            <Route path="/commit" element={<CommitPage />} />
            <Route path="/prompts" element={<PromptsPage />} />
            <Route path="/usage" element={<UsagePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
