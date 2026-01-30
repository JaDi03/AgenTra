# Estrategia Omnidireccional: Ganar en Todos los Regímenes

## 🎯 Filosofía Core

**"El mercado siempre está pagando. Solo hay que saber dónde cobrar."**

No existe "mercado malo". Solo existen traders usando la estrategia equivocada para el régimen actual.

---

## 📊 Los 3 Regímenes + Sus Estrategias

### **RÉGIMEN 1: TRENDING (Hurst > 0.65 o ADX > 25)**
**Naturaleza:** Momentum persistente. Los ganadores siguen ganando.

**Estrategia:** TREND FOLLOWING
```
LONG Setup:
- Precio > EMA200 (4H)
- Pullback a EMA20/50 (15M)
- RSI 50-70
- VPIN < 0.7
→ Entry: Bounce confirmado
→ SL: 1.5 ATR bajo swing low
→ TP: OPEN (trailing stop 2.5 ATR)

SHORT Setup:
- Precio < EMA200 (4H)
- Pullback a EMA20/50 (15M)
- RSI 30-50
- VPIN < 0.7
→ Entry: Rejection confirmado
→ SL: 1.5 ATR sobre swing high
→ TP: OPEN (trailing stop 2.5 ATR)
```

**Psicología:** "No pienses, sigue el flujo."
**Win Rate Esperado:** 45-55%
**R:R Típico:** 1:3 o mejor
**Mejor Momento:** Después de noticias fuertes, durante sesión USA/Europa

---

### **RÉGIMEN 2: MEAN REVERSION (Hurst < 0.35 y ADX < 20)**
**Naturaleza:** Rango definido. Lo que sube, baja. Lo que baja, sube.

**Estrategia:** PING-PONG entre VAH y VAL
```
LONG Setup (Comprar en VAL):
- Precio toca VAL (Value Area Low)
- RSI < 35
- Divergencia alcista (precio baja, RSI sube)
- Volumen bajo (no es capitulación)
→ Entry: VAL + confirmación (candle bullish)
→ SL: 0.5% bajo VAL (estructural, NO ATR)
→ TP1: POC (50% posición)
→ TP2: VAH (50% posición)

SHORT Setup (Vender en VAH):
- Precio toca VAH (Value Area High)
- RSI > 65
- Divergencia bajista
- Volumen bajo (no es breakout)
→ Entry: VAH + confirmación (candle bearish)
→ SL: 0.5% sobre VAH
→ TP1: POC (50%)
→ TP2: VAL (50%)

FILTROS OBLIGATORIOS:
1. Ancho del canal > 2.5 ATR (si es muy estrecho, saltar)
2. VPIN < 0.6 (evitar toxic flow)
3. TIME STOP: Si en 3 velas (45 min) no hay profit, CIERRA
```

**Psicología:** "Vende la codicia, compra el miedo."
**Win Rate Esperado:** 60-70% (pero R:R más bajo, ~1:1.5)
**Mejor Momento:** Fines de semana, horas asiáticas (bajo volumen)

---

### **RÉGIMEN 3: BREAKOUT/BREAKDOWN (Transición entre regímenes)**
**Naturaleza:** El mercado está saliendo de un rango o cambiando de tendencia.

**Estrategia:** CATCH THE MOMENTUM
```
LONG Breakout:
- Precio rompe VAH con VOLUMEN > 1.5x promedio
- RSI > 60 pero < 80
- VPIN < 0.7
- BTC correlación positiva (+1% mínimo)
→ Entry: Retest de VAH como soporte
→ SL: Bajo VAH (el breakout falló)
→ TP: Next resistance (R:R 1:2 mínimo)

SHORT Breakdown:
- Precio rompe VAL con VOLUMEN > 1.5x promedio
- RSI < 40 pero > 20
- VPIN < 0.7
- BTC correlación negativa (-1% mínimo)
→ Entry: Retest de VAL como resistencia
→ SL: Sobre VAL
→ TP: Next support (R:R 1:2 mínimo)

FILTRO CRÍTICO:
- Si rompe SIN volumen = FAKE BREAKOUT → NO ENTRAR
- Si rompe y no retesta en 3 velas = TOO LATE → ESPERAR
```

**Psicología:** "El impulso inicial es lo que cuenta."
**Win Rate Esperado:** 50-60%
**R:R Típico:** 1:2 a 1:3
**Mejor Momento:** Durante alta volatilidad, noticias importantes

---

## 🧠 Matriz de Decisión para la IA

La IA debe SIEMPRE considerar estos 3 regímenes y elegir la estrategia correcta:

