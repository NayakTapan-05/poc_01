'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { Image as ImageIcon, Sparkles, Download, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function ImageStudioPage() {
  const [brands, setBrands] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [prompt, setPrompt] = useState('')
  const [brand, setBrand] = useState('')
  const [templateType, setTemplateType] = useState('')
  const [templateValues, setTemplateValues] = useState<Record<string, string>>({})
  const [negativePrompt, setNegativePrompt] = useState('')
  const [modelId, setModelId] = useState('')
  const [width, setWidth] = useState(512)
  const [height, setHeight] = useState(512)
  const [steps, setSteps] = useState(4)
  const [seed, setSeed] = useState(-1)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [templates, setTemplates] = useState<any[]>([])
  const [masterPrompt, setMasterPrompt] = useState('')
  const [showMasterPrompt, setShowMasterPrompt] = useState(false)

  useEffect(() => {
    fetchBrands()
    fetchModels()
    fetchTemplates()
  }, [])

  const fetchBrands = async () => {
    try {
      const res = await api.getBrands()
      setBrands(res.data.brands || [])
    } catch (error) {
      console.error('Error fetching brands:', error)
    }
  }

  const fetchModels = async () => {
    try {
      const res = await api.getModels('image')
      const imageModels = res.data.models || []
      setModels(imageModels)
      // Set default model
      const defaultModel = imageModels.find((m: any) => m.default) || imageModels[0]
      if (defaultModel) {
        setModelId(defaultModel.id)
      }
    } catch (error) {
      console.error('Error fetching models:', error)
    }
  }

  const fetchTemplates = async () => {
    try {
      const res = await api.getTemplates('image')
      setTemplates(res.data.templates || [])
    } catch (error) {
      console.error('Error fetching templates:', error)
    }
  }

  const handleEnhancePrompt = async () => {
    if (!prompt) {
      alert('Please enter a prompt')
      return
    }

    try {
      const res = await api.enhancePrompt({
        user_input: prompt,
        brand_id: brand || undefined,
        template_id: templateType || undefined,
        template_values: Object.keys(templateValues).length > 0 ? templateValues : undefined,
        negative_prompt: negativePrompt || undefined,
        engine_type: 'image'
      })
      setMasterPrompt(res.data.master_prompt)
      setNegativePrompt(res.data.negative_prompt || negativePrompt)
      setShowMasterPrompt(true)
    } catch (error: any) {
      alert(`Enhancement failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleGenerate = async () => {
    if (!masterPrompt) {
      alert('Please enhance the prompt first')
      return
    }

    setGenerating(true)
    setResult(null)

    try {
      const res = await api.generateImage({
        prompt: masterPrompt,
        brand_id: brand || undefined,
        model_id: modelId,
        negative_prompt: negativePrompt || undefined,
        width,
        height,
        steps,
        seed,
      })
      setResult(res.data)
    } catch (error: any) {
      alert(`Generation failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleFinalize = async () => {
    if (!result?.item_id) return
    
    try {
      await api.finalizeAsset(result.item_id)
      alert('Asset marked as final!')
    } catch (error: any) {
      alert(`Failed to finalize: ${error.response?.data?.detail || error.message}`)
    }
  }

  const selectedTemplate = templates.find(t => t.id === templateType)

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/" className="text-blue-400 hover:text-blue-300">← Back to Home</Link>
        </div>

        <h1 className="text-5xl font-bold mb-8 flex items-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-purple-600">
          <ImageIcon className="mr-4 w-12 h-12 text-purple-400" />
          Image Studio
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Prompt & Brand</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Brand</label>
                  <select
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select a brand (optional)</option>
                    {brands.map((b: any, idx: number) => (
                      <option key={idx} value={b.brand}>{b.brand}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Template</label>
                  <select
                    value={templateType}
                    onChange={(e) => {
                      setTemplateType(e.target.value)
                      setTemplateValues({})
                    }}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">None</option>
                    {templates.map((t: any, idx: number) => (
                      <option key={idx} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>

                {selectedTemplate && selectedTemplate.fields && (
                  <div className="bg-gray-700 p-4 rounded">
                    <label className="block text-sm font-medium mb-2">Template Fields</label>
                    {selectedTemplate.fields.map((field: string) => (
                      <input
                        key={field}
                        type="text"
                        value={templateValues[field] || ''}
                        onChange={(e) => setTemplateValues({ ...templateValues, [field]: e.target.value })}
                        placeholder={field}
                        className="w-full mb-2 px-4 py-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
                      />
                    ))}
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-2">User Prompt *</label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    placeholder="Describe the image you want to generate..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Negative Prompt (optional)</label>
                  <textarea
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    rows={2}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    placeholder="What to avoid in the image..."
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Model & Parameters</h2>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Model</label>
                  <select
                    value={modelId}
                    onChange={(e) => setModelId(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  >
                    {models.map((m: any) => (
                      <option key={m.id} value={m.id}>
                        {m.name} {m.requires_token ? '(HF Token required)' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Width: {width}px</label>
                  <input
                    type="range"
                    min="256"
                    max="1024"
                    step="64"
                    value={width}
                    onChange={(e) => setWidth(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Height: {height}px</label>
                  <input
                    type="range"
                    min="256"
                    max="1024"
                    step="64"
                    value={height}
                    onChange={(e) => setHeight(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Steps: {steps}</label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={steps}
                    onChange={(e) => setSteps(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-2">Seed</label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value))}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    placeholder="-1 for random"
                  />
                </div>
              </div>
            </div>

            {showMasterPrompt && masterPrompt && (
              <div className="bg-gray-800 p-6 rounded-lg border-2 border-blue-500">
                <h2 className="text-2xl font-semibold mb-4 flex items-center">
                  <Sparkles className="mr-2" />
                  Master Prompt
                </h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Enhanced Master Prompt</label>
                    <textarea
                      value={masterPrompt}
                      onChange={(e) => setMasterPrompt(e.target.value)}
                      rows={4}
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  {negativePrompt && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Negative Prompt</label>
                    <div className="p-4 bg-gray-700 rounded text-sm">{negativePrompt}</div>
                  </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={handleEnhancePrompt}
                disabled={!prompt}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded font-semibold transition flex items-center"
              >
                <Sparkles className="mr-2 w-5 h-5" />
                Enhance Prompt
              </button>

              <button
                onClick={handleGenerate}
                disabled={generating || !masterPrompt}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition"
              >
                {generating ? 'Generating...' : 'Generate Image'}
              </button>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Result</h2>

            {result ? (
              <div className="space-y-4">
                <img
                  src={`http://localhost:8000${result.image_path}`}
                  alt="Generated"
                  className="w-full rounded"
                />
                <div className="text-sm text-gray-400 space-y-1">
                  <p>Item ID: {result.item_id}</p>
                  <p>Model: {result.model || 'Unknown'}</p>
                  <p>Brand: {result.brand_id || 'None'}</p>
                  {result.created_at && (
                    <p>Created: {new Date(result.created_at).toLocaleString()}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleFinalize}
                    className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-center font-semibold transition flex items-center justify-center"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Mark as Final
                  </button>
                <a
                  href={`http://localhost:8000${result.image_path}`}
                  download
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-center font-semibold transition flex items-center justify-center"
                >
                    <Download className="w-4 h-4 mr-2" />
                  Download
                </a>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-400 py-12">
                <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Generated image will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
