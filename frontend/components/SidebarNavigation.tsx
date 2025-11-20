'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  Image,
  Video,
  Database,
  BarChart3,
  FolderOpen,
  ChevronRight
} from 'lucide-react'

const navigationItems = [
  {
    name: 'Home',
    href: '/',
    icon: Home,
  },
  {
    name: 'Image Studio',
    href: '/image',
    icon: Image,
  },
  {
    name: 'Video Studio',
    href: '/video',
    icon: Video,
  },
  {
    name: 'Brand DNA',
    href: '/brand-dnai',
    icon: Database,
  },
  {
    name: 'Media Library',
    href: '/library',
    icon: FolderOpen,
  },
]

export default function SidebarNavigation() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showIcons, setShowIcons] = useState(false)
  const pathname = usePathname()

  return (
    <>
      {/* Invisible hover trigger area */}
      <div
        className="fixed left-0 top-0 w-6 h-full z-40"
        onMouseEnter={() => {
          setShowIcons(true)
          setIsExpanded(true)
        }}
      />

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full bg-gray-900 border-r border-gray-800 transition-all duration-300 ease-in-out z-50 overflow-hidden ${
          isExpanded ? 'w-64' : 'w-0'
        }`}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => {
          setIsExpanded(false)
          // Keep icons visible briefly before hiding
          setTimeout(() => setShowIcons(false), 300)
        }}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b border-gray-800 transition-opacity duration-300 ${
          isExpanded ? 'opacity-100' : 'opacity-0'
        }`}>
          <div className="font-bold text-white">
            Brand DNAi Studio
          </div>
          <ChevronRight
            className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${
              isExpanded ? 'rotate-180' : ''
            }`}
          />
        </div>

        {/* Navigation Items */}
        <nav className={`mt-8 transition-opacity duration-300 ${
          isExpanded ? 'opacity-100' : 'opacity-0'
        }`}>
          <ul className="space-y-2 px-3">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={`flex items-center px-3 py-3 rounded-lg transition-all duration-200 group ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <Icon
                      className={`w-6 h-6 flex-shrink-0 transition-colors duration-200 ${
                        isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                      }`}
                    />
                    <span
                      className={`ml-3 font-medium transition-all duration-300 ${
                        isExpanded
                          ? 'opacity-100 translate-x-0'
                          : 'opacity-0 -translate-x-4 pointer-events-none'
                      }`}
                    >
                      {item.name}
                    </span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className={`absolute bottom-4 left-0 right-0 px-3 transition-opacity duration-300 delay-100 ${
          isExpanded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
        }`}>
          <div className="text-xs text-gray-500">
            Brand DNAi Studio
          </div>
        </div>
      </div>

      {/* Overlay for mobile (if needed) */}
      {isExpanded && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </>
  )
}