```python
def determine_active_strategy(market_data, btc_context):
    """
    Returns the optimal strategy based on current market regime.
    """
    
    # Step 1: Classify Regime
    adx = market_data['ADX_14']
    hurst = market_data['hurst']
    vpin = market_data['vpin']
    volume_profile = market_data['volume_profile']
    
    # Step 2: BTC Override
    btc_pct = btc_context['pct_change_1h']
    
    # REGIME A: Strong Trend
    if (adx > 25 or hurst > 0.65) and abs(btc_pct) > 1.5:
        return {
            'regime': 'TRENDING',
            'strategy': 'TREND_FOLLOWING',
            'bias': 'LONG' if btc_pct > 0 else 'SHORT',
            'confidence_multiplier': 1.2  # Boost confidence
        }
    
    # REGIME B: Range-Bound
    elif adx < 20 and hurst < 0.35 and abs(btc_pct) < 1.0:
        return {
            'regime': 'RANGE',
            'strategy': 'MEAN_REVERSION',
            'bias': 'BIDIRECTIONAL',  # Can go both ways
            'confidence_multiplier': 1.0
        }
    
    # REGIME C: Breakout Conditions
    elif volume_profile['breakout_detected']:
        return {
            'regime': 'BREAKOUT',
            'strategy': 'MOMENTUM_CATCH',
            'bias': 'FOLLOW_VOLUME',
            'confidence_multiplier': 1.1
        }
    
    # REGIME D: Uncertainty (Concept Drift)
    elif market_data['drift_detected']:
        return {
            'regime': 'UNCERTAIN',
            'strategy': 'REDUCE_EXPOSURE',
            'bias': 'ONLY_HIGH_CONVICTION',  # Confidence >= 8
            'confidence_multiplier': 0.7
        }
    
    # Default: Neutral
    else:
        return {
            'regime': 'NEUTRAL',
            'strategy': 'WAIT_FOR_SETUP',
            'bias': None,
            'confidence_multiplier': 1.0
        }
```

---

## 🎯 Prompt Mejorado para la IA

```python
prompt = f"""
You are an OMNIDIRECTIONAL trading agent. Your job is to profit in ALL market conditions.

# Core Philosophy
"There is no bad market. Only wrong strategy for the current regime."

# Current Market Regime
{regime_analysis}

# Active Strategy for This Regime
{active_strategy}

# The 3 Playbooks

## PLAYBOOK 1: TRENDING MARKETS (ADX > 25 or Hurst > 0.65)
OBJECTIVE: Ride the wave. Don't fight momentum.
- LONG if price > EMA200 (4H) + pullback to EMA20 (15M)
- SHORT if price < EMA200 (4H) + rejection at EMA20 (15M)
- Use WIDE trailing stops (2.5 ATR)
- Let winners run (no fixed TP)
WIN RATE: 45-55% | R:R: 1:3+

## PLAYBOOK 2: RANGE MARKETS (ADX < 20 and Hurst < 0.35)
OBJECTIVE: Buy low, sell high. Fade extremes.
- LONG at VAL (Value Area Low) if RSI < 35 + divergence
- SHORT at VAH (Value Area High) if RSI > 65 + divergence
- Use STRUCTURAL stops (just outside VAL/VAH)
- Take profit at POC (mid-range) or opposite extreme
- TIME STOP: Exit if no profit in 45 minutes
WIN RATE: 60-70% | R:R: 1:1.5

## PLAYBOOK 3: BREAKOUT MARKETS (Volume spike > 1.5x + ADX rising)
OBJECTIVE: Catch early momentum. Exit if it fails.
- LONG on VAH breakout + retest (with volume confirmation)
- SHORT on VAL breakdown + retest (with volume confirmation)
- Use TIGHT stops (just below/above breakout level)
- Target next major S/R level
WIN RATE: 50-60% | R:R: 1:2

# Current Market Data
MACRO (4H):
{summary_macro}

MICRO (15M):
{summary_micro}

VOLUME PROFILE:
{vp_data}

BITCOIN CONTEXT:
{btc_context_str}

# Your Task
1. Identify which PLAYBOOK applies to current conditions
2. Look for setups within that playbook ONLY
3. If playbook is TRENDING → Can go LONG or SHORT (based on 4H direction)
4. If playbook is RANGE → Can go LONG or SHORT (based on 15M position in range)
5. If playbook is BREAKOUT → Wait for volume confirmation
6. If NO playbook fits → HOLD

# Confidence Scoring
- 9-10: Perfect textbook setup
- 7-8: Good setup, minor flag
- 5-6: Mediocre setup, multiple concerns
- <5: No clear edge, HOLD

# CRITICAL RULES
- DO NOT use trending strategy in range markets (you'll get chopped)
- DO NOT use mean reversion strategy in trending markets (you'll get run over)
- DO NOT chase breakouts without volume (fake breakouts destroy accounts)
- ALWAYS respect BTC correlation (Alts follow BTC 80% of the time)

# Output Format
{{
    "decision": "BUY" | "SELL" | "HOLD",
    "playbook_used": "TRENDING" | "RANGE" | "BREAKOUT" | "NONE",
    "reason": "Detailed explanation citing playbook rules and current data",
    "stop_loss": price,
    "take_profit": price (or null for trailing),
    "confidence": 1-10
}}
"""
```

