# trading_tools.py
# Module: Trading Tools
# Description: Pure functions for market data, technical analysis, and file I/O.
# Designed to be modular for future integration into Molt.bot.

import ccxt
import pandas as pd
import numpy as np
import feedparser
import requests
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Exchange Verification ---
def initialize_exchange():
    """
    Initializes CCXT Binance instance with API Keys if available.
    Supports TESTNET sandbox mode.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_SECRET")
    mode = os.getenv("TRADING_MODE", "PAPER").upper()
    
    config = {
        'options': {'defaultType': 'future'},
        'enableRateLimit': True
    }
    
    if api_key and secret:
        config['apiKey'] = api_key
        config['secret'] = secret
        
    exchange = ccxt.binance(config)
    
    if mode == "TESTNET" or mode == "LIVE_TESTNET":
        exchange.set_sandbox_mode(True)
        logger.info("⚠️ RUNNING IN BINANCE FUTURES TESTNET MODE ⚠️")
    
    return exchange

# Global Exchange Instance
exchange_client = initialize_exchange()

# --- Execution Functions ---
def execute_real_order(symbol: str, side: str, quantity: float, stop_loss: float = None, take_profit: float = None):
    """
    Executes a real order on Binance (Testnet or Mainnet).
    Handles OCO (One-Cancels-Other) logic manually via Stop Market and Take Profit Limit orders if needed.
    For MVP: Market Order + independent Stop Market.
    """
    try:
        # 1. Market Order (Entry)
        order = exchange_client.create_order(symbol, 'market', side.lower(), quantity)
        logger.info(f"✅ REAL EXECUTION: {side} {quantity} {symbol} - ID: {order['id']}")
        
        # 2. Stop Loss (Trigger)
        if stop_loss:
            # Determine SL side implies Opposite of Entry
            sl_side = 'sell' if side.lower() == 'buy' else 'buy'
            params = {'stopPrice': stop_loss}
            exchange_client.create_order(symbol, 'STOP_MARKET', sl_side, quantity, params=params)
            logger.info(f"🛡️ REAL SL SET: {stop_loss}")
            
        return order
    except Exception as e:
        logger.error(f"❌ EXECUTION FAILED: {e}")
        return None

# --- Notification Functions ---

def send_telegram_message(message: str):
    """
    Sends a message to the configured Telegram Chat.
    Requires TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in .env.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logger.warning("Telegram credentials not found. Message not sent.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Telegram Send Failed: {response.text}")
    except Exception as e:
        logger.error(f"Telegram Error: {e}")

# --- Market Data Functions ---

def get_market_sentiment() -> str:
    """
    Fetches the latest 3 headlines from Cointelegraph RSS.
    Returns a string summary.
    """
    rss_url = "https://cointelegraph.com/rss"
    try:
        feed = feedparser.parse(rss_url)
        headlines = []
        for entry in feed.entries[:3]:
            title = entry.title
            headlines.append(f"- {title}")
        
        if not headlines:
            return "No news available."
            
        return "\n".join(headlines)
    except Exception as e:
        logger.error(f"Error fetching RSS: {e}")
        return "Error fetching news."

def calculate_position_size(account_balance: float, risk_per_trade_pct: float, entry_price: float, stop_loss_price: float) -> float:
    """
    Calculates the position size (in base asset, e.g., BTC) based on risk percentage.
    Formula: (Balance * Risk%) / |Entry - StopLoss|
    """
    if entry_price <= 0 or stop_loss_price <= 0 or account_balance <= 0:
        return 0.0
    
    risk_amount = account_balance * (risk_per_trade_pct / 100.0)
    stop_distance = abs(entry_price - stop_loss_price)
    
    if stop_distance == 0:
        return 0.0
        
    raw_size = risk_amount / stop_distance
    
    # --- SAFETY: MAX LEVERAGE CAP (5x) ---
    max_lev = 5.0
    max_notional = account_balance * max_lev
    max_size = max_notional / entry_price
    
    final_size = min(raw_size, max_size)
    
    return round(final_size, 6)

