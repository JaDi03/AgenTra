# agent_logic.py
# Module: Agent Logic
# Description: AI decision-making reasoning using Google Gemini.
# Encapsulates prompts and model interaction.

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import google.generativeai as genai
import os
import json
import logging
import re

# PATH TO MEMORY ARTIFACT
BRAIN_DIR = r"C:\Users\USER\.gemini\antigravity\brain\051909d5-8fdc-4ae9-a167-2ad40a4c2163"
LESSONS_FILE = os.path.join(BRAIN_DIR, "lessons.md")

logger = logging.getLogger(__name__)

# Model Configuration
# Primary: Gemini 2.5 Pro (State of the Art)
# Fallback: gemini-2.0-flash
MODEL_NAME = 'gemini-2.5-pro' 

def configure_genai(api_key: str):
    """Configures the Google Generative AI client."""
    if not api_key:
        logger.error("No API Key provided for Gemini.")
        return
    genai.configure(api_key=api_key)

def _clean_json_response(text: str) -> str:
    """Extracts JSON from a potential Markdown code block."""
    # Look for ```json ... ``` or just ``` ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def analyze_market(summary_micro: str, summary_macro: str, strategy_content: str, constitution_content: str, sentiment_text: str = "", btc_context_str: str = "", smc_context_str: str = "", strategy_guidelines: str = "") -> dict:
    """
    Sends 15m (Trigger) and 4h (Trend) data to Gemini for Dual Analysis.
    """
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
    You are an Autonomous Trading Agent using a HYBRID DUAL-TIMEFRAME STRATEGY.
    
    # Context
    Analyze the market using the "Aligned Trend" philosophy: 
    1. Check MACRO (4H) to define the allowable direction (Long or Short).
    2. Check MICRO (15M) to find the precise entry trigger.
    3. Check BITCOIN (Leader) to gauge overall market sentiment (Correlation).
    
    # Inputs
    
    ## 1. Constitution & Strategy
    {constitution_content}
    
    STRATEGY:
    {strategy_content}
    
    ## 2. NEWS CONTEXT (Fundamental Override)
    {sentiment_text}
    
    ## 3. MARKET DATA
    
    --- CONTEXTO DE MERCADO (BITCOIN) ---
    {btc_context_str}
    (If Bitcoin is dumping > -1%, be EXTREMELY CAUTIOUS with Altcoin Longs).
    
    --- TENDENCIA MACRO (4H) ---
    (Use this ONLY to determine direction: Bullish or Bearish)
    {summary_macro}
    
    --- GATILLO MICRO (15M) ---
    (Includes ATR and Support/Resistance Levels)
    {summary_micro}

    {smc_context_str}
    
    {smc_context_str}
    
    # STRATEGY GUIDELINES (DYNAMIC)
    {strategy_guidelines}
    
    # GLOBAL RISKS (ALWAYS ACTIVE)
    1. **CRITICAL - AVOID BETA TRAPS**:
       - Do NOT trade if the chart looks identical to Bitcoin (Pure Beta).
       - If setup is a "Clone" -> Confidence < 5 (HOLD).
    2. **QUANT PHYSICS**:
        - VPIN > 0.8: TOXIC FLOW. REDUCE CONFIDENCE.
    3. **LIQUIDITY**:
       - Do not Short Support / Long Resistance. Wait for Sweep.
    
    # Task
    Determine the best course of action (BUY, SELL, or HOLD) and provide a CONFIDENCE SCORE (1-10).
    * If the setup is just a "Clone" of BTC's move with no unique edge, Confidence must be < 5 (HOLD).
    
    # Output Format
    Respond ONLY with a JSON object. No explanations outside the JSON.
    {{
        "decision": "BUY" | "SELL" | "HOLD",
        "reason": "Detailed explanation citing 4H Trend, 15M Trigger, and BTC Context.",
        "stop_loss": "Suggested price or None if HOLD",
        "take_profit": "Suggested price or None if HOLD",
        "confidence": (Integer 1-10)
    }}
    """
    

    try:
        response = model.generate_content(prompt)
        text = response.text
        cleaned_json = _clean_json_response(text)
        decision = json.loads(cleaned_json)
        logger.info(f"AI Decision: {decision.get('decision')} - {decision.get('reason')}")
        return decision
    except Exception as e:
        logger.error(f"Error in 'analyze_market': {e}")
        return {"decision": "HOLD", "reason": f"AI Error: {str(e)}", "confidence": 0}

def reflect_on_performance(trade_history: list, current_strategy: str, market_context: dict = None) -> tuple:
    """
    Analyzes past trades using FORENSIC ARCHITECTURE.
    market_context: Dict containing Regime (ADX), Volatility Rank, VPIN, etc. from the moment of loss.
    """
    if not trade_history:
        return current_strategy, "No trade history to analyze."

    model = genai.GenerativeModel(MODEL_NAME)
    
    # Get last trade (the one that caused the trigger)
    last_trade = trade_history[-1]
    history_dump = json.dumps(trade_history[-5:], indent=2) # Concise history
    
    # Context String
    ctx_str = "No specific regime context available."
    if market_context:
        ctx_str = json.dumps(market_context, indent=2)

    prompt = f"""
    You are a FORENSIC TRADING ARCHITECT. A loss occurred. diagnosis is required.
    
    # 1. Forensic Data
    LAST TRADE: {json.dumps(last_trade, indent=2)}
    
    MARKET REGIME AT REFLEXION:
    {ctx_str}
    
    # 2. Hard Constraints (THE LAW)
    You strictly adhere to this Diagnostic Decision Tree:
    
    A. IF LOSS WAS "EXECUTION FAILURE" (e.g. Price wicked SL and reversed, OR VPIN was > 0.7):
       - DIAGNOSIS: "Execution Failure (Wick/Toxic Flow)"
       - ACTION: Do NOT change Stop Loss Multiplier.
       - SUGESTION: Add logic filter (e.g. "Wait for candle close", "Avoid High VPIN").
       
    B. IF LOSS WAS "REGIME MISMATCH" (e.g. Bought trend strategy in ADX < 20 Chopping market):
       - DIAGNOSIS: "Regime Mismatch (Wrong Tool for Job)"
       - ACTION: Do NOT change numerical parameters.
       - SUGGESTION: Add Regime Filter (e.g. "Only trade if ADX > 25").
       
    C. IF LOSS WAS "EDGE DECAY" (Statistic failure over many trades, Regime was correct):
       - DIAGNOSIS: "Edge Decay"
       - ACTION: You MAY adjust risk parameters (SL distance) slightly.
    
    # 3. Current Strategy
    {current_strategy}
    
    # Output
    Respond ONLY with a JSON object.
    {{
        "diagnosis": "Execution Failure" | "Regime Mismatch" | "Edge Decay",
        "new_strategy_content": "FULL markdown of strategy (with logic updates if A/B, or param updates if C)",
        "change_reason": "FORENSIC LOG: [Diagnosis]. [Action Taken]. (e.g. 'Regime Mismatch detected (ADX 15). Added filter to ignore signals when ADX < 20.')"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        cleaned_json = _clean_json_response(text)
        data = json.loads(cleaned_json)
        
        new_strategy = data.get("new_strategy_content", current_strategy)
        reason = data.get("change_reason", "Strategy optimized by Forensic AI.")
            
        logger.info(f"Forensic Reflexion: {reason}")
        return new_strategy, reason
    except Exception as e:
        logger.error(f"Error in 'reflect_on_performance': {e}")
        return current_strategy, f"Error during reflexion: {e}"

def _read_lessons() -> str:
    """Reads the Forensic Memory file."""
    try:
        if os.path.exists(LESSONS_FILE):
            with open(LESSONS_FILE, "r", encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        logger.error(f"Memory Read Error: {e}")
    return "No lessons recorded yet."

def record_lesson(symbol, result, reason):
    """
    Appends a new lesson to the Forensic Memory.
    Called by main.py after a trade closes.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        lesson_entry = f"- [{timestamp}] {symbol} ({result}): {reason}\n"
        
        with open(LESSONS_FILE, "a", encoding='utf-8') as f:
            f.write(lesson_entry)
            
        logger.info(f"🧠 MEMORY UPDATED: {lesson_entry.strip()}")
    except Exception as e:
        logger.error(f"Memory Write Error: {e}")

def analyze_market_omnidirectional(summary_micro, summary_macro, regime_info, strategy_content, constitution_content, sentiment_text, btc_context_str, smc_context_str):
    """
    Enhanced analysis with regime-specific playbooks (OMNIDIRECTIONAL).
    """
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Build regime-specific instructions
    playbook = regime_info.get('playbook', 'WAIT')
    bias = regime_info.get('bias', 'None')
    reason = regime_info.get('reason', 'No regime detected')
    
    # READ MEMORY
    lessons_text = _read_lessons()
    
    # IMPORT STRATEGY RULES from strategies.py (SINGLE SOURCE OF TRUTH)
    import strategies
    
    # Map regime to strategy type for get_strategy_rules
    regime_type_map = {
        'BREAKOUT': 'TRENDING',  # Use TRENDING rules for breakouts
        'TRENDING': 'TRENDING',
        'RANGE': 'MEAN_REVERSION',
        'UNCERTAIN': 'DEFENSIVE',
        'NEUTRAL': 'DEFENSIVE'
    }
    
    regime_for_strategy = regime_type_map.get(regime_info.get('regime', 'NEUTRAL'), 'DEFENSIVE')
    
    # Get authoritative rules from strategies.py
    # Extract hurst from smc_context_str if available
    import re
    hurst_match = re.search(r'Hurst: ([\d.]+)', smc_context_str)
    hurst_value = float(hurst_match.group(1)) if hurst_match else 0.5
    
    strategy_instructions = strategies.get_strategy_rules(regime_for_strategy, hurst_value)
    
    # Add playbook-specific tactical notes
    if playbook == 'MOMENTUM_CATCH':
        strategy_instructions += """
    
    --- TACTICAL NOTES FOR BREAKOUT ---
    - CRITICAL: Wait for retest confirmation (don't chase)
    - Volume MUST be > 1.5x average
    - If no volume = FAKE BREAKOUT, skip
    """
    
    prompt = f"""
    You are an OMNIDIRECTIONAL trading agent operating in {playbook} mode.
    
    # 1. Market Regime Analysis
    {reason}
    
    Current Bias: {bias}
    
    # 2. Active Strategy (THE LAW)
    {strategy_instructions}
    
    # 3. Market Data
    MACRO (4H):
    {summary_macro}
    
    MICRO (15M):
    {summary_micro}
    
    {smc_context_str}
    
    BITCOIN CONTEXT (Leader):
    {btc_context_str}
    
    NEWS/SENTIMENT:
    {sentiment_text}
    
    # 4. FORENSIC MEMORY (LESSONS LEARNED)
    (Review these past mistakes/wins before deciding)
    {lessons_text}
    
    # Task
    Analyze the setup and determine if it matches your active playbook.
    - If perfect match → High confidence
    - If partial match → Medium confidence
    - If no match → HOLD
    
    Output JSON:
    {{
        "decision": "BUY" | "SELL" | "HOLD",
        "playbook_used": "{playbook}",
        "reason": "Explanation citing playbook rules and data",
        "stop_loss": price or null,
        "take_profit": price or null,
        "confidence": 1-10
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        decision = json.loads(_clean_json_response(response.text))
        
        # Apply confidence adjustment from regime (handled in main.py logic too but good to double check)
        original_conf = int(decision.get('confidence', 0))
        regime_adj = regime_info.get('confidence_adjustment', 0)
        
        adjusted_conf = max(1, min(10, original_conf + regime_adj))
        decision['confidence'] = adjusted_conf
        
        logger.info(f"AI Decision ({playbook}): {decision.get('decision')} [Conf: {adjusted_conf}/10]")
        return decision
        
    except Exception as e:
        logger.error(f"Error in omnidirectional analysis: {e}")
        return {"decision": "HOLD", "reason": f"AI Error: {e}", "confidence": 0}
