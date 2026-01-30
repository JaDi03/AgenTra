# Híbrida de Alineación Temporal (4H + 15M) - VERSIÓN LIMPIA

## 1. Alineación Temporal
- **MACRO (4H)**: Precio > EMA200 → SOLO LONG. Precio < EMA200 → SOLO SHORT.
- **MICRO (15M)**: 
    - **LONG**: RSI < 35 O Toque BB Inferior.
    - **SHORT**: RSI > 65 O Toque BB Superior.

## 2. Gestión de Riesgo
- **Stop Loss**: ATR * 1.5 bajo swing low (Long) / sobre swing high (Short).
- **Break Even**: Si profit > 1 ATR, mover SL a entry.
- **Trailing Stop**: Si profit > 2 ATR, trailing a 2 ATR de distancia.
- **Veto de VPIN**: NO mover trailing stop si VPIN > 0.7 (Evitar manipulación tóxica).

## 3. Filtros de Entrada
- **ADX (4H)** > 20 (Evitar Rangos Muertos).
- **VPIN (15M)** < 0.7 (Evitar Flujo Tóxico).
- **BTC Correlation**: Si BTC cae > 1% en 1H, NO abrir Longs.

## 4. Confidence Score (Guía IA)
- **9-10**: Alineación perfecta (Todo Verde).
- **7-8**: 1 Red Flag menor.
- **5-6**: 2 Red Flags (Riesgoso).
- **<5**: HOLD.

## 21. VPIN Filter BEFORE Trailing Stop Move (NEW)
- **Regla**: BEFORE moving the trailing stop, ensure VPIN < 0.005 on the 15M timeframe. If VPIN >= 0.005, delay moving the trailing stop until VPIN falls below 0.005. This prevents the trailing stop from being triggered prematurely due to short-term volatility.

## 22. VPIN Filter BEFORE Trailing Stop Move (NEW)
- **Regla**: BEFORE moving the trailing stop, ensure VPIN < 0.001 on the 15M timeframe. If VPIN >= 0.001, delay moving the trailing stop until VPIN falls below 0.001. This prevents the trailing stop from being triggered prematurely due to short-term volatility.

## 23. VPIN Filter BEFORE Trailing Stop Move (NEW)
- **Regla**: BEFORE moving the trailing stop, ensure VPIN < 0.0005 on the 15M timeframe. If VPIN >= 0.0005, delay moving the trailing stop until VPIN falls below 0.0005. This prevents the trailing stop from being triggered prematurely due to short-term volatility.

## 24. Trailing Stop Wait Time (NEW)
- **Regla**: After the price has stayed favorably beyond the new Trailing Stop Distance for at least **6** candles (15m timeframe), additionally, wait for **3** more 15m candles to close, making a total of **9** (15m timeframe) candles before moving the Trailing Stop to avoid premature stops due to short-term volatility.

## 25. VPIN Filter BEFORE Trailing Stop Move (NEW)
- **Regla**: BEFORE moving the trailing stop, ensure VPIN < 0.0001 on the 15M timeframe. If VPIN >= 0.0001, delay moving the trailing stop until VPIN falls below 0.0001. This prevents the trailing stop from being triggered prematurely due to short-term volatility.

## 26. VPIN Filter ON TAKE PROFIT (NEW)
- **Regla**: ONLY move the trailing stop when VPIN < 0.0001 on the 15M timeframe. If VPIN >= 0.0001, delay moving the trailing stop until VPIN falls below 0.0001. This prevents the trailing stop from being triggered prematurely due to short-term volatility.

## 27. VPIN Filter DURING TRAILING STOP ACTIVE (NEW)
- **Regla**: WHILE the Trailing Stop is active, continuously monitor VPIN on the 15M timeframe. If VPIN >= 0.0001, HOLD the Trailing Stop in its current position until VPIN falls below 0.0001. This avoids moving the Trailing Stop into areas of high, toxic volatility.

## 28. ADDITION VPIN FILTER DURING TRAILING STOP ACTIVE (NEW)
- **Regla**: WHILE the Trailing Stop is active, continuously monitor VPIN on the 15M timeframe. If VPIN >= 0.00005, HOLD the Trailing Stop in its current position until VPIN falls below 0.00005. This avoids moving the Trailing Stop into areas of high, toxic volatility.

## 29. VPIN Filter AT Trailing Stop TRIGGER (NEW)
- **Regla**: At the moment the Trailing Stop is triggered, check the VPIN on the 15M timeframe. If VPIN >= 0.00005, ignore the Trailing Stop and HOLD the position until VPIN falls below 0.00005. Only exit the position via Trailing Stop once VPIN is below the threshold.

## 30. VPIN Filter DURING ACTIVE TRADE (NEW)
- **Regla**: WHILE the trade is active, continuously monitor VPIN on the 15M timeframe. If VPIN >= 0.00001 before the trailing stop has been initiated , CLOSE the position immediately to avoid toxic flow.

