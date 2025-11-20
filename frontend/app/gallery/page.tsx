'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api-client'
import { Image as ImageIcon, Video, ExternalLink } from 'lucide-react'

export default function GalleryPage() {
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await api.getMediaLibrary(50, undefined, undefined, true)
        setAssets(res.data.items || [])
      } catch (error) {
        console.error('Error fetching assets:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchAssets()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">Inspiration Gallery</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Explore AI-generated content created with our platform
          </p>
        </div>

        {loading ? (
          <div className="text-center text-gray-400">Loading gallery...</div>
        ) : assets.length === 0 ? (
          <div className="text-center">
            <p className="text-gray-400 mb-8">No assets in gallery yet.</p>
            <Link
              href="/image"
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition inline-block"
            >
              Generate Your First Image
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
            {assets.map((asset) => (
              <Link
                key={asset.id}
                href={`/library?asset=${asset.id}`}
                className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700/50 hover:border-purple-500/50 transition group"
              >
                <div className="aspect-video bg-gray-900 flex items-center justify-center relative overflow-hidden">
                  {asset.type === 'image' ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/media/${asset.id}/download`}
                      alt={asset.prompt || 'Generated image'}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Video className="w-16 h-16 text-gray-600" />
                    </div>
                  )}
                  <div className="absolute top-2 right-2 bg-black/50 rounded px-2 py-1">
                    {asset.type === 'image' ? (
                      <ImageIcon className="w-4 h-4 text-white" />
                    ) : (
                      <Video className="w-4 h-4 text-white" />
                    )}
                  </div>
                </div>
                <div className="p-4">
                  <p className="text-white font-semibold mb-2 line-clamp-2">
                    {asset.prompt || 'Untitled'}
                  </p>
                  <div className="flex items-center justify-between text-sm text-gray-400">
                    <span>{asset.brand_id || 'Default'}</span>
                    <span>{asset.model || 'Unknown'}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        <div className="text-center mt-12">
          <Link
            href="/library"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition inline-flex items-center gap-2"
          >
            View Full Library
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}

