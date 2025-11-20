'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { Image, Video, Download, Eye, MessageSquare } from 'lucide-react'
import Link from 'next/link'

export default function LibraryPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [brandFilter, setBrandFilter] = useState('')
  const [brands, setBrands] = useState<any[]>([])
  const [selectedItem, setSelectedItem] = useState<any>(null)

  useEffect(() => {
    fetchLibrary()
    fetchBrands()
  }, [filter, brandFilter])

  const fetchBrands = async () => {
    try {
      const res = await api.getBrands()
      setBrands(res.data.brands || [])
    } catch (error) {
      console.error('Error fetching brands:', error)
    }
  }

  const fetchLibrary = async () => {
    setLoading(true)
    try {
      const type = filter === 'all' ? undefined : filter
      const res = await api.getMediaLibrary(100, brandFilter || undefined, type, true)
      setItems(res.data.items || [])
    } catch (error) {
      console.error('Error fetching library:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetails = async (item: any) => {
    try {
      const res = await api.getMediaItem(item.id)
      setSelectedItem(res.data)
    } catch (error) {
      alert('Failed to fetch item details')
    }
  }

  const filteredItems = items.filter(item => {
    if (filter === 'all') return true
    if (filter === 'image') return item.mime_type?.includes('image')
    if (filter === 'video') return item.mime_type?.includes('video')
    return true
  })

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/" className="text-blue-400 hover:text-blue-300">← Back to Home</Link>
        </div>

        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold">Media Library</h1>

          <div className="flex gap-2">
            <select
              value={brandFilter}
              onChange={(e) => setBrandFilter(e.target.value)}
              className="px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="">All Brands</option>
              {brands.map((b: any) => (
                <option key={b.brand} value={b.brand}>{b.brand}</option>
              ))}
            </select>
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-blue-600' : 'bg-gray-700'}`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('image')}
              className={`px-4 py-2 rounded ${filter === 'image' ? 'bg-blue-600' : 'bg-gray-700'}`}
            >
              Images
            </button>
            <button
              onClick={() => setFilter('video')}
              className={`px-4 py-2 rounded ${filter === 'video' ? 'bg-blue-600' : 'bg-gray-700'}`}
            >
              Videos
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-400">Loading library...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No final assets in library yet. Generate and finalize some content to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item: any) => (
              <div key={item.id} className="bg-gray-800 rounded-lg overflow-hidden">
                <div className="aspect-video bg-gray-700 flex items-center justify-center">
                  {item.mime_type?.includes('image') ? (
                    item.file_path ? (
                      <img
                        src={`http://localhost:8000${item.file_path}`}
                        alt={item.prompt}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Image className="w-16 h-16 text-gray-500" />
                    )
                  ) : item.mime_type?.includes('video') ? (
                    item.file_path ? (
                      <video
                        src={`http://localhost:8000${item.file_path}`}
                        className="w-full h-full object-cover"
                        muted
                      />
                    ) : (
                      <Video className="w-16 h-16 text-gray-500" />
                    )
                  ) : (
                    <div className="text-gray-500">Unknown type</div>
                  )}
                </div>

                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    {item.mime_type?.includes('image') ? (
                      <Image className="w-4 h-4 text-blue-400" />
                    ) : (
                      <Video className="w-4 h-4 text-purple-400" />
                    )}
                    <span className="text-sm font-semibold">{item.model || 'Unknown'}</span>
                    {item.brand_id && (
                      <span className="text-xs text-gray-500">• {item.brand_id}</span>
                    )}
                  </div>

                  <p className="text-sm text-gray-400 mb-2 line-clamp-2">
                    {item.metadata?.prompt?.master_prompt || item.prompt || 'No prompt'}
                  </p>

                  <div className="text-xs text-gray-500 mb-3">
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Unknown date'}
                  </div>

                  <div className="flex gap-2">
                    {item.file_path && (
                      <a
                        href={`http://localhost:8000${item.file_path}`}
                        download
                        className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm text-center transition"
                      >
                        <Download className="inline w-4 h-4 mr-1" />
                        Download
                      </a>
                    )}
                    <button
                      onClick={() => handleViewDetails(item)}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        // TODO: Open chat drawer with asset context
                        alert('Chat feature coming soon')
                      }}
                      className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm transition"
                      title="Refine via Chat"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold">Asset Details</h2>
                  <button
                    onClick={() => setSelectedItem(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-2">Basic Info</h3>
                    <div className="space-y-2 text-sm">
                      <p><span className="text-gray-400">ID:</span> {selectedItem.id}</p>
                      <p><span className="text-gray-400">Type:</span> {selectedItem.mime_type || 'Unknown'}</p>
                      <p><span className="text-gray-400">Model:</span> {selectedItem.model || 'Unknown'}</p>
                      <p><span className="text-gray-400">Brand:</span> {selectedItem.brand_id || 'None'}</p>
                      <p><span className="text-gray-400">Created:</span> {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleString() : 'Unknown'}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-2">Prompts</h3>
                    <div className="space-y-2 text-sm">
                      {selectedItem.metadata?.prompt?.user_input && (
                        <div>
                          <p className="text-gray-400">User Input:</p>
                          <p className="bg-gray-700 p-2 rounded">{selectedItem.metadata.prompt.user_input}</p>
                        </div>
                      )}
                      {selectedItem.metadata?.prompt?.master_prompt && (
                        <div>
                          <p className="text-gray-400">Master Prompt:</p>
                          <p className="bg-gray-700 p-2 rounded">{selectedItem.metadata.prompt.master_prompt}</p>
                        </div>
                      )}
                      {selectedItem.metadata?.prompt?.negative_prompt && (
                        <div>
                          <p className="text-gray-400">Negative Prompt:</p>
                          <p className="bg-gray-700 p-2 rounded">{selectedItem.metadata.prompt.negative_prompt}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {selectedItem.metadata?.model && (
                    <div>
                      <h3 className="font-semibold mb-2">Model Info</h3>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-gray-400">Model ID:</span> {selectedItem.metadata.model.model_id}</p>
                        <p><span className="text-gray-400">Provider:</span> {selectedItem.metadata.model.provider}</p>
                        {selectedItem.metadata.model.params && (
                          <div>
                            <p className="text-gray-400">Params:</p>
                            <pre className="bg-gray-700 p-2 rounded text-xs overflow-auto">
                              {JSON.stringify(selectedItem.metadata.model.params, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {selectedItem.metadata?.rag?.snippets && selectedItem.metadata.rag.snippets.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">RAG Snippets Used</h3>
                      <div className="space-y-2 text-sm max-h-40 overflow-y-auto">
                        {selectedItem.metadata.rag.snippets.map((snippet: string, idx: number) => (
                          <p key={idx} className="bg-gray-700 p-2 rounded text-xs">
                            {snippet.substring(0, 200)}...
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {selectedItem.file_path && (
                  <div className="mt-6">
                    {selectedItem.mime_type?.includes('image') ? (
                      <img
                        src={`http://localhost:8000${selectedItem.file_path}`}
                        alt="Asset"
                        className="max-w-full rounded"
                      />
                    ) : (
                      <video
                        src={`http://localhost:8000${selectedItem.file_path}`}
                        controls
                        className="max-w-full rounded"
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
