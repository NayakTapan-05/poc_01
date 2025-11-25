'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api-client'
import { Video, Sparkles, Download, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function VideoStudioPage() {
  const [brands, setBrands] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [prompt, setPrompt] = useState('')
  const [brand, setBrand] = useState('')
  const [imagePath, setImagePath] = useState('')
  const [templateType, setTemplateType] = useState('')
  const [templateValues, setTemplateValues] = useState<Record<string, string>>({})
  const [negativePrompt, setNegativePrompt] = useState('')
  const [modelId, setModelId] = useState('')
  const [frames, setFrames] = useState(25)
  const [fps, setFps] = useState(6)
  const [duration, setDuration] = useState(4)
  const [resolution, setResolution] = useState('576x1024')
  const [generating, setGenerating] = useState(false)
  const [jobId, setJobId] = useState('')
  const [result, setResult] = useState<any>(null)
  const [templates, setTemplates] = useState<any[]>([])
  const [masterPrompt, setMasterPrompt] = useState('')
  const [showMasterPrompt, setShowMasterPrompt] = useState(false)
  const [mediaItems, setMediaItems] = useState<any[]>([])

  useEffect(() => {
    fetchBrands()
    fetchModels()
    fetchTemplates()
    fetchMediaItems()
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
      const res = await api.getModels('video')
      const videoModels = res.data.models || []
      setModels(videoModels)
      // Set default model
      const defaultModel = videoModels.find((m: any) => m.default) || videoModels[0]
      if (defaultModel) {
        setModelId(defaultModel.id)
      }
    } catch (error) {
      console.error('Error fetching models:', error)
    }
  }

  const fetchTemplates = async () => {
    try {
      const res = await api.getTemplates('video')
      setTemplates(res.data.templates || [])
    } catch (error) {
      console.error('Error fetching templates:', error)
    }
  }

  const fetchMediaItems = async () => {
    try {
      const res = await api.getMediaLibrary(50, undefined, 'image', true)
      setMediaItems(res.data.items || [])
    } catch (error) {
      console.error('Error fetching media items:', error)
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
        engine_type: 'video'
      })
      setMasterPrompt(res.data.master_prompt)
      setNegativePrompt(res.data.negative_prompt || negativePrompt)
      setShowMasterPrompt(true)
    } catch (error: any) {
      alert(`Enhancement failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleGenerate = async () => {
    if (!imagePath) {
      alert('Please provide an image path')
      return
    }

    if (!masterPrompt) {
      alert('Please enhance the prompt first')
      return
    }

    setGenerating(true)
    setResult(null)

    try {
      const res = await api.generateVideo({
        image_path: imagePath,
        model_id: modelId,
        prompt: masterPrompt,
        brand_id: brand || undefined,
        frames,
        fps,
        duration,
        resolution,
      })
      setJobId(res.data.job_id)
      pollJobStatus(res.data.job_id)
    } catch (error: any) {
      alert(`Generation failed: ${error.response?.data?.detail || error.message}`)
      setGenerating(false)
    }
  }

  const pollJobStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await api.getVideoJobStatus(id)
        if (res.data.status === 'complete') {
          setResult(res.data)
          setGenerating(false)
          clearInterval(interval)
        } else if (res.data.status === 'failed') {
          alert(`Video generation failed: ${res.data.error}`)
          setGenerating(false)
          clearInterval(interval)
        }
      } catch (error) {
        console.error('Error polling job status:', error)
      }
    }, 2000)
  }

  const handleFinalize = async () => {
    if (!result?.job_id) return
    
    try {
      await api.finalizeAsset(result.job_id)
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

        <h1 className="text-5xl font-bold mb-8 flex items-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
          <Video className="mr-4 w-12 h-12 text-blue-400" />
          Video Studio
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-2xl font-semibold mb-4">Video Parameters</h2>

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
                  <label className="block text-sm font-medium mb-2">Source Image Path *</label>
                  <select
                    value={imagePath}
                    onChange={(e) => setImagePath(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select from library or enter path</option>
                    {mediaItems.map((item: any) => (
                      <option key={item.id} value={item.file_path}>
                        {item.prompt?.substring(0, 50)}... ({item.model})
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={imagePath}
                    onChange={(e) => setImagePath(e.target.value)}
                    placeholder="Or enter image path manually"
                    className="w-full mt-2 px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Tip: Generate an image first in Image Studio, then use its path here
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Motion Prompt (optional)</label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    placeholder="Describe the video motion/animation..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Negative Prompt (optional)</label>
                  <textarea
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    rows={2}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    placeholder="What to avoid in the video..."
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
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Resolution</label>
                  <select
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="576x1024">576x1024</option>
                    <option value="512x512">512x512</option>
                    <option value="768x768">768x768</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Frames: {frames}</label>
                  <input
                    type="range"
                    min="10"
                    max="50"
                    value={frames}
                    onChange={(e) => setFrames(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">FPS: {fps}</label>
                  <input
                    type="range"
                    min="4"
                    max="12"
                    value={fps}
                    onChange={(e) => setFps(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-2">Duration: {duration}s</label>
                  <input
                    type="range"
                    min="2"
                    max="10"
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    className="w-full"
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
                disabled={generating || !imagePath || !masterPrompt}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition"
            >
              {generating ? 'Generating Video...' : 'Generate Video'}
            </button>
            </div>

            {generating && jobId && (
              <div className="bg-blue-900 p-4 rounded">
                <p>Job ID: {jobId}</p>
                <p>Status: Processing... (this may take a while)</p>
              </div>
            )}
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Result</h2>

            {result ? (
              <div className="space-y-4">
                <video
                  src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.video_path}`}
                  controls
                  className="w-full rounded"
                />
                <div className="text-sm text-gray-400 space-y-1">
                  <p>Job ID: {result.job_id}</p>
                  <p>Status: {result.status}</p>
                  <p>Model: {result.model || 'Unknown'}</p>
                  <p>Brand: {result.brand_id || 'None'}</p>
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
                  href={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.video_path}`}
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
                <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Generated video will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