---

## 🔧 Modificaciones Necesarias en `main.py`

### 1. Detector de Breakout/Breakdown

```python
def detect_breakout(df_micro, vp_data):
    """
    Detects if price is breaking out of established range.
    """
    last_candle = df_micro.iloc[-1]
    prev_candle = df_micro.iloc[-2]
    
    price = last_candle['close']
    volume = last_candle['volume']
    avg_volume = df_micro['volume'].iloc[-20:-1].mean()
    
    vah = vp_data['vah']
    val = vp_data['val']
    
    # Bullish Breakout
    if price > vah and volume > avg_volume * 1.5:
        if prev_candle['close'] <= vah:  # Just broke out
            return {
                'type': 'BULLISH_BREAKOUT',
                'confidence': 'HIGH' if volume > avg_volume * 2 else 'MEDIUM',
                'level': vah
            }
    
    # Bearish Breakdown
    if price < val and volume > avg_volume * 1.5:
        if prev_candle['close'] >= val:  # Just broke down
            return {
                'type': 'BEARISH_BREAKDOWN',
                'confidence': 'HIGH' if volume > avg_volume * 2 else 'MEDIUM',
                'level': val
            }
    
    return None
```

### 2. Regime Classifier Mejorado

```python
def classify_market_regime(df_micro, df_macro, vp_data, btc_pct_change, drift_detected):
    """
    Comprehensive regime classification.
    Returns strategy name and bias.
    """
    
    adx_4h = df_macro.iloc[-1]['ADX_14']
    adx_15m = df_micro.iloc[-1]['ADX_14']
    hurst = calculate_hurst(df_macro)
    
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
        ema200_4h = df_macro.iloc[-1]['EMA_200']
        
        return {
            'regime': 'TRENDING',
            'playbook': 'TREND_FOLLOWING',
            'bias': 'LONG' if price_4h > ema200_4h else 'SHORT',
            'confidence_adjustment': +1 if abs(btc_pct_change) > 1.5 else 0,
            'reason': f"Strong trend detected (ADX {adx_4h:.1f}, Hurst {hurst:.2f})"
        }
    
    # Priority 3: Range (Low ADX + Low Hurst)
    if adx_4h < 20 and hurst < 0.35 and abs(btc_pct_change) < 1.0:
        channel_width = (vp_data['vah'] - vp_data['val']) / vp_data['poc']
        
        if channel_width > 0.025:  # At least 2.5% wide channel
            return {
                'regime': 'RANGE',
                'playbook': 'MEAN_REVERSION',
                'bias': 'BIDIRECTIONAL',
                'confidence_adjustment': 0,
                'reason': f"Range-bound market (ADX {adx_4h:.1f}, Channel {channel_width*100:.1f}%)"
            }
    
    # Priority 4: Concept Drift (Defensive)
    if drift_detected:
        return {
            'regime': 'UNCERTAIN',
            'playbook': 'DEFENSIVE',
            'bias': 'ONLY_IF_PERFECT',
            'confidence_adjustment': -2,
            'reason': "Concept drift detected - require exceptional setups"
        }
    
    # Default: Wait
    return {
        'regime': 'NEUTRAL',
        'playbook': 'WAIT',
        'bias': None,
        'confidence_adjustment': 0,
        'reason': "No clear regime - waiting for setup"
    }
```

### 3. Position Sizing Dinámico por Régimen

```python
def calculate_position_size_by_regime(regime_info, account_balance, risk_pct, entry, sl):
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
    
    regime = regime_info['regime']
    multiplier = multipliers.get(regime, 0.0)
    
    final_size = base_size * multiplier
    
    logger.info(f"Position sizing: {regime} → {multiplier*100:.0f}% allocation = {final_size:.4f}")
    
    return final_size
```

