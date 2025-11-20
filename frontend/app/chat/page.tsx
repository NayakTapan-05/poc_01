'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ChatPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to home - chat is now accessed via modal
    router.push('/')
  }, [router])

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <p>Redirecting to home...</p>
    </div>
  )
}
