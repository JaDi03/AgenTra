# AgenTra - Autonomous Trading Bot 🤖

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An AI-powered autonomous trading bot for cryptocurrency futures markets, featuring regime-based strategy selection, market microstructure analysis, and adaptive risk management.

## 🎯 Features

- **AI-Driven Decision Making**: Powered by Google Gemini 2.5 Pro for context-aware trade analysis
- **Regime Detection**: Automatically classifies market as TRENDING, MEAN_REVERSION, or DEFENSIVE
- **Advanced Indicators**:
  - Hurst Exponent (trend persistence)
  - VPIN (toxicity detection)
  - Volume Profile (POC/VAH/VAL)
  - Concept Drift Detection (KS-Test)
- **Smart Risk Management**:
  - Dynamic position sizing based on regime
  - Trailing stop-loss with break-even logic
  - Adaptive SL/TP based on ATR
- **Real-time Dashboard**: Streamlit-based UI for monitoring and manual controls

## 📁 Project Structure

```
AgenTra/
├── main.py                 # Main orchestrator & execution loop
├── agent_logic.py          # AI integration & decision engine
├── trading_tools.py        # Technical indicators & utilities
├── strategies.py           # Regime-based strategy selector
├── market_profile.py       # Volume Profile calculation
├── order_flow.py           # VPIN (toxicity detection)
├── market_monitor.py       # Concept drift detection
├── dashboard.py            # Streamlit dashboard
├── constitution.md         # Safety rules
├── strategy.md             # Active strategy parameters
└── omni.md                 # Omnidirectional strategy framework
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/JaDi03/AgenTra.git
cd AgenTra
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET=your_secret_here
GOOGLE_API_KEY=your_gemini_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TRADING_MODE=PAPER  # PAPER | TESTNET | LIVE
```

## 📊 Usage

### Start the Trading Bot
```bash
python main.py
```

### Launch Dashboard
```bash
streamlit run dashboard.py
```

## ⚙️ Configuration

- **Trading Pairs**: Modify `PAIRS` list in `main.py`
- **Risk Parameters**: Edit `constitution.md`
- **Strategy Rules**: Customize `strategy.md` or let AI adapt it

## 🔒 Security Notes

⚠️ **IMPORTANT**: This bot is currently in **BETA** and optimized for paper trading.

Before live trading:
- [ ] Implement file locking for `state.json`
- [ ] Migrate API keys to secure storage
- [ ] Add unit test coverage (>60%)
- [ ] Enable daily drawdown circuit breaker

See `audit_report.md` in the brain directory for full security assessment.

## 📈 Performance

- **Win Rate**: ~33% (16W/32L)
- **Optimized For**: 15-minute timeframe swing trading
- **Max Concurrent Positions**: 3
- **Max Leverage**: 5x

## 🧠 How It Works

1. **Gatekeeper Filter**: Pre-screens pairs with ADX/Volume criteria
2. **Data Fetching**: Pulls 15m + 4h OHLCV data from Binance
3. **Indicator Calculation**: Computes RSI, ADX, Hurst, VPIN, Volume Profile
4. **Regime Classification**: Determines market state (TRENDING/MEAN_REVERSION/DEFENSIVE)
5. **AI Analysis**: Gemini evaluates setup quality and proposes decision
6. **Execution**: Places trades with validated SL/TP
7. **Risk Management**: Monitors positions with trailing stops and break-even logic

## 🛠️ Known Limitations

- No multi-threading (sequential processing)
- State persistence uses single JSON file (race condition risk)
- AI reflection after losses not yet automated

## 📝 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. Use at your own risk.

---

**Built with** ❤️ **by the AgenTra Team**
