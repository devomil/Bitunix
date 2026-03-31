# Bitunix Trading Bot - Security & Quality Action Plan

**Project:** Bob-Trader  
**Created:** 2026-03-08  
**Priority:** Execute in order listed

---

## 🔴 PHASE 1: CRITICAL SECURITY (DO FIRST - 1-2 Hours)

### 1.1 Secure API Credentials

**Current Risk:** Exposed credentials = complete account compromise + fund theft

**Actions:**
```bash
# 1. Install python-dotenv
pip install python-dotenv

# 2. Create .env file (NEVER commit this)
cat > .env << EOF
BITUNIX_API_KEY=your_key_here
BITUNIX_API_SECRET=your_secret_here
EOF

# 3. Add to .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
echo ".env.*" >> .gitignore

# 4. Check Git history for leaks
git log --all --full-history --source -- '*env*'
git log --all --full-history --source -- '*secret*' | grep -i api

# 5. If secrets found in history, rotate keys immediately
```

**Code Changes:**
```python
# Before (DANGEROUS):
API_KEY = "abc123xyz"
API_SECRET = "def456uvw"

# After (SAFE):
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BITUNIX_API_KEY')
API_SECRET = os.getenv('BITUNIX_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError("Bitunix API credentials not found. Check .env file")
```

**Verification:**
```bash
# 1. Search for hardcoded secrets
grep -r "api_key\s*=" --include="*.py" .
grep -r "secret\s*=" --include="*.py" .

# 2. Ensure .env is ignored
git check-ignore .env
# Should output: .env

# 3. Run security audit
python tools/security_audit.py
```

---

### 1.2 Implement Order Size Limits

**Current Risk:** One bug could liquidate your entire account

**Create:** `config/risk_limits.py`
```python
"""Risk management configuration"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskLimits:
    """Trading risk limits"""
    
    # Order limits
    max_order_usd: float = 100.0  # Start SMALL
    min_order_usd: float = 10.0
    
    # Position limits
    max_position_usd: float = 500.0  # Total exposure
    max_position_pct: float = 0.25  # 25% of account
    
    # Loss limits
    max_loss_per_trade_pct: float = 0.02  # 2% per trade
    max_daily_loss_usd: float = 50.0
    max_daily_loss_pct: float = 0.05  # 5% of account per day
    
    # Safety
    require_confirmation: bool = True  # Manual confirmation
    emergency_stop_loss_pct: float = 0.10  # Kill switch at 10% loss


# Global limits instance
RISK_LIMITS = RiskLimits()
```

