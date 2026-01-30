# main.py
# Orchestrator for the Autonomous Trading Agent.
# Integrates Trading Tools and Agent Logic.

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


import logging
import time
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Import modules
# Import modules
import trading_tools as tools
import agent_logic as brain
import strategies # QUANT STRATEGIES
import market_profile as mp # VOLUME PROFILE STRATEGY
import market_monitor as mm # STATISTICAL DRIFT DETECTION
import order_flow as flow     # TOXICITY DETECTION

# FORCE UTF-8 for Windows Console to support Emojis 🚫
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass # Python < 3.7

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Main")

PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT',
    'DOGE/USDT', 'FET/USDT', 'WIF/USDT',
    'APT/USDT', 'AVAX/USDT', 'ENA/USDT', 'XRP/USDT', 'SUI/USDT', 'NEAR/USDT'
]
TIMEFRAME_MICRO = '15m'
TIMEFRAME_MACRO = '4h'

def check_gatekeeper(df):
    """
    The Gatekeeper (Pre-filter) on MICRO timeframe (15m).
    """
    last = df.iloc[-1]
    
    # 1. ADX > 20 (Expanded for 15m volatility)
    if last.get('ADX_14', 0) > 20:
        return True, "ADX Active"
        
    # 2. RSI Extremes
    rsi = last.get('RSI_14', 50)
    if rsi < 35 or rsi > 65:
        return True, f"RSI Alert ({rsi:.1f})"
        
    # 3. Bollinger Band Approach
    price = last['close']
    bb_up = last.get('BB_UPPER', 9999999)
    bb_low = last.get('BB_LOWER', 0)
    
    # 15m can be volatile, check touch
    if price >= bb_up * 0.998 or price <= bb_low * 1.002:
        return True, "BB Proximity"

    return False, "No Signal"

def detect_breakout(df_micro, vp_data):
    """
    Detects if price is breaking out of established range.
    """
    last_candle = df_micro.iloc[-1]
    prev_candle = df_micro.iloc[-2]
    
    price = last_candle['close']
    volume = last_candle['volume']
    
    # Calculate average volume (excluding current candle)
    avg_volume = df_micro['volume'].iloc[-21:-1].mean()
    if avg_volume == 0: avg_volume = 1 # Avoid div by zero
    
    vah = vp_data['VAH']
    val = vp_data['VAL']
    
    # Bullish Breakout
    if price > vah and volume > avg_volume * 1.5:
        if prev_candle['close'] <= vah * 1.002:  # Just broke out (or near enough)
            return {
                'type': 'BULLISH_BREAKOUT',
                'confidence': 'HIGH' if volume > avg_volume * 2 else 'MEDIUM',
                'level': vah
            }
    
    # Bearish Breakdown
    if price < val and volume > avg_volume * 1.5:
        if prev_candle['close'] >= val * 0.998:  # Just broke down
            return {
                'type': 'BEARISH_BREAKDOWN',
                'confidence': 'HIGH' if volume > avg_volume * 2 else 'MEDIUM',
                'level': val
            }
    
    return None

