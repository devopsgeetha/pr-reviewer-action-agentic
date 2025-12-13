#!/bin/bash
# Test script to verify OpenAI API connection

set -e

echo "🧪 OpenAI API Connection Test"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found"
    echo "Please copy backend/.env.example to backend/.env and configure it"
    exit 1
fi

# Source environment variables
export $(cat backend/.env | grep -v '^#' | xargs)

# Check required variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set in .env"
    exit 1
fi

if [ -z "$OPENAI_MODEL" ]; then
    export OPENAI_MODEL="gpt-4o"
fi

echo "✅ Environment variables loaded"
echo "  - API URL: https://api.openai.com/v1"
echo "  - Model: $OPENAI_MODEL"
echo "  - API Key: ${OPENAI_API_KEY:0:10}..."
echo ""

# Test 1: Check API endpoint
echo "📡 Test 1: Testing API endpoint..."

API_ENDPOINT="https://api.openai.com/v1/chat/completions"

echo "  Using endpoint: $API_ENDPOINT"
echo ""

# Test with verbose output for debugging
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_ENDPOINT" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$OPENAI_MODEL\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Say hello\"}],
        \"max_tokens\": 10
    }" 2>&1)

HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
    echo "✅ API endpoint is reachable (HTTP $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "400" ]; then
    echo "⚠️  Bad Request (HTTP 400) - Response:"
    echo "$RESPONSE_BODY" | head -5
elif [ "$HTTP_STATUS" = "401" ]; then
    echo "❌ Authentication failed (HTTP 401) - check your API key"
    echo "$RESPONSE_BODY" | head -5
    exit 1
elif [ "$HTTP_STATUS" = "404" ]; then
    echo "❌ API endpoint not found (HTTP 404) - check API URL"
    echo "$RESPONSE_BODY" | head -5
    exit 1
elif [ "$HTTP_STATUS" = "429" ]; then
    echo "⚠️  Rate limit exceeded (HTTP 429) - API key is valid but quota exceeded"
    echo "$RESPONSE_BODY" | head -5
elif [ "$HTTP_STATUS" = "500" ] || [ "$HTTP_STATUS" = "502" ] || [ "$HTTP_STATUS" = "503" ]; then
    echo "⚠️  OpenAI service error (HTTP $HTTP_STATUS) - API is temporarily unavailable"
    echo "$RESPONSE_BODY" | head -5
else
    echo "⚠️  Unexpected HTTP status: $HTTP_STATUS"
    echo "Response:"
    echo "$RESPONSE_BODY" | head -5
fi

echo ""

# Test 2: Test Python import
echo "🐍 Test 2: Testing Python imports..."
cd backend
python3 -c "
import sys
try:
    from app.services.llm_service import LLMService
    print('✅ LLM service imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" || exit 1

echo ""

# Test 3: Test LLM service initialization
echo "🤖 Test 3: Testing LLM service initialization..."
python3 -c "
import os
import sys
os.environ['OPENAI_API_KEY'] = '$OPENAI_API_KEY'
os.environ['OPENAI_MODEL'] = '$OPENAI_MODEL'

try:
    from app.services.llm_service import LLMService
    service = LLMService()
    if service.llm:
        print('✅ LLM service initialized successfully')
        print(f'   Model: {service.model}')
    else:
        print('❌ LLM service initialization failed')
        sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

echo ""

# Test 4: Test simple code analysis
echo "📝 Test 4: Testing simple code analysis..."
python3 -c "
import os
import sys
os.environ['OPENAI_API_KEY'] = '$OPENAI_API_KEY'
os.environ['OPENAI_MODEL'] = '$OPENAI_MODEL'

try:
    from app.services.llm_service import LLMService
    service = LLMService()
    
    # Test code snippet
    result = service.analyze_code_changes(
        code='def test():\n    print(\"hello\")',
        filename='test.py',
        language='python'
    )
    
    if 'issues' in result or 'suggestions' in result:
        print('✅ Code analysis works')
        print(f'   Found {len(result.get(\"issues\", []))} issues')
        print(f'   Found {len(result.get(\"suggestions\", []))} suggestions')
    else:
        print('⚠️  Code analysis returned unexpected format')
        print(f'   Result keys: {list(result.keys())}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

cd ..

echo ""
echo "================================"
echo "🎉 All tests passed!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Run 'cd backend && python init_rag.py' to initialize RAG"
echo "  2. Run 'cd backend && python run.py' to start the server"
echo "  3. Create a GitHub Action workflow to use this in PRs"
echo ""

