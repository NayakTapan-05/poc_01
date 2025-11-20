'use client'

import { useEffect } from 'react'
import { X } from 'lucide-react'
import ChatSidebar from './ChatSidebar'
import ChatInterface from './ChatInterface'

interface ChatModalProps {
  isOpen: boolean
  onClose: () => void
  currentSessionId?: string | null
  onSessionSelect: (sessionId: string) => void
  onNewChat: () => void
}

export default function ChatModal({
  isOpen,
  onClose,
  currentSessionId,
  onSessionSelect,
  onNewChat
}: ChatModalProps) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
    document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" />

      {/* Modal Container */}
      <div className="relative bg-gray-900 rounded-lg shadow-2xl w-[90%] md:w-[70%] lg:w-[60%] max-w-5xl h-[90vh] max-h-[90vh] flex flex-col z-50">
        {/* Header with close button */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Brand DNAi Chat</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition text-gray-400 hover:text-white"
            aria-label="Close chat"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Chat Content */}
        <div className="flex flex-1 overflow-hidden">
            <ChatSidebar
              currentSessionId={currentSessionId || undefined}
              onSessionSelect={onSessionSelect}
              onNewChat={onNewChat}
            />
          <ChatInterface sessionId={currentSessionId || null} />
        </div>
      </div>
    </div>
  )
}