def classify_market_regime(df_micro, df_macro, vp_data, btc_pct_change, drift_detected):
    """
    Comprehensive regime classification.
    Returns regime info dict.
    """
    adx_4h = df_macro.iloc[-1].get('ADX_14', 0)
    hurst = tools.calculate_hurst(df_macro)
    
    breakout_info = detect_breakout(df_micro, vp_data)
    
    # Priority 1: Breakout (overrides everything)
    if breakout_info:
        return {
            'regime': 'BREAKOUT',
            'playbook': 'MOMENTUM_CATCH',
            'bias': 'LONG' if breakout_info['type'] == 'BULLISH_BREAKOUT' else 'SHORT',
            'confidence_adjustment': +1,
            'reason': f"{breakout_info['type']} detected with {breakout_info['confidence']} volume"
        }
    
    # Priority 2: Strong Trend (4H)
    if adx_4h > 25 or hurst > 0.65:
        price_4h = df_macro.iloc[-1]['close']
        ema200_4h = df_macro.iloc[-1].get('EMA_200', 0)
        
        return {
            'regime': 'TRENDING',
            'playbook': 'TREND_FOLLOWING',
            'bias': 'LONG' if price_4h > ema200_4h else 'SHORT',
            'confidence_adjustment': +1 if abs(btc_pct_change) > 1.5 else 0,
            'reason': f"Strong trend detected (ADX {adx_4h:.1f}, Hurst {hurst:.2f})"
        }
    
    # Priority 3: Range (Low ADX + Low Hurst + No BTC Pump/Dump)
    if adx_4h < 25 and hurst < 0.45 and abs(btc_pct_change) < 1.0:
        channel_width = 0
        if vp_data['POC'] > 0:
            channel_width = (vp_data['VAH'] - vp_data['VAL']) / vp_data['POC']
        
        if channel_width > 0.025:  # At least 2.5% wide channel to trade
            return {
                'regime': 'RANGE',
                'playbook': 'MEAN_REVERSION',
                'bias': 'BIDIRECTIONAL',
                'confidence_adjustment': 0,
                'reason': f"Range-bound market (ADX {adx_4h:.1f}, Channel {channel_width*100:.1f}%)"
            }
    
    # Priority 4: Concept Drift (Defensive)
    if drift_detected or (hurst > 0.35 and hurst < 0.65): # Noise Zone
        return {
            'regime': 'UNCERTAIN',
            'playbook': 'DEFENSIVE',
            'bias': 'ONLY_IF_PERFECT',
            'confidence_adjustment': -2,
            'reason': "Market in Noise Zone / Drift - require exceptional setups"
        }
    
    # Default: Wait
    return {
        'regime': 'NEUTRAL',
        'playbook': 'WAIT',
        'bias': None,
        'confidence_adjustment': 0,
        'reason': "No clear regime - waiting for setup"
    }

def calculate_position_size_by_regime(regime, account_balance, risk_pct, entry, sl):
    """
    Adjust position size based on regime characteristics.
    """
    base_size = tools.calculate_position_size(account_balance, risk_pct, entry, sl)
    
    multipliers = {
        'TRENDING': 1.0,      # Full size (high R:R expected)
        'RANGE': 0.75,        # Reduced (lower R:R, higher frequency)
        'BREAKOUT': 0.85,     # Slightly reduced (can fail violently)
        'UNCERTAIN': 0.5,     # Half size (defensive)
        'NEUTRAL': 0.0        # No position
    }
    
    multiplier = multipliers.get(regime, 0.0)
    final_size = base_size * multiplier
    
    return final_size

