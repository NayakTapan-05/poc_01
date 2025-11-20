'use client'

import { useState } from 'react'
import { Plus, Image, Video, X } from 'lucide-react'
import Link from 'next/link'

export default function CreateButton() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="fixed bottom-6 left-6 z-40">
      {isOpen && (
        <div className="mb-4 space-y-2">
          <Link
            href="/image"
            className="flex items-center gap-3 px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg shadow-lg transition"
            onClick={() => setIsOpen(false)}
          >
            <Image className="w-5 h-5 text-white" />
            <span className="text-white font-semibold">Image Studio</span>
          </Link>
          <Link
            href="/video"
            className="flex items-center gap-3 px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg shadow-lg transition"
            onClick={() => setIsOpen(false)}
          >
            <Video className="w-5 h-5 text-white" />
            <span className="text-white font-semibold">Video Studio</span>
          </Link>
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition ${
          isOpen ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Plus className="w-6 h-6 text-white" />
        )}
      </button>
    </div>
  )
}

