# UCAi - Unilever Content Assistant AI

A fully functional POC that combines a Python FastAPI backend with a modern Next.js/React/TypeScript frontend to deliver AI-powered content generation with brand knowledge integration.

## 🎯 Features

### Core Functionality
- **Brand Knowledge Management** - Upload and ingest brand metadata (CSV/XLSX) with automatic chunking and embedding
- **RAG-Powered Chat** - Multi-session chat with brand context using local LLMs (Phi-3.5 Mini, Llama 3.1 8B)
- **Image Generation** - Generate brand-aware images using multiple models (SD Turbo, SD 1.5, SDXL Turbo)
- **Video Generation** - Create videos from images using Stable Video Diffusion XT 1.1 or frame composition
- **Prompt Enhancement** - AI-powered prompt enhancement using brand knowledge and RAG retrieval
- **Media Library** - Browse and manage generated assets with comprehensive metadata
- **Model Selection** - Choose different models for chat, image, and video generation via UI dropdowns
- **Top Navigation** - Modern navigation bar with Features, Built For, Gallery, Pricing, FAQs pages

### UI Components
- Modern Next.js 13+ with App Router
- Top Navigation Bar with logo and menu items
- Tailwind CSS + Custom Components
- Floating Chat Widget (bottom-right, opens modal overlay)
- Floating Create Button (bottom-left)
- Responsive Design with Dark Theme
- Marketing-style landing page with "Powerful Features" and "Built For" sections

## 🧱 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Local persistent vector database
- **sentence-transformers/all-MiniLM-L6-v2** - Local embeddings model
- **HuggingFace API** - Free tier image generation (FLUX.1-schnell)
- **SQLite** - Metadata storage
- **Pillow & imageio** - Image/video processing

### Frontend
- **Next.js 13+** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Axios** - API client
- **Lucide React** - Icon library
- **Framer Motion** - Animations

## 📁 Project Structure

```
/Users/tapan/Downloads/poc_updated/
├── backend/
│   ├── app/
│   │   └── main.py                    # FastAPI application
│   ├── services/
│   │   ├── image_gen.py               # Image generation service
│   │   ├── video_gen.py               # Video generation service
│   │   ├── qa_chain.py                # RAG chat service
│   │   ├── vector_store.py            # ChromaDB wrapper
│   │   ├── doc_loader.py              # Document loading
│   │   ├── text_splitter.py           # Text chunking
│   │   ├── prompt_orchestrator.py     # Prompt enhancement engine
│   │   ├── prompt_pipeline.py         # Simplified prompt API
│   │   └── negative_prompt_library.py # Negative prompt templates
│   ├── common/
│   │   ├── metadata.py                # SQLite metadata management
│   │   ├── storage.py                 # File storage utilities
│   │   └── error_handling.py          # Error handling
│   ├── config/
│   │   └── default.py                 # Configuration settings
│   └── pyproject.toml                 # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # Home page
│   │   ├── layout.tsx                 # Root layout with chat & create buttons
│   │   ├── brand-dnai/page.tsx        # Brand DNA ingestion page
│   │   ├── image/page.tsx             # Image Studio
│   │   ├── video/page.tsx             # Video Studio
│   │   ├── library/page.tsx           # Media library
│   │   └── settings/page.tsx          # Settings page
│   ├── components/
│   │   ├── ChatWidget.tsx             # Floating chat widget
│   │   └── CreateButton.tsx           # Floating create button
│   ├── lib/
│   │   └── api-client.ts              # API client wrapper
│   └── package.json                   # Node dependencies
├── data/
│   ├── chroma/                        # ChromaDB vector database (BRAND INGESTION DATA)
│   │                                   # - Stores all brand DNA embeddings and vectors
│   │                                   # - MUST be writable for brand ingestion to work
│   │                                   # - Contains SQLite files: chroma.sqlite3, etc.
│   │                                   # - Location: ./data/chroma (relative to repo root)
│   ├── uploaded_files/                # Uploaded brand documents (organized by brand)
│   ├── assets/                        # Generated assets (organized by brand/date)
│   │   └── <brand>/<YYYY-MM>/         # Assets organized by brand and month
│   ├── outputs/                       # Legacy output directory (still used)
│   │   ├── images/                    # Generated images
│   │   └── videos/                    # Generated videos
│   └── metadata.db                    # SQLite database for media metadata
├── models/
│   ├── registry.json                  # Model registry configuration
│   ├── text/                          # GGUF chat models
│   ├── image/                         # Image model cache (auto-downloaded)
│   └── video/                         # Video model cache (auto-downloaded)
```