---

## 📈 Expectativas Realistas por Régimen

### Distribución Típica del Mercado:
- **40% del tiempo:** TRENDING (aquí haces el dinero grande)
- **30% del tiempo:** RANGE (aquí haces victorias pequeñas pero consistentes)
- **15% del tiempo:** BREAKOUT (aquí capturas cambios de régimen)
- **15% del tiempo:** UNCERTAIN/CHOPPY (aquí solo operas setups perfectos)

### Métricas Esperadas (Después de 100 trades):

| Régimen | Trades | Win Rate | Avg R:R | Contribución al PnL |
|---------|--------|----------|---------|---------------------|
| TRENDING | 30 | 50% | 1:3 | +60% PnL total |
| RANGE | 45 | 65% | 1:1.5 | +30% PnL total |
| BREAKOUT | 15 | 55% | 1:2 | +15% PnL total |
| UNCERTAIN | 10 | 40% | 1:1 | -5% PnL total |
| **TOTAL** | **100** | **57%** | **1:2** | **+100% ROI** |

---

## 🚨 Errores Comunes a Evitar

### Error 1: Usar Mean Reversion en Trending Market
```
Síntomas: 
- Compras en VAL, pero precio sigue bajando
- "Catching a falling knife"

Solución:
- SIEMPRE verificar ADX y Hurst primero
- Si trending, NO usar mean reversion
```

### Error 2: Usar Trend Following en Range Market
```
Síntomas:
- Entras en breakout, pero precio vuelve al rango
- "Whipsawed constantemente"

Solución:
- Verificar volumen en breakouts
- Si volumen bajo, probablemente es fake
```

### Error 3: No Respetar BTC Correlation
```
Síntomas:
- Entras LONG en altcoin mientras BTC cae
- "Picking up pennies in front of a steamroller"

Solución:
- BTC dump > -2% = NO LONGS en alts
- BTC pump > +2% = NO SHORTS en alts
```

---

## 🎯 Implementación en agent_logic.py

