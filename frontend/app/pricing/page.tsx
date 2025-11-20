'use client'

import { Check } from 'lucide-react'

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">Pricing</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Free and open-source. Run everything locally on your infrastructure.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-12 border border-purple-500/50">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-white mb-4">Free & Local</h2>
              <p className="text-3xl font-bold text-purple-400 mb-2">$0</p>
              <p className="text-gray-400">Forever free, forever local</p>
            </div>

            <div className="space-y-6 mb-12">
              {[
                'Unlimited image generation',
                'Unlimited video generation',
                'Multi-session chat with local LLMs',
                'Brand knowledge ingestion',
                'Media library management',
                'All models run locally',
                'No API costs',
                'No data sent to external services',
                'Full source code access',
                'Enterprise-grade security',
              ].map((feature, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                  <p className="text-gray-300 text-lg">{feature}</p>
                </div>
              ))}
            </div>

            <div className="bg-purple-600/20 rounded-lg p-6 border border-purple-500/30">
              <h3 className="text-xl font-bold text-white mb-3">Self-Hosted</h3>
              <p className="text-gray-300">
                This is a self-hosted POC. All processing happens on your local machine or infrastructure.
                No cloud services required. Download models from Hugging Face and run everything offline.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

