'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { Settings as SettingsIcon, Trash2, Database, Image, Video, MessageSquare, Cpu } from 'lucide-react'
import Link from 'next/link'

export default function SettingsPage() {
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState('')
  const [registry, setRegistry] = useState<any>(null)

  useEffect(() => {
    fetchRegistry()
  }, [])

  const fetchRegistry = async () => {
    try {
      const res = await api.getModelRegistry()
      setRegistry(res.data.registry)
    } catch (error) {
      console.error('Error fetching registry:', error)
    }
  }

  const handleClearVectorStore = async () => {
    if (!confirm('Are you sure you want to clear all brand knowledge? This cannot be undone.')) {
      return
    }

    setClearing(true)
    setMessage('')

    try {
      const res = await api.clearVectorStore()
      setMessage(res.data.message || 'Vector store cleared successfully')
    } catch (error: any) {
      setMessage(`Failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setClearing(false)
    }
  }

  const handleClearOutputs = async () => {
    if (!confirm('Are you sure you want to delete all generated images and videos? This cannot be undone.')) {
      return
    }

    setClearing(true)
    setMessage('')

    try {
      const res = await api.clearOutputs()
      setMessage(res.data.message || 'Outputs cleared successfully')
    } catch (error: any) {
      setMessage(`Failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setClearing(false)
    }
  }

  const getProviderLabel = (provider: string, requiresToken?: boolean) => {
    if (provider === 'local') return 'Local'
    if (provider === 'diffusers') return 'Local (Diffusers)'
    if (provider === 'hf') return requiresToken ? 'HuggingFace (Token Required)' : 'HuggingFace'
    return provider
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/" className="text-blue-400 hover:text-blue-300">← Back to Home</Link>
        </div>

        <h1 className="text-4xl font-bold mb-8 flex items-center">
          <SettingsIcon className="mr-3" />
          Settings
        </h1>

        <div className="max-w-4xl space-y-6">
          {registry && (
          <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Model Registry</h2>
              
              <div className="space-y-6">
                {/* Chat Models */}
                {registry.chat && Object.keys(registry.chat).length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center">
                      <MessageSquare className="w-5 h-5 mr-2 text-blue-400" />
                      Chat Models
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.values(registry.chat).map((model: any) => (
                        <div key={model.id} className="bg-gray-700 p-4 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{model.name}</span>
                            {model.default && (
                              <span className="text-xs bg-blue-600 px-2 py-1 rounded">Default</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400 space-y-1">
                            <p>ID: {model.id}</p>
                            <p>Provider: {getProviderLabel(model.provider)}</p>
                            {model.path && <p className="text-xs">Path: {model.path}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Image Models */}
                {registry.image && Object.keys(registry.image).length > 0 && (
                <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center">
                      <Image className="w-5 h-5 mr-2 text-purple-400" />
                      Image Models
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.values(registry.image).map((model: any) => (
                        <div key={model.id} className="bg-gray-700 p-4 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{model.name}</span>
                            {model.default && (
                              <span className="text-xs bg-blue-600 px-2 py-1 rounded">Default</span>
                            )}
                            {model.requires_token && (
                              <span className="text-xs bg-yellow-600 px-2 py-1 rounded">Optional</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400 space-y-1">
                            <p>ID: {model.id}</p>
                            <p>Provider: {getProviderLabel(model.provider, model.requires_token)}</p>
                            {model.path && <p className="text-xs">Path: {model.path}</p>}
                          </div>
                        </div>
                      ))}
                </div>
              </div>
                )}

                {/* Video Models */}
                {registry.video && Object.keys(registry.video).length > 0 && (
                <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center">
                      <Video className="w-5 h-5 mr-2 text-green-400" />
                      Video Models
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.values(registry.video).map((model: any) => (
                        <div key={model.id} className="bg-gray-700 p-4 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{model.name}</span>
                            {model.default && (
                              <span className="text-xs bg-blue-600 px-2 py-1 rounded">Default</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400 space-y-1">
                            <p>ID: {model.id}</p>
                            <p>Provider: {getProviderLabel(model.provider)}</p>
                            {model.path && <p className="text-xs">Path: {model.path}</p>}
                          </div>
                        </div>
                      ))}
                </div>
              </div>
                )}

                {/* Embedding Models */}
                {registry.embeddings && Object.keys(registry.embeddings).length > 0 && (
                <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center">
                      <Database className="w-5 h-5 mr-2 text-green-400" />
                      Embedding Models
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.values(registry.embeddings).map((model: any) => (
                        <div key={model.id} className="bg-gray-700 p-4 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{model.name}</span>
                            {model.default && (
                              <span className="text-xs bg-blue-600 px-2 py-1 rounded">Default</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400 space-y-1">
                            <p>ID: {model.id}</p>
                            <p>Provider: {getProviderLabel(model.provider)}</p>
                            {model.path && <p className="text-xs">Path: {model.path}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                </div>
                )}
              </div>
            </div>
          )}

          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Maintenance</h2>
            <div className="space-y-4">
              <div className="flex items-start justify-between p-4 bg-gray-700 rounded">
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Clear Vector Store</h3>
                  <p className="text-sm text-gray-400">
                    Remove all brand knowledge from the vector database. You will need to re-ingest documents.
                  </p>
                </div>
                <button
                  onClick={handleClearVectorStore}
                  disabled={clearing}
                  className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded font-semibold transition flex items-center"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear
                </button>
              </div>

              <div className="flex items-start justify-between p-4 bg-gray-700 rounded">
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Clear Generated Outputs</h3>
                  <p className="text-sm text-gray-400">
                    Delete all generated images and videos from the outputs directory.
                  </p>
                </div>
                <button
                  onClick={handleClearOutputs}
                  disabled={clearing}
                  className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded font-semibold transition flex items-center"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear
                </button>
              </div>
            </div>
          </div>

          {message && (
            <div className={`p-4 rounded ${message.includes('Failed') ? 'bg-red-900' : 'bg-green-900'}`}>
              {message}
            </div>
          )}

          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">About</h2>
            <div className="text-gray-300 space-y-2">
              <p><strong>Version:</strong> 1.0.0</p>
              <p><strong>Backend:</strong> FastAPI</p>
              <p><strong>Frontend:</strong> Next.js + React + TypeScript</p>
              <p><strong>Database:</strong> SQLite + ChromaDB</p>
              <p className="text-sm text-gray-400 mt-4">
                Brand DNAi Content Studio - A local-first, free-only AI content generation platform.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
