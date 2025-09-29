#!/bin/bash

set -e

# Check Python version
PY_VERSION=$(python3 --version | cut -d" " -f2)
REQUIRED_VERSION="3.13.2"

if [[ "$PY_VERSION" != "$REQUIRED_VERSION" ]]; then
    echo "⚠️ Python version mismatch. Found $PY_VERSION, but expected $REQUIRED_VERSION"
    echo "Proceeding anyway..."
fi

# 1. Install uv
echo "📦 Installing uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv installed."

# 2. Create virtual environment
echo "📁 Creating virtual environment with uv..."
uv venv
source .venv/bin/activate

# 3. Write pyproject.toml
cat > pyproject.toml <<EOF
[project]
name = "ai-news-summariser"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = "==3.13.2"
dependencies = [
    "beautifulsoup4==4.13.5",
    "crewai==0.193.0",
    "dataclasses==0.8",
    "dotenv==0.9.9",
    "fastapi==0.117.1",
    "langchain==0.3.27",
    "langchain-google-genai==2.1.12",
    "langchain-openai==0.3.33",
    "langgraph==0.6.7",
    "motor==3.7.1",
    "pathlib==1.0.1",
    "pydantic==2.11.9",
    "sseclient==0.0.27",
    "tavily-python==0.7.12",
    "torch==2.8.0",
    "transformers==4.56.1",
    "uvicorn==0.36.0",
]
EOF

# 4. Compile and install dependencies
echo "📦 Compiling dependencies from pyproject.toml..."
uv pip compile pyproject.toml --output-file=requirements.txt

echo "📦 Installing dependencies from requirements.txt..."
uv pip install -r requirements.txt

echo "✅ All set! Activate with: source .venv/bin/activate"