def process_pair(symbol, btc_context_str, global_sentiment):
    """
    Analyzes and manages a single pair.
    Returns True if AI analysis was performed (used for rate limiting).
    """
    logger.info(f"--- Processing {symbol} ---")
    
    state = tools.read_state()
    constitution = tools.read_constitution()
    strategy = tools.read_strategy()
    
    if not constitution or not strategy:
        logger.critical("Constitution or Strategy missing. Aborting.")
        return False

    # 2. Fetch Data (MICRO FIRST)
    try:
        # --- PASO 1: MICRO (15m) ---
        df_micro = tools.fetch_market_data(symbol, TIMEFRAME_MICRO, limit=100)
        df_micro = tools.calculate_indicators(df_micro)
        
        if df_micro.empty:
             logger.warning(f"Insufficient data for {symbol} (MICRO). Skipping.")
             return False
        
        # --- PASO 2: FILTRO (Gatekeeper) en 15m ---
        is_interesting, gate_reason = check_gatekeeper(df_micro)
        
        current_positions = state.get('current_positions', [])
        has_open_position = any(p['symbol'] == symbol for p in current_positions)
        
        # --- HIGH PRIORITY: MANUAL CLOSE CHECK ---
        safe_symbol = symbol.replace('/', '_')
        close_req_path = os.path.join(r"C:\Users\USER\AgenTra", f"CLOSE_{safe_symbol}.req")
        is_manual_close = os.path.exists(close_req_path)
        
        if is_manual_close:
            logger.info(f"🚨 MANUAL CLOSE SIGNAL DETECTED for {symbol}. Bypassing filters to Execute.")
            has_open_position = True # Force recognition just in case
        
        if not is_interesting and not has_open_position and not is_manual_close:
            logger.info(f">> Skipping {symbol}: {gate_reason} (Token Saver Mode)")
            return False
            
        if has_open_position:
            # logger.info(f"Position active for {symbol}. Proceeding to AI management.")
            pass # Silent continue
        else:
            logger.info(f"[OK] CANDIDATE DETECTED: {symbol} [{gate_reason}]. Fetching MACRO...")

        # --- PASO 3: MACRO (4h) ---
        # Solo descargamos esto si pasa el filtro (Ahorro de API de Exchange y proceso)
        df_macro = tools.fetch_market_data(symbol, TIMEFRAME_MACRO, limit=100)
        df_macro = tools.calculate_indicators(df_macro)

        # Prepare Contexts
        sentiment = global_sentiment
        summary_micro = tools.get_latest_market_snippet(df_micro, label=f"({TIMEFRAME_MICRO})")
        summary_macro = tools.get_latest_market_snippet(df_macro, label=f"({TIMEFRAME_MACRO})")
        
        # --- QUANT METRICS (Regime & VPIN Pro) ---
        regime_data = tools.get_market_regime(df_micro)
        vpin_score = flow.calculate_vpin_pro(df_micro)
        regime_data['vpin'] = vpin_score # Combine for context
        
        smc_data = tools.calculate_smart_money(df_micro)
        hurst_val = tools.calculate_hurst(df_macro)
        
        # --- VOLUME PROFILE (POC, VAH, VAL) ---
        vp_data = mp.calculate_volume_profile(df_micro)
        
        # --- BTC VOLATILITY CONTEXT ---
        btc_pct = 0.0
        try:
             # Parse "-2.01%" string to float
             btc_pct = float(btc_context_str.split('%')[0].split(':')[-1].strip())
        except: pass
        
        # --- CONCEPT DRIFT DETECTION (KS-TEST) ---
        # Compare last 50 candles (current) vs prior 50-200 (baseline)
        drift_data = mm.detect_drift(df_micro['close'].iloc[-50:], df_micro['close'].iloc[-200:-50])
        
        # --- REGIME CLASSIFICATION (OMNIDIRECTIONAL) ---
        regime_info = classify_market_regime(df_micro, df_macro, vp_data, btc_pct, drift_data['drift_detected'])
        
        # Extract for Logging & Context
        regime_type = regime_info['regime']
        playbook = regime_info['playbook']
        
        smc_context_str = f"--- MARKET PHYSICS (QUANT) ---\n" \
                          f"Regime: {regime_type} (Playbook: {playbook})\n" \
                          f"Bias: {regime_info['bias']}\n" \
                          f"Reason: {regime_info['reason']}\n" \
                          f"Hurst: {hurst_val:.2f} | VPIN: {vpin_score}\n\n" \
                          f"--- VOLUME PROFILE (15m) ---\n" \
                          f"{vp_data['profile_str']}\n\n" \
                          f"--- SMART MONEY CONCEPTS (15m) ---\n" \
                          f"FAIR VALUE GAPS:\n{smc_data['fvg_str']}\n\n" \
                          f"LIQUIDITY POOLS (Swing Highs/Lows):\n{smc_data['liquidity_str']}\n\n" \
                          f"CANDLE PATTERNS (Vision):\n{smc_data.get('patterns_str', 'None')}"

        current_price = df_micro.iloc[-1]['close'] # Execution price is always Micro close
        
    except Exception as e:
        logger.error(f"Data/Filter failed for {symbol}: {e}")
        return False

    # 3. AI Analysis (Dual Context + Correlation + SMC)
    # --- RATE LIMIT LOGIC: Only call AI once per candle (15m) ---
    current_time_ts = datetime.now(timezone.utc).timestamp()
    last_analysis_str = state.get('last_ai_analysis', {}).get(symbol, "1970-01-01 00:00:00 UTC")
    try:
        if ' UTC' not in last_analysis_str: last_analysis_str += ' UTC'
        last_analysis_dt = datetime.strptime(last_analysis_str, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        last_analysis_ts = last_analysis_dt.timestamp()
    except:
        last_analysis_ts = 0
        
    seconds_since_analysis = current_time_ts - last_analysis_ts
    
    # Defaults (if AI is skipped)
    decision = "HOLD"
    confidence = 0
    reason = "Rate Limit (Waiting for Candle Close)"
    stop_loss_price = None
    take_profit_price = None
    
    # LOGIC: Call AI if > 14 mins have passed OR if we have no record
    # ABSOLUTELY SKIP AI IF MANUAL CLOSE IS PENDING
    should_call_ai = (seconds_since_analysis > (14 * 60)) and not is_manual_close
    
    if should_call_ai:
        logger.info(f"Requesting AI decision for {symbol} (Playbook: {playbook})...")
        decision_packet = brain.analyze_market_omnidirectional(
            summary_micro=summary_micro, 
            summary_macro=summary_macro, 
            regime_info=regime_info,
            strategy_content=strategy, 
            constitution_content=constitution, 
            sentiment_text=sentiment,
            btc_context_str=btc_context_str,
            smc_context_str=smc_context_str
        )
        decision = decision_packet.get("decision", "HOLD").upper()
        reason = decision_packet.get("reason", "No reason provided")
        confidence = int(decision_packet.get("confidence", 0))
        stop_loss_price = decision_packet.get("stop_loss")
        take_profit_price = decision_packet.get("take_profit")
        
        logger.info(f"AI Decision ({symbol}): {decision} [Confidence: {confidence}/10]")
        
        # Update Timestamp (init dict if needed)
        if 'last_ai_analysis' not in state: state['last_ai_analysis'] = {}
        state['last_ai_analysis'][symbol] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        tools.write_state(state) # Persist immediately
    else:
        logger.debug(f"Skipping AI for {symbol} (Analysed {int(seconds_since_analysis/60)}m ago)")

    # 4. Execution Logic (Runs EVERY TICK for Trailing/SL/TP)
    # We pass 'decision' down. If AI was skipped, decision is HOLD, 
    # BUT Trailing Logic below can override it to "SELL" / "BUY" if stops are hit.
    my_positions = [p for p in state.get('current_positions', []) if p['symbol'] == symbol]

    
    trade_executed = False
    
    # helper to safe cast
    def safe_float(val):
        try: return float(val)
        except: return None

    stop_loss_price = safe_float(stop_loss_price)
    take_profit_price = safe_float(take_profit_price)
    
    # --- SL LOGIC GUARD (Prevent AI Hallucinations) ---
    if stop_loss_price and current_price > 0:
        # Calculate backup ATR for safety
        atr_guard = df_micro.iloc[-1].get('ATR_14', current_price * 0.01)
        
        if decision == "BUY" and stop_loss_price >= current_price:
             old_sl = stop_loss_price
             stop_loss_price = current_price - (2.0 * atr_guard)
             logger.warning(f"⚠️ SL FIXED: AI proposed LONG SL {old_sl} >= Entry {current_price}. Corrected to {stop_loss_price:.5f}")
             
        elif decision == "SELL" and stop_loss_price <= current_price:
             old_sl = stop_loss_price
             # For Shorts, SL must be ABOVE entry
             stop_loss_price = current_price + (2.0 * atr_guard)
             logger.warning(f"⚠️ SL FIXED: AI proposed SHORT SL {old_sl} <= Entry {current_price}. Corrected to {stop_loss_price:.5f}")
    
    if not my_positions:
        # DEBUG TRACE
        print(f"DEBUG: NO POSITION for {symbol}")
        # NO POSITION - CHECK CONFIDENCE
        total_open_positions = len(state.get('current_positions', []))
        MAX_CONCURRENT = 3 # RISK GUARD: Max 3 positions at once

        if total_open_positions >= MAX_CONCURRENT and decision != "HOLD":
             logger.warning(f"🚫 MAX POSITIONS ({MAX_CONCURRENT}) REACHED. Ignoring Entry for {symbol}.")
             decision = "HOLD"

        if confidence < 5 and decision != "HOLD":
            logger.info(f"Decision {decision} ignored due to LOW CONFIDENCE ({confidence}/10).")
            decision = "HOLD" # Force Hold

        size = 0.0
        if stop_loss_price and decision != "HOLD":
            # --- OMNIDIRECTIONAL SIZING ---
            raw_size = calculate_position_size_by_regime(
                regime=regime_info['regime'],
                account_balance=state.get("account_balance", 10000.0),
                risk_pct=2.0,
                entry=current_price,
                sl=stop_loss_price
            )
            
            # --- DYNAMIC ALLOCATION (Based on Confidence) ---
            allocation_pct = 1.0 # Default 100%
            if confidence >= 9:
                allocation_pct = 1.0
                logger.info(f"High Confidence ({confidence}/10): Using 100% Allocation.")
            elif confidence >= 7:
                allocation_pct = 0.75
                logger.info(f"Mid-High Confidence ({confidence}/10): Using 75% Allocation.")
            elif confidence >= 5:
                allocation_pct = 0.50
                logger.info(f"Mid Confidence ({confidence}/10): Using 50% Allocation.")
            else:
                 allocation_pct = 0.0 # Should be filtered by <5 check above, but purely safe
                 logger.info(f"Low Confidence ({confidence}/10): Skipping.")
            
            size = raw_size * allocation_pct
            
            # --- SAFETY NET: Ensure TP Exists ---
            if not take_profit_price and stop_loss_price:
                risk = abs(current_price - stop_loss_price)
                # Default 2R Target
                if decision == "BUY":
                    take_profit_price = current_price + (risk * 2.0)
                elif decision == "SELL":
                    take_profit_price = current_price - (risk * 2.0)
                logger.info(f"⚠️ AI missing TP. Calculated Safety Net TP: {take_profit_price:.4f} (2R)")
            elif not take_profit_price:
                 # Fallback if even SL is missing (unlikely due to Trading Tools)
                 atr_fallback = df_micro.iloc[-1].get('ATR_14', current_price*0.01)
                 if decision == "BUY": take_profit_price = current_price + (3 * atr_fallback)
                 elif decision == "SELL": take_profit_price = current_price - (3 * atr_fallback)
            
        if decision == "BUY":
            if size > 0:
                entry = {
                    "symbol": symbol,
                    "type": "LONG",
                    "entry_price": current_price,
                    "quantity": size,
                    "entry_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "stop_loss": stop_loss_price,
                    "initial_stop_loss": stop_loss_price, # SAVE ORIGINAL
                    "take_profit": take_profit_price,
                    "reason": decision_packet.get("reason"),
                    "regime_at_entry": regime_data,
                    "strategy_used": regime_type, # TAG FOR META-LEARNER
                    "current_price": current_price,
                    "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                state['current_positions'].append(entry)
                msg = f"[LONG] **OPEN LONG** {symbol}\nPrice: {current_price}\nSize: {size:.4f} (Conf: {confidence})\nSL: {stop_loss_price}"
                logger.info(msg)
                tools.send_telegram_message(msg)
                trade_executed = True
                
        elif decision == "SELL":
             if size > 0:
                entry = {
                    "symbol": symbol,
                    "type": "SHORT",
                    "entry_price": current_price,
                    "quantity": size,
                    "entry_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "stop_loss": stop_loss_price,
                    "initial_stop_loss": stop_loss_price, # SAVE ORIGINAL
                    "take_profit": take_profit_price,
                    "reason": decision_packet.get("reason"),
                    "regime_at_entry": regime_data,
                    "strategy_used": regime_type, # TAG FOR META-LEARNER
                    "current_price": current_price,
                    "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                state['current_positions'].append(entry)
                msg = f"[SHORT] **OPEN SHORT** {symbol}\nPrice: {current_price}\nSize: {size:.4f} (Conf: {confidence})\nSL: {stop_loss_price}"
                logger.info(msg)
                tools.send_telegram_message(msg)
                trade_executed = True

    else:
        # EXISTING POSITION
        # DEBUG TRACE
        print(f"DEBUG: EXISTING POS for {symbol}")
        
        decision = "HOLD" # Initialize default to prevent UnboundLocalError
        pos = my_positions[0]
        pos_type = pos['type']
        entry_price = float(pos['entry_price'])
        quantity = pos.get('quantity', 0.0)
        # Ensure we have a stop_loss, even if None initially (safety)
        current_sl = float(pos.get('stop_loss') or (entry_price * 0.95 if pos_type == 'LONG' else entry_price * 1.05))
        
        # Define Take Profit & Distance for BE Logic
        take_profit = float(pos.get('take_profit', 0) or 0)
        if take_profit > 0:
            tp_dist = abs(take_profit - entry_price)
        else:
            tp_dist = float('inf') # Infinite distance if no TP
        
        # Use REAL TIME price for Execution and Trailing (Not candle close)
        real_price = tools.get_current_price(symbol)
        if real_price == 0: real_price = current_price # Fallback to candle close

        # DEBUG PRICE MONITOR (For User Confidence)
        print(f"DEBUG PRICE: {symbol} | Live: {real_price} | SL: {current_sl} | TP: {take_profit}")

        # Update current price in state for Dashboard visibility
        pos['current_price'] = real_price
        pos['last_update'] = str(df_micro.iloc[-1]['timestamp']) # Keep candle timestamp
        
        # --- TRAILING STOP LOGIC (SIMPLIFIED / ROBUST) ---
        atr = df_micro.iloc[-1].get('ATR_14', 0)
        
        # Hard Floor Logic: 0.2% minimum distance to allow breathing room
        min_dist = entry_price * 0.002
        
        # Simplified Calculation: Just ATR * 1.5
        # No more "Volatility Factors" or "Buffers" that block movement
        atr_dist = 1.5 * atr if atr > 0 else 0
        
        final_dist = max(atr_dist, min_dist)
        
        if atr > 0:
            # 1. Break Even Check (If profit > 1x ATR, OR > 50% of TP)
            be_trigger = min(atr, tp_dist * 0.5) if tp_dist != float('inf') else atr
            
            if pos_type == "LONG":
                # Use real_price for triggering
                if real_price > (entry_price + be_trigger) and current_sl < entry_price:
                    logger.info(f"Moving SL to Break Even for {symbol}")
                    pos['stop_loss'] = entry_price
                    current_sl = entry_price
                    tools.send_telegram_message(f"🛡️ **BREAK EVEN** {symbol}\nStop moved to Entry: {entry_price}")
                
                # 2. Trailing (If price moves up, drag SL at final_dist)
                new_sl = real_price - final_dist
                if new_sl > current_sl:
                    logger.info(f"Trailing SL Up for {symbol} to {new_sl:.2f} (Dist: {final_dist:.4f})")
                    pos['stop_loss'] = new_sl
                    current_sl = new_sl
                    
                # 3. STOP HIT CHECK
                if real_price <= current_sl: # Check Live Price vs SL
                    decision = "SELL"
                    # GUARANTEED STOP EMULATION: Exit at SL Price (Limit Stop Simulator)
                    current_price = current_sl 
                    reason = "TRAILING STOP HIT (LIVE)"
                
                # 4. TAKE PROFIT CHECK
                take_profit = float(pos.get('take_profit', 0) or 0)
                
                 # SENSOR UPGRADE: Check Last 3 Candles relative to ENTRY TIME (Long)
                entry_time_str = pos.get('entry_time', '')
                try:
                    et_clean = entry_time_str.replace(' UTC', '')
                    entry_dt = pd.to_datetime(et_clean)
                    relevant_candles = df_micro[df_micro['timestamp'] >= entry_dt]
                    
                    if not relevant_candles.empty:
                         last_highs = relevant_candles['high'].max()
                    else:
                         last_highs = df_micro.iloc[-1]['high']
                except:
                    last_highs = df_micro.iloc[-1]['high']

                # Check BOTH Live Price and Valid History (Wick)
                if take_profit > 0 and (real_price >= take_profit or last_highs >= take_profit):
                    logger.info(f"✅ TP TRIGGERED! Price/Wick:{max(real_price, last_highs)} >= TP:{take_profit}")
                    decision = "SELL"
                    current_price = real_price if real_price >= take_profit else take_profit
                    reason = "TAKE PROFIT HIT (LIVE/WICK)"
                    
            elif pos_type == "SHORT":
                # Use be_trigger (Dynamic 50% TP or ATR) instead of fixed ATR
                if real_price < (entry_price - be_trigger) and current_sl > entry_price:
                    logger.info(f"Moving SL to Break Even for {symbol}")
                    pos['stop_loss'] = entry_price
                    current_sl = entry_price
                    tools.send_telegram_message(f"🛡️ **BREAK EVEN** {symbol}\nStop moved to Entry: {entry_price}")

                # 2. Trailing (Drag SL down at final_dist)
                new_sl = real_price + final_dist
                if new_sl < current_sl:
                    logger.info(f"Trailing SL Down for {symbol} to {new_sl:.2f} (Dist: {final_dist:.4f})")
                    pos['stop_loss'] = new_sl
                    current_sl = new_sl
                    
                # 3. STOP HIT CHECK
                if real_price >= current_sl: # Check Live Price vs SL
                    decision = "BUY"
                    # GUARANTEED STOP EMULATION: Exit at SL Price
                    current_price = current_sl
                    reason = "TRAILING STOP HIT (LIVE)"

                # 4. TAKE PROFIT CHECK
                take_profit_val = pos.get('take_profit', 0)
                take_profit = float(take_profit_val) if take_profit_val else 0
                
                # SENSOR UPGRADE: Check Last 3 Candles relative to ENTRY TIME
                # Fixes 'Time Travel' bug where old wicks triggered new trades
                entry_time_str = pos.get('entry_time', '')
                try:
                    # Convert Entry Time string to Timestamp
                    # Format: 2026-01-29 01:54:35 UTC
                    et_clean = entry_time_str.replace(' UTC', '')
                    entry_dt = pd.to_datetime(et_clean)
                    
                    # Filter candles that happened AFTER or ON entry
                    # df_micro['timestamp'] is already dt object per fetch_market_data
                    relevant_candles = df_micro[df_micro['timestamp'] >= entry_dt]
                    
                    if not relevant_candles.empty:
                         last_lows = relevant_candles['low'].min()
                    else:
                         last_lows = df_micro.iloc[-1]['low'] # Fallback to current
                except Exception as e:
                    # logger.error(f"Time Filter Error: {e}")
                    last_lows = df_micro.iloc[-1]['low']

                # Check BOTH Live Price and Valid History
                if take_profit > 0 and (real_price <= take_profit or last_lows <= take_profit):
                    logger.info(f"✅ TP TRIGGERED! Price/Wick:{min(real_price, last_lows)} <= TP:{take_profit}")
                    decision = "BUY"
                    current_price = real_price if real_price <= take_profit else take_profit
                    reason = "TAKE PROFIT HIT (LIVE/WICK)"

        
        if os.path.exists("STOP_REQUEST"):
             decision = "SELL" if pos_type == "LONG" else "BUY"
             reason = "KILL SWITCH"
             try: os.remove("STOP_REQUEST")
             except: pass

        # --- CHECK FOR MANUAL CLOSE REQUEST (From Dashboard) ---
        safe_symbol = symbol.replace('/', '_')
        # USE ABSOLUTE PATH matching dashboard
        close_req_path = os.path.join(r"C:\Users\USER\AgenTra", f"CLOSE_{safe_symbol}.req")
        
        
        # DEBUG LOGGING (Temporary)
        print(f"DEBUG Check: {symbol} -> {close_req_path} | Exists: {os.path.exists(close_req_path)}")
        
        if os.path.exists(close_req_path):
            decision = "SELL" if pos_type == "LONG" else "BUY"
            reason = "MANUAL DASHBOARD CLOSE"
            try: os.remove(close_req_path)
            except: pass
            logger.info(f"🚨 MANUAL CLOSE DETECTED for {symbol}")

        if (pos_type == "LONG" and decision == "SELL") or \
           (pos_type == "SHORT" and decision == "BUY"):
            
            price_change = (current_price - entry_price) if pos_type == "LONG" else (entry_price - current_price)
            realized_pnl_usd = price_change * quantity
            pnl_percent = (price_change / entry_price) * 100
            
            # --- FORENSIC DATA FOR RECORDING ---
            forensic_context = {
                "exit_regime": regime_data,
                "entry_regime": pos.get("regime_at_entry", {}),
                "strategy_used": pos.get("strategy_used", "UNKNOWN") # DATA FOR META-LEARNER
            }
            
            _record_trade(state, symbol, pos_type, entry_price, current_price, pnl_percent, realized_pnl_usd, reason, forensic_context)
            
            # --- FORENSIC MEMORY: Save Lesson ---
            result_str = "WIN" if realized_pnl_usd > 0 else "LOSS"
            brain.record_lesson(symbol, result_str, f"{reason} | PnL: {pnl_percent:.2f}%")
            
            msg = f"[WIN/LOSS] **CLOSE {pos_type}** {symbol}\nPnL: ${realized_pnl_usd:.2f} ({pnl_percent:.2f}%)"
            logger.info(msg)
            tools.send_telegram_message(msg)
            trade_executed = True
            
            state['current_positions'] = [p for p in state['current_positions'] if p['symbol'] != symbol]
            
        else:
             logger.info(f"Holding {symbol} {pos_type}.")

    # Save State
    state['last_run'] = str(df_micro.iloc[-1]['timestamp'])
    
    # Update dashboard (Show MICRO indicators as primary for liveliness)
    state['latest_analysis'] = {
        "symbol": symbol,
        "price": current_price,
        "rsi": df_micro.iloc[-1]['RSI_14'],
        "adx": df_micro.iloc[-1].get('ADX_14', 0)
    }
    tools.write_state(state)
    return True # AI was called


def _record_trade(state, symbol, type, entry, exit, pnl_pct, pnl_usd, reason, context):
    """Helper to save trade history with Forensic Context"""
    trade_record = {
        "symbol": symbol,
        "type": type,
        "entry_price": entry,
        "exit_price": exit,
        "exit_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "pnl_percent": pnl_pct,
        "realized_pnl": pnl_usd,
        "reason": reason,
        "context": context # SAVE FORENSIC CONTEXT
    }
    
    state['trade_history'].append(trade_record)
    state['performance_metrics']['total_pnl'] += pnl_usd
    state["account_balance"] += pnl_usd
    
    if pnl_usd > 0: state['performance_metrics']['wins'] += 1
    else: state['performance_metrics']['losses'] += 1
    
    if pnl_usd < 0:
        logger.info("Loss detected. Triggering Forensic Reflexion...")
        strategy = tools.read_strategy()
        
        # PASS CONTEXT TO REFLEXION ENGINE (COMMENTED OUT FOR RESCUE PLAN)
        # market_context = context.get('exit_regime', {})
        # new_strategy, change_reason = brain.reflect_on_performance(state['trade_history'], strategy, market_context)
        
        # if new_strategy != strategy:
        #     logger.info("Agent proposed a strategy update.")
        #     tools.send_telegram_message(f"[BRAIN] **STRATEGY UPDATED**\nReason: {change_reason}")
            
            # Log the specific reason to the history file
            # tools.log_strategy_update(change_reason, symbol, pnl_usd)
            
            # tools.update_strategy(new_strategy)


def run_orchestrator():
    """Loops through all pairs."""
    print("\n--- 💓 HEARTBEAT: Starting Loop 💓 ---")
    logger.info("--- Starting Multi-Pair Cycle (15m/4h) ---")
    
    # --- BITCOIN (THE LEADER) CHECK ---
    btc_context_str = "Unknown"
    try:
        # Fetch tiny snapshot of BTC 1h just for correlation
        btc_df = tools.fetch_market_data('BTC/USDT', '1h', limit=5)
        if not btc_df.empty and len(btc_df) >= 2:
            now_price = btc_df.iloc[-1]['close']
            prev_price = btc_df.iloc[-2]['close'] # Previous hour close
            pct_change = ((now_price - prev_price) / prev_price) * 100
            trend_label = "DUMPING 🩸" if pct_change < -1.0 else "PUMPING 🚀" if pct_change > 1.0 else "NEUTRAL"
            btc_context_str = f"Bitcoin 1h Change: {pct_change:.2f}% ({trend_label})"
            logger.info(f"LEADER CHECK: {btc_context_str}")
    except Exception as e:
        logger.warning(f"Failed to fetch Bitcoin context: {e}")

    # Fetch GLOBAL sentiment once per cycle (SPEED UP)
    global_sentiment = tools.get_market_sentiment()

    # --- PRIORITY QUEUE LOGIC (MANUAL CLOSE FIRST) ---
    priority_pairs = []
    normal_pairs = []
    
    for p in PAIRS:
        safe_p = p.replace('/', '_')
        if os.path.exists(os.path.join(r"C:\Users\USER\AgenTra", f"CLOSE_{safe_p}.req")):
            priority_pairs.append(p)
        else:
            normal_pairs.append(p)
            
    ordered_pairs = priority_pairs + normal_pairs
    
    if priority_pairs:
        logger.info(f"🚨 PRIORITY OVERRIDE: Processing {priority_pairs} FIRST due to Manual Signal.")

    for pair in ordered_pairs:
        ai_called = process_pair(pair, btc_context_str, global_sentiment)
        if ai_called:
            logger.info("[WAIT] Rate Limit breathing (2s)...")
            time.sleep(2)
            
    # Sleep 1 minute (15m timeframe doesn't need 1s loop)
    # The outer loop is controlled by caller, but here we enforce a reasonable cycle delay
    # Or just return to allow caller to decide. The user suggested time.sleep(60) in main loop.
    # We will assume this function runs ONCE per cycle.
    pass


def main():
    # Load Environment Variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in .env. agent_logic will likely fail.")
    else:
        brain.configure_genai(api_key)

    try:
        # Run Multi-Pair Cycle
        # Uncomment to run in a loop:
        while True:
            run_orchestrator()
            logger.info("--- Cycle Complete. Waiting 3s for next tick check ---")
            time.sleep(3) 
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")

if __name__ == "__main__":
    main()
