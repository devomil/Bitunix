# Security & Quality Quick Reference

⚡ **Quick Start:** Run `bash setup_security.sh` first!

---

## 🔴 BEFORE YOU TRADE - CRITICAL CHECKLIST

### Must-Have Security (Do NOT skip!)

- [ ] **API keys in environment variables ONLY**
  ```bash
  # Check for hardcoded secrets
  grep -r "api.*key.*=" --include="*.py" . | grep -v ".env"
  # Should return nothing
  ```

- [ ] **`.env` in `.gitignore`**
  ```bash
  git check-ignore .env
  # Should output: .env
  ```

- [ ] **No secrets in Git history**
  ```bash
  git log --all --source -- "*env*" | grep -i secret
  # Should return nothing
  ```

- [ ] **Order size limits implemented**
  ```python
  # Before EVERY order:
  is_valid, error = risk_manager.validate_order(...)
  if not is_valid:
      raise RiskLimitException(error)
  ```

- [ ] **SSL verification enabled**
  ```bash
  grep -r "verify.*False" --include="*.py" .
  # Should return nothing
  ```

- [ ] **All API calls have timeouts**
  ```python
  # ✓ Good
  requests.get(url, timeout=10)
  
  # ✗ Bad
  requests.get(url)  # Can hang forever
  ```

- [ ] **Error handling on all API calls**
  ```python
  try:
      response = api.get_balance()
  except APIException as e:
      logger.error(f"API failed: {e}")
      # Handle gracefully
  ```

---

## 🟠 HIGH PRIORITY CHECKLIST

### Financial Safety

- [ ] **Max order size**: $100 or less to start
- [ ] **Max position size**: $500 or less total exposure
- [ ] **Daily loss limit**: Stop trading after $50 loss
- [ ] **Emergency stop**: Auto-kill at 10% account loss
- [ ] **Positive value validation**: Reject negative amounts/prices

### API Security

- [ ] **Rate limiting**: Handle 429 responses
- [ ] **Retry logic**: Exponential backoff on failures
- [ ] **Connection pooling**: Use `requests.Session()`
- [ ] **Minimal API permissions**: Only what's needed for trading

### Exchange Account Security

- [ ] **2FA enabled**: On your exchange account
- [ ] **IP whitelist**: If exchange supports it
- [ ] **Withdrawal whitelist**: Pre-approve withdrawal addresses
- [ ] **API key restrictions**: Disable withdrawals if possible

---

## 🟡 BEFORE PRODUCTION CHECKLIST

### Testing

- [ ] **Tested on testnet/demo**: Run for at least 24 hours
- [ ] **Start with dry run**: Set `DRY_RUN=true` initially
- [ ] **Small positions first**: Max $10 orders to start
- [ ] **Monitor first hour**: Watch logs constantly
- [ ] **Unit tests**: Critical paths tested

### Monitoring

- [ ] **Structured logging**: JSON logs for analysis
- [ ] **No secrets in logs**: Redact API keys, passwords
- [ ] **Health checks**: Bot sends heartbeat every 60s
- [ ] **Alerting**: Get notified of errors
- [ ] **Daily review**: Check logs every day

### Code Quality

- [ ] **No bare excepts**: Specify exception types
- [ ] **Type hints**: On function signatures
- [ ] **Docstrings**: Explain complex logic
- [ ] **No magic numbers**: Use named constants
- [ ] **Security audit passed**: Run `python tools/security_audit.py`

---

## 📋 DAILY OPERATIONS CHECKLIST

### Morning

- [ ] Check bot is running: `ps aux | grep bot`
- [ ] Review overnight logs: `tail -n 100 logs/bot.log`
- [ ] Check account balance: Verify no unexpected losses
- [ ] Review open positions: Close any that shouldn't be open

### Before Any Code Changes

- [ ] Run tests: `pytest tests/`
- [ ] Security scan: `python tools/security_audit.py`
- [ ] Code review: `python tools/auto_code_review.py`

### After Code Changes

- [ ] All tests pass
- [ ] No new security issues
- [ ] Deploy to testnet first
- [ ] Monitor for 1 hour before production

### Evening

- [ ] Check daily P&L
- [ ] Review all trades: Were they as expected?
- [ ] Check error count: `grep ERROR logs/bot.log | wc -l`
- [ ] Verify positions closed (if day trading)

---

## 🚨 EMERGENCY PROCEDURES

### If Bot Acts Strange

```bash
# 1. STOP IMMEDIATELY
pkill -f "python.*main"

# 2. Check what happened
tail -n 50 logs/bot.log

# 3. Review recent orders on exchange

# 4. Close positions manually if needed

# 5. Don't restart until you know what went wrong
```