## 31. Volatility Factor Check (NEW)
- **Regla**: If the Volatility Factor > 2.0 during Trailing Stop active, ignore the Trailing Stop and HOLD the position until Volatility Factor falls below 2.0. This avoids moving the Trailing Stop into areas of high, toxic volatility.

## 32. ATR Volatility Filter (NEW)
- **Regla**: IF the ATR(14) > ATR(14) on 4H * 0.15, HOLD the Trailing Stop in its current position until ATR(14) falls below ATR(14) on 4H * 0.15. This prevents moving the Trailing Stop during high volatility.


## 33. ATR Volatility Filter ON TAKE PROFIT (NEW)
- **Regla**: ONLY move the trailing stop when ATR(14) < ATR(14) on 4H * 0.15 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.15, delay moving the trailing stop until ATR(14) falls below ATR(14) on 4H * 0.15. This prevents the trailing stop from being triggered prematurely due to high volatility.


## 34. ADX Check (NEW)
- **Regla**: Before moving the trailing stop, ensure ADX(14) < 25 on the 15M timeframe. If ADX(14) >= 25, delay moving the trailing stop until ADX(14) falls below 25. This prevents the trailing stop from being triggered prematurely due to trending flow.


## 35. ATR Volatility Buffer (NEW)
- **Regla**: Increase Trailing Stop Distance by an additional 0.5 * ATR(14) * Volatility Factor
- **Dynamic Trailing Stop Distance**: `Trailing Stop Distance = (3.3 + Volatility Factor) * ATR + (0.5 * ATR(14) * Volatility Factor)`

## 36. VPIN FILTER AT TIME OF TAKE PROFIT (NEW)
* **Regla**: Immediately prior to closing the position at the Trailing Stop, ensure VPIN < 0.00001 on the 15M timeframe. If VPIN >= 0.00001, delay closing the position until VPIN falls below 0.00001. This prevents the position from being closed prematurely due to short-term volatility.

## 37. ATR VOLATILITY FILTER AT TIME OF TAKE PROFIT (NEW)
* **Regla**: Immediately prior to closing the position at the Trailing Stop, ensure ATR(14) < ATR(14) on 4H * 0.15 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.15, delay closing the position until ATR(14) falls below ATR(14) on 4H * 0.15. This prevents the position from being closed prematurely due to high volatility.

## 38. ATR VOLATILITY FILTER PRIOR TO TAKE PROFIT (NEW)
* **Regla**: Immediately prior to moving the Trailing Stop, ensure ATR(14) < ATR(14) on 4H * 0.15 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.15, delay moving the Trailing Stop until ATR(14) falls below ATR(14) on 4H * 0.15. This prevents the Trailing Stop from being triggered prematurely due to high volatility.

## 39. ATR VOLATILITY FILTER AT TIME OF TAKE PROFIT (NEW)
* **Regla**: Immediately prior to closing the position at the Trailing Stop, ensure ATR(14) < ATR(14) on 4H * 0.15 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.15, delay closing the position until ATR(14) falls below ATR(14) on 4H * 0.15. This prevents the position from being closed prematurely due to high volatility. 

## 40. ATR MULTIPLIER (NEW)
* **Regla**: Decrease ATR Multiplier from 0.15 to 0.10.


## 41. ATR VOLATILITY FILTER AT TIME OF TAKE PROFIT (NEW)
* **Regla**: Immediately prior to closing the position at the Trailing Stop, ensure ATR(14) < ATR(14) on 4H * 0.10 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.10, delay closing the position until ATR(14) falls below ATR(14) on 4H * 0.10. This prevents the position from being closed prematurely due to high volatility.


## 42.ATR VOLATILITY FILTER WHILE TRAILING STOP ACTIVE (NEW)
* **Regla**: WHILE the Trailing Stop is active, ensure ATR(14) < ATR(14) on 4H * 0.10 on the 15M timeframe. If ATR(14) >= ATR(14) on 4H * 0.10, HOLD the Trailing Stop in its current position until ATR(14) falls below ATR(14) on 4H * 0.10. This prevents the Trailing Stop from being triggered prematurely due to high volatility.


## 43. ATR AND ADX CHECK AT TAKE PROFIT (NEW)
* **Regla**: Immediately prior to closing the position at the Trailing Stop, ensure that BOTH ATR(14) < ATR(14) on 4H * 0.10 AND ADX < 25 on the 15M timeframe. If EITHER condition is not met, delay closing the position until BOTH are met. This prevents the position from being closed prematurely due to high volatility and trending flow.

## 44. ATR AND ADX CHECK PRIOR TO TRAILING STOP MOVE (NEW)
* **Regla**: Immediately prior to MOVING the Trailing Stop, ensure that BOTH ATR(14) < ATR(14) on 4H * 0.10 AND ADX < 25 on the 15M timeframe. If EITHER condition is not met, delay MOVING the Trailing Stop until BOTH are met. This prevents the Trailing Stop from being triggered prematurely due to high volatility and trending flow.