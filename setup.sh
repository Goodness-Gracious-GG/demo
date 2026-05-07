#!/bin/bash
# Setup and validation script for Code Twins backend

set -e  # Exit on error

echo "=========================================="
echo "  Code Twins - Backend Setup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your API keys:"
    echo "  cp .env.example .env"
    exit 1
fi

echo "✓ .env file found"

# Check required environment variables
echo ""
echo "Checking required environment variables..."

required_vars=("GEMINI_API_KEY" "SUPABASE_URL" "SUPABASE_ANON_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    value=$(grep "^${var}=" .env 2>/dev/null | cut -d'=' -f2-)
    if [ -z "$value" ] || [ "$value" = "your_*_here" ]; then
        echo "❌ $var is not set or has placeholder value"
        missing_vars+=("$var")
    else
        echo "✓ $var is configured"
    fi
done

# Check Vite frontend variables (optional but recommended)
echo ""
echo "Checking frontend configuration..."

vite_vars=("VITE_SUPABASE_URL" "VITE_SUPABASE_ANON_KEY")
for var in "${vite_vars[@]}"; do
    value=$(grep "^${var}=" .env 2>/dev/null | cut -d'=' -f2-)
    if [ -z "$value" ] || [ "$value" = "your_*_here" ]; then
        echo "⚠️  $var is not set (frontend may not work properly)"
    else
        echo "✓ $var is configured"
    fi
done

# If any required vars are missing, exit
if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required environment variables: ${missing_vars[*]}"
    echo "Please edit your .env file and add the missing values."
    echo "You can use .env.example as a template."
    exit 1
fi

echo ""
echo "✓ All required environment variables are set"
echo ""
echo "Starting backend server..."
echo "Server will run on http://0.0.0.0:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
