'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { api } from '@/lib/api-client'
import { 
  Image, Video, Database, Zap, Shield, Lightbulb, Users, Building,
  ArrowRight, Sparkles, Layers, Rocket, Globe, Code, Palette, Star, TrendingUp
} from 'lucide-react'

export default function HomePage() {
  const [stats, setStats] = useState({ brands: 0, media: 0 })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [brandsRes, mediaRes] = await Promise.all([
          api.getBrands(),
          api.getMediaLibrary(100)
        ])
        setStats({
          brands: brandsRes.data.brands?.length || 0,
          media: mediaRes.data.items?.length || 0
        })
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }
    fetchStats()
  }, [])

  // Animated Feature Card
  const FeatureCard = ({ 
    icon: Icon, 
    title, 
    description, 
    color, 
    delay = 0,
    index 
  }: { 
    icon: any, 
    title: string, 
    description: string, 
    color: string,
    delay?: number,
    index: number
  }) => {
    const { ref, inView } = useInView({
      threshold: 0.2,
      triggerOnce: true
    })

    const colorMap: Record<string, { icon: string, iconBg: string, text: string, shadow: string }> = {
      purple: { icon: 'text-purple-400', iconBg: 'from-purple-500/20 to-purple-700/20', text: 'group-hover:text-purple-200', shadow: 'rgba(168, 85, 247, 0.2)' },
      blue: { icon: 'text-blue-400', iconBg: 'from-blue-500/20 to-blue-700/20', text: 'group-hover:text-blue-200', shadow: 'rgba(59, 130, 246, 0.2)' },
      green: { icon: 'text-green-400', iconBg: 'from-green-500/20 to-green-700/20', text: 'group-hover:text-green-200', shadow: 'rgba(34, 197, 94, 0.2)' },
      pink: { icon: 'text-pink-400', iconBg: 'from-pink-500/20 to-pink-700/20', text: 'group-hover:text-pink-200', shadow: 'rgba(236, 72, 153, 0.2)' },
      cyan: { icon: 'text-cyan-400', iconBg: 'from-cyan-500/20 to-cyan-700/20', text: 'group-hover:text-cyan-200', shadow: 'rgba(6, 182, 212, 0.2)' },
      orange: { icon: 'text-orange-400', iconBg: 'from-orange-500/20 to-orange-700/20', text: 'group-hover:text-orange-200', shadow: 'rgba(249, 115, 22, 0.2)' }
    }

    const colors = colorMap[color] || colorMap.purple

    const cardVariants = {
      hidden: { 
        opacity: 0, 
        y: 50,
        rotateX: -15
      },
      visible: { 
        opacity: 1, 
        y: 0,
        rotateX: 0
      }
    }

    return (
      <motion.div
        ref={ref}
        variants={cardVariants}
        initial="hidden"
        animate={inView ? "visible" : "hidden"}
        className="group relative"
        transition={{ 
          duration: 0.6, 
          delay,
          ease: "easeOut"
        }}
      >
        <div 
          className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-xl rounded-3xl p-8 border border-gray-700/50 h-full relative overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1"
          style={{
            boxShadow: `0 20px 60px -10px ${colors.shadow}`
          }}
        >
          {/* Gradient overlay - CSS transition only */}
          <div className={`absolute inset-0 bg-gradient-to-br ${colors.iconBg} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
          
          {/* Static background pattern - no animation to prevent flickering */}
          <div
            className="absolute inset-0 opacity-5"
            style={{
              backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
              backgroundSize: '40px 40px'
            }}
          />
          
          <div className="relative z-10">
            <div className={`w-20 h-20 bg-gradient-to-br ${colors.iconBg} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
              <Icon className={`w-10 h-10 ${colors.icon}`} />
            </div>
            <h3 className={`text-2xl font-bold text-white mb-4 ${colors.text} transition-colors`}>
              {title}
            </h3>
            <p className="text-gray-400 group-hover:text-gray-300 transition-colors leading-relaxed">
              {description}
            </p>
          </div>
        </div>
      </motion.div>
    )
  }

  // Studio Card with 3D effect
  const StudioCard = ({ 
    title, 
    description, 
    icon: Icon, 
    href, 
    gradient, 
    delay = 0 
  }: { 
    title: string, 
    description: string, 
    icon: any, 
    href: string, 
    gradient: string,
    delay?: number
  }) => {
    const { ref, inView } = useInView({
      threshold: 0.2,
      triggerOnce: true
    })

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 100, rotateY: -20 }}
        animate={inView ? { 
          opacity: 1, 
          y: 0, 
          rotateY: 0 
        } : {}}
        transition={{ 
          duration: 0.8, 
          delay,
          ease: "easeOut"
        }}
        className="group relative"
      >
        <Link href={href} className="block h-full">
          <div 
            className={`${gradient} backdrop-blur-xl rounded-3xl p-10 border border-white/10 relative overflow-hidden h-full transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl`}
            style={{
              boxShadow: '0 30px 80px -20px rgba(0,0,0,0.5)'
            }}
          >
            {/* Static background pattern */}
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
                backgroundSize: '40px 40px'
              }}
            />
            
            {/* Glowing effect - only on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <div className="relative z-10 flex flex-col items-center text-center">
              <div className="w-28 h-28 bg-white/10 rounded-3xl flex items-center justify-center mb-8 backdrop-blur-sm group-hover:scale-110 transition-transform duration-300">
                <Icon className="w-14 h-14 text-white" />
              </div>
              
              <h3 className="text-5xl font-bold text-white mb-6 group-hover:scale-105 transition-transform duration-300">
                {title}
              </h3>
              
              <p className="text-white/80 mb-8 text-lg leading-relaxed max-w-md">
                {description}
              </p>
              
              <div className="flex items-center gap-2 text-white font-semibold group-hover:translate-x-2 transition-transform duration-300">
                <span>Start Creating</span>
                <ArrowRight className="w-5 h-5" />
              </div>
            </div>
          </div>
        </Link>
      </motion.div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950 to-blue-950 relative overflow-hidden">
      {/* Static Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute rounded-full blur-3xl opacity-20 bg-purple-500" style={{ width: 400, height: 400, top: '10%', left: '10%' }} />
        <div className="absolute rounded-full blur-3xl opacity-20 bg-blue-500" style={{ width: 300, height: 300, top: '60%', right: '10%' }} />
        <div className="absolute rounded-full blur-3xl opacity-20 bg-pink-500" style={{ width: 350, height: 350, bottom: '20%', left: '50%' }} />
        <div className="absolute rounded-full blur-3xl opacity-20 bg-purple-500" style={{ width: 250, height: 250, top: '30%', right: '30%' }} />
        <div className="absolute rounded-full blur-3xl opacity-20 bg-blue-500" style={{ width: 200, height: 200, bottom: '40%', left: '20%' }} />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="relative z-10 text-center px-4">
          {/* Badge */}
          <div className="inline-block mb-8">
            <span className="inline-flex items-center px-6 py-3 rounded-full bg-gradient-to-r from-purple-600/20 to-blue-600/20 backdrop-blur-xl border border-purple-500/30 text-purple-300 text-sm font-medium">
              <Sparkles className="w-4 h-4 mr-2" />
              Powered by Advanced AI
            </span>
          </div>

          {/* Main Title */}
          <h1 className="text-8xl md:text-9xl font-black mb-6 relative"
            style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #a855f7 50%, #3b82f6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              filter: 'drop-shadow(0 0 40px rgba(168, 85, 247, 0.5))'
            }}
          >
            UCAi
            {/* Static glow effect - no animation */}
            <span
              className="absolute inset-0 blur-2xl opacity-30"
              style={{
                background: 'linear-gradient(135deg, #a855f7 0%, #3b82f6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                zIndex: -1
              }}
            />
          </h1>

          <div className="text-3xl md:text-4xl text-gray-300 font-light mb-8">
            Unilever Content Assistant AI
          </div>

          <p className="text-xl md:text-2xl text-gray-400 mb-16 max-w-3xl mx-auto leading-relaxed">
            Transform your brand vision into stunning visual content with our enterprise-grade AI platform
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <div>
              <Link
              href="/image"
                className="px-10 py-5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-2xl font-bold text-lg transition-all duration-300 shadow-2xl shadow-purple-500/30 flex items-center gap-3 relative overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <Rocket className="w-6 h-6 relative z-10" />
                <span className="relative z-10">Start Creating</span>
              </Link>
            </div>
            <div>
            <Link
              href="/brand-dnai"
                className="px-10 py-5 bg-white/10 hover:bg-white/20 backdrop-blur-xl text-white rounded-2xl font-bold text-lg transition-all duration-300 border border-white/20 flex items-center gap-3"
            >
                <Database className="w-6 h-6" />
                Upload Brand DNA
            </Link>
            </div>
          </div>
        </div>

        {/* Scroll Indicator - static to prevent flickering */}
        <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 opacity-60">
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <span className="text-sm">Scroll to explore</span>
            <ArrowRight className="w-5 h-5 rotate-90" />
          </div>
        </div>
      </section>

      {/* Studio Cards Section */}
      <section className="relative py-32 px-4">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-20"
          >
            <motion.h2 
              className="text-6xl md:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-blue-200 mb-6"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              Create Anything
            </motion.h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Powerful AI tools for image and video generation
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            <StudioCard
              title="Image Studio"
              description="Create stunning AI-generated images with advanced controls and brand integration"
              icon={Image}
              href="/image"
              gradient="bg-gradient-to-br from-purple-600/30 to-purple-800/30"
              delay={0}
            />
            <StudioCard
              title="Video Studio"
              description="Generate stunning AI-powered videos from images with cinematic effects"
              icon={Video}
              href="/video"
              gradient="bg-gradient-to-br from-blue-600/30 to-blue-800/30"
              delay={0.2}
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-32 px-4">
        <div className="container mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-20"
          >
            <motion.h2 
              className="text-6xl md:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-blue-200 mb-6"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              Powerful Features
            </motion.h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Cutting-edge AI technology meets intuitive design
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={Zap}
              title="Lightning Fast"
              description="Generate high-quality content in seconds with advanced AI models and optimized pipelines"
              color="purple"
              delay={0}
              index={0}
            />
            <FeatureCard
              icon={Database}
              title="Brand Intelligence"
              description="AI-powered brand analysis and context-aware content generation for authentic brand voice"
              color="blue"
              delay={0.2}
              index={1}
            />
            <FeatureCard
              icon={Shield}
              title="Enterprise Security"
              description="Bank-level encryption, secure content storage, and compliance-ready architecture"
              color="green"
              delay={0.4}
              index={2}
            />
          </div>
        </div>
      </section>

      {/* Built For Section */}
      <section className="relative py-32 px-4">
        <div className="container mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-20"
          >
            <motion.h2 
              className="text-6xl md:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-200 to-purple-200 mb-6"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              Built For
            </motion.h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Designed for professionals who demand the best
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={Lightbulb}
              title="Content Creators"
              description="Streamline your creative workflow with AI-powered content generation and professional tools"
              color="pink"
              delay={0}
              index={3}
            />
            <FeatureCard
              icon={Users}
              title="Marketing Teams"
              description="Create compelling visual content at scale for campaigns, social media, and brand storytelling"
              color="cyan"
              delay={0.2}
              index={4}
            />
            <FeatureCard
              icon={Building}
              title="Enterprises"
              description="Enterprise-grade AI content generation with security, compliance, and scalability"
              color="orange"
              delay={0.4}
              index={5}
            />
          </div>
        </div>
      </section>

      {/* Stats Section with Enhanced Animations */}
      <section className="relative py-32 px-4">
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-8"
          >
            <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-xl rounded-3xl p-12 border border-gray-700/50 text-center relative overflow-hidden hover:scale-[1.02] transition-transform duration-300">
              {/* Static background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent" />
              <motion.h3
                className="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400 mb-4 relative z-10"
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
              >
                {stats.brands}
              </motion.h3>
              <p className="text-gray-400 text-xl relative z-10">Brands Ingested</p>
            </div>
            <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-xl rounded-3xl p-12 border border-gray-700/50 text-center relative overflow-hidden hover:scale-[1.02] transition-transform duration-300">
              {/* Static background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent" />
              <motion.h3
                className="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400 mb-4 relative z-10"
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, delay: 0.4 }}
              >
                {stats.media}
              </motion.h3>
              <p className="text-gray-400 text-xl relative z-10">Assets Generated</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer CTA with Enhanced Design */}
      <section className="relative py-32 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <motion.h2 
            className="text-5xl md:text-6xl font-bold text-white mb-8"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Ready to Transform Your Content?
          </motion.h2>
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
            Join thousands of creators and brands using UCAi to create stunning visual content
          </p>
          <div>
            <Link
              href="/image"
              className="inline-flex items-center gap-3 px-12 py-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-2xl font-bold text-xl transition-all duration-300 shadow-2xl shadow-purple-500/30 relative overflow-hidden group hover:scale-105"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <span className="relative z-10">Get Started Now</span>
              <ArrowRight className="w-6 h-6 relative z-10" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