## 🚀 Quick Start (macOS)

### Prerequisites Check
```bash
# Check Python version (should be 3.12+)
python3 --version

# Check Node.js version (should be 18+)
node --version

# Check if Poetry is installed
poetry --version

# Check if npm is installed
npm --version
```

If any tools are missing, install them:
- **Poetry**: `curl -sSL https://install.python-poetry.org | python3 -`
- **Node.js**: Download from https://nodejs.org/

### Model Registry

Models are defined in `models/registry.json`. The system supports:

**Chat Models** (GGUF format, local):
- `phi-3.5-mini` - Phi-3.5 Mini Instruct, Q4 GGUF (default)
- `llama-3.1-8b` - Llama 3.1 8B Instruct, Q4 GGUF

**Image Models**:
- `sd-turbo` - Stable Diffusion Turbo (local, default)
- `sd-1.5` - Stable Diffusion 1.5 (local)
- `sdxl-turbo` - SDXL Turbo (local)
- `flux-schnell` - FLUX.1-schnell (HF API, optional, requires HF_TOKEN)

**Video Models**:
- `svd` - Stable Video Diffusion XT 1.1 (local, default)
- `frame-composition` - Simple frame-based fallback (local)

**Embeddings**:
- `all-MiniLM-L6-v2` - sentence-transformers model (local, default)

### Step 1: Clone and Navigate
```bash
cd /Users/tapansmac/repo/poc_01-main
```

### Step 2: Start Backend Server
Open **Terminal 1** and run:
```bash
cd backend
poetry install
poetry run python scripts/download_models.py  # Downloads chat models (first time only)
poetry run python app/main.py
```
✅ Backend will start on: http://localhost:8000

### Step 3: Start Frontend Server
Open **Terminal 2** and run:
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend will start on: http://localhost:3000

### Step 4: Access the Application
Open http://localhost:3000 in your browser!

### Alternative: One-Command Start
```bash
chmod +x start.sh
./start.sh
```

## 📖 Demo Workflow

After starting the servers (see Quick Start above), follow these steps:

### Step 1: Upload Brand Knowledge
1. Go to **UCAi Brand Knowledge** page
2. For each brand, create an Excel/CSV file with exactly 2 columns:
   - **BrandKey** (or Brand_Key, Brand Key) - brand attribute name (e.g., "Brand Communication Idea", "Tone of Voice")
   - **Description** (or Desc, Brand DNA Response) - detailed description of that brand attribute
3. Each brand should have 12-13 unique brand keys with their descriptions
4. Upload each brand file individually by specifying the brand name (e.g., "Dove", "Sunsilk")
5. Click **Upload** then **Process Brand Data**
6. The system creates separate vector collections for each brand, allowing brands to share brand key names but have unique descriptions

**Sample file format:** See `sample_brand_format.csv` for the expected structure.

**Note:** To clear all brand data, use the Settings page or API endpoint `/api/settings/clear-vector-store`
4. Wait for processing (chunking and embedding)
5. Verify brand appears in the Brand Overview table

**Example CSV format:**
```csv
BrandKey,Description
Dove,"Dove is a personal care brand focused on real beauty and self-esteem..."
Axe,"Axe is a men's grooming brand targeting young adults with bold, confident messaging..."
```

### Step 4: Generate an Image