**Create:** `execution/risk_manager.py`
```python
"""Risk management and order validation"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from config.risk_limits import RISK_LIMITS

logger = logging.getLogger(__name__)


class RiskManager:
    """Validates orders against risk limits"""
    
    def __init__(self):
        self.daily_losses: Dict[str, float] = {}  # date -> loss amount
        self.current_positions: Dict[str, float] = {}  # symbol -> usd value
        self.account_balance: float = 0.0
    
    def validate_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate order against risk limits.
        
        Returns:
            (is_valid, error_message)
        """
        order_value = amount * price
        
        # 1. Check order size limits
        if order_value > RISK_LIMITS.max_order_usd:
            return False, f"Order ${order_value:.2f} exceeds max ${RISK_LIMITS.max_order_usd}"
        
        if order_value < RISK_LIMITS.min_order_usd:
            return False, f"Order ${order_value:.2f} below min ${RISK_LIMITS.min_order_usd}"
        
        # 2. Check position limits
        current_position = self.current_positions.get(symbol, 0.0)
        new_position = current_position + order_value if side == 'buy' else current_position - order_value
        
        if new_position > RISK_LIMITS.max_position_usd:
            return False, f"Position would be ${new_position:.2f}, max is ${RISK_LIMITS.max_position_usd}"
        
        if self.account_balance > 0:
            position_pct = new_position / self.account_balance
            if position_pct > RISK_LIMITS.max_position_pct:
                return False, f"Position would be {position_pct:.1%}, max is {RISK_LIMITS.max_position_pct:.1%}"
        
        # 3. Check daily loss limits
        today = datetime.now().date().isoformat()
        daily_loss = self.daily_losses.get(today, 0.0)
        
        if daily_loss >= RISK_LIMITS.max_daily_loss_usd:
            return False, f"Daily loss limit reached: ${daily_loss:.2f}"
        
        if self.account_balance > 0:
            daily_loss_pct = daily_loss / self.account_balance
            if daily_loss_pct >= RISK_LIMITS.max_daily_loss_pct:
                return False, f"Daily loss % limit reached: {daily_loss_pct:.1%}"
        
        # 4. Validate parameters
        if amount <= 0 or price <= 0:
            return False, "Amount and price must be positive"
        
        logger.info(f"Order validated: {side} {amount} {symbol} @ ${price}")
        return True, None
    
    def update_balance(self, balance: float):
        """Update account balance"""
        self.account_balance = balance
        logger.info(f"Account balance updated: ${balance:.2f}")
    
    def record_loss(self, loss_amount: float):
        """Record a loss for daily limit tracking"""
        today = datetime.now().date().isoformat()
        self.daily_losses[today] = self.daily_losses.get(today, 0.0) + loss_amount
        logger.warning(f"Loss recorded: ${loss_amount:.2f}, Daily total: ${self.daily_losses[today]:.2f}")
    
    def update_position(self, symbol: str, usd_value: float):
        """Update position tracking"""
        self.current_positions[symbol] = usd_value
        logger.info(f"Position updated: {symbol} = ${usd_value:.2f}")
    
    def check_emergency_stop(self) -> tuple[bool, str]:
        """Check if emergency stop should trigger"""
        if self.account_balance <= 0:
            return False, "No balance data"
        
        today = datetime.now().date().isoformat()
        daily_loss = self.daily_losses.get(today, 0.0)
        loss_pct = daily_loss / self.account_balance
        
        if loss_pct >= RISK_LIMITS.emergency_stop_loss_pct:
            msg = f"🚨 EMERGENCY STOP: {loss_pct:.1%} loss (${daily_loss:.2f})"
            logger.critical(msg)
            return True, msg
        
        return False, ""


# Global risk manager instance
risk_manager = RiskManager()
```

**Usage Example:**
```python
from execution.risk_manager import risk_manager

# Before placing any order
is_valid, error = risk_manager.validate_order(
    symbol='BTC/USDT',
    side='buy',
    amount=0.001,
    price=50000
)

if not is_valid:
    logger.error(f"Order rejected: {error}")
    return

# Order is safe to place
place_order(...)
```

**Verification:**
```bash
# Test risk manager
python -c "
from execution.risk_manager import risk_manager

# Should pass
print(risk_manager.validate_order('BTC/USDT', 'buy', 0.001, 50000))

# Should fail - too large
print(risk_manager.validate_order('BTC/USDT', 'buy', 1.0, 50000))
"
```

---

### 1.3 Enable SSL Verification

**Search for disabled SSL:**
```bash
grep -r "verify.*False" --include="*.py" .
```

**Fix ALL instances:**
```python
# NEVER do this
response = requests.get(url, verify=False)

# ALWAYS verify SSL
response = requests.get(url, verify=True, timeout=10)

# Better: Use session with defaults
session = requests.Session()
session.verify = True
response = session.get(url, timeout=10)
```

---

### 1.4 Run Security Audit

```bash
# Run automated security scan
python tools/security_audit.py > security_audit.txt

# Review all CRITICAL findings
grep -A 10 "CRITICAL" security_audit.txt

# Fix all CRITICAL issues before proceeding
```

---

## 🟠 PHASE 2: HIGH PRIORITY (24-48 Hours)

### 2.1 Implement Comprehensive Error Handling

**Create:** `utils/exceptions.py`
```python
"""Custom exceptions for trading bot"""


class TradingBotException(Exception):
    """Base exception for trading bot"""
    pass


class APIException(TradingBotException):
    """API communication errors"""
    pass


class ValidationException(TradingBotException):
    """Order validation errors"""
    pass


class RiskLimitException(TradingBotException):
    """Risk limit violations"""
    pass


class InsufficientBalanceException(TradingBotException):
    """Not enough balance for order"""
    pass
```

