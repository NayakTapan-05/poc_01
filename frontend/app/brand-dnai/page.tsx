'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { Upload, Database, Eye } from 'lucide-react'
import Link from 'next/link'

export default function BrandDNAiPage() {
  const [brands, setBrands] = useState<any[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [brandName, setBrandName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [uploadedFilePath, setUploadedFilePath] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchBrands()
  }, [])

  const fetchBrands = async () => {
    try {
      const res = await api.getBrands()
      setBrands(res.data.brands || [])
    } catch (error) {
      console.error('Error fetching brands:', error)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file')
      return
    }

    setUploading(true)
    setMessage('')

    try {
      const res = await api.uploadBrandDocument(file, brandName || undefined)
      setUploadedFilePath(res.data.file_path)
      setMessage('File uploaded successfully! Now click "Ingest" to process it.')
    } catch (error: any) {
      setMessage(`Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleIngest = async () => {
    if (!uploadedFilePath) {
      setMessage('Please upload a file first')
      return
    }

    setIngesting(true)
    setMessage('')

    try {
      const res = await api.ingestBrandDocument(uploadedFilePath, brandName || undefined)
      setMessage(`Ingested successfully! Brands: ${res.data.brands.join(', ')}, Chunks: ${res.data.total_chunks}`)
      fetchBrands()
      setFile(null)
      setUploadedFilePath('')
      setBrandName('')
    } catch (error: any) {
      setMessage(`Ingestion failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIngesting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/" className="text-blue-400 hover:text-blue-300">← Back to Home</Link>
        </div>

        <h1 className="text-5xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400">UCAi Brand Knowledge</h1>
        <p className="text-xl text-gray-300 mb-8 max-w-3xl">
          Upload individual brand files containing 12-13 brand keys with their descriptions.
          Each brand should have its own Excel/CSV file with unique brand keys and descriptions.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              <Upload className="mr-2" />
              Upload & Ingest
            </h2>

            <div className="space-y-4">
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-4">
                <h3 className="font-semibold text-blue-300 mb-2">File Format Requirements:</h3>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Excel (.xlsx) or CSV files with columns: BrandKey, Description</li>
                  <li>• Each file should contain one brand's data (12-13 brand keys)</li>
                  <li>• Brand keys can be shared across brands but descriptions are unique</li>
                  <li>• Example: "Brand Communication Idea", "Tone of Voice", "Brand Benefits", etc.</li>
                </ul>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Brand Name *</label>
                <input
                  type="text"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  placeholder="e.g., Dove, Sunsilk, Simple"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Upload Brand File</label>
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileChange}
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 file:bg-blue-600 file:text-white file:border-0 file:rounded file:px-3 file:py-1 file:mr-3 hover:file:bg-blue-700"
                />
                <p className="text-xs text-gray-400 mt-1">Supported formats: Excel (.xlsx), CSV</p>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleUpload}
                  disabled={uploading || !file}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>

                <button
                  onClick={handleIngest}
                  disabled={ingesting || !uploadedFilePath}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded font-semibold transition"
                >
                  {ingesting ? 'Processing...' : 'Process Brand Data'}
                </button>
              </div>

              {message && (
                <div className={`p-4 rounded ${message.includes('failed') ? 'bg-red-900' : 'bg-green-900'}`}>
                  {message}
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              <Database className="mr-2" />
              Brand Knowledge Base
            </h2>

            <div className="space-y-4">
              {brands.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg">No brands uploaded yet.</p>
                  <p className="text-gray-500 text-sm mt-2">Upload individual brand files to build your knowledge base.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {brands.map((brand: any, idx: number) => (
                    <div key={idx} className="bg-gray-700 p-4 rounded">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold text-lg">{brand.brand}</h3>
                          <p className="text-sm text-gray-400">
                            Chunks: {brand.chunks || 0} | Vectors: {brand.vectors || 0}
                          </p>
                        </div>
                        <button
                          onClick={async () => {
                            try {
                              const res = await api.getBrandSnippet(brand.brand)
                              alert(`Sample snippet:\n\n${res.data.snippet}`)
                            } catch (error) {
                              alert('Failed to fetch snippet')
                            }
                          }}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm flex items-center"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View Sample
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