1. Navigate to **Generate Image** page (or click "Image Generation" on homepage)
2. Select a **Brand** from dropdown (if you ingested brand data)
3. Select a **Template** (optional, e.g., "Campaign Ad", "Product Feature")
4. Enter your **User Prompt** (e.g., "a beautiful sunset over mountains")
5. Optionally enter a **Negative Prompt** (e.g., "blurry, low quality")
6. Select an **Image Model** (SD Turbo, SD 1.5, or SDXL Turbo)
7. Adjust parameters (Width, Height, Steps, Seed)
8. Click **Enhance Prompt** - this will:
   - Retrieve relevant brand snippets from RAG
   - Use LLM to create a master prompt
   - Display the enhanced prompt for review
9. Review the **Master Prompt** (you can edit it if needed)
10. Click **Generate Image**
11. Wait for generation (may take 10-60 seconds depending on model)
12. View the generated image
13. Click **Mark as Final** to save to media library
14. Optionally click **Refine via Chat** to improve the prompt

### Step 5: Generate a Video

1. Navigate to **Generate Video** page
2. Select a **Brand** (optional)
3. Either:
   - Upload a base image, OR
   - Select a previously generated image from the media library
4. Enter your **User Prompt**
5. Select a **Video Model**:
   - **SVD** (Stable Video Diffusion XT 1.1) - requires base image, generates video frames
   - **Frame Composition** - simple pan/zoom effect (CPU-only fallback)
6. Adjust parameters (Frames, FPS, Duration, Resolution)
7. Click **Enhance Prompt** to get master prompt
8. Click **Generate Video**
9. Wait for generation (may take 1-5 minutes)
10. Preview the video player
11. Mark as final to save to library

### Step 6: Multi-Session Chat

1. Click the **Chat** button (floating button, bottom-right)
2. The chat modal opens (50-60% screen width)
3. Select a **Chat Model** from dropdown (Phi-3.5 Mini or Llama 3.1 8B)
4. Start a new conversation or select an existing session from sidebar
5. Ask questions about your brands:
   - "What is Dove's brand essence?"
   - "Create a prompt for a Dove campaign image"
   - "What are Axe's key messages?"
6. The chat will:
   - Retrieve relevant brand snippets via RAG
   - Build context with session memory
   - Generate responses using the selected LLM
7. Create multiple sessions for different topics
8. Rename or delete sessions as needed

### Step 7: Browse Media Library

1. Navigate to **Media Library** page
2. View all finalized assets (images and videos)
3. Filter by:
   - Brand
   - Type (image/video)
   - Date
4. Click an asset to see:
   - Full metadata (prompt, model, parameters, RAG snippets)
   - Download button
   - "Refine via Chat" button (opens chat with asset context)

### Step 8: Refine Content via Chat

1. From Media Library, click an asset
2. Click **Refine via Chat**
3. Chat modal opens with asset context pre-loaded
4. Ask for improvements:
   - "Make this more vibrant"
   - "Add more brand elements"
   - "Change the style to be more modern"
5. Use the enhanced prompt to regenerate

## 📖 Usage Guide

### 1. Ingest Brand DNA

1. Navigate to **UCAi Brand Knowledge** page
2. Upload a brand document (CSV or XLSX)
   - **Required columns**: 
     - Brand key column: `BrandKey`, `Brand_Key`, or `Brand Key` (case-insensitive)
     - Description column: `Description`, `Desc`, `Brand DNA Response`, `Brand_DNA_Response`, `DNA Response`, `DNA_Response`, or `Response` (case-insensitive)
   - CSV/XLSX files must have these columns (case-insensitive matching)
   - For PDF/TXT: Enter brand name manually (not recommended)
3. Click **Upload** then **Ingest to DNAi**
4. Wait for processing to complete
5. Verify brand appears in the Brand Overview table

### 2. Generate Images

