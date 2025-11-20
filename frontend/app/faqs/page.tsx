'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function FAQsPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const faqs = [
    {
      question: 'What is AI Content Suite?',
      answer: 'AI Content Suite is a local, open-source platform for generating images and videos using AI models. It runs entirely on your machine, ensuring privacy and eliminating API costs.'
    },
    {
      question: 'Do I need an internet connection?',
      answer: 'You need internet to download models initially from Hugging Face. Once models are downloaded, you can run everything offline. Only the initial model download requires internet.'
    },
    {
      question: 'What models are supported?',
      answer: 'For chat: Llama 3.1 8B and Phi-3.5 Mini (GGUF format). For images: SD Turbo, SD 1.5, and SDXL Turbo. For videos: Stable Video Diffusion XT 1.1 and frame composition fallback.'
    },
    {
      question: 'How do I download the models?',
      answer: 'Use the download script: `python backend/scripts/download_models.py` or manually download GGUF files from Hugging Face and place them in the `models/text/` directory. See README for exact commands.'
    },
    {
      question: 'Is my data secure?',
      answer: 'Yes! Everything runs locally on your machine. No data is sent to external services. Your brand knowledge, generated content, and chat sessions all stay on your local storage.'
    },
    {
      question: 'Can I use this commercially?',
      answer: 'This is a POC (Proof of Concept). Check the license of individual models you use. Most models have permissive licenses, but verify the specific license for each model you download.'
    },
    {
      question: 'What are the system requirements?',
      answer: 'Minimum: 8GB RAM, Python 3.12+, Node.js 18+. For GPU acceleration: CUDA-compatible GPU recommended. Models can run on CPU but will be slower.'
    },
    {
      question: 'How do I upload brand knowledge?',
      answer: 'Go to Brand DNAi page, upload a CSV or XLSX file with BrandKey and Description columns. The system will automatically chunk and embed the content for RAG retrieval.'
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">FAQs</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Frequently asked questions about AI Content Suite
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-700/50 transition"
              >
                <span className="text-white font-semibold text-lg">{faq.question}</span>
                {openIndex === index ? (
                  <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                )}
              </button>
              {openIndex === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

