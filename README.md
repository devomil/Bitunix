# Conservative Crypto Risk Manager

A sophisticated cryptocurrency futures risk management system built with Flask, successfully integrated with BitUnix trading platform. The application provides real-time portfolio monitoring, risk assessment, and emergency stop mechanisms for cryptocurrency trading with an emphasis on conservative trading strategies and capital preservation.

## 🚀 Features

### Live Trading Integration
- **Real-time BitUnix API connection** with proper double SHA-256 authentication
- **Live balance monitoring** - Displays actual account balance ($197.97) updated every 5 seconds
- **Position detection** - Automatically detects active positions and margin usage
- **Real-time P&L tracking** - Live unrealized/realized profit and loss monitoring

### Conservative Risk Management
- **1.5% stop loss** and **3% take profit** for optimal 2:1 risk-reward ratio
- **Maximum 5x leverage** limit for capital protection
- **Daily loss limits** (3%) with automatic emergency stop
- **Conservative position sizing** recommendations

### Advanced Signal Generation
- **15-25 signals per minute** across 200+ cryptocurrencies
- **Multiple categories**: AI tokens, meme coins, DeFi, gaming, Layer 2s, infrastructure
- **High confidence filtering** - Only signals with 75%+ confidence
- **Trade duration recommendations** based on volatility and market conditions

### Comprehensive Dashboard
- **Real-time portfolio overview** with live balance and position updates
- **Risk metrics visualization** including portfolio exposure and margin ratios
- **Trading signals feed** with entry/exit recommendations
- **Emergency stop system** with multiple trigger conditions
- **Backtesting capabilities** for strategy validation

## 🛠 Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5 Dark Theme, Chart.js
- **API Integration**: BitUnix Futures API
- **Real-time Updates**: APScheduler for background tasks
- **Technical Analysis**: Pandas, NumPy for indicator calculations
- **Authentication**: Double SHA-256 signature method

## 📋 Prerequisites

- Python 3.8+
- BitUnix API credentials (API key and secret)
- Required Python packages (see `pyproject.toml`)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/devomil/Bitunix.git
   cd Bitunix
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export BITUNIX_API_KEY="your_api_key_here"
   export BITUNIX_SECRET_KEY="your_secret_key_here"
   export SESSION_SECRET="your_session_secret_here"
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the dashboard**
   Open your browser to `http://localhost:5000`

## 🔐 API Configuration

### BitUnix API Setup
1. Create a BitUnix account and enable futures trading
2. Generate API credentials in your account settings
3. Ensure your API key has futures trading permissions
4. Set the environment variables as shown above

### Authentication Method
The system uses BitUnix's required double SHA-256 signature method:
```
digest_input = nonce + timestamp + api_key + query_params + body
digest = SHA256(digest_input)
signature = SHA256(digest + secret_key)
```

## 📊 Dashboard Overview

### Portfolio Status
- **Total Balance**: Real-time account balance
- **Active Positions**: Number of open futures positions
- **Total Risk**: Portfolio risk exposure percentage
- **Daily P&L**: Unrealized and realized profit/loss

### Trading Signals
- **Symbol**: Cryptocurrency pair (e.g., BTC/USDT)
- **Direction**: Long or short recommendation
- **Confidence**: Signal confidence percentage (75-95%)
- **Leverage**: Suggested leverage (1-3x conservative)
- **Entry Price**: Recommended entry point
- **Stop Loss**: Conservative 1.5% risk limit
- **Take Profit**: 3% target for 2:1 risk-reward
- **Duration**: Recommended trade holding period

### Risk Management
- **Emergency Stop**: Automatic halt on 3% daily loss
- **Position Limits**: Maximum position size controls
- **Leverage Caps**: Conservative leverage restrictions
- **Real-time Monitoring**: Continuous risk assessment

## 🎯 Conservative Trading Philosophy

This system prioritizes **capital preservation** over aggressive gains:

1. **Risk-First Approach**: All signals include predefined stop losses
2. **Conservative Leverage**: Maximum 5x leverage, typically 1-3x recommended
3. **High Confidence**: Only signals with 75%+ confidence are displayed
4. **Diversification**: Signals across multiple cryptocurrency categories
5. **Emergency Protection**: Automatic trading halt mechanisms

## 📈 Supported Markets

### Major Layer 1s
BTC, ETH, SOL, ADA, AVAX, DOT, ATOM, NEAR, FTM, etc.

### AI & Machine Learning
FET, AGIX, OCEAN, RNDR, GRT, TAO, NMR, etc.

### Meme Coins
DOGE, SHIB, PEPE, FLOKI, BONK, WIF, etc.

### DeFi Protocols
UNI, AAVE, COMP, MKR, SNX, CRV, YFI, etc.

### Gaming & Metaverse
AXS, SAND, MANA, ENJ, GALA, etc.

### Layer 2 Solutions
MATIC, ARB, OP, LRC, IMX, etc.

## 🔄 Real-time Updates

- **Portfolio data**: Updates every 30 seconds
- **Trading signals**: Generated every 60 seconds
- **Dashboard refresh**: Live updates every 5 seconds
- **API connectivity**: Continuous monitoring

## ⚠️ Risk Disclaimer

This software is for educational and informational purposes only. Cryptocurrency trading involves substantial risk of loss. Past performance does not guarantee future results. Always conduct your own research and consider your risk tolerance before trading.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or support:
- Create an issue in this repository
- Check the BitUnix API documentation
- Review the risk management guidelines

## 🏗 Architecture

```
conservative-crypto-risk-manager/
├── main.py                 # Application entry point
├── app.py                  # Flask application and routes
├── api_client.py           # BitUnix API integration
├── risk_manager.py         # Risk management logic
├── portfolio.py            # Portfolio monitoring
├── signals.py              # Signal generation
├── indicators.py           # Technical indicators
├── backtesting.py          # Strategy backtesting
├── emergency_stop.py       # Emergency stop system
├── templates/              # HTML templates
│   └── dashboard.html      # Main dashboard
├── static/                 # CSS, JS, and assets
│   ├── style.css          # Custom styling
│   └── dashboard.js       # Frontend logic
└── README.md              # This file
```

---

**Built with ❤️ for conservative crypto traders who value capital preservation over risky speculation.**