1. Navigate to **Image Studio**
2. Select a brand from the dropdown
3. Select a model (sd-turbo, sd-1.5, sdxl-turbo, or flux-schnell)
4. Enter your prompt (e.g., "A serene spa scene with natural elements")
5. Optionally select style presets, lighting, or templates
6. Check **Use Brand Enhancement** to merge brand context
7. Click **Preview Enhanced Prompt** to see the enhanced version
8. Click **Generate Image** and wait for the result
9. Image is saved to `data/assets/<brand>/<YYYY-MM>/`
10. Download or view in Library

### 3. Generate Videos

1. Navigate to **Video Studio**
2. First generate an image in Image Studio (or use existing)
3. Enter the image path (e.g., `/Users/tapan/Downloads/poc_updated/data/outputs/images/image_20241114_104816795.png`)
4. Select a brand and enter motion prompt
5. Click **Generate Video**
6. Wait for processing (this takes longer than images)
7. Video will appear when complete

### 4. Chat with Brand DNA

1. Click the **chat bubble** icon in the bottom-right corner
2. Ask questions about your brands (e.g., "What is Dove's brand essence?")
3. View answers with expandable sources showing Brand DNA snippets
4. Chat history persists during the session

### 5. Browse Library

1. Navigate to **Library**
2. Filter by All / Images / Videos
3. Click **Download** to save files
4. Click **Eye** icon to view metadata

## 🔧 Configuration

### Backend Configuration

Models are configured in `models/registry.json`. Default model IDs can be set via environment variables:

```bash
CHAT_MODEL_ID=phi-3.5-mini      # or llama-3.1-8b
IMAGE_MODEL_ID=sd-turbo         # or sd-1.5, sdxl-turbo, flux-schnell
VIDEO_MODEL_ID=svd              # or frame-composition
EMBEDDING_MODEL_ID=all-MiniLM-L6-v2
HF_TOKEN=your_token_here        # Only needed for flux-schnell (optional, hardcoded in config for POC)
```

Or edit `backend/config/default.py` to change defaults.

**Note**: 
- Local models (sd-turbo, sd-1.5, sdxl-turbo, svd) work without API keys
- `flux-schnell` requires HF_TOKEN and uses HuggingFace Inference API (token is hardcoded in config for POC)
- Chat models require GGUF files in `models/text/` (nested directories supported)
- Models are automatically filtered in `/api/models` endpoint - HF models are hidden if token not available

### Frontend Configuration

Edit `/frontend/lib/api-client.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

## 🛠️ API Endpoints

### Brand Management
- `GET /api/brands` - List all brands with stats
- `POST /api/brands/upload` - Upload brand document
- `POST /api/brands/ingest` - Ingest uploaded document
- `GET /api/brands/{brand}/snippet` - Get sample snippet

### Content Generation
- `POST /api/image/generate` - Generate image
- `POST /api/video/generate` - Generate video (async)
- `GET /api/video/job/{job_id}` - Check video generation status

### Prompt Enhancement
- `POST /api/prompt/preview` - Preview enhanced prompt
- `GET /api/prompt/templates` - Get available templates
- `GET /api/prompt/presets` - Get style/lighting presets

### Chat & RAG
- `POST /api/chat` - Ask question using RAG (legacy endpoint)
- `GET /api/chat/sessions` - List all chat sessions
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions/{id}` - Get session with messages
- `POST /api/chat/sessions/{id}/messages` - Send message in session (supports model_id)
- `PATCH /api/chat/sessions/{id}` - Update session (rename, brand)
- `DELETE /api/chat/sessions/{id}` - Delete session

### Models
- `GET /api/models/registry` - Get complete model registry
- `GET /api/models?type=chat|image|video` - Get filtered list of models

### Media Library
- `GET /api/media` - List all media items
- `GET /api/media/{item_id}` - Get item details
- `GET /api/media/{item_id}/download` - Download media file

### Utilities
- `GET /healthz` - Health check
- `POST /api/settings/clear-vector-store` - Clear all brand data
- `POST /api/settings/clear-outputs` - Delete all generated files

## 🎨 Prompt Enhancement Pipeline