```python
def analyze_market_omnidirectional(
    summary_micro: str,
    summary_macro: str,
    regime_info: dict,  # NEW: Includes playbook and bias
    strategy_content: str,
    constitution_content: str,
    sentiment_text: str = "",
    btc_context_str: str = "",
    smc_context_str: str = ""
) -> dict:
    """
    Enhanced analysis with regime-specific playbooks.
    """
    
    model = genai.GenerativeModel(
        'gemini-1.5-pro-002',
        generation_config={
            'temperature': 0.15,  # Slightly higher for adaptive reasoning
            'response_mime_type': 'application/json'
        }
    )
    
    # Build regime-specific instructions
    playbook = regime_info['playbook']
    bias = regime_info['bias']
    
    if playbook == 'TREND_FOLLOWING':
        strategy_instructions = """
        ACTIVE PLAYBOOK: TREND FOLLOWING
        
        YOUR GOAL: Ride momentum. Don't fight the trend.
        
        LONG Setup:
        - Price > EMA200 (4H)
        - Pullback to EMA20/50 (15M)
        - RSI 50-70
        - Entry on bounce confirmation
        - Wide trailing stop (2.5 ATR)
        
        SHORT Setup:
        - Price < EMA200 (4H)
        - Pullback to EMA20/50 (15M)
        - RSI 30-50
        - Entry on rejection confirmation
        - Wide trailing stop (2.5 ATR)
        
        FORBIDDEN:
        - Counter-trend trades
        - Tight take profits (let it run)
        """
    
    elif playbook == 'MEAN_REVERSION':
        strategy_instructions = """
        ACTIVE PLAYBOOK: MEAN REVERSION
        
        YOUR GOAL: Buy low, sell high within the range.
        
        LONG Setup (at VAL):
        - Price touches VAL
        - RSI < 35 + bullish divergence
        - Low volume (not capitulation)
        - SL: 0.5% below VAL
        - TP: POC (50%) + VAH (50%)
        
        SHORT Setup (at VAH):
        - Price touches VAH
        - RSI > 65 + bearish divergence
        - Low volume (not breakout)
        - SL: 0.5% above VAH
        - TP: POC (50%) + VAL (50%)
        
        MANDATORY:
        - Channel width > 2.5 ATR
        - TIME STOP: Exit if no profit in 45min
        
        FORBIDDEN:
        - Chasing breakouts
        - Trading in narrow ranges
        """
    
    elif playbook == 'MOMENTUM_CATCH':
        strategy_instructions = """
        ACTIVE PLAYBOOK: BREAKOUT/BREAKDOWN
        
        YOUR GOAL: Catch early momentum shifts.
        
        LONG Setup (Breakout):
        - Price breaks VAH with volume > 1.5x avg
        - Wait for retest of VAH as support
        - RSI > 60 but < 80
        - Entry on retest confirmation
        - SL: Below VAH
        - TP: Next resistance
        
        SHORT Setup (Breakdown):
        - Price breaks VAL with volume > 1.5x avg
        - Wait for retest of VAL as resistance
        - RSI < 40 but > 20
        - Entry on retest confirmation
        - SL: Above VAL
        - TP: Next support
        
        CRITICAL:
        - NO volume = NO trade (fake breakout)
        - NO retest = TOO LATE (don't chase)
        """
    
    elif playbook == 'DEFENSIVE':
        strategy_instructions = """
        ACTIVE PLAYBOOK: DEFENSIVE (Concept Drift Detected)
        
        YOUR GOAL: Preserve capital. Only trade perfect setups.
        
        RULES:
        - Reduce position size to 50%
        - Only trade if confidence >= 8/10
        - Prefer mean reversion over trend (more predictable)
        - Tighter stops (1.0 ATR)
        
        ACCEPTABLE SCENARIOS:
        - Extreme RSI (< 25 or > 75) at key levels
        - High volume breakout with BTC confirmation
        - Clear support/resistance bounce with divergence
        
        FORBIDDEN:
        - Complex setups
        - Ambiguous signals
        - Any trade < 8/10 confidence
        """
    
    else:  # WAIT
        strategy_instructions = """
        ACTIVE PLAYBOOK: WAIT
        
        No clear regime detected. Do NOT force trades.
        
        Only consider entry if:
        - Confidence would be 9/10 or higher
        - Setup is textbook perfect
        - Multiple confirmations align
        
        Otherwise: HOLD and preserve capital.
        """
    
    prompt = f"""
You are an omnidirectional trading agent operating in {playbook} mode.

# Market Regime Analysis
{regime_info['reason']}

Current Bias: {bias}

# Active Strategy
{strategy_instructions}

# Market Data
MACRO (4H):
{summary_macro}

MICRO (15M):
{summary_micro}

{smc_context_str}

BITCOIN CONTEXT:
{btc_context_str}

NEWS/SENTIMENT:
{sentiment_text}

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
        
        # Apply confidence adjustment from regime
        original_conf = decision.get('confidence', 5)
        adjusted_conf = max(1, min(10, original_conf + regime_info['confidence_adjustment']))
        decision['confidence'] = adjusted_conf
        
        logger.info(f"AI Decision ({playbook}): {decision.get('decision')} [Conf: {adjusted_conf}/10]")
        return decision
        
    except Exception as e:
        logger.error(f"Error in omnidirectional analysis: {e}")
        return {"decision": "HOLD", "reason": f"AI Error: {e}", "confidence": 0}
```

---

## 🎬 Flujo Completo

```
1. Fetch Data (15M + 4H) + Calculate Indicators
         ↓
2. Detect Breakout/Breakdown (volume + VAH/VAL)
         ↓
3. Classify Regime (TRENDING / RANGE / BREAKOUT / UNCERTAIN)
         ↓
4. Select Playbook based on regime
         ↓
5. AI analyzes with playbook-specific instructions
         ↓
6. Position sizing adjusted by regime multiplier
         ↓
7. Execute trade (or HOLD if no match)
         ↓
8. Exit management based on playbook rules
```

---

## ✅ Ventajas de Este Enfoque

1. **Adaptabilidad:** El bot nunca está "out of sync" con el mercado
2. **Diversificación de Edge:** Ganas en trending Y en ranging markets
3. **Menor Drawdown:** Cuando trending falla, range markets compensan
4. **Claridad:** La IA sabe exactamente qué buscar en cada régimen
5. **Realismo:** No esperas ganar 100% del tiempo en todos lados

---

## 🎯 Resumen Ejecutivo

**TL;DR:**
- 3 Playbooks: TREND, RANGE, BREAKOUT
- Cada uno con sus propias reglas
- La IA clasifica el mercado primero, luego elige estrategia
- Position sizing ajustado por régimen
- Expectativa: 57% win rate, 1:2 R:R, ROI positivo en todos los regímenes

**Próximos pasos:**
1. Implementar `classify_market_regime()` en main.py
2. Modificar `analyze_market()` para aceptar `regime_info`
3. Actualizar prompts con playbook-specific instructions
4. Testear en dry run durante 100 trades

¿Quieres que genere el código completo integrado?