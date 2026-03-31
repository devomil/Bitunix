#!/bin/bash
# Quick security setup script for Bitunix trading bot
# Run this FIRST before using the bot

set -e  # Exit on error

echo "🔒 Bitunix Trading Bot - Security Setup"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Run this script from the project root directory${NC}"
    exit 1
fi

echo "📋 Step 1: Checking .gitignore"
echo "--------------------------------"
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}Creating .gitignore...${NC}"
    cat > .gitignore << 'EOF'
# Environment variables
.env
.env.*
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/
EOF
    echo -e "${GREEN}✓ .gitignore created${NC}"
else
    # Check if .env is in .gitignore
    if grep -q "^\.env$" .gitignore; then
        echo -e "${GREEN}✓ .env already in .gitignore${NC}"
    else
        echo -e "${YELLOW}Adding .env to .gitignore...${NC}"
        echo ".env" >> .gitignore
        echo ".env.*" >> .gitignore
        echo "*.env" >> .gitignore
        echo -e "${GREEN}✓ .env added to .gitignore${NC}"
    fi
fi
echo ""

echo "📋 Step 2: Creating .env.example template"
echo "------------------------------------------"
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# Bitunix API Credentials
# Get these from: https://bitunix.com/api-management
BITUNIX_API_KEY=your_api_key_here
BITUNIX_API_SECRET=your_api_secret_here

# Trading Settings
TRADING_ENABLED=false
DRY_RUN=true

# Risk Limits (USD)
MAX_ORDER_USD=100
MAX_POSITION_USD=500
MAX_DAILY_LOSS_USD=50

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
EOF
    echo -e "${GREEN}✓ .env.example created${NC}"
else
    echo -e "${GREEN}✓ .env.example already exists${NC}"
fi
echo ""

echo "📋 Step 3: Creating your .env file"
echo "-----------------------------------"
if [ -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file already exists${NC}"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping .env creation"
    else
        cp .env.example .env
        echo -e "${GREEN}✓ .env created from template${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and add your real API keys!${NC}"
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ .env created from template${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and add your real API keys!${NC}"
fi
echo ""

echo "📋 Step 4: Checking Git for leaked secrets"
echo "-------------------------------------------"
if [ -d ".git" ]; then
    echo "Searching Git history for potential secrets..."
    
    # Check if .env was ever committed
    if git log --all --full-history --source -- "*env*" 2>/dev/null | grep -q "env"; then
        echo -e "${RED}⚠️  WARNING: Found .env files in Git history!${NC}"
        echo "You should:"
        echo "  1. Rotate all API keys immediately"
        echo "  2. Use git filter-branch or BFG to clean history"
        echo ""
    else
        echo -e "${GREEN}✓ No .env files found in Git history${NC}"
    fi
    
    # Check current tracked files
    if git ls-files | grep -q "\.env$"; then
        echo -e "${RED}⚠️  WARNING: .env is currently tracked by Git!${NC}"
        echo "Removing from Git..."
        git rm --cached .env 2>/dev/null || true
        echo -e "${GREEN}✓ .env removed from Git tracking${NC}"
        echo -e "${YELLOW}⚠️  Rotate your API keys as they may be in history!${NC}"
    else
        echo -e "${GREEN}✓ .env is not tracked by Git${NC}"
    fi
else
    echo -e "${YELLOW}Not a Git repository - skipping${NC}"
fi
echo ""

echo "📋 Step 5: Creating directory structure"
echo "----------------------------------------"
mkdir -p config
mkdir -p api
mkdir -p execution
mkdir -p strategies
mkdir -p utils
mkdir -p tests
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo "📋 Step 6: Installing Python dependencies"
echo "------------------------------------------"
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt"
else
    echo "Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core dependencies
python-dotenv==1.0.0
requests==2.31.0
pydantic==2.4.2
pydantic-settings==2.0.3

# Async support
aiohttp==3.8.6

# Development tools
pytest==7.4.3
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
mypy==1.7.0
isort==5.12.0

# Security scanning
bandit==1.7.5
safety==2.3.5
EOF
    echo -e "${GREEN}✓ requirements.txt created${NC}"
fi

read -p "Install dependencies with pip? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo "Skipping dependency installation"
    echo "Install manually: pip install -r requirements.txt"
fi
echo ""

echo "📋 Step 7: Running security audit"
echo "----------------------------------"
if [ -f "tools/security_audit.py" ]; then
    chmod +x tools/security_audit.py
    echo "Running security scan..."
    python3 tools/security_audit.py > security_audit_initial.txt 2>&1 || true
    
    if grep -q "CRITICAL" security_audit_initial.txt; then
        echo -e "${RED}⚠️  CRITICAL security issues found!${NC}"
        echo "Review: cat security_audit_initial.txt"
    else
        echo -e "${GREEN}✓ No critical issues found${NC}"
    fi
else
    echo -e "${YELLOW}Security audit tool not found - skipping${NC}"
fi
echo ""

echo "📋 Step 8: Setting up pre-commit hooks (optional)"
echo "--------------------------------------------------"
read -p "Install pre-commit hooks? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    else
        echo "Installing pre-commit..."
        pip install pre-commit
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    fi
else
    echo "Skipping pre-commit setup"
fi
echo ""

echo "========================================"
echo -e "${GREEN}✓ Security setup complete!${NC}"
echo "========================================"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. ${YELLOW}Edit .env file and add your real API keys:${NC}"
echo "   nano .env"
echo ""
echo "2. ${YELLOW}Review the action plan:${NC}"
echo "   cat ACTION_PLAN.md"
echo ""
echo "3. ${YELLOW}Read the security audit:${NC}"
echo "   cat security_audit_initial.txt"
echo ""
echo "4. ${YELLOW}Review code quality:${NC}"
echo "   python tools/auto_code_review.py"
echo ""
echo "5. ${YELLOW}Before going live:${NC}"
echo "   - Test on Bitunix testnet/demo account"
echo "   - Start with SMALL position sizes"
echo "   - Monitor for 24 hours before scaling"
echo ""
echo "⚠️  ${RED}CRITICAL SECURITY REMINDERS:${NC}"
echo "   - NEVER commit .env file to Git"
echo "   - NEVER share your API keys"
echo "   - Enable 2FA on your exchange account"
echo "   - Set API key permissions to minimum required"
echo "   - Use IP whitelist if available"
echo "   - Start with TRADING_ENABLED=false and DRY_RUN=true"
echo ""
echo "📚 Documentation:"
echo "   - Full review report: code_review_report.md"
echo "   - Action plan: ACTION_PLAN.md"
echo "   - Tools guide: tools/README.md"
echo ""
echo "Happy (safe) trading! 🚀"