The prompt enhancement system merges user prompts with Brand DNA context:

1. **User Prompt** - Original description
2. **Brand DNA Retrieval** - Query vector store for relevant snippets
3. **Context Extraction** - Extract tone, key messages, style keywords
4. **Template Application** - Apply optional templates (Product Hero, Lifestyle, etc.)
5. **Style & Lighting** - Add preset enhancements (Cinematic, Minimal, etc.)
6. **Master Prompt** - Final enhanced prompt sent to generation engine
7. **Negative Prompt** - Automatically generated to avoid unwanted elements

### Example Enhancement

**User Prompt:**
```
A product photo of a moisturizer on a marble surface
```

**Enhanced Prompt (with Dove brand + Cinematic style):**
```
Professional marketing campaign photography: A product photo of a moisturizer on a marble surface. 
Brand context: Dove - known for gentle care, real beauty philosophy, nourishing ingredients. 
Style: gentle, authentic, caring. Cinematic lighting, film grain, shallow depth of field, 
dramatic composition, professional color grading. High quality, detailed, professional, 8k, 
vibrant, well-lit, commercial style, product showcase
```

## 🧪 Testing the Integration

See the **End-to-End Demo Workflow** section above for detailed step-by-step instructions.

### Quick Test Checklist

- [ ] Models downloaded successfully (`models/text/` contains GGUF files)
- [ ] Backend starts without errors (check `http://localhost:8000/healthz`)
- [ ] Frontend starts without errors (check `http://localhost:3000`)
- [ ] Top navigation appears on all pages
- [ ] Landing page shows "Powerful Features" and "Built For" sections
- [ ] Brand ingestion works (upload CSV/XLSX, verify in Brand Overview)
- [ ] Chat modal opens from floating button
- [ ] Chat model dropdown shows available models
- [ ] Image generation works with model selection
- [ ] Video generation works with model selection
- [ ] Prompt enhancer returns master_prompt
- [ ] Media library displays finalized assets
- [ ] "Refine via Chat" opens chat with asset context

## 🐛 Troubleshooting

### Backend Issues

**ChromaDB not persisting:**
- Ensure `/data/chroma/` directory exists
- Check file permissions

**Image generation fails:**
- Verify model is selected in dropdown
- Check if model requires HF_TOKEN (flux-schnell)
- For local models (sd-turbo, sd-1.5, sdxl-turbo), ensure diffusers is installed
- Try reducing image size or steps for CPU-only systems
- Check backend logs for specific error messages

**Chat model not found:**
- Verify GGUF files are in `models/text/` (nested directories supported)
- Run `poetry run python backend/scripts/download_models.py`
- Check model paths in `models/registry.json` match actual file locations
- Backend will return clear error: `{"error": "model_not_installed", "message": "...", "instructions": "..."}`

**Embeddings model download slow:**
- First run downloads ~90MB model
- Check internet connection
- Model caches in `~/.cache/huggingface/`

### Frontend Issues

**Cannot connect to backend:**
- Verify backend is running on port 8000
- Check CORS is enabled in main.py
- Update API_URL if needed

**Components not rendering:**
- Clear `.next` cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

**TypeScript errors:**
- Run type check: `npx tsc --noEmit`

## 📊 Data Persistence

All data is stored locally:

- **ChromaDB collections** - `/data/chroma/`
- **SQLite metadata** - `/data/metadata.db`
- **Uploaded files** - `/data/uploaded_files/{brand}/`
- **Generated assets** - `/data/assets/{brand}/{YYYY-MM}/` (images and videos)
- **Legacy outputs** - `/data/outputs/images/` and `/data/outputs/videos/` (still used)
- **GGUF models** - `models/text/{model-dir}/{filename}.gguf` (nested directories)
- **Model cache** - `~/.cache/huggingface/` (for diffusers models)

To reset everything:
1. Go to Settings page
2. Click "Clear Vector Store" (removes all brand data)
3. Click "Clear Generated Outputs" (removes all images/videos)

