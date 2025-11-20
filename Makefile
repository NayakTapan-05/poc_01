.PHONY: help install backend frontend dev clean

help:
	@echo "Brand DNAi Content Studio - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install all dependencies (backend + frontend)"
	@echo ""
	@echo "Run Services:"
	@echo "  make backend        Start FastAPI backend (port 8000)"
	@echo "  make frontend       Start Next.js frontend (port 3000)"
	@echo "  make dev            Start both backend and frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove generated files and caches"
	@echo "  make reset-data     Clear all brand data and outputs"
	@echo ""

install:
	@echo "Installing backend dependencies..."
	cd backend && poetry install
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

backend:
	@echo "Starting FastAPI backend on http://localhost:8000..."
	cd backend && poetry run python app/main.py

frontend:
	@echo "Starting Next.js frontend on http://localhost:3000..."
	cd frontend && npm run dev

dev:
	@echo "Starting both backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@make -j2 backend frontend

clean:
	@echo "Cleaning up..."
	rm -rf backend/__pycache__
	rm -rf backend/**/__pycache__
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	@echo "✅ Cleanup complete!"

reset-data:
	@echo "⚠️  WARNING: This will delete all brand data and generated outputs!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -rf data/chroma/*
	rm -f data/metadata.db
	rm -rf data/outputs/images/*
	rm -rf data/outputs/videos/*
	@echo "✅ Data reset complete!"

test-backend:
	@echo "Running backend tests..."
	cd backend && poetry run pytest

check-backend:
	@echo "Checking backend health..."
	@curl -s http://localhost:8000/healthz || echo "Backend not running!"

check-frontend:
	@echo "Checking frontend..."
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend is running" || echo "❌ Frontend not running!"