**Create:** `api/client.py` (or update existing)
```python
"""Bitunix API client with robust error handling"""
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Any, Optional
from utils.exceptions import APIException

logger = logging.getLogger(__name__)


class BitunixClient:
    """Bitunix exchange API client"""
    
    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API credentials required")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitunix.com"  # Update with actual URL
        
        # Create session with retry logic
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create session with connection pooling and retry logic"""
        session = requests.Session()
        
        # Retry strategy
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Always verify SSL
        session.verify = True
        
        return session
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add authentication headers
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=(3, 10)  # 3s connect, 10s read
            )
            
            # Log request
            logger.debug(f"{method} {endpoint} -> {response.status_code}")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after}s")
                time.sleep(retry_after)
                return self._request(method, endpoint, params, data)
            
            # Raise for error status
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {method} {endpoint}")
            raise APIException(f"API timeout: {endpoint}")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise APIException(f"Connection failed: {endpoint}")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise APIException(f"API error: {response.status_code} - {endpoint}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIException(f"Request failed: {endpoint}")
        
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise APIException(f"Invalid response from {endpoint}")
    
    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            response = self._request('GET', '/api/v1/account/balance')
            return response.get('balances', {})
        except APIException:
            logger.exception("Failed to get balance")
            raise
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create order with validation"""
        data = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'amount': amount
        }
        
        if price:
            data['price'] = price
        
        try:
            response = self._request('POST', '/api/v1/orders', data=data)
            logger.info(f"Order created: {response.get('order_id')}")
            return response
        except APIException:
            logger.exception(f"Failed to create order: {data}")
            raise
```

---

### 2.2 Implement Structured Logging

**Create:** `utils/logger.py`
```python
"""Structured logging configuration"""
import logging
import json
from datetime import datetime
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """JSON structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, 'order_id'):
            log_data['order_id'] = record.order_id
        if hasattr(record, 'symbol'):
            log_data['symbol'] = record.symbol
        
        return json.dumps(log_data)


def setup_logging(log_level: str = 'INFO', log_file: str = 'bot.log'):
    """Configure logging for the bot"""
    
    # Create logs directory
    log_path = Path('logs')
    log_path.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler - human readable
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler - structured JSON
    file_handler = logging.FileHandler(log_path / log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(StructuredFormatter())
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logging.info("Logging configured")
```

**Usage:**
```python
from utils.logger import setup_logging
import logging

setup_logging(log_level='INFO')
logger = logging.getLogger(__name__)

logger.info("Bot started")
logger.error("Order failed", extra={'order_id': '12345', 'symbol': 'BTC/USDT'})
```

---

### 2.3 Add Type Hints & Validation

**Install:**
```bash
pip install mypy pydantic
```

**Example with Pydantic:**
```python
"""Type-safe configuration and validation"""
from pydantic import BaseModel, Field, validator
from typing import Literal


class OrderRequest(BaseModel):
    """Validated order request"""
    symbol: str = Field(..., min_length=3, max_length=20)
    side: Literal['buy', 'sell']
    order_type: Literal['market', 'limit']
    amount: float = Field(..., gt=0)
    price: float = Field(None, gt=0)
    
    @validator('price')
    def validate_price_for_limit(cls, v, values):
        """Require price for limit orders"""
        if values.get('order_type') == 'limit' and v is None:
            raise ValueError('Price required for limit orders')
        return v


# Usage
try:
    order = OrderRequest(
        symbol='BTC/USDT',
        side='buy',
        order_type='limit',
        amount=0.001,
        price=50000
    )
except ValueError as e:
    logger.error(f"Invalid order: {e}")
```

---

### 2.4 Add Health Checks & Monitoring