## 🌟 Key Differences from Legacy

### What's New
✅ Modern Next.js frontend (replaces Streamlit)
✅ Top navigation bar with marketing pages (Features, Built For, Gallery, Pricing, FAQs)
✅ Landing page redesign with "Powerful Features" and "Built For" sections
✅ Prompt orchestrator with templates & presets
✅ Negative prompt library
✅ Floating chat widget (opens modal overlay, 50-60% screen width)
✅ Multi-session chat with model selection dropdown
✅ Floating create button (quick access to studios)
✅ Enhanced UI with Tailwind CSS
✅ Real-time prompt preview before generation
✅ Model selection dropdowns for chat, image, and video
✅ Better error handling with clear model_not_installed messages
✅ Support for Phi-3.5 Mini and Llama 3.1 8B with proper chat templates
✅ Updated model registry with nested directory support
✅ HF token validation and model filtering

### What's Preserved
✅ All working backend logic from legacy repo
✅ ChromaDB vector store integration
✅ HuggingFace image generation
✅ Frame composition video generation
✅ RAG chat with brand-scoped retrieval
✅ Brand stats and metadata tracking

## 📝 License

This is a proof-of-concept project using free/OSS tools only.

## 🤝 Contributing

This is a POC project. For production use:
- Add authentication
- Implement rate limiting
- Use environment variables for secrets
- Add comprehensive error logging
- Implement job queuing for video generation
- Add unit and integration tests
- Set up CI/CD pipeline

## 🎉 Credits

Built with:
- FastAPI
- Next.js
- ChromaDB
- HuggingFace Inference API
- sentence-transformers
- And many other open-source libraries

---

## 🛠️ Complete macOS Setup Guide

### Prerequisites Installation
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12+
brew install python@3.12

# Install Node.js 18+
brew install node

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Verify installations
python3 --version  # Should show 3.12.x or higher
node --version     # Should show 18.x or higher
poetry --version   # Should show version info
```

### Repository Setup
```bash
# Navigate to your workspace
cd /Users/tapansmac/repo

# Clone or navigate to the project
cd poc_01-main

# Copy environment template
cp .env.example .env
# Edit .env if you have HF_TOKEN for FLUX model (optional)
```

### Backend Setup
```bash
# Navigate to backend
cd backend

# Install Python dependencies
poetry install

# Download chat models (required, ~7GB total)
poetry run python scripts/download_models.py

# Start backend server
poetry run python app/main.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
```

### Frontend Setup
```bash
# Open new terminal window
cd /Users/tapansmac/repo/poc_01-main/frontend

# Install Node dependencies
npm install

# Start frontend server
npm run dev &
FRONTEND_PID=$!

echo "Frontend started with PID: $FRONTEND_PID"
```

### Verification
```bash
# Wait 10 seconds for servers to start
sleep 10

# Test backend
curl http://localhost:8000/healthz

# Test frontend
curl -s -I http://localhost:3000 | head -1

# Open browser
open http://localhost:3000
```

### Stopping Servers
```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9

# Or use the PIDs saved earlier
kill $BACKEND_PID $FRONTEND_PID
```

## 🔧 Troubleshooting

### Common Issues

**Brand Ingestion fails with "readonly database" error:**

This error occurs when ChromaDB cannot write to the vector database directory. The system automatically fixes permissions, but if it persists:

1. **Check directory permissions:**
   ```bash
   ls -la data/chroma
   # Should show: drwxrwxrwx (777 permissions)
   ```

2. **Fix permissions manually:**
   ```bash
   chmod -R 777 data/chroma
   chmod -R 777 data/
   ```

3. **Verify directory is writable:**
   ```bash
   touch data/chroma/.test_write && rm data/chroma/.test_write
   # Should succeed without errors
   ```

4. **Check ChromaDB health:**
   ```bash
   curl http://localhost:8000/api/brands/health
   curl http://localhost:8000/api/brands/diagnose
   ```

5. **Database locations:**
   - ChromaDB vector database: `./data/chroma/` (stores all brand DNA embeddings)
   - SQLite metadata: `./data/metadata.db` (stores media metadata)
   - Both must be writable for the application to function

6. **If using Docker or containerized environment:**
   - Ensure `./data` directory is mounted as a writable volume
   - Check that the directory is not on a read-only filesystem

**Poetry not found:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Ports already in use:**
```bash
# Check what's using port 8000/3000
lsof -i:8000
lsof -i:3000

