'use client'

import { Inter } from 'next/font/google'
import { useState, useEffect } from 'react'
import '../styles/globals.css'
import TopNavigation from '@/components/TopNavigation'
import SidebarNavigation from '@/components/SidebarNavigation'
import ChatWidget from '@/components/ChatWidget'
import ChatModal from '@/components/ChatModal'
import CreateButton from '@/components/CreateButton'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  // Listen for session creation events from ChatInterface
  useEffect(() => {
    const handleSessionCreated = (e: CustomEvent) => {
      if (e.detail.sessionId) {
        setCurrentSessionId(e.detail.sessionId)
      }
    }
    window.addEventListener('sessionCreated', handleSessionCreated as EventListener)
    return () => window.removeEventListener('sessionCreated', handleSessionCreated as EventListener)
  }, [])

  const handleOpenChat = () => {
    setIsChatOpen(true)
  }

  const handleCloseChat = () => {
    setIsChatOpen(false)
  }

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId)
  }

  const handleNewChat = () => {
    setCurrentSessionId(null)
  }

  return (
    <html lang="en">
      <body className={inter.className}>
        <TopNavigation />
        <SidebarNavigation />
        {children}
        <CreateButton />
        <ChatWidget onOpenChat={handleOpenChat} />
        <ChatModal
          isOpen={isChatOpen}
          onClose={handleCloseChat}
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
        />
      </body>
    </html>
  )
}
