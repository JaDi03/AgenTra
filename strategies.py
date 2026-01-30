def get_strategy_rules(regime_type: str, hurst_value: float = 0.5) -> str:
    """
    Returns the specific Trading Rules (Prompt Section) based on the Market Regime.
    Aggregates logic so agent_logic.py remains clean.
    Refined with Institutional Thresholds.
    """
    
    # 1. NOISE ZONE / CONCEPT DRIFT
    # Triggered by Hurst (Random Walk) or KS-Test (Statistical Shift).
    if regime_type == "DEFENSIVE":
        return f"""
    *** ACTIVE STRATEGY: DEFENSIVE (Hurst {hurst_value:.2f}) ***
    OBJECTIVE: Reduce exposure, but HIGH-CONVICTION setups allowed.
    
    RULES:
    1. REDUCE POSITION SIZE to 50% of normal.
    2. ONLY trade if Confidence >= 8/10.
    3. TIGHTEN STOPS to 1.0 ATR (instead of 1.5 ATR).
    4. FORBIDDEN: Complex setups, tight ranges.
    5. ALLOWED: Strong directional moves with clear BTC correlation.
    
    SPECIAL CASE - BTC DUMP SCENARIO:
    - IF BTC dumping > -2% in 1H:
      → SHORT altcoins IS ALLOWED (High correlation expected).
      → Confidence must be >= 7/10.
      → Use wider stops (alts can wick violently).
    """

    # 2. TREND FOLLOWING (High Hurst > 0.65)
    # The Classic Strategy: Follow the Flow.
    elif regime_type == "TRENDING":
        return f"""
    *** ACTIVE STRATEGY: TREND FOLLOWING (Hurst {hurst_value:.2f}) ***
    OBJECTIVE: Ride the wave. Catch big moves. Do not fight the trend.
    
    ENTRADAS PERMITIDAS:
    - Long: Solo si RSI 50-70 + Pullback a EMA20/50 + Precio > VWAP/EMA200.
    - Short: Solo si RSI 30-50 + Pullback a EMA20/50 + Precio < EMA200.
    
    FORBIDDEN (FILTROS DE SEGURIDAD):
    - **RSI > 80**: PROHIBIDO ENTRAR LONG (Peligro de 'Blow-off Top'). Esperar reset.
    - **RSI < 20**: PROHIBIDO ENTRAR SHORT (Peligro de 'Capitulation Bottom').
    - **VPIN > 0.7**: PROHIBIDO ENTRAR (Distribución Institucional / Flujo Tóxico).
    
    GESTIÓN:
    - Trailing Stop: 2.5 ATR.
    - **Structural Stop**: Si el precio rompe el VAL (en Longs) o el VAH (en Shorts) con volumen, considerar cierre de emergencia.
    - Take Profit: OPEN (Dejar correr).
    """

    # 3. MEAN REVERSION (Low Hurst < 0.35)
    # The Range Strategy: Buy Low, Sell High within a channel.
    elif regime_type == "MEAN_REVERSION":
        return f"""
    *** ACTIVE STRATEGY: MEAN REVERSION (Hurst {hurst_value:.2f}) ***
    OBJECTIVE: Ping-Pong. Buy VAL, Sell VAH. Use POC as target.
    
    FILTROS OBLIGATORIOS (Todas deben cumplirse para entrar):
    1. **Rango Amplio**: Ancho del canal > 2.5 ATR.
    2. **Divergencia RSI**: Precio hace Lower Low, RSI hace Higher Low (o viceversa).
    3. **Ubicación**: 
       - Long: Precio cerca del VAL (Value Area Low).
       - Short: Precio cerca del VAH (Value Area High).
    4. **VPIN < 0.6**: NO atrapar cuchillos.
    
    GESTIÓN:
    - **STOPS ESTRUCTURALES**: SL debe estar fuera del VAL/VAH (un pequeño % de margen). YA NO USAR ATR CIEGO.
    - **TIME STOP (CRÍTICO)**: Si en 3 velas (45 min) no estás en ganancia, CIERRA.
    - TP1: 50% de la posición en el POC (Point of Control).
    - TP2: 50% de la posición en la banda/extremo opuesto.
    """ 

    return "No Strategy Defined"