# Kill processes on these ports
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

**npm install fails:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Model download fails:**
- Check your internet connection
- Models are ~2-7GB each, ensure you have space
- Manual download: Visit https://huggingface.co/bartowski and download GGUF files

**Image/Video generation slow:**
- CPU works but is slow (10-60 seconds per image, 1-5 minutes per video)
- GPU acceleration requires CUDA-compatible GPU

**Backend health check fails:**
```bash
cd backend
poetry run python app/main.py
# Check logs for errors
```

**Frontend build fails:**
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Verify Everything is Running

```bash
# Test backend health
curl http://localhost:8000/healthz

# Test frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Test API endpoints
curl http://localhost:8000/api/brands
curl http://localhost:8000/api/models?type=chat
```

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 18+
- Poetry (Python package manager)
- npm (Node package manager)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
poetry install
```

3. Create a `.env` file in the `backend/` directory:
```bash
# backend/.env

# HuggingFace API token (required for FLUX image generation)
HF_TOKEN=your_huggingface_token_here

# Optional: Override data directory (default: ./data)
# DATA_DIR_OVERRIDE=/path/to/data

# Optional: Override database path (default: ./data/metadata.db)
# DB_PATH=/path/to/metadata.db

# Optional: Future model platform integration
# MODEL_API_URL=https://your-model-api.com
# MODEL_API_KEY=your_api_key

# Model selection (defaults shown)
CHAT_MODEL_ID=phi-3.5-mini
IMAGE_MODEL_ID=flux-schnell
VIDEO_MODEL_ID=composition
EMBEDDING_MODEL_ID=all-MiniLM-L6-v2

# API server settings
API_HOST=0.0.0.0
API_PORT=8000

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

4. Download chat models (optional, for local LLM chat):
```bash
poetry run python scripts/download_models.py
```

5. Start the backend server:
```bash
poetry run python app/main.py
```

The backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Create a `.env.local` file in the `frontend/` directory:
```bash
# frontend/.env.local

# Backend API URL (required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Start the frontend development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

### Environment Variables Reference

#### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes* | - | HuggingFace API token for FLUX image generation |
| `DATA_DIR_OVERRIDE` | No | `./data` | Override default data directory path |
| `DB_PATH` | No | `./data/metadata.db` | Override default SQLite database path |
| `MODEL_API_URL` | No | - | External model API endpoint (future use) |
| `MODEL_API_KEY` | No | - | External model API key (future use) |
| `CHAT_MODEL_ID` | No | `phi-3.5-mini` | Default chat model ID |
| `IMAGE_MODEL_ID` | No | `flux-schnell` | Default image model ID |
| `VIDEO_MODEL_ID` | No | `composition` | Default video model ID |
| `EMBEDDING_MODEL_ID` | No | `all-MiniLM-L6-v2` | Default embedding model ID |
| `API_HOST` | No | `0.0.0.0` | API server host |
| `API_PORT` | No | `8000` | API server port |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins |
| `DATABASE_URL` | No | `sqlite:///./data/metadata.db` | SQLite database URL |

*Required for FLUX image generation via HuggingFace API

#### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost:8000` | Backend API base URL |

---

## Deploying to Azure App Service

### Architecture Overview

The application consists of two Azure Web Apps:
1. **Backend** - Python FastAPI application on Linux Web App
2. **Frontend** - Next.js application on Linux Web App (Node.js)

### Backend Deployment

#### 1. Create Azure Web App (Linux, Python)

