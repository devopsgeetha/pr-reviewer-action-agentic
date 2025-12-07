#!/bin/bash
# Pre-commit checklist for production readiness

set -e

echo "🔍 Production Readiness Check"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES=0

# Check 1: No sensitive data
echo -n "1. Checking for sensitive data... "
SENSITIVE_FILES=$(grep -rl "sk-[a-zA-Z0-9]\{32,\}\|ghp_[a-zA-Z0-9]\{36,\}" \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude=".env" \
    --exclude="*.sh" \
    . 2>/dev/null | grep -v ".env.example" | grep -v ".nfs" || true)

if [ -n "$SENSITIVE_FILES" ]; then
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Found potential sensitive data in:"
    echo "$SENSITIVE_FILES" | head -5
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✅ PASSED${NC}"
fi

# Check 2: No __pycache__ or .pyc files
echo -n "2. Checking for Python cache files... "
if find . -name "__pycache__" -o -name "*.pyc" 2>/dev/null | grep -v ".venv" | grep -q .; then
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Found cache files. Run: find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✅ PASSED${NC}"
fi

# Check 3: .env is gitignored
echo -n "3. Checking .env in gitignore... "
if grep -q "^\.env$" .gitignore 2>/dev/null || grep -q "^\.env$" backend/.gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Add '.env' to .gitignore"
    ISSUES=$((ISSUES + 1))
fi

# Check 4: .env.example exists
echo -n "4. Checking .env.example exists... "
if [ -f "backend/.env.example" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Create backend/.env.example with placeholder values"
    ISSUES=$((ISSUES + 1))
fi

# Check 5: No log files
echo -n "5. Checking for log files... "
if find . -name "*.log" -not -path "./.venv/*" 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo "   Found log files (will be ignored by git):"
    find . -name "*.log" -not -path "./.venv/*" 2>/dev/null
else
    echo -e "${GREEN}✅ PASSED${NC}"
fi

# Check 6: Required files exist
echo -n "6. Checking required files... "
REQUIRED_FILES=("README.md" "LICENSE" "action.yml" "Dockerfile.action" "backend/requirements.txt")
MISSING=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING+=("$file")
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Missing files:"
    for file in "${MISSING[@]}"; do
        echo "   - $file"
    done
    ISSUES=$((ISSUES + 1))
fi

# Check 7: Test script works (optional)
echo -n "7. Testing OpenAI connection (optional)... "
if [ -f "backend/.env" ] && [ -f "test-openai-connection.sh" ]; then
    if ./test-openai-connection.sh > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠️  SKIPPED${NC} (requires valid .env with OPENAI_API_KEY)"
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC} (no .env file or test script)"
fi

echo ""
echo "=============================="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Ready to commit to GitHub:"
    echo "  git add ."
    echo "  git commit -m 'Your commit message'"
    echo "  git push origin main"
    exit 0
else
    echo -e "${RED}❌ Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    exit 1
fi

