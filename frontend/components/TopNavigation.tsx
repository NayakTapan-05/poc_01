'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Moon, Sun, User } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function TopNavigation() {
  const pathname = usePathname()
  const [darkMode, setDarkMode] = useState(true)

  useEffect(() => {
    // Check if dark mode is set in localStorage
    const stored = localStorage.getItem('darkMode')
    const isDark = stored === null ? true : stored === 'true' // Default to dark mode
    setDarkMode(isDark)
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    localStorage.setItem('darkMode', String(newDarkMode))
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const navLinks = [
    { href: '/', label: 'Overview' },
    { href: '/features', label: 'Features' },
    { href: '/built-for', label: 'Built For' },
    { href: '/gallery', label: 'Inspiration Gallery' },
    { href: '/faqs', label: 'FAQs' },
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname?.startsWith(href)
  }

  return (
    <nav className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800/50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:scale-105 transition-all duration-300 group">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 via-blue-500 to-purple-700 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-purple-500/30 transition-shadow">
              <span className="text-white font-bold text-xl">U</span>
            </div>
            <span className="text-white font-bold text-lg bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              UCAi
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  isActive(link.href)
                    ? 'bg-purple-600/20 text-purple-400'
                    : 'text-gray-300 hover:text-white hover:bg-gray-800'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-4">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* Profile */}
            <button className="px-4 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-gray-800 transition flex items-center gap-2">
              <User className="w-4 h-4" />
              <span className="hidden sm:inline">Profile</span>
            </button>

            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden pb-4 border-t border-gray-800 mt-2 pt-4">
          <div className="flex flex-col gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  isActive(link.href)
                    ? 'bg-purple-600/20 text-purple-400'
                    : 'text-gray-300 hover:text-white hover:bg-gray-800'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

