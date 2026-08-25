#!/usr/bin/env bash
# Quick start script for Deutsch News

set -e

echo "🚀 Deutsch News - Quick Start"
echo "=============================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ollama
    else
        echo "Please install Ollama manually: https://ollama.ai"
        exit 1
    fi
fi

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "🔄 Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Pull model
echo "📥 Pulling Llama 3.1 model (this may take a while)..."
ollama pull llama3.1:8b

# Install Python deps
echo "📦 Installing Python dependencies..."
cd "$(dirname "$0")/.."
pip3 install -r requirements.txt

# Generate site
echo "🏗️  Generating site..."
python3 scripts/run.py

echo ""
echo "✅ Done! Open frontend/index.html in your browser"
echo "🌐 For GitHub Pages: push frontend/ contents to gh-pages branch"