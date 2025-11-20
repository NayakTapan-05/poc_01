'use client'

import { useState, useEffect } from 'react'
import { Plus, MessageSquare, Trash2, Edit2, X, Check } from 'lucide-react'
import { api } from '@/lib/api-client'

interface Session {
  id: string
  title: string
  brand?: string
  updated_at?: string
  last_message_at?: string
}

interface ChatSidebarProps {
  currentSessionId?: string
  onSessionSelect: (sessionId: string) => void
  onNewChat: () => void
}

export default function ChatSidebar({ currentSessionId, onSessionSelect, onNewChat }: ChatSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const loadSessions = async () => {
    try {
      setLoading(true)
      const res = await api.listChatSessions()
      setSessions(res.data || [])
    } catch (error) {
      console.error('Error loading sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadSessions, 30000)
    
    // Listen for refresh events
    const handleRefresh = () => {
      loadSessions()
    }
    window.addEventListener('refreshSessions', handleRefresh)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('refreshSessions', handleRefresh)
    }
  }, [])

  // Refresh when session is selected
  useEffect(() => {
    if (currentSessionId) {
      // Small delay to ensure backend has updated
      setTimeout(() => loadSessions(), 500)
    }
  }, [currentSessionId])

  const handleNewChat = async () => {
    try {
      const res = await api.createChatSession()
      const newSession = res.data
      await loadSessions() // Refresh to get updated list
      onNewChat()
      onSessionSelect(newSession.id)
    } catch (error) {
      console.error('Error creating session:', error)
      alert('Failed to create chat session')
    }
  }

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this chat?')) {
      return
    }

    try {
      await api.deleteSession(sessionId)
      await loadSessions() // Refresh list
      if (currentSessionId === sessionId) {
        onNewChat()
      }
    } catch (error) {
      console.error('Error deleting session:', error)
      alert('Failed to delete session')
    }
  }

  const handleStartEdit = (session: Session, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditTitle(session.title)
  }

  const handleSaveEdit = async (sessionId: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (!editTitle.trim()) {
      handleCancelEdit()
      return
    }
    try {
      await api.updateSession(sessionId, { title: editTitle.trim() })
      await loadSessions() // Refresh to get updated data
      setEditingId(null)
      setEditTitle('')
    } catch (error) {
      console.error('Error updating session:', error)
      alert('Failed to update session title')
    }
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditTitle('')
  }

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col h-full">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white mb-4">Brand DNAi</h1>
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition text-white"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <div className="mb-4">
          <div className="text-xs text-gray-400 px-2 mb-2">Chats</div>
          {loading ? (
            <div className="text-sm text-gray-400 px-2">Loading...</div>
          ) : sessions.length === 0 ? (
            <div className="text-sm text-gray-400 px-2 py-4 text-center">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No chats yet</p>
              <p className="text-xs mt-1">Start a new conversation</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative mb-1 rounded transition ${
                  currentSessionId === session.id
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-800'
                }`}
              >
                <button
                  onClick={() => onSessionSelect(session.id)}
                  className="w-full text-left px-3 py-2 rounded transition"
                >
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 flex-shrink-0 text-gray-400" />
                    <div className="flex-1 min-w-0">
                      {editingId === session.id ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              handleSaveEdit(session.id)
                            } else if (e.key === 'Escape') {
                              handleCancelEdit()
                            }
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1 bg-gray-600 text-white text-sm rounded"
                          autoFocus
                        />
                      ) : (
                        <>
                          <div className="text-sm text-white truncate">{session.title}</div>
                          {session.brand && (
                            <div className="text-xs text-gray-400 truncate">{session.brand}</div>
                          )}
                          {session.last_message_at && (
                            <div className="text-xs text-gray-500 mt-1">
                              {new Date(session.last_message_at).toLocaleDateString()}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </button>
                {editingId !== session.id && (
                  <div className="absolute right-2 top-2 flex gap-1 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={(e) => handleStartEdit(session, e)}
                      className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-white"
                      title="Rename"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="p-1 hover:bg-red-600 rounded text-gray-400 hover:text-white"
                      title="Delete"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
