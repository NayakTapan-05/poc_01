'use client'

import { MessageSquare } from 'lucide-react'

interface ChatWidgetProps {
  onOpenChat: () => void
}

export default function ChatWidget({ onOpenChat }: ChatWidgetProps) {
  return (
    <button
      onClick={onOpenChat}
      className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 rounded-full shadow-lg flex items-center justify-center transition z-50"
      title="Open Chat"
    >
      <MessageSquare className="w-6 h-6 text-white" />
    </button>
  )
}
