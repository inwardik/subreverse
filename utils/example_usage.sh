#!/bin/bash
# Example usage scripts for evaluate.py

# Exit on error
set -e

echo "=== SubReverse Evaluation Examples ==="
echo ""

# Check if files exist
if [ ! -f "$1" ] || [ ! -f "$2" ]; then
    echo "Usage: ./example_usage.sh <en_srt_file> <ru_srt_file>"
    echo ""
    echo "Example:"
    echo "  ./example_usage.sh ../data/movie_en.srt ../data/movie_ru.srt"
    exit 1
fi

EN_FILE=$1
RU_FILE=$2

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  Warning: OPENROUTER_API_KEY not set"
    echo "   OpenRouter examples will be skipped"
    echo "   Set it with: export OPENROUTER_API_KEY='sk-or-v1-...'"
    echo ""
    SKIP_OPENROUTER=1
else
    SKIP_OPENROUTER=0
    echo "✅ OpenRouter API key found"
    echo ""
fi

# Example 1: Quick evaluation with OpenRouter
if [ $SKIP_OPENROUTER -eq 0 ]; then
    echo "Example 1: Quick evaluation (5 pairs) with OpenRouter Claude 3.5 Sonnet"
    echo "Command: python evaluate.py $EN_FILE $RU_FILE 5 --provider openrouter"
    echo ""
    python evaluate.py "$EN_FILE" "$RU_FILE" 5 --provider openrouter
    echo ""
    echo "Press Enter to continue..."
    read
fi

# Example 2: LMStudio local model (if available)
echo "Example 2: Evaluation with LMStudio (local model)"
echo "Command: python evaluate.py $EN_FILE $RU_FILE 3 --provider lmstudio"
echo ""
echo "Note: Make sure LMStudio is running on localhost:1234"
echo "Press Enter to try, or Ctrl+C to skip..."
read

python evaluate.py "$EN_FILE" "$RU_FILE" 3 --provider lmstudio || {
    echo "⚠️  LMStudio connection failed. Make sure:"
    echo "   1. LMStudio is installed and running"
    echo "   2. Local server is started in LMStudio"
    echo "   3. Server is listening on localhost:1234"
    echo ""
}

# Example 3: Reproducible evaluation with seed
if [ $SKIP_OPENROUTER -eq 0 ]; then
    echo ""
    echo "Example 3: Reproducible evaluation with fixed seed"
    echo "Command: python evaluate.py $EN_FILE $RU_FILE 5 --provider openrouter --seed 42"
    echo ""
    python evaluate.py "$EN_FILE" "$RU_FILE" 5 --provider openrouter --seed 42
fi

# Example 4: Using different OpenRouter model
if [ $SKIP_OPENROUTER -eq 0 ]; then
    echo ""
    echo "Example 4: Using Claude 3 Haiku (faster, cheaper)"
    echo "Command: python evaluate.py $EN_FILE $RU_FILE 5 --provider openrouter --model anthropic/claude-3-haiku"
    echo ""
    python evaluate.py "$EN_FILE" "$RU_FILE" 5 --provider openrouter --model anthropic/claude-3-haiku
fi

echo ""
echo "=== Examples completed! ==="