def get_current_price(symbol: str) -> float:
    """
    Fetches the REAL-TIME current price (ticker) for execution accuracy.
    Avoids using 'Last Candle Close' which can be stale.
    """
    try:
        # Use GLOBAL exchange client (Reuse connection)
        ticker = exchange_client.fetch_ticker(symbol)
        return float(ticker['last'])
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return 0.0

def fetch_market_data(symbol: str, timeframe: str = '1h', limit: int = 500) -> pd.DataFrame:
    """
    Fetches OHLCV data from Binance using CCXT.
    Returns a DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
    """
    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
        return df
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        raise

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators using pure pandas (Manual Implementation for Py3.14 Compatibility).
    Includes: RSI(14), EMA(200), MACD, Bollinger Bands(20,2), ADX(14).
    """
    try:
        close = df['close']
        high = df['high']
        low = df['low']
        
        # --- RSI 14 ---
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # --- EMA 200 ---
        df['EMA_200'] = close.ewm(span=200, adjust=False).mean()
        
        # --- EMA 50 (Trend Filter) ---
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()
        
        # --- Bollinger Bands (20, 2) ---
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        df['BB_UPPER'] = sma_20 + (2 * std_20)
        df['BB_LOWER'] = sma_20 - (2 * std_20)
        df['BB_MID'] = sma_20 # SMA 20 Base Line

        # --- ADX 14 ---
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean() # Simplified ATR for stability
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        
        # Smooth DM and TR (Wilder's Smoothing usually, but simple rolling for approx is robust here)
        plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/14, adjust=False).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/14, adjust=False).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX_14'] = dx.ewm(alpha=1/14, adjust=False).mean()

        # --- ATR 14 (Volatility) ---
        df['ATR_14'] = atr

        # --- Support & Resistance (20-candle lookback) ---
        df['RES_20'] = high.rolling(window=20).max()
        df['SUP_20'] = low.rolling(window=20).min()

        # --- MACD (12, 26, 9) ---
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        df['MACD_12_26_9'] = macd
        df['MACDs_12_26_9'] = signal
        
        # Drop NaN values
        df.dropna(inplace=True)
        
        logger.info("Technical indicators calculated successfully (Pure Pandas).")
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        raise

def calculate_smart_money(df: pd.DataFrame) -> dict:
    """
    detects Smart Money Concepts (FVG, Swing Points) for AI Context.
    Returns a dict with formatted strings of key levels.
    """
    try:
        if df.empty or len(df) < 5:
            return {"fvg_str": "No FVG Detected", "liquidity_str": "No Liquidity Levels"}
            
        # 1. Fair Value Gaps (FVG)
        # Bullish FVG: Candle 1 High < Candle 3 Low
        # Bearish FVG: Candle 1 Low > Candle 3 High
        fvg_list = []
        
        # Check last 10 candles only for FRESH gaps (improving performance)
        subset = df.iloc[-15:]
        for i in range(len(subset) - 2):
            idx = subset.index[i]
            # Candle 1 (i), Candle 2 (i+1), Candle 3 (i+2)
            c1_high = subset['high'].iloc[i]
            c1_low = subset['low'].iloc[i]
            c3_high = subset['high'].iloc[i+2]
            c3_low = subset['low'].iloc[i+2]
            
            # Bullish FVG
            if c1_high < c3_low:
                fvg_list.append(f"🟢 Bullish FVG at {c1_high:.4f}-{c3_low:.4f} (Index -{len(subset)-i-2})")
            
            # Bearish FVG
            if c1_low > c3_high:
                fvg_list.append(f"🔴 Bearish FVG at {c3_high:.4f}-{c1_low:.4f} (Index -{len(subset)-i-2})")
        
        fvg_str = "\n".join(fvg_list[-3:]) if fvg_list else "None recently."
        
        # 2. Liquidity (Swing Highs/Lows) 
        # Pivot High: Higher than 2 left and 2 right
        # Pivot Low: Lower than 2 left and 2 right
        swings = []
        
        # Need a bit more historical context for swings
        # Analyze last 50 candles
        swing_subset = df.iloc[-50:]
        
        # Simple local extrema
        for i in range(2, len(swing_subset) - 2):
            curr_low = swing_subset['low'].iloc[i]
            curr_high = swing_subset['high'].iloc[i]
            
            # Swing Low
            if (swing_subset['low'].iloc[i-1] > curr_low) and \
               (swing_subset['low'].iloc[i-2] > curr_low) and \
               (swing_subset['low'].iloc[i+1] > curr_low) and \
               (swing_subset['low'].iloc[i+2] > curr_low):
                 swings.append(f"💧 Sell-Side Liquidity (Low): {curr_low:.4f}")
                 
            # Swing High
            if (swing_subset['high'].iloc[i-1] < curr_high) and \
               (swing_subset['high'].iloc[i-2] < curr_high) and \
               (swing_subset['high'].iloc[i+1] < curr_high) and \
               (swing_subset['high'].iloc[i+2] < curr_high):
                 swings.append(f"🔥 Buy-Side Liquidity (High): {curr_high:.4f}")
        
        liquidity_str = "\n".join(swings[-3:]) if swings else "None defined nearby."
        
        # 3. Candle Pattern Vision (NEW)
        patterns_str = detect_candle_patterns(df)
        
        return {
            "fvg_str": fvg_str,
            "liquidity_str": liquidity_str,
            "patterns_str": patterns_str # Expose to AI
        }

    except Exception as e:
        logger.error(f"SMC/Pattern Error: {e}")
        return {"fvg_str": "Error", "liquidity_str": "Error", "patterns_str": "None"}

def detect_candle_patterns(df: pd.DataFrame) -> str:
    """
    Scans the last 3 candles for classic Price Action patterns.
    Returns a descriptive string for the AI.
    """
    try:
        if df.empty: return "No Data"
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        patterns = []
        
        # Candle Properties
        body_last = abs(last['close'] - last['open'])
        range_last = last['high'] - last['low']
        
        # 1. ENGULFING (Strong Reversal)
        # Bullish Engulfing: Prev RED, Last GREEN, Last Body engulfs Prev Body
        if prev['close'] < prev['open']: # Red
            if last['close'] > last['open']: # Green
                if last['close'] > prev['open'] and last['open'] < prev['close']:
                     patterns.append("🔥 BULLISH ENGULFING (Strong Reversal)")
                     
        # Bearish Engulfing: Prev GREEN, Last RED, Last Body engulfs Prev Body
        if prev['close'] > prev['open']: # Green
            if last['close'] < last['open']: # Red
                if last['close'] < prev['open'] and last['open'] > prev['close']:
                     patterns.append("🩸 BEARISH ENGULFING (Strong Reversal)")
                     
        # 2. PINBARS (Rejection)
        # Hammer (Bullish): Small body, Long lower wick (>2x body), Little upper wick
        lower_wick = min(last['open'], last['close']) - last['low']
        upper_wick = last['high'] - max(last['open'], last['close'])
        
        if lower_wick > (body_last * 2) and upper_wick < (body_last * 0.5):
            patterns.append("🔨 HAMMER / PINBAR (Bullish Rejection)")
            
        # Shooting Star (Bearish): Small body, Long upper wick (>2x body), Little lower wick
        if upper_wick > (body_last * 2) and lower_wick < (body_last * 0.5):
            patterns.append("☄️ SHOOTING STAR (Bearish Rejection)")
            
        # 3. DOJI (Indecision)
        if range_last > 0 and body_last <= (range_last * 0.1): # Body is < 10% of total range
            patterns.append("✨ DOJI (Indecision)")
            
        return "\n".join(patterns) if patterns else "No clear patterns."
        
    except Exception as e:
        return f"Pattern Error: {e}"

def get_market_regime(df: pd.DataFrame) -> dict:
    """
    Diagnoses the current market environment (Trend vs. Chop).
    Used to filter simple parameter tweaks vs. logic changes.
    """
    try:
        last = df.iloc[-1]
        adx = last.get('ADX_14', 0)
        
        # Volatility Percentile (Are we in high or low vol relative to last 100 candles?)
        atr_series = df['ATR_14']
        current_atr = atr_series.iloc[-1]
        atr_rank = atr_series.rank(pct=True).iloc[-1] * 100 # 0-100 score
        
        regime = "UNDEFINED"
        if adx > 25:
            regime = "TRENDING"
        elif adx < 20:
            regime = "RANGING/CHOP"
            
        return {
            "type": regime,
            "adx": round(adx, 2),
            "volatility_rank": round(atr_rank, 1), # High rank = High Risk
            "current_atr": current_atr
        }
    except Exception as e:
        logger.error(f"Regime Error: {e}")
        return {"type": "ERROR", "adx": 0, "volatility_rank": 50}

def calculate_vpin_lite(df: pd.DataFrame) -> float:
    """
    VPIN Proxy (Volume-Synchronized Probability of Informed Trading) - LITE VERSION.
    Uses Volume / PriceRange ratio to detect 'churn' or 'toxic flow'.
    High VPIN (>0.8) = High volume with little movement (Absorption/Turning Point).
    """
    try:
        # Look at last 10 candles
        subset = df.iloc[-10:].copy()
        
        # Calculate Range (High - Low)
        subset['range'] = subset['high'] - subset['low']
        subset['range'] = subset['range'].replace(0, 0.000001) # Avoid div by zero
        
        # Metric: Volume per unit of movement
        subset['vol_per_move'] = subset['volume'] / subset['range']
        
        # Normalize relative to recent history (z-score-ish)
        avg_vpm = subset['vol_per_move'].mean()
        curr_vpm = subset['vol_per_move'].iloc[-1]
        
        # Ratio: Current / Average
        # If Current > 2.0 * Average -> Massive volume for candle size -> Toxic/Fighting
        vpin_score = min(curr_vpm / (avg_vpm if avg_vpm > 0 else 1), 3.0) 
        
        # Normalized 0.0 to 1.0 (Approx mapping)
        # 1.0 means 3x normal volume density (Very Toxic)
        return round(vpin_score / 3.0, 2) 
        
    except Exception as e:
        logger.error(f"VPIN Error: {e}")
        return 0.5

def get_latest_market_snippet(df: pd.DataFrame, label: str = "") -> str:
    """
    Returns a string summary of the most recent market data for AI context.
    ENRICHED: Now includes historical trends, last 3 candles, and volume analysis.
    """
    try:
        if df.empty:
            return f"{label} No Data"
        
        last = df.iloc[-1]
        current_close = last['close']
        current_rsi = last.get('RSI_14', 0)
        current_adx = last.get('ADX_14', 0)
        current_vol = last.get('volume', 0)
        
        # === BASE INFO ===
        snippet = f"{label}\n"
        snippet += f"Current: Close {current_close:.2f} | RSI {current_rsi:.2f} | ADX {current_adx:.2f}\n"
        
        # === HISTORICAL TRENDS (5 candles ago = 75 min for 15m, 20h for 4h) ===
        if len(df) >= 5:
            candles_ago_5 = df.iloc[-5]
            rsi_5_ago = candles_ago_5.get('RSI_14', 0)
            adx_5_ago = candles_ago_5.get('ADX_14', 0)
            vol_5_ago = candles_ago_5.get('volume', 0)
            
            # Calculate trends
            rsi_change = current_rsi - rsi_5_ago
            adx_change = current_adx - adx_5_ago
            vol_change_pct = ((current_vol - vol_5_ago) / vol_5_ago * 100) if vol_5_ago > 0 else 0
            
            # Trend arrows
            rsi_arrow = "↑" if rsi_change > 2 else "↓" if rsi_change < -2 else "→"
            adx_arrow = "↑" if adx_change > 2 else "↓" if adx_change < -2 else "→"
            vol_arrow = "↑" if vol_change_pct > 20 else "↓" if vol_change_pct < -20 else "→"
            
            snippet += f"5-Candle Trends:\n"
            snippet += f"  RSI: {rsi_5_ago:.1f} → {current_rsi:.1f} {rsi_arrow} ({rsi_change:+.1f})\n"
            snippet += f"  ADX: {adx_5_ago:.1f} → {current_adx:.1f} {adx_arrow} ({adx_change:+.1f})\n"
            snippet += f"  Volume: {vol_change_pct:+.1f}% {vol_arrow}\n"
        
        # === LAST 3 CANDLES (Price Action Journey) ===
        if len(df) >= 3:
            last_3 = df.iloc[-3:][['close', 'high', 'low', 'volume']].to_dict('records')
            snippet += f"Last 3 Candles:\n"
            for i, candle in enumerate(last_3, 1):
                candle_label = "NOW" if i == 3 else f"-{3-i}"
                snippet += f"  [{candle_label}] C:{candle['close']:.2f} H:{candle['high']:.2f} L:{candle['low']:.2f} V:{candle['volume']:.0f}\n"
        
        # === VOLUME ANALYSIS ===
        if len(df) >= 20:
            vol_recent_5 = df.iloc[-5:]['volume'].mean()
            vol_older_15 = df.iloc[-20:-5]['volume'].mean()
            
            if vol_recent_5 > vol_older_15 * 1.2:
                vol_trend = "INCREASING (Conviction growing)"
            elif vol_recent_5 < vol_older_15 * 0.8:
                vol_trend = "DECREASING (Low conviction)"
            else:
                vol_trend = "STABLE"
            
            snippet += f"Volume Trend: {vol_trend} (Avg: {vol_recent_5:.0f} vs {vol_older_15:.0f})\n"
        
        return snippet.strip()
        
    except Exception as e:
        logger.error(f"Snippet Error for {label}: {e}")
        return f"{label} Snippet Error"

def calculate_hurst(df: pd.DataFrame, max_lag=20) -> float:
    """
    Calculates the Hurst Exponent (H) to diagnose Market State.
    H > 0.5: Persistent (Trend) - Use Trend Following.
    H < 0.5: Anti-Persistent (Mean Reversion) - Use Ping-Pong.
    H = 0.5: Random Walk (Noise) - DO NOT TRADE.
    """
    try:
        # Use log-prices
        lags = range(2, max_lag)
        # Calculate standard deviation of differences
        tau = [np.sqrt(np.std(np.subtract(df['close'].values[lag:], df['close'].values[:-lag]))) for lag in lags]
        
        # Polyfit log(lags) vs log(tau)
        m = np.polyfit(np.log(lags), np.log(tau), 1)
        hurst = m[0] * 2.0
        
        return round(hurst, 3)
    except Exception as e:
        logger.error(f"Hurst Calc Error: {e}")
        return 0.5 # Default to Neutral (Random)
    """
    Returns a string representation of the last 10 candles for the LLM.
    Includes High/Low, ADX, BB, and News Sentiment.
    """
    # Get last 10 rows
    snippet = df.tail(10).copy()
    
    # Format as a readable string
    output = f"Recent Market Data {label} (Last 10 Candles):\n"
    # Select cols including new indicators
    cols = ['timestamp', 'close', 'high', 'low', 'RSI_14', 'ADX_14', 'EMA_50', 'EMA_200', 'BB_UPPER', 'BB_LOWER']
    output += snippet[cols].to_string(index=False)
    
    # Add explicit reference to latest vs trend
    latest = df.iloc[-1]
    output += f"\n\nLATEST SNAPSHOT:\n"
    output += f"Price: {latest['close']}\n"
    output += f"RSI: {latest['RSI_14']:.2f}\n"
    output += f"ADX Trend Strength: {latest['ADX_14']:.2f}\n"
    output += f"EMA 50: {latest['EMA_50']:.2f}\n"
    output += f"EMA 200: {latest['EMA_200']:.2f}\n"
    output += f"BB Width: {(latest['BB_UPPER'] - latest['BB_LOWER']):.2f}\n"
    
    # --- PRE-CALCULATED LOGIC (Prevent AI Math Hallucinations) ---
    ema50 = latest['EMA_50']
    ema200 = latest['EMA_200']
    price = latest['close']
    
    trend = "UPTREND (EMA50 > EMA200)" if ema50 > ema200 else "DOWNTREND (EMA50 < EMA200)"
    price_pos = "ABOVE EMA50" if price > ema50 else "BELOW EMA50"
    
    # Dynamic Targets
    res = latest.get('RES_20', 0)
    sup = latest.get('SUP_20', 0)
    atr = latest.get('ATR_14', 0)
    
    output += f"\n--- ANALISIS PRE-CALCULADO (Verificado por Python) ---\n"
    output += f"- Tendencia EMA: {trend}\n"
    output += f"- Posicion Precio: {price_pos}\n"
    output += f"- Volatilidad (ATR): {atr:.2f}\n"
    output += f"- Techo (Resistencia): {res}\n"
    output += f"- Piso (Soporte): {sup}\n"
    
    if sentiment_text:
        output += f"\n\nNEWS SENTIMENT (Context):\n{sentiment_text}\n"
    
    return output

# --- File I/O Functions ---

def _read_file_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='cp1252', errors='replace') as f:
                return f.read()
        except:
            return ""
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        return ""

def read_constitution(path: str = 'constitution.md') -> str:
    """Result: Content of constitution.md (Safety Rules)."""
    content = _read_file_safe(path)
    if not content:
        # logging handled in safe reader for file not found, but we can log specific error if needed
        pass
    return content

def read_strategy(path: str = 'strategy.md') -> str:
    """Result: Content of strategy.md (Operational Rules)."""
    content = _read_file_safe(path)
    if not content:
        logger.warning(f"Strategy file missing at {path}. Creating default strategy.")
        default_strat = "# Hybrid Strategy\n\n1. Trend Following on 4H.\n2. Overbought/Oversold entries on 15m.\n3. Risk clean 2% per trade."
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(default_strat)
            return default_strat
        except:
             return "Strategy unavailable."
    return content

def update_strategy(new_content):
    """Overwrites strategy.md safely."""
    try:
        with open("strategy.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        logger.info("Strategy file updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update strategy: {e}")

def log_strategy_update(reason: str, symbol: str, pnl: float):
    """Appends an entry to strategy_history.md"""
    history_file = "strategy_history.md"
    if not os.path.exists(history_file):
        with open(history_file, "w", encoding="utf-8") as f:
            f.write("# Historial de Cambios de Estrategia\n\n| Fecha | Símbolo | PnL | Razón/Cambio |\n|---|---|---|---|\n")
            
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Simple table row
    entry = f"| {timestamp} | {symbol} | ${pnl:.2f} | {reason} |\n"
    
    try:
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        logger.error(f"Failed to write to history log: {e}")
        return False

def read_state(path: str = 'state.json') -> dict:
    """Reads the agent's persistent state."""
    default_state = {
        "current_positions": [],
        "trade_history": [],
        "performance_metrics": {
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0
        },
        "account_balance": 10000.0,
        "last_run": "",
        "latest_analysis": {}
    }

    try:
        if not os.path.exists(path):
            logger.info("State file not found. Initializing new default state.")
            return default_state
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key, value in default_state.items():
                if key not in data:
                    data[key] = value
            return data
    except Exception as e:
        logger.error(f"Error reading state: {e}. Reverting to temporary default state.")
        return default_state

def write_state(state: dict, path: str = 'state.json') -> bool:
    """Writes the agent's persistent state."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error writing state: {e}")
        return False
