'use client'

import { Lightbulb, Users, Building } from 'lucide-react'

export default function BuiltForPage() {
  const audiences = [
    {
      icon: Lightbulb,
      title: 'Content Creators',
      description: 'Streamline your creative workflow with AI-powered content generation. Focus on what matters most - your creative vision.',
      features: [
        'Fast image and video generation',
        'Brand-consistent content',
        'Multiple model options',
        'Easy-to-use interface'
      ],
      color: 'purple'
    },
    {
      icon: Users,
      title: 'Marketing Teams',
      description: 'Create compelling visual content at scale for campaigns and social media. Maintain brand consistency across all channels.',
      features: [
        'Bulk content generation',
        'Template-based workflows',
        'Brand knowledge integration',
        'Media library management'
      ],
      color: 'blue'
    },
    {
      icon: Building,
      title: 'Enterprises',
      description: 'Enterprise-grade AI content generation with security and scalability. All processing happens locally on your infrastructure.',
      features: [
        'Local-only processing',
        'Enterprise security',
        'Scalable architecture',
        'Custom brand integration'
      ],
      color: 'green'
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">Built For</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Designed for creators, marketers, and enterprises who need powerful, secure, and scalable AI content generation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {audiences.map((audience, index) => {
            const Icon = audience.icon
            const colorClasses = {
              purple: 'bg-purple-600/20 text-purple-400 border-purple-500/50',
              blue: 'bg-blue-600/20 text-blue-400 border-blue-500/50',
              green: 'bg-green-600/20 text-green-400 border-green-500/50',
            }
            
            return (
              <div
                key={index}
                className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700/50 hover:border-purple-500/50 transition"
              >
                <div className={`w-16 h-16 ${colorClasses[audience.color as keyof typeof colorClasses]} rounded-full flex items-center justify-center mb-6 border`}>
                  <Icon className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">{audience.title}</h3>
                <p className="text-gray-400 mb-6 leading-relaxed">{audience.description}</p>
                <ul className="space-y-2">
                  {audience.features.map((feature, idx) => (
                    <li key={idx} className="text-gray-300 flex items-start gap-2">
                      <span className="text-purple-400 mt-1">•</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