```bash
# Create resource group
az group create --name rg-ucai-poc --location eastus

# Create App Service plan
az appservice plan create \
  --name asp-ucai-backend \
  --resource-group rg-ucai-poc \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --name ucai-backend \
  --resource-group rg-ucai-poc \
  --plan asp-ucai-backend \
  --runtime "PYTHON:3.12"
```

#### 2. Configure Environment Variables

Set the following environment variables in Azure App Service Configuration:

```bash
# Required
HF_TOKEN=your_huggingface_token_here
DATA_DIR_OVERRIDE=/home/site/wwwroot/data

# Optional (with recommended values)
DB_PATH=/home/site/wwwroot/data/metadata.db
CHAT_MODEL_ID=phi-3.5-mini
IMAGE_MODEL_ID=flux-schnell
VIDEO_MODEL_ID=composition
EMBEDDING_MODEL_ID=all-MiniLM-L6-v2
CORS_ORIGINS=https://your-frontend-app.azurewebsites.net

# Future model platform integration (set via Azure Key Vault)
# MODEL_API_URL=https://your-model-api.com
# MODEL_API_KEY=your_api_key
```

#### 3. Configure Startup Command

In Azure Portal > Web App > Configuration > General settings > Startup Command:

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or set via Azure CLI:

```bash
az webapp config set \
  --name ucai-backend \
  --resource-group rg-ucai-poc \
  --startup-file "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
```

#### 4. Deploy Backend Code

Option A: Deploy via ZIP:
```bash
cd backend
zip -r ../backend.zip . -x "*.pyc" -x "__pycache__/*" -x ".env"
az webapp deployment source config-zip \
  --name ucai-backend \
  --resource-group rg-ucai-poc \
  --src ../backend.zip
```

Option B: Deploy via Git (see Azure DevOps pipelines below)

### Frontend Deployment

#### 1. Create Azure Web App (Linux, Node.js)

```bash
# Create App Service plan (can share with backend)
az appservice plan create \
  --name asp-ucai-frontend \
  --resource-group rg-ucai-poc \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --name ucai-frontend \
  --resource-group rg-ucai-poc \
  --plan asp-ucai-frontend \
  --runtime "NODE:18-lts"
```

#### 2. Configure Environment Variables

Set the following environment variables in Azure App Service Configuration:

```bash
NEXT_PUBLIC_API_BASE_URL=https://ucai-backend.azurewebsites.net
```

#### 3. Build and Deploy

```bash
cd frontend
npm install
npm run build

# Deploy the .next folder and other required files
zip -r ../frontend.zip .next public package.json next.config.js node_modules
az webapp deployment source config-zip \
  --name ucai-frontend \
  --resource-group rg-ucai-poc \
  --src ../frontend.zip
```

### Using Azure Key Vault for Secrets

For production deployments, store sensitive values in Azure Key Vault:

```bash
# Create Key Vault
az keyvault create \
  --name kv-ucai-poc \
  --resource-group rg-ucai-poc \
  --location eastus

# Add secrets
az keyvault secret set --vault-name kv-ucai-poc --name HF-TOKEN --value "your_token"
az keyvault secret set --vault-name kv-ucai-poc --name MODEL-API-KEY --value "your_key"

# Enable managed identity for Web App
az webapp identity assign --name ucai-backend --resource-group rg-ucai-poc

# Grant Key Vault access to Web App
az keyvault set-policy \
  --name kv-ucai-poc \
  --object-id <webapp-principal-id> \
  --secret-permissions get list
```

Then reference secrets in App Settings:
```
HF_TOKEN=@Microsoft.KeyVault(SecretUri=https://kv-ucai-poc.vault.azure.net/secrets/HF-TOKEN/)
MODEL_API_KEY=@Microsoft.KeyVault(SecretUri=https://kv-ucai-poc.vault.azure.net/secrets/MODEL-API-KEY/)
```

---

**Ready to generate brand-true content!** 🚀
