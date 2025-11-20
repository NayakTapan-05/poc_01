'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Copy, RefreshCw, MessageSquare } from 'lucide-react'
import { api } from '@/lib/api-client'

interface Message {
  role: 'user' | 'assistant'
  content: string
  intent?: string
  sources?: Array<{
    brand: string
    snippet: string
    score: number
  }>
  created_at?: string
}

interface ChatInterfaceProps {
  sessionId: string | null
}

export default function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(sessionId)
  const [chatModels, setChatModels] = useState<any[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    setActiveSessionId(sessionId)
    if (sessionId) {
      loadMessages()
    } else {
      setMessages([])
      setError(null)
    }
  }, [sessionId])

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await api.getModels('chat')
        const models = res.data.models || []
        setChatModels(models)
        // Set default model
        const defaultModel = models.find((m: any) => m.default) || models[0]
        if (defaultModel) {
          setSelectedModelId(defaultModel.id)
        }
      } catch (error) {
        console.error('Error fetching chat models:', error)
      }
    }
    fetchModels()
  }, [])

  // Listen for session creation events to update active session
  useEffect(() => {
    const handleSessionCreated = (e: CustomEvent) => {
      if (e.detail.sessionId) {
        setActiveSessionId(e.detail.sessionId)
        // Small delay to ensure backend has processed
        setTimeout(() => {
          if (e.detail.sessionId) {
            loadMessages()
          }
        }, 300)
      }
    }
    window.addEventListener('sessionCreated', handleSessionCreated as EventListener)
    return () => window.removeEventListener('sessionCreated', handleSessionCreated as EventListener)
  }, [])

  const loadMessages = async () => {
    const sessionToLoad = activeSessionId || sessionId
    if (!sessionToLoad) return
    
    try {
      const res = await api.getChatSession(sessionToLoad)
      const sessionData = res.data
      if (sessionData.messages) {
        const loadedMessages = sessionData.messages.map((m: any) => ({
        role: m.role,
        content: m.content,
        created_at: m.created_at
      }))
      setMessages(loadedMessages)
      }
      setError(null)
    } catch (error) {
      console.error('Error loading messages:', error)
      setError('Failed to load messages')
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = { 
      role: 'user', 
      content: input,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)
    setError(null)

    try {
      // Create session if needed
      let actualSessionId = activeSessionId || sessionId
      if (!actualSessionId) {
        const createRes = await api.createChatSession()
        actualSessionId = createRes.data.id
        setActiveSessionId(actualSessionId)
        // Update session title based on first message
        if (currentInput.length > 0) {
          const title = currentInput.substring(0, 50) + (currentInput.length > 50 ? '...' : '')
          try {
          await api.updateSession(actualSessionId, { title })
          } catch (e) {
            console.warn('Failed to update session title:', e)
          }
        }
        // Trigger session select callback via custom event
        window.dispatchEvent(new CustomEvent('sessionCreated', { detail: { sessionId: actualSessionId } }))
        // Also trigger a refresh event for sidebar
        window.dispatchEvent(new CustomEvent('refreshSessions'))
      }

      const res = await api.sendSessionMessage(actualSessionId, currentInput, undefined, selectedModelId)
      
      const aiMessage: Message = {
        role: 'assistant',
        content: res.data.answer || res.data.content || 'No response received',
        intent: res.data.intent,
        sources: res.data.sources || [],
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      
      // Reload messages to get updated session data if session exists
      if (actualSessionId) {
        try {
      await loadMessages()
        } catch (e) {
          console.warn('Failed to reload messages:', e)
        }
      }
    } catch (error: any) {
      let errorContent = 'Failed to send message'
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (typeof detail === 'object' && detail.error === 'model_not_installed') {
          errorContent = `Model Not Installed: ${detail.message}\n\nInstructions: ${detail.instructions}`
        } else {
          errorContent = typeof detail === 'string' ? detail : JSON.stringify(detail)
        }
      } else {
        errorContent = error.message || 'Failed to send message'
      }
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${errorContent}`,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
      setError(errorContent)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content)
    // Could add a toast notification here
  }

  const handleRegenerate = async () => {
    if (messages.length < 2) return
    
    // Remove last assistant message
    const lastUserMessage = messages[messages.length - 2]
    if (lastUserMessage.role !== 'user') return
    
    setMessages(prev => prev.slice(0, -1))
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const sessionToUse = activeSessionId || sessionId
      if (!sessionToUse) {
        throw new Error('No active session')
      }
      const res = await api.sendSessionMessage(sessionToUse, lastUserMessage.content, undefined, selectedModelId)
      
      const aiMessage: Message = {
        role: 'assistant',
        content: res.data.answer || 'No response received',
        intent: res.data.intent,
        sources: res.data.sources || [],
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      setInput('')
    } catch (error: any) {
      let errorContent = 'Failed to regenerate'
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (typeof detail === 'object' && detail.error === 'model_not_installed') {
          errorContent = `Model Not Installed: ${detail.message}\n\nInstructions: ${detail.instructions}`
        } else {
          errorContent = typeof detail === 'string' ? detail : JSON.stringify(detail)
        }
      } else {
        errorContent = error.message || 'Failed to regenerate'
      }
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${errorContent}`,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
      setError(errorContent)
    } finally {
      setLoading(false)
    }
  }

  const getIntentBadge = (intent?: string) => {
    if (!intent) return null
    
    const colors: Record<string, string> = {
      qa_brand: 'bg-green-600',
      creative_copy: 'bg-blue-600',
      image_prompt: 'bg-purple-600',
      video_prompt: 'bg-pink-600',
      setup_or_onboarding: 'bg-yellow-600',
      small_talk: 'bg-gray-600'
    }
    
    const labels: Record<string, string> = {
      qa_brand: 'Brand Q&A',
      creative_copy: 'Creative Copy',
      image_prompt: 'Image Prompt',
      video_prompt: 'Video Prompt',
      setup_or_onboarding: 'Help',
      small_talk: 'Small Talk'
    }

    return (
      <span className={`text-xs px-2 py-1 rounded ${colors[intent] || 'bg-gray-600'}`}>
        {labels[intent] || intent.toUpperCase().replace('_', ' ')}
      </span>
    )
  }

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return ''
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return ''
    }
  }


  return (
    <div className="flex-1 flex flex-col bg-gray-800">
      {/* Model Selector */}
      {chatModels.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-700 bg-gray-750">
          <label className="text-xs text-gray-400 mr-2">Model:</label>
          <select
            value={selectedModelId}
            onChange={(e) => setSelectedModelId(e.target.value)}
            className="px-3 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            disabled={loading}
          >
            {chatModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} {model.requires_token ? '(HF Token Required)' : ''}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-12">
            <p className="text-lg mb-2">Start a conversation</p>
            <p className="text-sm">Ask me anything about your brands!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl rounded-lg p-4 relative group ${
                msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-100'
              }`}>
                {msg.intent && msg.role === 'assistant' && (
                  <div className="mb-2">{getIntentBadge(msg.intent)}</div>
                )}
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.created_at && (
                  <div className="text-xs opacity-60 mt-2">
                    {formatTime(msg.created_at)}
                  </div>
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <details className="mt-3 text-xs opacity-75">
                    <summary className="cursor-pointer">Based on Brand DNA ({msg.sources.length})</summary>
                    <div className="mt-2 space-y-2">
                      {msg.sources.map((source, sidx) => (
                        <div key={sidx} className="p-2 bg-black bg-opacity-20 rounded">
                          <p className="font-semibold">{source.brand}</p>
                          <p className="mt-1">{source.snippet}</p>
                          <p className="text-xs opacity-60 mt-1">Relevance: {(source.score * 100).toFixed(0)}%</p>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                {msg.role === 'assistant' && (
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={() => handleCopy(msg.content)}
                      className="p-1 hover:bg-gray-600 rounded text-gray-300 hover:text-white"
                      title="Copy"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                    {idx === messages.length - 1 && (
                      <button
                        onClick={handleRegenerate}
                        className="p-1 hover:bg-gray-600 rounded text-gray-300 hover:text-white"
                        title="Regenerate"
                      >
                        <RefreshCw className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                <span className="text-sm text-gray-300 ml-2">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="bg-red-900 bg-opacity-50 border border-red-700 rounded-lg p-4 text-sm text-red-200">
            <p>Error: {error}</p>
            <button
              onClick={handleSend}
              className="mt-2 text-xs underline hover:text-red-100"
            >
              Retry
            </button>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-700">
        {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && !loading && (activeSessionId || sessionId) && (
          <div className="mb-2 flex justify-end">
            <button
              onClick={handleRegenerate}
              className="text-xs text-gray-400 hover:text-gray-300 flex items-center gap-1 transition"
              title="Regenerate last response"
            >
              <RefreshCw className="w-3 h-3" />
              Regenerate
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !loading) {
                handleSend()
              }
            }}
            placeholder="Ask about your brands..."
            className="flex-1 px-4 py-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded transition"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