**Create:** `utils/health_check.py`
```python
"""Health check and monitoring"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor bot health and activity"""
    
    def __init__(self):
        self.last_heartbeat = datetime.now()
        self.last_trade = None
        self.last_api_call = None
        self.error_count = 0
        self.trade_count = 0
    
    def heartbeat(self):
        """Record heartbeat"""
        self.last_heartbeat = datetime.now()
        logger.debug("Heartbeat")
    
    def record_trade(self):
        """Record successful trade"""
        self.last_trade = datetime.now()
        self.trade_count += 1
    
    def record_api_call(self):
        """Record API call"""
        self.last_api_call = datetime.now()
    
    def record_error(self):
        """Record error"""
        self.error_count += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get health status"""
        now = datetime.now()
        
        return {
            'healthy': self.is_healthy(),
            'uptime_seconds': (now - self.last_heartbeat).total_seconds(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'last_trade': self.last_trade.isoformat() if self.last_trade else None,
            'last_api_call': self.last_api_call.isoformat() if self.last_api_call else None,
            'trade_count': self.trade_count,
            'error_count': self.error_count
        }
    
    def is_healthy(self) -> bool:
        """Check if bot is healthy"""
        now = datetime.now()
        
        # No heartbeat in 5 minutes
        if (now - self.last_heartbeat).total_seconds() > 300:
            logger.error("No heartbeat in 5 minutes")
            return False
        
        # Too many errors
        if self.error_count > 10:
            logger.error(f"Too many errors: {self.error_count}")
            return False
        
        return True


# Global monitor
health_monitor = HealthMonitor()
```

---

## 🟡 PHASE 3: MEDIUM PRIORITY (1 Week)

### 3.1 Add Unit Tests

**Create:** `tests/test_risk_manager.py`
```python
"""Tests for risk manager"""
import pytest
from execution.risk_manager import RiskManager
from config.risk_limits import RiskLimits


def test_order_validation_max_size():
    """Test max order size enforcement"""
    rm = RiskManager()
    
    # Valid order
    is_valid, error = rm.validate_order('BTC/USDT', 'buy', 0.001, 50000)
    assert is_valid
    
    # Exceeds max
    is_valid, error = rm.validate_order('BTC/USDT', 'buy', 10, 50000)
    assert not is_valid
    assert 'exceeds max' in error.lower()


def test_order_validation_negative_values():
    """Test rejection of negative values"""
    rm = RiskManager()
    
    is_valid, error = rm.validate_order('BTC/USDT', 'buy', -1, 50000)
    assert not is_valid
    
    is_valid, error = rm.validate_order('BTC/USDT', 'buy', 1, -50000)
    assert not is_valid


def test_daily_loss_limit():
    """Test daily loss limit enforcement"""
    rm = RiskManager()
    rm.update_balance(1000)
    
    # Record losses
    rm.record_loss(40)
    
    # Should still allow orders
    is_valid, _ = rm.validate_order('BTC/USDT', 'buy', 0.001, 50000)
    assert is_valid
    
    # Hit daily limit
    rm.record_loss(20)
    
    # Should reject
    is_valid, error = rm.validate_order('BTC/USDT', 'buy', 0.001, 50000)
    assert not is_valid
    assert 'daily loss' in error.lower()
```

**Run tests:**
```bash
pip install pytest pytest-cov
pytest tests/ -v
pytest tests/ --cov=execution --cov=api
```

---

### 3.2 Performance Optimization

**Use async for API calls:**
```bash
pip install aiohttp asyncio
```

**Example async client:**
```python
import aiohttp
import asyncio


class AsyncBitunixClient:
    """Async API client for better performance"""
    
    async def get_multiple_prices(self, symbols: list[str]) -> dict:
        """Fetch multiple prices concurrently"""
        async with aiohttp.ClientSession() as session:
            tasks = [self._get_price(session, symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)
            return dict(zip(symbols, results))
    
    async def _get_price(self, session, symbol):
        """Get single price"""
        async with session.get(f"{self.base_url}/ticker/{symbol}") as resp:
            data = await resp.json()
            return data['price']
```

---

### 3.3 Configuration Management