### If Account Compromised

1. **Disable API keys** in exchange immediately
2. **Change password** with 2FA
3. **Review all activity** in exchange
4. **Check Git history** for leaked keys
5. **Rotate all credentials**
6. **Contact exchange support** if funds missing

### If Major Loss

1. **Stop the bot** immediately
2. **Review logs** to understand what happened
3. **Check strategy logic** for bugs
4. **Verify risk limits** were enforced
5. **Don't restart** until issue identified and fixed

---

## 🔧 QUICK COMMANDS

### Security Checks

```bash
# Full security audit
python tools/security_audit.py

# Code quality review
python tools/auto_code_review.py

# Check for secrets in code
grep -rn "api_key\s*=" --include="*.py" .
grep -rn "secret\s*=" --include="*.py" .

# Verify .env not tracked
git ls-files | grep .env

# Check SSL verification
grep -rn "verify.*False" --include="*.py" .
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test
pytest tests/test_risk_manager.py -v
```

### Linting & Type Checking

```bash
# Format code
black .

# Check style
flake8 .

# Type check
mypy .

# Import sorting
isort .
```

### Dependency Checks

```bash
# Security vulnerabilities
safety check

# Outdated packages
pip list --outdated

# Unused imports
autoflake --remove-all-unused-imports --recursive .
```

---

## 📊 METRICS TO MONITOR

### Security Metrics

- **API key age**: Rotate every 90 days
- **Failed auth attempts**: Should be 0
- **SSL errors**: Should be 0
- **Secrets in logs**: Should be 0

### Trading Metrics

- **Win rate**: % of profitable trades
- **Average profit**: Per trade
- **Max drawdown**: Largest peak-to-trough loss
- **Sharpe ratio**: Risk-adjusted returns

### Operational Metrics

- **Uptime**: Bot running time %
- **Error rate**: Errors per hour
- **API latency**: Average response time
- **Order execution time**: Seconds from signal to filled

### Risk Metrics

- **Current position size**: USD value
- **Daily loss**: Today's total losses
- **Largest order**: Biggest order size
- **Risk limit violations**: Should be 0

---

## 🎯 SUCCESS CRITERIA

### Week 1: Testing Phase

- [ ] No CRITICAL security issues
- [ ] Bot runs 24h without crashes
- [ ] All trades match expected strategy
- [ ] Risk limits working (test by trying to exceed)
- [ ] Error handling working (simulate failures)

### Week 2: Small Live Trading

- [ ] Profitable or break-even
- [ ] No unexpected orders
- [ ] Logs show all decisions clearly
- [ ] Can explain every trade
- [ ] Emergency stop works

### Month 1: Scaling Up

- [ ] Consistent profitability
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 5%
- [ ] No manual interventions needed
- [ ] Monitoring/alerting proven

---

## 📚 REFERENCE LINKS

### Security

- **CWE Database**: https://cwe.mitre.org/
- **OWASP API Security**: https://owasp.org/www-project-api-security/
- **Python Security**: https://snyk.io/blog/python-security-best-practices-cheat-sheet/

### Trading

- **Risk Management**: Calculate position sizes properly
- **Backtesting**: Test strategy on historical data
- **Paper Trading**: Practice with fake money first

### Documentation

- **Main Review**: `code_review_report.md`
- **Action Plan**: `ACTION_PLAN.md`
- **Tools Guide**: `tools/README.md`

---

## 💡 PRO TIPS

1. **Start tiny**: First live trade should be <$10
2. **Test failures**: Manually trigger errors to test handling
3. **Log everything**: You can't debug what you can't see
4. **Automate checks**: Use pre-commit hooks
5. **Review daily**: 5 minutes/day prevents disasters
6. **Keep learning**: Markets change, adapt your strategy
7. **Stay paranoid**: Security is never "done"
8. **Backup data**: Save all trades for analysis

---

## ⚠️ COMMON MISTAKES TO AVOID

- ❌ Committing `.env` to Git
- ❌ Skipping risk limits "just this once"
- ❌ Increasing position size after losses
- ❌ Ignoring error messages
- ❌ Not testing on demo first
- ❌ Deploying on Friday afternoon
- ❌ Logging sensitive data
- ❌ Disabling SSL verification
- ❌ Bare `except:` blocks
- ❌ Trading with money you can't afford to lose

---

**Remember:** It's better to miss profits than to lose principal.  
Start small, test thoroughly, scale gradually. 🛡️
