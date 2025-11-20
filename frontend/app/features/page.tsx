'use client'

import { Zap, Shield, FileText, Sparkles, Database, MessageSquare } from 'lucide-react'

export default function FeaturesPage() {
  const features = [
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Generate high-quality content in seconds with advanced AI models optimized for speed and performance.',
      color: 'purple'
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Bank-level encryption and secure content storage for your peace of mind. All data stays local and private.',
      color: 'blue'
    },
    {
      icon: FileText,
      title: 'Multiple Formats',
      description: 'Support for images, videos, and various content formats. Export in your preferred format.',
      color: 'green'
    },
    {
      icon: Sparkles,
      title: 'AI-Powered Enhancement',
      description: 'Advanced prompt enhancement using brand knowledge and RAG to create perfect prompts for generation.',
      color: 'yellow'
    },
    {
      icon: Database,
      title: 'Brand DNA Integration',
      description: 'Upload and ingest brand knowledge to ensure all generated content aligns with your brand identity.',
      color: 'purple'
    },
    {
      icon: MessageSquare,
      title: 'Multi-Session Chat',
      description: 'Chat with your brand knowledge using local LLMs. Multiple sessions with memory and context.',
      color: 'blue'
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">Powerful Features</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Everything you need to create stunning AI-generated content with brand consistency and enterprise-grade security
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon
            const colorClasses = {
              purple: 'bg-purple-600/20 text-purple-400 border-purple-500/50',
              blue: 'bg-blue-600/20 text-blue-400 border-blue-500/50',
              green: 'bg-green-600/20 text-green-400 border-green-500/50',
              yellow: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/50',
            }
            
            return (
              <div
                key={index}
                className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700/50 hover:border-purple-500/50 transition"
              >
                <div className={`w-16 h-16 ${colorClasses[feature.color as keyof typeof colorClasses]} rounded-full flex items-center justify-center mb-6 border`}>
                  <Icon className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

