#!/bin/bash

# Setup script for GraphRAG + Multi-Agent Debate System
# This script sets up both backend and frontend

set -e  # Exit on error

echo "🚀 Setting up GraphRAG + Multi-Agent Debate System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your credentials before continuing."
    echo ""
    echo "Required environment variables:"
    echo "  - NEO4J_URI"
    echo "  - NEO4J_USERNAME"
    echo "  - NEO4J_PASSWORD"
    echo "  - GEMINI_API_KEY"
    echo ""
    read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
fi

# Backend Setup
echo "📦 Setting up Backend..."
cd backend

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "  Creating virtual environment..."
python3 -m venv venv

echo "  Activating virtual environment..."
source venv/bin/activate

echo "  Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete!"
echo ""

cd ..

# Frontend Setup
echo "📦 Setting up Frontend..."
cd frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "  Installing Node dependencies..."
npm install

echo "✅ Frontend setup complete!"
echo ""

cd ..

# Summary
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Make sure your .env file is configured with:"
echo "     - Neo4j AuraDB credentials"
echo "     - Google Gemini API key"
echo ""
echo "  2. Start the backend:"
echo "     cd backend"
echo "     source venv/bin/activate"
echo "     uvicorn main:app --reload"
echo ""
echo "  3. In a new terminal, start the frontend:"
echo "     cd frontend"
echo "     npm run dev"
echo ""
echo "  4. Open http://localhost:3000 in your browser"
echo ""
echo "  5. (Optional) Clear the graph and ingest the mock documents:"
echo "     cd backend"
echo "     source venv/bin/activate"
echo "     python test_ingestion.py"

# Made with Bob