**Create:** `config/settings.py`
```python
"""Centralized configuration"""
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # API credentials
    bitunix_api_key: str = Field(..., env='BITUNIX_API_KEY')
    bitunix_api_secret: str = Field(..., env='BITUNIX_API_SECRET')
    
    # Trading
    trading_enabled: bool = Field(True, env='TRADING_ENABLED')
    dry_run: bool = Field(False, env='DRY_RUN')
    
    # Logging
    log_level: str = Field('INFO', env='LOG_LEVEL')
    log_file: str = Field('bot.log', env='LOG_FILE')
    
    # Monitoring
    enable_health_checks: bool = Field(True, env='ENABLE_HEALTH_CHECKS')
    heartbeat_interval: int = Field(60, env='HEARTBEAT_INTERVAL')
    
    class Config:
        env_file = '.env'
        case_sensitive = False


settings = Settings()
```

---

## 🟢 PHASE 4: NICE TO HAVE (Ongoing)

### 4.1 Code Quality Tools

**Create:** `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

**Install:**
```bash
pip install pre-commit black flake8 isort
pre-commit install
```

---

### 4.2 Documentation

**Create:** `docs/TRADING_STRATEGY.md`
```markdown
# Trading Strategy Documentation

## Overview
Brief description of your strategy

## Entry Conditions
- Condition 1
- Condition 2

## Exit Conditions
- Stop loss
- Take profit

## Risk Management
- Max position size
- Stop loss percentage

## Backtesting Results
- Win rate
- Average profit
- Max drawdown
```

---

### 4.3 Deployment Checklist

**Create:** `DEPLOYMENT.md`
```markdown
# Deployment Checklist

## Pre-Deployment
- [ ] All tests passing
- [ ] No CRITICAL security issues
- [ ] API keys in environment variables
- [ ] Risk limits configured
- [ ] Tested on testnet/demo account

## Deployment
- [ ] Monitor logs for first hour
- [ ] Start with minimal position sizes
- [ ] Verify order execution
- [ ] Check balance updates

## Post-Deployment
- [ ] Set up alerts
- [ ] Monitor daily
- [ ] Review logs weekly
```

---

## Verification Commands

Run these after each phase:

```bash
# Security check
python tools/security_audit.py

# Code quality
python tools/auto_code_review.py

# Tests (when implemented)
pytest tests/ -v

# Linting
flake8 .
mypy .

# Check for secrets
git log --all --full-history -- '*.env*'
grep -r "api.*key.*=" --include="*.py" . | grep -v ".env"
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] No CRITICAL security issues in audit
- [ ] All API keys in environment variables
- [ ] Risk manager blocks oversized orders
- [ ] SSL verification enabled everywhere

### Phase 2 Complete When:
- [ ] All API calls have error handling
- [ ] All API calls have timeouts
- [ ] Structured logging implemented
- [ ] Type hints added to core functions

### Phase 3 Complete When:
- [ ] >80% test coverage on critical paths
- [ ] Performance optimizations implemented
- [ ] Configuration centralized
- [ ] Documentation written

### Phase 4 Complete When:
- [ ] Pre-commit hooks working
- [ ] CI/CD pipeline set up
- [ ] Monitoring/alerting configured
- [ ] Successfully traded on testnet for 1 week

---

## Emergency Procedures

### If Bot Misbehaves
```bash
# 1. STOP IMMEDIATELY
pkill -f "python.*main.py"

# 2. Check positions
# Log into exchange and manually close positions if needed

# 3. Review logs
tail -n 100 logs/bot.log | grep ERROR

# 4. Check recent orders
# Review in exchange UI

# 5. Identify issue before restarting
```

### If Account Compromised
1. Immediately disable API keys in exchange
2. Change password with 2FA
3. Review all recent activity
4. Rotate all credentials
5. Check Git history for leaked secrets
6. Report to exchange if needed

---

## Timeline Summary

- **Phase 1 (Critical):** 1-2 hours - DO FIRST
- **Phase 2 (High):** 1-2 days
- **Phase 3 (Medium):** 1 week
- **Phase 4 (Low):** Ongoing

**Total to production-ready:** ~2 weeks

Start with Phase 1 TODAY. Do not skip CRITICAL security fixes.
